from .playlist_candidates import PlaylistCandidateGenerator
from .playlist_query_builder import PlaylistQueryBuilder
from .playlist_recommender import PlaylistRecommendation
from .playlist_scoring import (
    PlaylistScorer,
    playlist_era_conflict,
)


class PlaylistEngine:

    MAX_PLAYLISTS = 5
    MAX_CANDIDATES = 30
    PER_QUERY_LIMIT = 8

    def __init__(self, spotify):
        self.candidates = PlaylistCandidateGenerator(
            spotify
        )
        self.scorer = PlaylistScorer()

    def generate(self, request):

        queries = PlaylistQueryBuilder.build_many(
            request
        )

        if not queries:
            return []

        candidates = self.candidates.search_many(
            queries,
            per_query=self.PER_QUERY_LIMIT,
            max_candidates=self.MAX_CANDIDATES,
        )

        playlists = []

        for candidate in candidates:

            if playlist_era_conflict(
                candidate.playlist,
                request.era,
            ):
                continue

            score, reasons, relevance = (
                self.scorer.score(
                    candidate.playlist,
                    request,
                    source_query=candidate.query,
                )
            )

            if relevance <= 0 or score <= 0:
                continue

            playlists.append(
                self._to_playlist(
                    candidate.playlist,
                    score,
                    reasons,
                )
            )

        playlists.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return playlists[: self.MAX_PLAYLISTS]

    @staticmethod
    def _extract_track_count(playlist):
        """Extract the track count from a Spotify playlist search item.

        Spotify's search payload exposes the count either under
        ``tracks`` (``{"href": ..., "total": N}``) or, as returned by the
        live search endpoint, under ``items`` with the same shape. A value
        is only reported when present; otherwise 0 is returned rather than
        inventing one.
        """
        tracks = playlist.get("tracks") or {}
        total = tracks.get("total")

        if total is not None:
            return total

        items = playlist.get("items")
        if isinstance(items, dict):
            total = items.get("total")
            if total is not None:
                return total

        return 0

    @staticmethod
    def _to_playlist(playlist, score, reasons):

        images = playlist.get("images", [])

        artwork_url = (
            images[0]["url"]
            if images
            else ""
        )

        owner = playlist.get("owner", {}) or {}

        owner_name = (
            owner.get("display_name")
            or owner.get("id")
            or ""
        )

        return PlaylistRecommendation(
            spotify_playlist_id=playlist["id"],
            name=playlist.get("name", ""),
            description=(
                playlist.get("description", "")
                or ""
            ),
            artwork_url=artwork_url,
            spotify_url=(
                playlist
                .get("external_urls", {})
                .get("spotify", "")
            ),
            owner_name=owner_name,
            track_count=PlaylistEngine._extract_track_count(
                playlist
            ),
            score=score,
            reasons=reasons,
        )