from dataclasses import dataclass


@dataclass
class RecommendationRequest:
    mood: str = ""
    genre: str = ""
    era: str = ""
    artist: str = ""
    discovery_style: str = "balanced"


@dataclass
class Recommendation:
    spotify_track_id: str
    name: str
    artist: str
    album: str
    artwork_url: str
    spotify_url: str
    score: float
    reasons: list[str]