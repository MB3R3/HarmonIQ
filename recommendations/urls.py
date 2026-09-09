from django.urls import path

from .views import RecommendationDiscoverView


urlpatterns = [
    # path(
    #     "sessions/",
    #     DiscoverySessionListCreateView.as_view(),
    #     name="discovery-sessions",
    # ),
    path("discover/", RecommendationDiscoverView.as_view(), name="recommendation-discover")
]