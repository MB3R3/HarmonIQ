import requests


class SpotifyAPIError(Exception):
    """Raised when Spotify returns an API error."""

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SpotifyService:
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, access_token):
        if not access_token:
            raise ValueError("SpotifyService requires an access_token.")
        self.access_token = access_token

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
        }

    def get(self, endpoint, params=None):
        response = requests.get(
            f"{self.BASE_URL}{endpoint}",
            headers=self.headers,
            params=params,
            timeout=10,
        )

        if not response.ok:
            try:
                payload = response.json()
            except ValueError:
                payload = {"raw": response.text}
            raise SpotifyAPIError(
                f"Spotify API error: {response.status_code}",
                status_code=response.status_code,
                payload=payload,
            )

        return response.json()

    def get_current_user(self):
        return self.get("/me")

    def search(self, query, search_type="track", limit=10):
        # NOTE: Spotify's /search currently rejects limit > 10
        # ("Invalid limit"), so default/clamp to 10.
        try:
            limit = max(1, min(int(limit), 10))
        except (TypeError, ValueError):
            limit = 10
        return self.get(
            "/search",
            params={
                "q": query,
                "type": search_type,
                "limit": limit,
            },
        )

    def get_track(self, track_id):
        return self.get(f"/tracks/{track_id}")

    def get_artist(self, artist_id):
        return self.get(f"/artists/{artist_id}")

    def get_album(self, album_id):
        return self.get(f"/albums/{album_id}")

    def get_top_tracks(self, limit=10):
        try:
            limit = max(1, min(int(limit), 50))
        except (TypeError, ValueError):
            limit = 10
        return self.get(
            "/me/top/tracks",
            params={
                "limit": limit,
            },
        )

    def get_top_artists(self, limit=10):
        try:
            limit = max(1, min(int(limit), 50))
        except (TypeError, ValueError):
            limit = 10
        return self.get(
            "/me/top/artists",
            params={
                "limit": limit,
            },
        )
