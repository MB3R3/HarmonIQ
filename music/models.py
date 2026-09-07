from django.db import models
from django.conf import settings

# Create your models here.


class SavedTrack(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_tracks",
    )

    spotify_track_id = models.CharField(max_length=100)

    track_name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_name = models.CharField(max_length=255)

    artwork_url = models.URLField(
        blank=True,
        default="",
    )

    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-saved_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "spotify_track_id"],
                name="unique_saved_track_per_user",
            )
        ]

    def __str__(self):
        return f"{self.track_name} - {self.artist_name}"