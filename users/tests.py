from datetime import timedelta
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.conf import settings
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

        # The browser is bounced back to the HarmonIQ frontend so the SPA
        # can refresh authentication state after connecting.
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response.url,
            f"{settings.FRONTEND_URL}/#/discover",
        )

        connection = SpotifyConnection.objects.get(user=self.user)
        self.assertEqual(connection.spotify_account_id, "spotify-user-1")
        self.assertEqual(
            connection.spotify_display_name,
            "Spotify User",
        )
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

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
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

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        connection = SpotifyConnection.objects.get(user=self.user)
        self.assertGreater(
            connection.token_expires_at,
            timezone.now(),
        )

    def test_callback_does_not_change_the_django_username(self):
        patch_post, patch_get = self._mock_spotify_exchange_and_profile()

        with patch_post, patch_get:
            self.client.force_login(self.user)
            self.client.get(
                self.callback_url,
                {"code": "auth-code"},
            )

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "listener")


class SpotifySharedAccountRegressionTests(TestCase):
    """Regression: a Spotify account id must not be globally unique.

    The Spotify callback keys every connection by ``user`` (one HarmonIQ
    account, one Spotify connection). Before the fix an extra ``UNIQUE`` on
    ``spotify_account_id`` meant a SECOND HarmonIQ user could never connect
    the same Spotify account once any other user had connected it; the
    ``update_or_create`` in the callback raised IntegrityError.
    """

    def setUp(self):
        self.user_a = auth.get_user_model().objects.create_user(
            username="listener-a",
            password="pw12345",
        )
        self.user_b = auth.get_user_model().objects.create_user(
            username="listener-b",
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

    def _connect(self, user):
        patch_post, patch_get = self._mock_spotify_exchange_and_profile()
        with patch_post, patch_get:
            self.client.force_login(user)
            return self.client.get(
                self.callback_url,
                {"code": "auth-code"},
            )

    def test_two_django_users_can_connect_the_same_spotify_account(self):
        # Both users receive the same Spotify profile from the fixture, so
        # this exercises the exact collision the old unique constraint
        # rejected with an IntegrityError on the second connect.
        first = self._connect(self.user_a)
        second = self._connect(self.user_b)

        self.assertEqual(first.status_code, status.HTTP_302_FOUND)
        self.assertEqual(second.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            SpotifyConnection.objects.get(user=self.user_a).spotify_account_id,
            "spotify-user-1",
        )
        self.assertEqual(
            SpotifyConnection.objects.get(user=self.user_b).spotify_account_id,
            "spotify-user-1",
        )

    def test_reconnecting_annotated_by_user_not_account_id(self):
        self._connect(self.user_a)

        self._connect(self.user_a)

        # Reconnecting overwrites the first user's row in place; it must
        # never leak over to the other user's connection.
        self.assertEqual(
            SpotifyConnection.objects.filter(user=self.user_a).count(),
            1,
        )
        self.assertFalse(
            SpotifyConnection.objects.filter(user=self.user_b).exists(),
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

    def _delete(self, user):
        self.client.force_login(user)
        return self.client.delete(
            self.url,
            content_type="application/json",
        )

    def test_clear_preferences_resets_to_defaults(self):
        self._put(self.user_a, self._payload())

        response = self._delete(self.user_a)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["favorite_genres"], [])
        self.assertEqual(body["preferred_eras"], [])
        self.assertEqual(body["default_mood"], "")
        self.assertEqual(body["discovery_style"], "balanced")
        self.assertEqual(body["recommendation_frequency"], "on_demand")

    def test_cleared_preferences_persist_as_defaults(self):
        self._put(self.user_a, self._payload())
        self._delete(self.user_a)

        response = self.client.get(self.url)
        body = response.json()
        self.assertEqual(body["favorite_genres"], [])
        self.assertEqual(body["preferred_eras"], [])
        self.assertEqual(body["default_mood"], "")
        self.assertEqual(body["discovery_style"], "balanced")
        self.assertEqual(body["recommendation_frequency"], "on_demand")

    def test_clear_preferences_keeps_preference_record(self):
        self._put(self.user_a, self._payload())
        self._delete(self.user_a)

        self.assertTrue(
            UserPreference.objects.filter(user=self.user_a).exists()
        )

    def test_clear_preferences_does_not_delete_the_account(self):
        self._put(self.user_a, self._payload())

        response = self._delete(self.user_a)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            auth.get_user_model().objects.filter(pk=self.user_a.pk).exists()
        )

    def test_clear_preferences_does_not_touch_spotify_connection(self):
        SpotifyConnection.objects.create(
            user=self.user_a,
            spotify_account_id="spotify-user-1",
            spotify_display_name="Essien Mbereidem",
            access_token="access",
            refresh_token="refresh",
            token_expires_at=timezone.now() + timedelta(hours=1),
        )
        self._put(self.user_a, self._payload())

        response = self._delete(self.user_a)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        connection = SpotifyConnection.objects.get(user=self.user_a)
        self.assertEqual(connection.spotify_account_id, "spotify-user-1")
        self.assertEqual(
            connection.spotify_display_name,
            "Essien Mbereidem",
        )

    def test_clear_preferences_only_affects_the_owning_user(self):
        self._put(self.user_a, self._payload())
        self._put(
            self.user_b,
            self._payload(
                favorite_genres=["rock"],
                default_mood="happy",
            ),
        )

        self._delete(self.user_a)

        preference_b = UserPreference.objects.get(user=self.user_b)
        self.assertEqual(preference_b.favorite_genres, ["rock"])
        self.assertEqual(preference_b.default_mood, "happy")

    def test_unauthenticated_clear_preferences_is_rejected(self):
        response = self.client.delete(
            self.url,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SignupApiTests(TestCase):

    def setUp(self):
        self.url = reverse("signup")

    @staticmethod
    def _payload(**overrides):
        payload = {
            "username": "essien",
            "email": "essien@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        payload.update(overrides)
        return payload

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

    def test_successful_signup_creates_user_and_session(self):
        response = self._post(self._payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["user"]["username"], "essien")
        self.assertEqual(
            body["user"]["email"],
            "essien@example.com",
        )

        User = auth.get_user_model()
        user = User.objects.get(username="essien")
        self.assertEqual(user.email, "essien@example.com")
        self.assertTrue(user.check_password("SecurePass123!"))

        # The session is established — /api/users/me/ sees the new user.
        me_response = self.client.get(reverse("current-user"))
        self.assertTrue(me_response.json()["authenticated"])
        self.assertEqual(me_response.json()["user"]["username"], "essien")

    def test_signup_hashes_the_password(self):
        self._post(self._payload())

        user = auth.get_user_model().objects.get(username="essien")
        self.assertNotEqual(user.password, "SecurePass123!")
        self.assertTrue(user.password.startswith(("pbkdf2_", "argon2")))

    def test_signup_response_never_returns_the_password(self):
        response = self._post(self._payload())

        self.assertNotIn("password", str(response.json()))
        self.assertNotIn("password_confirm", str(response.json()))

    def test_duplicate_username_is_rejected(self):
        auth.get_user_model().objects.create_user(
            username="essien",
            password="OtherPass123!",
            email="other@example.com",
        )

        response = self._post(self._payload())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["authenticated"])
        self.assertIn("username is already taken", response.json()["error"])
        self.assertEqual(
            auth.get_user_model().objects.filter(
                username="essien"
            ).count(),
            1,
        )

    def test_duplicate_email_is_rejected_case_insensitively(self):
        auth.get_user_model().objects.create_user(
            username="someone-else",
            password="OtherPass123!",
            email="ESSIEN@EXAMPLE.COM",
        )

        response = self._post(self._payload())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email already exists", response.json()["error"])

        User = auth.get_user_model()
        self.assertFalse(User.objects.filter(username="essien").exists())

    def test_password_confirmation_mismatch_is_rejected(self):
        response = self._post(
            self._payload(password_confirm="DifferentPass123!")
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("do not match", response.json()["error"])
        self.assertFalse(
            auth.get_user_model()
            .objects.filter(username="essien")
            .exists()
        )

    def test_missing_password_confirmation_is_rejected(self):
        response = self._post(
            self._payload(password_confirm="")
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(auth.get_user_model().objects.filter(
            username="essien"
        ).exists())

    def test_missing_required_fields_are_rejected(self):
        for key in ("username", "email", "password"):
            payload = self._payload()
            payload.pop(key)
            response = self._post(payload)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"expected {key} to be required",
            )
            self.assertFalse(response.json()["authenticated"])

    def test_invalid_email_is_rejected(self):
        response = self._post(self._payload(email="not-an-email"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valid email", response.json()["error"])
        self.assertFalse(
            auth.get_user_model()
            .objects.filter(username="essien")
            .exists()
        )

    def test_unauthenticated_signup_is_allowed(self):
        # No force_login here — anyone may create an account.
        response = self._post(self._payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["authenticated"])

    def test_weak_password_is_rejected(self):
        response = self._post(self._payload(password="12345", password_confirm="12345"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["authenticated"])
        self.assertFalse(
            auth.get_user_model()
            .objects.filter(username="essien")
            .exists()
        )

    def test_signup_username_is_independent_of_spotify_identity(self):
        response = self._post(self._payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # New accounts have no Spotify identity yet.
        body = response.json()["user"]
        self.assertFalse(body["spotify_connected"])
        self.assertIsNone(body["spotify_display_name"])
        self.assertEqual(body["username"], "essien")


class LogoutApiTests(TestCase):

    def setUp(self):
        self.user = auth.get_user_model().objects.create_user(
            username="listener",
            password="pw12345",
            email="listener@example.com",
        )
        self.url = reverse("logout")

    def test_logout_ends_the_django_session(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertFalse(body["authenticated"])
        self.assertIsNone(body["user"])

        me_response = self.client.get(reverse("current-user"))
        me_body = me_response.json()
        self.assertFalse(me_body["authenticated"])
        self.assertIsNone(me_body["user"])

    def test_logout_of_an_anonymous_session_is_harmless(self):
        response = self.client.post(
            self.url,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertFalse(body["authenticated"])
        self.assertIsNone(body["user"])

    def test_logout_response_contains_no_user_data(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url)

        self.assertEqual(response.json()["user"], None)


class LoginApiTests(TestCase):

    def setUp(self):
        self.user = auth.get_user_model().objects.create_user(
            username="listener",
            password="pw12345",
            email="listener@example.com",
        )
        self.url = reverse("login")

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

    def test_valid_credentials_start_a_session(self):
        response = self._post(
            {"username": "listener", "password": "pw12345"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["user"]["username"], "listener")
        self.assertEqual(body["user"]["email"], "listener@example.com")

        me_response = self.client.get(reverse("current-user"))
        self.assertTrue(me_response.json()["authenticated"])

    def test_invalid_credentials_return_401(self):
        response = self._post(
            {"username": "listener", "password": "wrong-password"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        body = response.json()
        self.assertFalse(body["authenticated"])
        self.assertEqual(body["error"], "Invalid username or password.")

        me_response = self.client.get(reverse("current-user"))
        self.assertFalse(me_response.json()["authenticated"])

    def test_unknown_username_returns_401(self):
        response = self._post(
            {"username": "nobody", "password": "pw12345"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()["authenticated"])

    def test_missing_credentials_return_400(self):
        response = self._post({"username": "listener"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["authenticated"])

        response = self._post({"password": "pw12345"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["authenticated"])

    def test_login_marks_spotify_connected(self):
        SpotifyConnection.objects.create(
            user=self.user,
            spotify_account_id="spotify-user-1",
            access_token="access",
            refresh_token="refresh",
            token_expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self._post(
            {"username": "listener", "password": "pw12345"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["user"]["spotify_connected"])

    def test_login_response_never_exposes_password(self):
        response = self._post(
            {"username": "listener", "password": "pw12345"}
        )

        self.assertEqual(
            set(response.json()["user"].keys()),
            {
                "id",
                "username",
                "email",
                "spotify_connected",
                "spotify_display_name",
            },
        )


class CurrentUserApiTests(TestCase):

    def setUp(self):
        self.user = auth.get_user_model().objects.create_user(
            username="listener",
            password="pw12345",
            email="listener@example.com",
        )
        self.url = reverse("current-user")

    def test_authenticated_user_gets_safe_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(
            self.url,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["user"]["id"], self.user.pk)
        self.assertEqual(body["user"]["username"], "listener")
        self.assertEqual(body["user"]["email"], "listener@example.com")

    def test_authenticated_response_never_exposes_password(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(
            set(response.json()["user"].keys()),
            {
                "id",
                "username",
                "email",
                "spotify_connected",
                "spotify_display_name",
            },
        )

    def test_unauthenticated_user_gets_false_status(self):
        response = self.client.get(
            self.url,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertFalse(body["authenticated"])
        self.assertIsNone(body["user"])

    def test_spotify_connected_is_false_without_connection(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertTrue(response.json()["authenticated"])
        self.assertFalse(response.json()["user"]["spotify_connected"])

    def test_spotify_connected_is_true_with_connection(self):
        SpotifyConnection.objects.create(
            user=self.user,
            spotify_account_id="spotify-user-1",
            access_token="access",
            refresh_token="refresh",
            token_expires_at=timezone.now() + timedelta(hours=1),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertTrue(response.json()["authenticated"])
        self.assertTrue(response.json()["user"]["spotify_connected"])

    def test_spotify_display_name_is_null_without_connection(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertIsNone(
            response.json()["user"]["spotify_display_name"]
        )

    def test_spotify_display_name_uses_spotify_identity_not_username(self):
        SpotifyConnection.objects.create(
            user=self.user,
            spotify_account_id="spotify-user-1",
            spotify_display_name="Essien Mbereidem",
            access_token="access",
            refresh_token="refresh",
            token_expires_at=timezone.now() + timedelta(hours=1),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        body = response.json()["user"]
        # The Django username is untouched; the Spotify display name is a
        # separate identity exposed alongside it.
        self.assertEqual(body["username"], "listener")
        self.assertEqual(
            body["spotify_display_name"],
            "Essien Mbereidem",
        )

    def test_profile_never_exposes_spotify_tokens(self):
        SpotifyConnection.objects.create(
            user=self.user,
            spotify_account_id="spotify-user-1",
            access_token="super-secret-access",
            refresh_token="super-secret-refresh",
            token_expires_at=timezone.now() + timedelta(hours=1),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertNotIn("access_token", str(response.json()))
        self.assertNotIn("refresh_token", str(response.json()))

    def test_each_user_sees_their_own_profile(self):
        other = auth.get_user_model().objects.create_user(
            username="other",
            password="pw12345",
            email="other@example.com",
        )
        self.client.force_login(other)

        response = self.client.get(self.url)

        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["user"]["username"], "other")
        self.assertEqual(response.json()["user"]["email"], "other@example.com")
