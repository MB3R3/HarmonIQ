from django.urls import path

from .views import DiscoverySessionListCreateView


urlpatterns = [
    path(
        "sessions/",
        DiscoverySessionListCreateView.as_view(),
        name="discovery-sessions",
    ),
]