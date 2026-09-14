from datetime import timedelta
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.contrib import auth
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from .models import SpotifyConnection, UserPreference
from .services.spotify import (
    SPOTIFY_SCOPES,
    SpotifyAuthService,
)


def make_token_response(
    access_token="new-access-token",
    refresh_token="new-refresh-token",
    expires_in=3600,
):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
    }
    return mock_response


def make_profile_response():
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "id": "spotify-user-1",
        "display_name": "Spotify User",
    }
    return mock_response


class SpotifyAuthServiceTests(TestCase):

    def _authorization_params(self):
        url = SpotifyAuthService.get_authorization_url()
        parsed = urlparse(url)
        return parse_qs(parsed.query)

    def test_authorization_url_includes_playlist_modify_private(self):
        with patch("users.services.spotify.settings.SPOTIFY_CLIENT_ID", "cid"):
            with patch(
                "users.services.spotify.settings.SPOTIFY_REDIRECT_URI",
                "http://localhost/callback",
            ):
                params = self._authorization_params()

        self.assertIn(
            "playlist-modify-private",
            params["scope"][0].split(),
        )

    def test_authorization_url_includes_playlist_modify_public(self):
        with patch("users.services.spotify.settings.SPOTIFY_CLIENT_ID", "cid"):
            with patch(
                "users.services.spotify.settings.SPOTIFY_REDIRECT_URI",
                "http://localhost/callback",
            ):
                params = self._authorization_params()

        self.assertIn(
            "playlist-modify-public",
            params["scope"][0].split(),
        )

    def test_authorization_url_preserves_existing_scopes(self):
        with patch("users.services.spotify.settings.SPOTIFY_CLIENT_ID", "cid"):
            with patch(
                "users.services.spotify.settings.SPOTIFY_REDIRECT_URI",
                "http://localhost/callback",
            ):
                params = self._authorization_params()

        scopes = params["scope"][0].split()
        for required_scope in (
            "user-read-private",
            "user-read-email",
            "user-top-read",
        ):
            self.assertIn(required_scope, scopes)

    def test_authorization_url_is_single_source_of_scopes(self):
        requested = parse_qs(
            urlparse(
                SpotifyAuthService.get_authorization_url()
            ).query
        )["scope"][0].split()

        self.assertEqual(sorted(requested), sorted(SPOTIFY_SCOPES))
        for scope in SPOTIFY_SCOPES:
            self.assertIn(scope, requested)

    def test_authorization_url_missing_client_id_raises(self):
        with patch("users.services.spotify.settings.SPOTIFY_CLIENT_ID", ""):
            with patch(
                "users.services.spotify.settings.SPOTIFY_REDIRECT_URI",
                "http://localhost/callback",
            ):
                with self.assertRaises(ValueError):
                    SpotifyAuthService.get_authorization_url()


class SpotifyLoginViewTests(TestCase):

    def setUp(self):
        self.login_url = reverse("spotify-login")

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_user_is_redirected_to_spotify_authorize(self):
        user = auth.get_user_model().objects.create_user(
            username="listener",
            password="pw12345",
        )
        self.client.force_login(user)

        with patch("users.services.spotify.settings.SPOTIFY_CLIENT_ID", "cid"):
            with patch(
                "users.services.spotify.settings.SPOTIFY_REDIRECT_URI",
                "http://localhost/callback",
            ):
                response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        parsed = urlparse(response.url)
        self.assertEqual(parsed.netloc, "accounts.spotify.com")
        params = parse_qs(parsed.query)
        scopes = params["scope"][0].split()
        self.assertIn("playlist-modify-private", scopes)
        self.assertIn("playlist-modify-public", scopes)


