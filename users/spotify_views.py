from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta

import requests

from .models import SpotifyConnection
from .services.spotify import SpotifyAuthService


User = get_user_model()


def spotify_login(request):
    try:
        authorization_url = SpotifyAuthService.get_authorization_url()
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    return redirect(authorization_url)



def spotify_callback(request):

    # User denied access on Spotify side: ?error=access_denied
    spotify_error = request.GET.get("error")
    if spotify_error:
        return JsonResponse(
            {
                "error": "Spotify authorization failed",
                "detail": spotify_error,
            },
            status=400,
        )

    code = request.GET.get("code")

    if not code:
        return JsonResponse(
            {"error": "Spotify authorization failed"},
            status=400,
        )

    try:
        token_data = SpotifyAuthService.exchange_code(code)
    except requests.RequestException as exc:
        detail = "Failed to exchange code with Spotify"
        if exc.response is not None:
            try:
                detail = exc.response.json()
            except ValueError:
                detail = exc.response.text
        return JsonResponse(
            {"error": "Spotify authorization failed", "detail": detail},
            status=400,
        )

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        return JsonResponse(
            {
                "error": "Spotify authorization failed",
                "detail": token_data,
            },
            status=400,
        )

    return JsonResponse({
        "message": "Spotify authentication successful",
        "access_token_received": bool(access_token),
        "refresh_token_received": bool(refresh_token),
    })