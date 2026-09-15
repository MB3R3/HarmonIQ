from dataclasses import dataclass


@dataclass
class PlaylistRecommendation:
    spotify_playlist_id: str
    name: str
    description: str
    artwork_url: str
    spotify_url: str
    owner_name: str
    track_count: int
    score: float
    reasons: list[str]