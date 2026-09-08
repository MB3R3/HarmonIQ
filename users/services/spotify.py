import requests

from django.conf import settings
from urllib.parse import urlencode

# Re-export so views can do:
#   from .services.spotify import SpotifyAuthService, SpotifyService
# Canonical implementation lives in music/services/spotify.py.
from music.services.spotify import SpotifyAPIError, SpotifyService  # noqa: F401


SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyAuthService:

    @staticmethod
    def get_authorization_url():

        params = {
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "scope": "user-read-private user-read-email user-top-read",
        }

        if not params["client_id"] or not params["redirect_uri"]:
            raise ValueError(
                "Missing SPOTIFY_CLIENT_ID or SPOTIFY_REDIRECT_URI. Check your .env and config/settings.py."
            )

        return f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}"
    

    @staticmethod
    def exchange_code(code):

        response = requests.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
                "client_id": settings.SPOTIFY_CLIENT_ID,
                "client_secret": settings.SPOTIFY_CLIENT_SECRET,
            },
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    @staticmethod
    def refresh_access_token(refresh_token):
        """Exchange a refresh token for a new access token."""

        response = requests.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.SPOTIFY_CLIENT_ID,
                "client_secret": settings.SPOTIFY_CLIENT_SECRET,
            },
            timeout=10,
        )

        response.raise_for_status()

        return response.json()