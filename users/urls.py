from django.urls import path

from .csrf_views import csrf_token
from .spotify_views import (
    spotify_callback,
    spotify_login,
)


urlpatterns = [
    path(
        "csrf/",
        csrf_token,
        name="csrf-token",
    ),
    path(
        "spotify/login/",
        spotify_login,
        name="spotify-login",
    ),
    path(
        "spotify/callback/",
        spotify_callback,
        name="spotify-callback",
    ),
]