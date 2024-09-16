from django.urls import path
from .views import *


urlpatterns = [
    path('', home, name='home'),
    path('auth-url', AuthenticationURL.as_view()),
    path('redirect', spotify_redirect),
    path('check-auth', CheckAuthentication.as_view()),
    path('current-song', CurrentSong.as_view(), name='current-song'),
]