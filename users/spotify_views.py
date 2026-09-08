from datetime import timedelta

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone

from .models import SpotifyConnection
from .services.spotify import SpotifyAuthService, SpotifyService


User = get_user_model()


def spotify_login(request):
    try:
        authorization_url = SpotifyAuthService.get_authorization_url()
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    return redirect(authorization_url)


def spotify_callback(request):

    code = request.GET.get("code")

    if not code:
        return JsonResponse(
            {"error": "Spotify authorization failed"},
            status=400,
        )

    token_data = SpotifyAuthService.exchange_code(code)

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data["expires_in"]

    spotify = SpotifyService(access_token)

    spotify_profile = spotify.get_current_user()

    spotify_account_id = spotify_profile["id"]

    username = (
        spotify_profile.get("display_name")
        or f"spotify_{spotify_account_id}"
    )

    user, _ = User.objects.get_or_create(
        username=username
    )

    SpotifyConnection.objects.update_or_create(
        user=user,
        defaults={
            "spotify_account_id": spotify_account_id,
            "access_token": access_token,
            "refresh_token": refresh_token or "",
            "token_expires_at": (
                timezone.now()
                + timedelta(seconds=expires_in)
            ),
        },
    )

    return JsonResponse({
        "message": "Spotify connection saved",
        "spotify_account_id": spotify_account_id,
        "display_name": spotify_profile.get("display_name"),
        "user_id": user.id,
    })