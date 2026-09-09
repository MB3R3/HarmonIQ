from rest_framework import serializers

from .models import DiscoverySession


class DiscoverySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoverySession
        fields = [
            "id",
            "mood",
            "genre",
            "era",
            "artist",
            "discovery_style",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DiscoveryRequestSerializer(serializers.Serializer):
    mood = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
    )
    genre = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    era = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
    )
    artist = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    discovery_style = serializers.ChoiceField(
        choices=["familiar", "balanced", "new"],
        default="balanced",
    )

class RecommendationSerializer(serializers.Serializer):
    spotify_track_id = serializers.CharField()
    name = serializers.CharField()
    artist = serializers.CharField()
    album = serializers.CharField()
    artwork_url = serializers.URLField(
        allow_blank=True
    )
    spotify_url = serializers.URLField(
        allow_blank=True
    )
    score = serializers.FloatField()
    reasons = serializers.ListField(
        child=serializers.CharField()
    )