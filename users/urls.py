from django.urls import path

from .csrf_views import csrf_token
from .spotify_views import (
    spotify_callback,
    spotify_login,
)
from .views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    SignupView,
    UserPreferenceView,
)


urlpatterns = [
    path(
        "csrf/",
        csrf_token,
        name="csrf-token",
    ),
    path(
        "signup/",
        SignupView.as_view(),
        name="signup",
    ),
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
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
    path(
        "preferences/",
        UserPreferenceView.as_view(),
        name="user-preferences",
    ),
]