from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from users.models import SpotifyConnection

from .models import SavedTrack


def make_saved_track(
    user,
    spotify_track_id="track-1",
    track_name="Nights",
    artist_name="Frank Ocean",
    album_name="Blonde",
    artwork_url="https://example.com/artwork.jpg",
):
    return SavedTrack.objects.create(
        user=user,
        spotify_track_id=spotify_track_id,
        track_name=track_name,
        artist_name=artist_name,
        album_name=album_name,
        artwork_url=artwork_url,
    )


class SavedTrackApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="saver",
            password="pw12345",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other",
            password="pw12345",
        )
        self.list_url = reverse("saved-tracks")
        self.track_payload = {
            "spotify_track_id": "track-1",
            "track_name": "Nights",
            "artist_name": "Frank Ocean",
            "album_name": "Blonde",
            "artwork_url": "https://example.com/artwork.jpg",
        }

    def test_authenticated_user_can_save_a_track(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.list_url,
            self.track_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SavedTrack.objects.count(), 1)
        self.assertEqual(
            response.data["spotify_track_id"],
            "track-1",
        )

    def test_saved_track_is_associated_with_correct_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.list_url,
            self.track_payload,
            format="json",
        )

        saved = SavedTrack.objects.get(pk=response.data["id"])
        self.assertEqual(saved.user, self.user)
        self.assertNotEqual(saved.user, self.other_user)

    def test_same_user_cannot_create_duplicate_saved_tracks(self):
        self.client.force_authenticate(user=self.user)

        first = self.client.post(
            self.list_url,
            self.track_payload,
            format="json",
        )
        second = self.client.post(
            self.list_url,
            self.track_payload,
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(SavedTrack.objects.count(), 1)
        self.assertEqual(second.data["id"], first.data["id"])

    def test_user_can_list_their_own_saved_tracks(self):
        make_saved_track(self.user, spotify_track_id="track-1")
        make_saved_track(self.user, spotify_track_id="track-2")
        make_saved_track(self.other_user, spotify_track_id="track-3")

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        ids = {item["spotify_track_id"] for item in response.data}
        self.assertEqual(ids, {"track-1", "track-2"})

    def test_user_cannot_see_another_users_saved_tracks(self):
        make_saved_track(self.user, spotify_track_id="track-1")
        make_saved_track(self.other_user, spotify_track_id="track-2")

        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["spotify_track_id"],
            "track-2",
        )

    def test_user_can_delete_their_own_saved_track(self):
        saved = make_saved_track(
            self.user,
            spotify_track_id="track-1",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            reverse("saved-track", args=[saved.pk])
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(SavedTrack.objects.count(), 0)

    def test_user_cannot_delete_another_users_saved_track(self):
        saved = make_saved_track(
            self.user,
            spotify_track_id="track-1",
        )
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            reverse("saved-track", args=[saved.pk])
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(SavedTrack.objects.count(), 1)

    def test_unauthenticated_access_is_rejected(self):
        response = self.client.get(self.list_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        response = self.client.post(
            self.list_url,
            self.track_payload,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unauthenticated_delete_is_rejected(self):
        saved = make_saved_track(
            self.user,
            spotify_track_id="track-1",
        )

        response = self.client.delete(
            reverse("saved-track", args=[saved.pk])
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(SavedTrack.objects.count(), 1)

    def test_required_fields_are_validated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.list_url,
            {"spotify_track_id": "track-1"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(SavedTrack.objects.count(), 0)

    def test_track_can_be_saved_without_artwork(self):
        self.client.force_authenticate(user=self.user)

        payload = dict(self.track_payload)
        payload["artwork_url"] = ""

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["artwork_url"], "")


def make_spotify_playlist_response(
    playlist_id="pl-1",
    name="Chill",
    public=False,
):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": playlist_id,
        "name": name,
        "public": public,
        "external_urls": {
            "spotify": f"https://open.spotify.com/playlist/{playlist_id}",
        },
        "tracks": {"total": 3},
    }
    return mock_response


def make_spotify_items_response():
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 201
    mock_response.json.return_value = {"snapshot_id": "snap-1"}
    return mock_response


def make_spotify_error_response(status_code, message="nope"):
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = status_code
    mock_response.json.return_value = {
        "error": {"status": status_code, "message": message},
    }
    return mock_response


def make_spotify_token_response(access_token="refreshed-token"):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "access_token": access_token,
        "expires_in": 3600,
    }
    return mock_response


def make_spotify_connection(user, token="access-token", account_id="spotify-user-1"):
    return SpotifyConnection.objects.create(
        user=user,
        spotify_account_id=account_id,
        access_token=token,
        refresh_token="refresh-token",
        token_expires_at=timezone.now() + timedelta(hours=1),
    )


class CreateSpotifyPlaylistTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="creator",
            password="pw12345",
        )
        self.create_url = reverse("create-spotify-playlist")
        self.track_a = "a" * 22
        self.track_b = "b" * 22
        self.payload = {
            "name": "HarmonIQ — Chill R&B",
            "description": "A playlist created from my HarmonIQ discoveries.",
            "public": False,
            "track_ids": [self.track_a, self.track_b],
        }

    def test_authenticated_user_with_connection_can_create_playlist(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()

        with patch(
            "music.services.spotify.requests.post",
            Mock(side_effect=[create_resp, items_resp]),
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["playlist"]["id"], "pl-1")

    def test_correct_spotify_endpoint_is_called(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()
        mock_post = Mock(side_effect=[create_resp, items_resp])

        with patch("music.services.spotify.requests.post", mock_post):
            self.client.post(self.create_url, self.payload, format="json")

        calls = mock_post.call_args_list
        self.assertEqual(
            calls[0].args[0],
            "https://api.spotify.com/v1/me/playlists",
        )
        self.assertEqual(
            calls[1].args[0],
            "https://api.spotify.com/v1/playlists/pl-1/items",
        )

    def test_playlist_creation_receives_name_description_public(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()
        mock_post = Mock(side_effect=[create_resp, items_resp])

        with patch("music.services.spotify.requests.post", mock_post):
            self.client.post(self.create_url, self.payload, format="json")

        create_payload = mock_post.call_args_list[0].kwargs["json"]
        self.assertEqual(
            create_payload["name"],
            "HarmonIQ — Chill R&B",
        )
        self.assertEqual(
            create_payload["description"],
            "A playlist created from my HarmonIQ discoveries.",
        )
        self.assertFalse(create_payload["public"])

    def test_public_flag_is_respected_when_true(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        payload = dict(self.payload)
        payload["public"] = True

        create_resp = make_spotify_playlist_response(public=True)
        items_resp = make_spotify_items_response()
        mock_post = Mock(side_effect=[create_resp, items_resp])

        with patch("music.services.spotify.requests.post", mock_post):
            response = self.client.post(
                self.create_url,
                payload,
                format="json",
            )

        self.assertTrue(
            mock_post.call_args_list[0].kwargs["json"]["public"]
        )
        self.assertTrue(response.data["playlist"]["public"])

    def test_public_defaults_to_false(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        payload = {
            "name": "Default Privacy",
            "track_ids": [self.track_a],
        }

        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()
        mock_post = Mock(side_effect=[create_resp, items_resp])

        with patch("music.services.spotify.requests.post", mock_post):
            response = self.client.post(
                self.create_url,
                payload,
                format="json",
            )

        self.assertFalse(
            mock_post.call_args_list[0].kwargs["json"]["public"]
        )
        self.assertFalse(response.data["playlist"]["public"])

    def test_tracks_are_converted_to_spotify_uris(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()
        mock_post = Mock(side_effect=[create_resp, items_resp])

        with patch("music.services.spotify.requests.post", mock_post):
            self.client.post(self.create_url, self.payload, format="json")

        items_payload = mock_post.call_args_list[1].kwargs["json"]
        self.assertEqual(
            items_payload["uris"],
            [
                f"spotify:track:{self.track_a}",
                f"spotify:track:{self.track_b}",
            ],
        )

    def test_authorization_header_uses_user_token(self):
        make_spotify_connection(self.user, token="user-access-token")
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()
        mock_post = Mock(side_effect=[create_resp, items_resp])

        with patch("music.services.spotify.requests.post", mock_post):
            self.client.post(self.create_url, self.payload, format="json")

        auth_header = (
            mock_post.call_args_list[0].kwargs["headers"]["Authorization"]
        )
        self.assertEqual(auth_header, "Bearer user-access-token")

    def test_duplicate_track_ids_are_removed(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        payload = dict(self.payload)
        payload["track_ids"] = [self.track_a, self.track_a, self.track_b]

        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()
        mock_post = Mock(side_effect=[create_resp, items_resp])

        with patch("music.services.spotify.requests.post", mock_post):
            response = self.client.post(
                self.create_url,
                payload,
                format="json",
            )

        items_payload = mock_post.call_args_list[1].kwargs["json"]
        self.assertEqual(items_payload["uris"], [
            f"spotify:track:{self.track_a}",
            f"spotify:track:{self.track_b}",
        ])
        self.assertEqual(response.data["playlist"]["track_count"], 2)

    def test_tracks_are_batched_in_playlist_item_requests(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        track_ids = [f"{i:022d}" for i in range(250)]
        payload = dict(self.payload)
        payload["track_ids"] = track_ids

        create_resp = make_spotify_playlist_response()
        items_responses = [
            make_spotify_items_response()
            for _ in range(3)
        ]
        mock_post = Mock(
            side_effect=[create_resp, *items_responses]
        )

        with patch("music.services.spotify.requests.post", mock_post):
            response = self.client.post(
                self.create_url,
                payload,
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 100 + 100 + 50 split.
        items_calls = mock_post.call_args_list[1:]
        self.assertEqual(len(items_calls), 3)
        self.assertEqual(
            len(items_calls[0].kwargs["json"]["uris"]),
            100,
        )
        self.assertEqual(
            len(items_calls[2].kwargs["json"]["uris"]),
            50,
        )
        self.assertEqual(
            response.data["playlist"]["track_count"],
            250,
        )

    def test_empty_track_list_is_rejected(self):
        self.client.force_authenticate(user=self.user)
        payload = dict(self.payload)
        payload["track_ids"] = []

        response = self.client.post(
            self.create_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_track_ids_is_rejected(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url,
            {"name": "No Tracks"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_name_is_rejected(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url,
            {"track_ids": [self.track_a]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_name_is_rejected(self):
        self.client.force_authenticate(user=self.user)

        payload = dict(self.payload)
        payload["name"] = " "

        response = self.client.post(
            self.create_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_urls_are_not_accepted_as_track_ids(self):
        self.client.force_authenticate(user=self.user)

        payload = dict(self.payload)
        payload["track_ids"] = [
            "https://open.spotify.com/track/abc123",
        ]

        response = self.client.post(
            self.create_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_is_rejected(self):
        response = self.client.post(
            self.create_url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_spotify_connection_gets_error(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Spotify not connected", response.data["error"])

    def test_expired_token_is_refreshed_via_connection(self):
        connection = make_spotify_connection(self.user, token="old-token")
        connection.token_expires_at = timezone.now() - timedelta(hours=1)
        connection.save(update_fields=["token_expires_at"])
        self.client.force_authenticate(user=self.user)

        refresh_resp = make_spotify_token_response()
        create_resp = make_spotify_playlist_response()
        items_resp = make_spotify_items_response()

        token_url = "https://accounts.spotify.com/api/token"
        create_url = "https://api.spotify.com/v1/me/playlists"

        def dispatch_post(request_url, *args, **kwargs):
            if request_url == token_url:
                return refresh_resp
            if request_url == create_url:
                return create_resp
            return items_resp

        with patch(
            "music.services.spotify.requests.post",
            side_effect=dispatch_post,
        ) as mock_music_post:
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(mock_music_post.call_count, 3)
        auth_header = (
            mock_music_post.call_args_list[1].kwargs["headers"]["Authorization"]
        )
        self.assertEqual(auth_header, "Bearer refreshed-token")
        connection.refresh_from_db()
        self.assertEqual(connection.access_token, "refreshed-token")

    def test_spotify_401_is_handled_cleanly(self):
        make_spotify_connection(self.user, token="TOKEN-SECRET-123")
        self.client.force_authenticate(user=self.user)

        err_resp = make_spotify_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "The access token expired",
        )

        with patch(
            "music.services.spotify.requests.post",
            return_value=err_resp,
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("expired", response.data["error"])
        self.assertNotIn(
            "TOKEN-SECRET-123",
            response.content.decode(),
        )

    def test_spotify_403_is_handled_cleanly(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        err_resp = make_spotify_error_response(
            status.HTTP_403_FORBIDDEN,
            "Insufficient scopes",
        )

        with patch(
            "music.services.spotify.requests.post",
            return_value=err_resp,
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("permission", response.data["error"])
        self.assertIn(
            "Insufficient scopes",
            response.data["detail"],
        )

    def test_spotify_429_is_handled_cleanly(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        err_resp = make_spotify_error_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Slow down",
        )

        with patch(
            "music.services.spotify.requests.post",
            return_value=err_resp,
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
        self.assertIn("rate", response.data["error"])

    def test_spotify_5xx_is_mapped_to_502(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        err_resp = make_spotify_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal error",
        )

        with patch(
            "music.services.spotify.requests.post",
            return_value=err_resp,
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )

    def test_spotify_errors_do_not_expose_tokens_or_secrets(self):
        make_spotify_connection(
            self.user,
            token="super-secret-access-token",
        )
        self.client.force_authenticate(user=self.user)

        err_resp = make_spotify_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "boom",
        )

        with patch(
            "music.services.spotify.requests.post",
            return_value=err_resp,
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        content = response.content.decode()
        self.assertNotIn("super-secret-access-token", content)
        self.assertNotIn("refresh-token", content)
        self.assertNotIn("Bearer", content)

    def test_response_contains_expected_playlist_fields(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response(name="Chill")
        items_resp = make_spotify_items_response()

        with patch(
            "music.services.spotify.requests.post",
            Mock(side_effect=[create_resp, items_resp]),
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        playlist = response.data["playlist"]
        self.assertEqual(playlist["id"], "pl-1")
        self.assertEqual(playlist["name"], "Chill")
        self.assertEqual(
            playlist["spotify_url"],
            "https://open.spotify.com/playlist/pl-1",
        )
        self.assertFalse(playlist["public"])
        self.assertEqual(playlist["track_count"], 2)

    def test_spotify_url_uses_playlist_external_url(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response(
            playlist_id="pl-42",
            name="Chill",
        )
        items_resp = make_spotify_items_response()

        with patch(
            "music.services.spotify.requests.post",
            Mock(side_effect=[create_resp, items_resp]),
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(
            response.data["playlist"]["spotify_url"],
            "https://open.spotify.com/playlist/pl-42",
        )

    def test_add_items_failure_returns_incomplete_error(self):
        make_spotify_connection(self.user)
        self.client.force_authenticate(user=self.user)

        create_resp = make_spotify_playlist_response()
        err_resp = make_spotify_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "boom",
        )

        with patch(
            "music.services.spotify.requests.post",
            Mock(side_effect=[create_resp, err_resp]),
        ):
            response = self.client.post(
                self.create_url,
                self.payload,
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )
        self.assertIn("incomplete", response.data["error"])
        self.assertEqual(response.data["playlist"]["id"], "pl-1")
        self.assertEqual(response.data["playlist"]["track_count"], 0)