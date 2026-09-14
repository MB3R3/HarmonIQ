from django.urls import path

from .views import DiscoverySessionListView, RecommendationDiscoverView


urlpatterns = [
    path(
        "sessions/",
        DiscoverySessionListView.as_view(),
        name="discovery-sessions",
    ),
    path("discover/", RecommendationDiscoverView.as_view(), name="recommendation-discover")
]