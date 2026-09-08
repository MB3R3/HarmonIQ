"""Thin HarmonIQ API over the Spotify service layer.

Views coordinate. Services do the work.
No Spotify URLs, headers, or HTTP details live here.
"""

from django.http import JsonResponse

from .services.spotify import SpotifyAPIError, SpotifyService


def _extract_token_from_header(request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):].strip()
        return token or None
    # Django < 2.2 / some clients use META directly
    meta_auth = request.META.get("HTTP_AUTHORIZATION", "")
    if meta_auth.startswith("Bearer "):
        token = meta_auth[len("Bearer "):].strip()
        return token or None
    return None


def get_spotify_service(request):
    """Resolve a SpotifyService for this request or return None.

    Priority:
      1. Authorization: Bearer <spotify_access_token> header (useful for React/testing)
      2. Django session set by users.spotify_callback
      3. Logged-in user's persisted SpotifyConnection
    """
    token = _extract_token_from_header(request)

    if not token:
        token = request.session.get("spotify_access_token")

    if not token and getattr(request, "user", None) and request.user.is_authenticated:
        connection = getattr(request.user, "spotify_connection", None)
        if connection is None:
            # Reverse OneToOne may raise if missing; handle gracefully.
            try:
                from django.core.exceptions import ObjectDoesNotExist  # noqa: F401
                connection = request.user.spotify_connection
            except Exception:
                connection = None
        if connection is not None:
            token = connection.access_token

    if not token:
        return None
    try:
        return SpotifyService(token)
    except ValueError:
        return None


def _require_spotify(request):
    spotify = get_spotify_service(request)
    if spotify is None:
        return None, JsonResponse(
            {
                "error": "Spotify not connected",
                "detail": (
                    "Authenticate via /api/users/spotify/login/ first, or "
                    "provide 'Authorization: Bearer <spotify_token>' header."
                ),
            },
            status=401,
        )
    return spotify, None


def _spotify_error_response(exc):
    status = getattr(exc, "status_code", None) or 502
    # Pass through Spotify 401/403/404/429 meaningfully, else 502.
    if status not in (400, 401, 403, 404, 429):
        status = 502
    return JsonResponse(
        {
            "error": "Spotify request failed",
            "detail": getattr(exc, "payload", None) or str(exc),
        },
        status=status,
    )


def _parse_limit(request, default=10, max_value=50):
    try:
        limit = int(request.GET.get("limit", default))
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, max_value))


def me(request):
    spotify, error = _require_spotify(request)
    if error:
        return error
    try:
        return JsonResponse(spotify.get_current_user())
    except SpotifyAPIError as exc:
        return _spotify_error_response(exc)


def search(request):
    spotify, error = _require_spotify(request)
    if error:
        return error
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse(
            {"error": "Missing required query param: ?q=..."},
            status=400,
        )
    search_type = request.GET.get("type", "track")
    limit = _parse_limit(request)
    try:
        return JsonResponse(spotify.search(query, search_type=search_type, limit=limit))
    except SpotifyAPIError as exc:
        return _spotify_error_response(exc)


def track_detail(request, spotify_id):
    spotify, error = _require_spotify(request)
    if error:
        return error
    try:
        return JsonResponse(spotify.get_track(spotify_id))
    except SpotifyAPIError as exc:
        return _spotify_error_response(exc)


def artist_detail(request, spotify_id):
    spotify, error = _require_spotify(request)
    if error:
        return error
    try:
        return JsonResponse(spotify.get_artist(spotify_id))
    except SpotifyAPIError as exc:
        return _spotify_error_response(exc)


def album_detail(request, spotify_id):
    spotify, error = _require_spotify(request)
    if error:
        return error
    try:
        return JsonResponse(spotify.get_album(spotify_id))
    except SpotifyAPIError as exc:
        return _spotify_error_response(exc)


def top_tracks(request):
    spotify, error = _require_spotify(request)
    if error:
        return error
    try:
        return JsonResponse(spotify.get_top_tracks(limit=_parse_limit(request)))
    except SpotifyAPIError as exc:
        return _spotify_error_response(exc)


def top_artists(request):
    spotify, error = _require_spotify(request)
    if error:
        return error
    try:
        return JsonResponse(spotify.get_top_artists(limit=_parse_limit(request)))
    except SpotifyAPIError as exc:
        return _spotify_error_response(exc)
