import os

import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()

from users.models import SpotifyConnection
from music.services.spotify import SpotifyService

from recommendations.services.engine import (
    RecommendationEngine,
)

from recommendations.services.recommender import (
    RecommendationRequest,
)


connection = SpotifyConnection.objects.first()

if not connection:
    raise SystemExit(
        "No Spotify connection found."
    )

spotify = SpotifyService(
    connection.access_token
)

engine = RecommendationEngine(spotify)

request = RecommendationRequest(
    mood="chill",
    genre="r&b",
    era="2010s",
    discovery_style="new",
)

recommendations = engine.generate(request)

for recommendation in recommendations:

    print(
        f"{recommendation.name}  - {recommendation.artist}"
    )

    print(
        f"Score: {recommendation.score}"
    )

    print(
        f"Reasons: {', '.join(recommendation.reasons)}"
    )

    print("-" * 40)