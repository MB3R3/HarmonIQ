from django.urls import path

from .spotify_views import (
    spotify_callback,
    spotify_login,
)


urlpatterns = [
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