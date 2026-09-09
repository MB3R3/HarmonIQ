import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from music.services.spotify import SpotifyAPIError, SpotifyService
from users.models import SpotifyConnection
from .models import DiscoverySession
from .serializers import (
    DiscoveryRequestSerializer,
    RecommendationSerializer,
)
from .services.engine import RecommendationEngine
from .services.recommender import RecommendationRequest


logger = logging.getLogger(__name__)


class RecommendationDiscoverView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DiscoveryRequestSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            connection = request.user.spotify_connection
        except SpotifyConnection.DoesNotExist:
            return Response(
                {
                    "error": "Spotify account is not connected."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = connection.get_valid_access_token()
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        spotify = SpotifyService(
            access_token
        )

        recommendation_request = RecommendationRequest(
            mood=data.get("mood", ""),
            genre=data.get("genre", ""),
            era=data.get("era", ""),
            artist=data.get("artist", ""),
            discovery_style=data.get(
                "discovery_style",
                "balanced",
            ),
        )

        engine = RecommendationEngine(spotify)

        try:
            recommendations = engine.generate(
                recommendation_request
            )
        except SpotifyAPIError as exc:
            logger.warning(
                "Spotify API error for user %s: %s",
                request.user,
                exc,
            )
            return Response(
                {
                    "error": "Spotify API returned an error.",
                    "detail": f"{exc}",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            logger.exception(
                "Unexpected error generating recommendations for user %s",
                request.user,
            )
            return Response(
                {
                    "error": (
                        "Something went wrong while generating "
                        "recommendations."
                    ),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        DiscoverySession.objects.create(
            user=request.user,
            mood=recommendation_request.mood,
            genre=recommendation_request.genre,
            era=recommendation_request.era,
            artist=recommendation_request.artist,
            discovery_style=(
                recommendation_request.discovery_style
            ),
        )

        response_serializer = RecommendationSerializer(
            recommendations,
            many=True,
        )

        return Response(
            {
                "request": data,
                "results": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )