from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from requests import HTTPError

from .models import SpotifyConnection
from .services.spotify import (
    SpotifyAPIError,
    SpotifyAuthService,
    SpotifyService,
)


@login_required
def spotify_login(request):
    try:
        authorization_url = (
            SpotifyAuthService.get_authorization_url()
        )
    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=500,
        )

    return redirect(authorization_url)


@login_required
def spotify_callback(request):
    code = request.GET.get("code")

    if not code:
        return JsonResponse(
            {"error": "Spotify authorization failed"},
            status=400,
        )

    try:
        token_data = SpotifyAuthService.exchange_code(code)
    except HTTPError as exc:
        return JsonResponse(
            {
                "error": (
                    "Failed to exchange Spotify "
                    "authorization code"
                ),
                "detail": str(exc),
            },
            status=502,
        )

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data["expires_in"]

    spotify = SpotifyService(access_token)

    try:
        spotify_profile = spotify.get_current_user()
    except SpotifyAPIError as exc:
        return JsonResponse(
            {
                "error": "Failed to fetch Spotify profile",
                "detail": str(exc),
            },
            status=502,
        )

    spotify_account_id = (
        spotify_profile.get("account_id")
        or spotify_profile.get("id")
    )

    if not spotify_account_id:
        return JsonResponse(
            {
                "error": (
                    "Spotify account identifier "
                    "was not returned."
                )
            },
            status=502,
        )

    SpotifyConnection.objects.update_or_create(
        user=request.user,
        defaults={
            "spotify_account_id": spotify_account_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": (
                timezone.now()
                + timedelta(seconds=expires_in)
            ),
        },
    )

    return JsonResponse(
        {
            "message": "Spotify account connected successfully.",
            "spotify_account_id": spotify_account_id,
        }
    )