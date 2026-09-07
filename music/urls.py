from django.urls import path

from .views import SavedTrackListCreateView


urlpatterns = [
    path(
        "saved/",
        SavedTrackListCreateView.as_view(),
        name="saved-tracks",
    ),
]