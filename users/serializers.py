from rest_framework import serializers
from .models import UserPreference


class UserPreferenceSerializer(serializers.ModelSerializer):
    favorite_genres = serializers.ListField(
        child=serializers.CharField(required=False, allow_blank=True),
        required=False,
    )
    preferred_eras = serializers.ListField(
        child=serializers.CharField(required=False, allow_blank=True),
        required=False,
    )
    default_mood = serializers.CharField(
        max_length=50,
        allow_blank=True,
        required=False,
    )

    class Meta:
        model = UserPreference
        fields = [
            "favorite_genres",
            "preferred_eras",
            "default_mood",
            "discovery_style",
            "recommendation_frequency",
        ]