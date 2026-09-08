from .candidates import CandidateGenerator
from .query_builder import RecommendationQueryBuilder
from .recommender import Recommendation
from .scoring import RecommendationScorer


class RecommendationEngine:

    def __init__(self, spotify):

        self.candidates = CandidateGenerator(
            spotify
        )

        self.scorer = RecommendationScorer()

    def generate(self, request):

        query = RecommendationQueryBuilder.build(
            request
        )

        tracks = self.candidates.search_by_query(
            query=query,
            limit=10,
        )

        recommendations = []

        for track in tracks:

            score, reasons = self.scorer.score(
                track,
                request,
            )

            album = track.get("album", {})

            images = album.get("images", [])

            artwork_url = (
                images[0]["url"]
                if images
                else ""
            )

            spotify_url = (
                track
                .get("external_urls", {})
                .get("spotify", "")
            )

            recommendations.append(
                Recommendation(
                    spotify_track_id=track["id"],
                    name=track["name"],
                    artist=track["artists"][0]["name"],
                    album=album.get("name", ""),
                    artwork_url=artwork_url,
                    spotify_url=spotify_url,
                    score=score,
                    reasons=reasons,
                )
            )

        recommendations.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return recommendations