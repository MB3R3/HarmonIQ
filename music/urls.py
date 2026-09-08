from django.urls import path

from .views import SavedTrackListCreateView
from . import spotify_views


urlpatterns = [
    path(
        "saved/",
        SavedTrackListCreateView.as_view(),
        name="saved-tracks",
    ),
    # HarmonIQ Spotify proxy — React never talks to Spotify directly.
    path("me/", spotify_views.me, name="spotify-me"),
    path("search/", spotify_views.search, name="spotify-search"),
    path("tracks/<str:spotify_id>/", spotify_views.track_detail, name="spotify-track"),
    path("artists/<str:spotify_id>/", spotify_views.artist_detail, name="spotify-artist"),
    path("albums/<str:spotify_id>/", spotify_views.album_detail, name="spotify-album"),
    path("top-tracks/", spotify_views.top_tracks, name="spotify-top-tracks"),
    path("top-artists/", spotify_views.top_artists, name="spotify-top-artists"),
]