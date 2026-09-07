from rest_framework import serializers
from .models import SavedTrack


class SavedTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedTrack
        fields = [
            "id",
            "spotify_track_id",
            "track_name",
            "artist_name",
            "album_name",
            "artwork_url",
            "saved_at",
        ]
        read_only_fields = ["id", "saved_at"]