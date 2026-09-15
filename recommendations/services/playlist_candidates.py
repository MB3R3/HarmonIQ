import logging

from dataclasses import dataclass

from music.services.spotify import SpotifyAPIError


logger = logging.getLogger(__name__)


@dataclass
class PlaylistCandidate:
    playlist: dict
    query: str


class PlaylistCandidateGenerator:

    def __init__(self, spotify):
        self.spotify = spotify

    def search_by_query(self, query, limit=10):
        return self.spotify.search_playlists(
            query=query,
            limit=limit,
        )

    def search_many(
        self,
        queries,
        per_query=8,
        max_candidates=30,
    ) -> list[PlaylistCandidate]:
        """Run multiple playlist searches into a unique, bounded pool.

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
                    "Spotify playlist search failed for %r: %s",
                    query,
                    exc,
                )
                continue

            for item in items or []:
                playlist_id = item.get("id")
                if not playlist_id or playlist_id in seen_ids:
                    continue
                seen_ids.add(playlist_id)
                candidates.append(
                    PlaylistCandidate(
                        playlist=item,
                        query=query,
                    )
                )

                if len(candidates) >= max_candidates:
                    return candidates

        return candidates