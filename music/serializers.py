from rest_framework import serializers
from .models import SavedTrack

import re


SPOTIFY_TRACK_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{22}$")


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


class CreateSpotifyPlaylistSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        trim_whitespace=True,
        allow_blank=False,
    )
    description = serializers.CharField(
        max_length=300,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )
    public = serializers.BooleanField(
        required=False,
        default=False,
    )
    track_ids = serializers.ListField(
        child=serializers.CharField(
            max_length=50,
            trim_whitespace=True,
        ),
        allow_empty=False,
    )

    def validate_track_ids(self, value):
        cleaned = []
        seen = set()
        for track_id in value:
            track_id = track_id.strip()
            if not SPOTIFY_TRACK_ID_PATTERN.match(track_id):
                raise serializers.ValidationError(
                    "Each track ID must be a valid Spotify track ID."
                )
            if track_id not in seen:
                seen.add(track_id)
                cleaned.append(track_id)

        if not cleaned:
            raise serializers.ValidationError(
                "At least one valid Spotify track ID is required."
            )

        return cleaned


class CreateSpotifyPlaylistResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    spotify_url = serializers.URLField(allow_blank=True)
    public = serializers.BooleanField()
    track_count = serializers.IntegerField()