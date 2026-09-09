from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/users/",
        include("users.urls"),
    ),

    path(
        "api/music/",
        include("music.urls"),
    ),

    path(
        "api/recommendations/",
        include("recommendations.urls"),
    ),

    path(
        "api-auth/",
        include("rest_framework.urls"),
    ),
]