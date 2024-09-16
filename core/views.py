from django.shortcuts import redirect, render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import response
from requests import Request, post, session
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from .credentials import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from .extras import *

def home(request):
    return HttpResponse("<h1>Waba laba dub dub</h1>")



class AuthenticationURL(APIView):
    def get(self, request, format=None):
        scopes = "user-read-currently-playing user-read-playback-state user-modify-playback-state"
        url = Request('GET', 'https://accounts.spotify.com/authorize', params= {
            'scope':scopes,
            'response_type':'code',
            'redirect_uri':REDIRECT_URI,
            'client_id':CLIENT_ID
        }).prepare().url
        return HttpResponseRedirect(url)


def spotify_redirect(request, format=None):
    code = request.GET.get('code')
    error = request.GET.get('error')

    if error:
        return HttpResponse(f"Error: {error}", status=status.HTTP_400_BAD_REQUEST)
    
    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,  # Fixed key
        'client_id': CLIENT_ID,        # Fixed key
        'client_secret': CLIENT_SECRET
    }).json()

    if 'error' in response:
        return HttpResponse(f"Error: {response.get('error')}", status=status.HTTP_400_BAD_REQUEST)

    access_token = response.get('access_token')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    token_type = response.get('token_type')

    authkey = request.session.session_key
    if not request.session.exists(authkey):
        request.session.create()
        authkey = request.session.session_key

    print(f"Session key created: {authkey}")
    # print(f"Tokens retrieved: {check_tokens.tokens}")



    create_or_update_tokens(
        session_id=authkey,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=token_type  # Missing comma fixed
    )

    redirect_url = f"http://localhost:8000/harmoniq/current-song?key={authkey}" 
    return HttpResponseRedirect(redirect_url)



#  Checking if the user is authenticated by spotify
class CheckAuthentication(APIView):
    def get(self, request, format=None):
        key = self.request.session.session_key
        if not self.request.session.exists(key):
            self.request.session.create()
            key =  self.request.session.session_key

        auth_status = is_spotify_autheticated(key)

        if auth_status:
            redirect_url = f"http://localhost:8000/harmoniq/current-song?key={key}" 

            return HttpResponseRedirect(redirect_url)
        else:
            redirect_url = "http://localhost:8000/harmoniq/auth-url"
            return HttpResponseRedirect(redirect_url)



class CurrentSong(APIView):
    def get(self, request, format=None):
        # Retrieve the session key from the query parameters
        key = request.GET.get("key")

        if not key:
            return Response({"error": "Session key is missing"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the token for the session key
        token = check_tokens(key)
        if not token:
            return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)

        # Define the endpoint for currently playing song
        endpoint = "player/currently-playing"

        # Make a request to the Spotify API
        response = spotify_requests_execution(key, endpoint)
        if "error" in response:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # Process the response
        if not response.get('item'):
            return Response({"message": "No song currently playing"}, status=status.HTTP_204_NO_CONTENT)

        item = response.get('item')
        progress = response.get('progress_ms', 0)
        is_playing = response.get('is_playing', False)
        duration = item.get('duration_ms', 0)
        song_id = item.get('id', '')
        title = item.get('name', '')
        album_cover = item.get("album", {}).get("images", [{}])[0].get("url", '')

        artists = ", ".join(artist.get("name") for artist in item.get("artists", []))

        song = {
            "id": song_id,
            "title": title,
            "artist": artists,
            "duration": duration,
            "time": progress,
            "album_cover": album_cover,
            "is_playing": is_playing
        }

        return Response(song, status=status.HTTP_200_OK)