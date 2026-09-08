# import os
# import django

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# django.setup()

# from users.models import SpotifyConnection
# from music.services.spotify import SpotifyService


# connection = SpotifyConnection.objects.first()

# if not connection:
#     print("No Spotify connection found.")
#     raise SystemExit

# spotify = SpotifyService(connection.access_token)

# profile = spotify.get_current_user()

# print("Spotify user:")
# print(profile.get("display_name"))
# print(profile.get("account_id"))


# import os
# import django

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# django.setup()

# from users.models import SpotifyConnection
# from music.services.spotify import SpotifyService


# connection = SpotifyConnection.objects.first()

# if not connection:
#     print("No Spotify connection found.")
#     raise SystemExit

# spotify = SpotifyService(connection.access_token)

# results = spotify.search("Frank Ocean")

# tracks = results.get("tracks", {}).get("items", [])

# print(f"Found {len(tracks)} tracks:\n")

# for track in tracks[:5]:
#     print(
#         f"{track['name']} - {track['artists'][0]['name']}"
#     )


import os 
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


from users.models import SpotifyConnection
from music.services.spotify import SpotifyService


connection = SpotifyConnection.objects.first()

if not connection:
    print("Cant connect spotify, no connection found")
    raise SystemExit

spotify = SpotifyService(connection.access_token)

results = spotify.search("Yeat")

# print("\nRAW SEARCH RESPONSE:")
# print(results)

tracks = results.get("tracks", {}).get("items", [])

if not tracks:
    print("No tracks Found")
    raise SystemExit


artist = tracks[0]["artists"][0]

print("Artist name:", artist["name"]) 
print("Artist ID:", artist["id"])

# artist_id = artist["id"]
# artist_data = spotify.get(artist_id)

# print("\nArtist retrieved successfully!")
# print("Name:", artist_data["name"])
# print("Spotify ID:", artist_data["id"])
# print("Genres:", artist_data.get("genres", []))
# print("Popularity:", artist_data.get("popularity"))


artist_id = artist["id"]

artist_data = spotify.get_artist(artist_id)

print("\nArtist retrieved successfully!")
print("Name:", artist_data["name"])
print("Spotify ID:", artist_data["id"])
print("Genres:", artist_data.get("genres", []))
print("Popularity:", artist_data.get("popularity"))


images = artist_data.get("images", [])

print("\nImages:", len(images))

if images:
    print("First image URL:", images[0]["url"])
else:
    print("No artist images returned.")