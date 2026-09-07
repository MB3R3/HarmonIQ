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