class SpotifyCallbackViewTests(TestCase):

    def setUp(self):
        self.user = auth.get_user_model().objects.create_user(
            username="listener",
            password="pw12345",
        )
        self.callback_url = reverse("spotify-callback")

    @staticmethod
    def _mock_spotify_exchange_and_profile():
        patch_post = patch(
            "users.services.spotify.requests.post",
            return_value=make_token_response(),
        )
        patch_get = patch(
            "music.services.spotify.requests.get",
            return_value=make_profile_response(),
        )
        return patch_post, patch_get

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(self.callback_url, {"code": "abc"})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/accounts/login/", response.url)

    def test_callback_missing_code_returns_error(self):
        self.client.force_login(self.user)

        response = self.client.get(self.callback_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_callback_creates_connection_for_authenticated_user(self):
        patch_post, patch_get = self._mock_spotify_exchange_and_profile()

        with patch_post, patch_get:
            self.client.force_login(self.user)
            response = self.client.get(
                self.callback_url,
                {"code": "auth-code"},
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["message"],
            "Spotify account connected successfully.",
        )

        connection = SpotifyConnection.objects.get(user=self.user)
        self.assertEqual(connection.spotify_account_id, "spotify-user-1")
        self.assertEqual(connection.access_token, "new-access-token")
        self.assertEqual(connection.refresh_token, "new-refresh-token")

    def test_callback_updates_existing_connection_for_same_user(self):
        SpotifyConnection.objects.create(
            user=self.user,
            spotify_account_id="old-spotify-id",
            access_token="old-access-token",
            refresh_token="old-refresh-token",
            token_expires_at=timezone.now() + timedelta(hours=1),
        )

        patch_post, patch_get = self._mock_spotify_exchange_and_profile()

        with patch_post, patch_get:
            self.client.force_login(self.user)
            response = self.client.get(
                self.callback_url,
                {"code": "auth-code"},
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SpotifyConnection.objects.count(), 1)
        connection = SpotifyConnection.objects.get(user=self.user)
        # Reauthorization keeps the connection bound to the same user.
        self.assertEqual(connection.user, self.user)
        self.assertEqual(connection.access_token, "new-access-token")
        self.assertEqual(connection.spotify_account_id, "spotify-user-1")

    def test_callback_stores_token_expiry(self):
        patch_post, patch_get = self._mock_spotify_exchange_and_profile()

        with patch_post, patch_get:
            self.client.force_login(self.user)
            response = self.client.get(
                self.callback_url,
                {"code": "auth-code"},
)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        connection = SpotifyConnection.objects.get(user=self.user)
        self.assertGreater(
            connection.token_expires_at,
            timezone.now(),
        )


class UserPreferenceApiTests(TestCase):

    def setUp(self):
        self.user_a = auth.get_user_model().objects.create_user(
            username="listener-a",
            password="pw12345",
        )
        self.user_b = auth.get_user_model().objects.create_user(
            username="listener-b",
            password="pw12345",
        )
        self.url = reverse("user-preferences")

    @staticmethod
    def _payload(**overrides):
        payload = {
            "favorite_genres": ["r&b", "jazz"],
            "preferred_eras": ["2010s", "2020s"],
            "default_mood": "chill",
            "discovery_style": "balanced",
            "recommendation_frequency": "weekly",
        }
        payload.update(overrides)
        return payload

    def _get(self, user=None):
        if user:
            self.client.force_login(user)
        return self.client.get(self.url, content_type="application/json")

    def _put(self, user, payload):
        self.client.force_login(user)
        return self.client.put(
            self.url,
            data=payload,
            content_type="application/json",
        )

    def test_authenticated_user_can_get_preferences(self):
        UserPreference.objects.create(
            user=self.user_a,
            favorite_genres=["r&b", "jazz"],
            preferred_eras=["2010s"],
            default_mood="chill",
            discovery_style="new",
            recommendation_frequency="weekly",
        )

        response = self._get(self.user_a)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["favorite_genres"], ["r&b", "jazz"])
        self.assertEqual(body["preferred_eras"], ["2010s"])
        self.assertEqual(body["default_mood"], "chill")
        self.assertEqual(body["discovery_style"], "new")
        self.assertEqual(body["recommendation_frequency"], "weekly")

    def test_unauthenticated_get_is_rejected(self):
        response = self._get()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_put_preferences(self):
        response = self._put(self.user_a, self._payload())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["favorite_genres"], ["r&b", "jazz"])
        self.assertEqual(body["preferred_eras"], ["2010s", "2020s"])
        self.assertEqual(body["default_mood"], "chill")
        self.assertEqual(body["discovery_style"], "balanced")
        self.assertEqual(body["recommendation_frequency"], "weekly")

    def test_updated_preferences_persist(self):
        self._put(self.user_a, self._payload())

        preference = UserPreference.objects.get(user=self.user_a)
        self.assertEqual(preference.favorite_genres, ["r&b", "jazz"])
        self.assertEqual(preference.preferred_eras, ["2010s", "2020s"])
        self.assertEqual(preference.default_mood, "chill")
        self.assertEqual(preference.discovery_style, "balanced")
        self.assertEqual(preference.recommendation_frequency, "weekly")

    def test_user_cannot_access_or_update_another_users_preferences(self):
        UserPreference.objects.create(
            user=self.user_b,
            default_mood="melancholic",
            discovery_style="familiar",
            recommendation_frequency="daily",
        )

        response = self._get(self.user_a)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["default_mood"], "")
        self.assertNotEqual(
            response.json()["default_mood"],
            "melancholic",
        )
        self.assertEqual(
            UserPreference.objects.get(user=self.user_a).favorite_genres,
            [],
        )

        self._put(self.user_a, self._payload())

        preference_b = UserPreference.objects.get(user=self.user_b)
        self.assertEqual(preference_b.default_mood, "melancholic")
        self.assertNotEqual(preference_b.default_mood, "chill")

    def test_invalid_discovery_style_is_rejected(self):
        response = self._put(
            self.user_a,
            self._payload(discovery_style="chaotic"),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            UserPreference.objects.filter(user=self.user_a).exists()
            and UserPreference.objects.get(
                user=self.user_a
            ).discovery_style
            == "chaotic",
        )

    def test_invalid_recommendation_frequency_is_rejected(self):
        response = self._put(
            self.user_a,
            self._payload(recommendation_frequency="hourly"),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_response_does_not_expose_user_field(self):
        self._put(self.user_a, self._payload())

        response = self._get(self.user_a)

        body = response.json()
        self.assertNotIn("user", body)
        self.assertNotIn("id", body)
        self.assertNotIn("created_at", body)
        self.assertNotIn("updated_at", body)
        self.assertEqual(
            set(body.keys()),
            {
                "favorite_genres",
                "preferred_eras",
                "default_mood",
                "discovery_style",
                "recommendation_frequency",
            },
        )

    def test_missing_preferences_are_created_with_defaults(self):
        response = self._get(self.user_a)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            UserPreference.objects.filter(user=self.user_a).exists(),
        )
        body = response.json()
        self.assertEqual(body["favorite_genres"], [])
        self.assertEqual(body["preferred_eras"], [])
        self.assertEqual(body["default_mood"], "")
        self.assertEqual(body["discovery_style"], "balanced")
        self.assertEqual(body["recommendation_frequency"], "on_demand")

    def test_put_replaces_intended_preference_values(self):
        self._put(
            self.user_a,
            self._payload(
                favorite_genres=["rock"],
                default_mood="happy",
                discovery_style="new",
                recommendation_frequency="daily",
            ),
        )

        response = self._put(self.user_a, self._payload())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["favorite_genres"], ["r&b", "jazz"])
        self.assertEqual(body["preferred_eras"], ["2010s", "2020s"])
        self.assertEqual(body["default_mood"], "chill")
        self.assertEqual(body["discovery_style"], "balanced")
        self.assertEqual(body["recommendation_frequency"], "weekly")
