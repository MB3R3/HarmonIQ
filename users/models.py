from django.db import models
from django.conf import settings

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