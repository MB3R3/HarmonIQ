from django.db import models
from django.conf import settings

# Create your models here.


class DiscoverySession(models.Model):
    DISCOVERY_STYLES = [
        ("familiar", "Familiar"),
        ("balanced", "Balanced"),
        ("new", "New"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discovery_sessions",
    )

    mood = models.CharField(
        max_length=50,
        blank=True,
    )

    genre = models.CharField(
        max_length=100,
        blank=True,
    )

    era = models.CharField(
        max_length=50,
        blank=True,
    )

    artist = models.CharField(
        max_length=255,
        blank=True,
    )

    discovery_style = models.CharField(
        max_length=20,
        choices=DISCOVERY_STYLES,
        default="balanced",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Discovery session #{self.id}"