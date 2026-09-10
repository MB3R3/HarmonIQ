import logging

from dataclasses import dataclass

from music.services.spotify import SpotifyAPIError


logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    track: dict
    query: str


class CandidateGenerator:

    def __init__(self, spotify):
        self.spotify = spotify

    def search_by_query(self, query, limit=10):
        response = self.spotify.search(
            query=query,
            search_type="track",
            limit=limit,
        )

        return response.get("tracks", {}).get("items", [])

    def search_many(
        self,
        queries,
        per_query=10,
        max_candidates=50,
    ) -> list[Candidate]:
        """Run multiple searches and combine results into a unique pool.

        Empty queries are skipped and individual Spotify errors are
        tolerated so one failing search cannot sink the whole request.
        """
        candidates = []
        seen_ids = set()

        for query in queries:
            if not query or not query.strip():
                continue

            try:
                items = self.search_by_query(
                    query=query,
                    limit=per_query,
                )
            except SpotifyAPIError as exc:
                logger.warning(
                    "Spotify search failed for query %r: %s",
                    query,
                    exc,
                )
                continue

            for item in items:
                track_id = item.get("id")
                if not track_id or track_id in seen_ids:
                    continue
                seen_ids.add(track_id)
                candidates.append(Candidate(track=item, query=query))

                if len(candidates) >= max_candidates:
                    return candidates

        return candidates

    def fetch_artist_genres(self, candidates, limit=6) -> dict:
        """Fetch verified genres for a bounded set of artists.

        Only the most frequent artists in the pool are queried, so genre
        metadata never becomes an N+1 request per candidate.
        """
        counts = {}
        for candidate in candidates:
            for artist in candidate.track.get("artists", []):
                artist_id = artist.get("id")
                if not artist_id:
                    continue
                counts[artist_id] = counts.get(artist_id, 0) + 1

        ranked_artist_ids = sorted(
            counts,
            key=counts.get,
            reverse=True,
        )

        artist_genres = {}
        for artist_id in ranked_artist_ids[:limit]:
            genres = self._artist_genres(artist_id)
            if genres:
                artist_genres[artist_id] = genres

        return artist_genres

    def _artist_genres(self, artist_id) -> list[str]:
        try:
            artist = self.spotify.get_artist(artist_id)
        except SpotifyAPIError as exc:
            logger.warning(
                "Spotify artist lookup failed for %s: %s",
                artist_id,
                exc,
            )
            return []
        return artist.get("genres", [])