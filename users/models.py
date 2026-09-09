import requests
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.

class UserPreference(models.Model):
    DISCOVERY_STYLES = [
        ("familiar", "Familiar"),
        ("balanced", "Balanced"),
        ("new", "New"),
    ]

    FREQUENCIES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("on_demand", "On demand"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )

    favorite_genres = models.JSONField(default=list)
    preferred_eras = models.JSONField(default=list)

    default_mood = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    discovery_style = models.CharField(
        max_length=20,
        choices=DISCOVERY_STYLES,
        default="balanced",
    )

    recommendation_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCIES,
        default="on_demand",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s preferences"
    

class SpotifyConnection(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="spotify_connection",
    )

    spotify_account_id = models.CharField(
        max_length=255,
        unique=True,
    )

    access_token = models.TextField()

    refresh_token = models.TextField()

    token_expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Spotify connection for {self.user.username}"

    def get_valid_access_token(self):
        """Return a usable access token, refreshing it if expired."""
        if (
            self.access_token
            and self.token_expires_at
            and self.token_expires_at > timezone.now()
        ):
            return self.access_token

        return self.refresh_tokens()

    def refresh_tokens(self):
        """Exchange the refresh token for a new access token."""
        if not self.refresh_token:
            raise ValueError(
                "Spotify connection has no refresh token. "
                "Please reconnect your Spotify account."
            )

        from .services.spotify import SpotifyAuthService

        try:
            token_data = SpotifyAuthService.refresh_access_token(
                self.refresh_token
            )
        except requests.HTTPError as exc:
            raise ValueError(
                "Spotify token refresh failed. "
                "Please reconnect your Spotify account."
            ) from exc

        self.access_token = token_data["access_token"]
        if token_data.get("refresh_token"):
            self.refresh_token = token_data["refresh_token"]
        self.token_expires_at = timezone.now() + timedelta(
            seconds=token_data["expires_in"]
        )
        self.save(update_fields=[
            "access_token",
            "refresh_token",
            "token_expires_at",
            "updated_at",
        ])

        return self.access_token