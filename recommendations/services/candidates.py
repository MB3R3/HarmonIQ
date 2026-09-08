from music.services.spotify import SpotifyService


class CandidateGenerator:

    def __init__(self, spotify: SpotifyService):
        self.spotify = spotify

    def search_by_query(self, query, limit=10):
        response = self.spotify.search(
            query=query,
            search_type="track",
            limit=limit,
        )

        return response.get("tracks", {}).get("items", [])