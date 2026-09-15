import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

sys.stdout.reconfigure(encoding="utf-8")

import django

django.setup()

from users.models import SpotifyConnection
from music.services.spotify import SpotifyService


connection = SpotifyConnection.objects.first()

if not connection:
    raise RuntimeError("No SpotifyConnection found.")

token = connection.get_valid_access_token()

spotify = SpotifyService(token)

queries = [
    "r&b",
    "chill r&b",
    "2010s r&b",
]

for query in queries:
    print(f"\n===== {query} =====")

    playlists = spotify.search_playlists(
        query=query,
        limit=5,
    )

    print(f"Found: {len(playlists)} playlists")

    for playlist in playlists:
        print(
            playlist.get("id"),
            "|",
            playlist.get("name"),
        )