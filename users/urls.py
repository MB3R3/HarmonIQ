from django.urls import path

from .views import UserPreferenceView
from .spotify_views import spotify_login, spotify_callback


urlpatterns = [
    path(
        "preferences/",
        UserPreferenceView.as_view(),
        name="user-preferences",
    ),
    path("spotify/login/", spotify_login, name="spotify-login"),
    path("spotify/callback/", spotify_callback, name="spotify-callback")
]