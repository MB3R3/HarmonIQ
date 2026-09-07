from rest_framework import serializers
from .models import UserPreference


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            "favorite_genres",
            "preferred_eras",
            "default_mood",
            "discovery_style",
            "recommendation_frequency",
        ]