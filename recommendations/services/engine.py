from .candidates import CandidateGenerator
from .query_builder import RecommendationQueryBuilder
from .recommender import Recommendation
from .scoring import RecommendationScorer


class RecommendationEngine:

    MAX_RECOMMENDATIONS = 10
    MAX_CANDIDATES = 50
    ARTIST_METADATA_LIMIT = 6
    MAX_TRACKS_PER_ARTIST = 2
    MAX_TRACKS_PER_REQUESTED_ARTIST = 6

    def __init__(self, spotify):

        self.candidates = CandidateGenerator(
            spotify
        )

        self.scorer = RecommendationScorer()

    def generate(self, request):

        queries = RecommendationQueryBuilder.build_many(
            request
        )

        candidates = self.candidates.search_many(
            queries,
            max_candidates=self.MAX_CANDIDATES,
        )

        artist_genres = {}

        if request.genre:
            artist_genres = (
                self.candidates.fetch_artist_genres(
                    candidates,
                    limit=self.ARTIST_METADATA_LIMIT,
                )
            )

        recommendations = []

        for candidate in candidates:

            score, reasons, relevance_points = (
                self.scorer.score(
                    candidate.track,
                    request,
                    artist_genres=artist_genres,
                    source_query=candidate.query,
                )
            )

            if (
                relevance_points
                < self.scorer.relevance_threshold(
                    request
                )
            ):
                continue

            recommendations.append(
                self._to_recommendation(
                    candidate.track,
                    score,
                    reasons,
                )
            )

        recommendations.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return self._apply_diversity(
            recommendations,
            request,
        )

    @staticmethod
    def _to_recommendation(track, score, reasons):

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

        return Recommendation(
            spotify_track_id=track["id"],
            name=track["name"],
            artist=track["artists"][0]["name"],
            album=album.get("name", ""),
            artwork_url=artwork_url,
            spotify_url=spotify_url,
            score=score,
            reasons=reasons,
        )

    def _apply_diversity(self, recommendations, request):

        per_artist = {}
        selected = []

        for recommendation in recommendations:

            artist = (
                recommendation.artist or ""
            ).lower()

            limit = (
                self.MAX_TRACKS_PER_REQUESTED_ARTIST
                if (
                    request.artist
                    and request.artist.lower()
                    in artist
                )
                else self.MAX_TRACKS_PER_ARTIST
            )

            count = per_artist.get(artist, 0)

            if count >= limit:
                continue

            per_artist[artist] = count + 1
            selected.append(recommendation)

            if (
                len(selected)
                >= self.MAX_RECOMMENDATIONS
            ):
                break

        return selected