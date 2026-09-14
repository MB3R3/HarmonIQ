from rest_framework import serializers
from .models import SavedTrack


class SavedTrackSerializer(serializers.ModelSerializer):
    spotify_url = serializers.SerializerMethodField()

    class Meta:
        model = SavedTrack
        fields = [
            "id",
            "spotify_track_id",
            "track_name",
            "artist_name",
            "album_name",
            "artwork_url",
            "spotify_url",
            "saved_at",
        ]
        read_only_fields = ["id", "saved_at"]

    def get_spotify_url(self, obj):
        return f"https://open.spotify.com/track/{obj.spotify_track_id}"