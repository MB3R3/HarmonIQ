import requests

from django.conf import settings
from urllib.parse import urlencode


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
                "Missing SPOTIFY_CLIENT_ID or SPOTIFY_REDIRECT_URI. heck your .env and config/settings.py."
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