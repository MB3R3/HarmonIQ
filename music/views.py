from rest_framework import generics, permissions, status
from rest_framework.response import Response

from users.models import SpotifyConnection

from .models import SavedTrack
from .serializers import (
    CreateSpotifyPlaylistResponseSerializer,
    CreateSpotifyPlaylistSerializer,
    SavedTrackSerializer,
)
from .services.spotify import SpotifyAPIError, SpotifyService


class SavedTrackListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedTrackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedTrack.objects.filter(
            user=self.request.user
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        existing = SavedTrack.objects.filter(
            user=request.user,
            spotify_track_id=serializer.validated_data[
                "spotify_track_id"
            ],
        ).first()

        if existing is not None:
            response_serializer = self.get_serializer(
                existing
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(
            serializer.data
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SavedTrackDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = SavedTrackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedTrack.objects.filter(
            user=self.request.user
        )


def _get_user_spotify_connection(user):
    try:
        return user.spotify_connection
    except SpotifyConnection.DoesNotExist:
        return None


def _spotify_error_message(exc):
    """Best-effort safe detail from a Spotify error payload."""
    try:
        return exc.payload.get("error", {}).get("message", "")
    except AttributeError:
        return ""


def _spotify_error_status(exc):
    raw_status = getattr(exc, "status_code", None)
    # Pass through meaningful statuses, otherwise a generic 502.
    if raw_status in (400, 401, 403, 404, 429):
        return raw_status
    return status.HTTP_502_BAD_GATEWAY


def _friendly_spotify_error(exc):
    if getattr(exc, "status_code", None) == 401:
        return (
            "Your Spotify connection is invalid or expired. "
            "Reconnect your Spotify account."
        )
    if getattr(exc, "status_code", None) == 403:
        return (
            "HarmonIQ does not have permission to create or "
            "modify your playlists. Reconnect your Spotify account."
        )
    if getattr(exc, "status_code", None) == 429:
        return (
            "Spotify is temporarily rate-limited. "
            "Please try again shortly."
        )
    return (
        "Spotify could not complete this request. "
        "Please try again shortly."
    )


class CreateSpotifyPlaylistView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateSpotifyPlaylistSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        connection = _get_user_spotify_connection(request.user)
        if connection is None:
            return Response(
                {
                    "error": "Spotify not connected",
                    "detail": (
                        "Connect your Spotify account before "
                        "creating a playlist."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = connection.get_valid_access_token()
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        spotify = SpotifyService(access_token)

        try:
            playlist = spotify.create_playlist(
                name=data["name"],
                description=data.get("description", ""),
                public=data["public"],
            )
        except SpotifyAPIError as exc:
            return Response(
                {
                    "error": _friendly_spotify_error(exc),
                    "detail": _spotify_error_message(exc),
                },
                status=_spotify_error_status(exc),
            )

        playlist_id = playlist["id"]

        try:
            spotify.add_items_to_playlist(
                playlist_id,
                data["track_ids"],
            )
        except SpotifyAPIError as exc:
            return Response(
                {
                    "error": (
                        "The playlist was created on Spotify, but "
                        "adding the selected tracks failed. The "
                        "playlist is incomplete."
                    ),
                    "detail": _spotify_error_message(exc),
                    "playlist": {
                        "id": playlist_id,
                        "name": playlist.get("name", data["name"]),
                        "spotify_url": (
                            playlist.get("external_urls", {}).get(
                                "spotify", ""
                            )
                            or f"https://open.spotify.com/playlist/{playlist_id}"
                        ),
                        "public": bool(
                            playlist.get("public", data["public"])
                        ),
                        "track_count": 0,
                    },
                },
                status=_spotify_error_status(exc),
            )

        track_count = len(data["track_ids"])
        response_data = CreateSpotifyPlaylistResponseSerializer(
            data={
                "id": playlist_id,
                "name": playlist.get("name", data["name"]),
                "spotify_url": (
                    playlist.get("external_urls", {}).get("spotify", "")
                    or f"https://open.spotify.com/playlist/{playlist_id}"
                ),
                "public": bool(playlist.get("public", data["public"])),
                "track_count": track_count,
            }
        )
        response_data.is_valid(raise_exception=True)

        return Response(
            {"playlist": response_data.data},
            status=status.HTTP_201_CREATED,
        )