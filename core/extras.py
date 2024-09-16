                                                                                               	    
from .models import Token
from django.utils import timezone
from datetime import timedelta
from requests import post, get
from .credentials import CLIENT_ID, CLIENT_SECRET


BASE_URL = "https://api.spotify.com/v1/me/"

# Check tokens
def check_tokens(session_id):
    tokens = Token.objects.filter(user=session_id).first()  # Use .first() to avoid errors
    if not tokens:
        print(f"Token not found for session: {session_id}")
    return tokens
    


# Create and update the token model
def create_or_update_tokens(session_id, access_token, refresh_token, expires_in, token_type):
    tokens = check_tokens(session_id)
    expires_in = timezone.now() + timedelta(seconds=expires_in)

    # Update tokens if they exist
    if tokens:
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=['access_token', 'refresh_token', 'expires_in', 'token_type'])
    else:
        # Create a new token if it doesn't exist
        new_token = Token(
            user=session_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            token_type=token_type
        )
        new_token.save()
        print(f"New token created for session: {session_id}")

# Check if the user is authenticated by Spotify
def is_spotify_autheticated(session_id):
    tokens = check_tokens(session_id)

    if tokens:
        if tokens.expires_in <= timezone.now():
            # Token expired, refresh it
            refresh_token_func(session_id)
        return True
    return False


# Refresh token function
def refresh_token_func(session_id):
    tokens = check_tokens(session_id)
    refresh_token = tokens.refresh_token

    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,  # Fixed key
        'client_secret': CLIENT_SECRET
    }).json()

    access_token = response.get('access_token')
    expires_in = response.get('expires_in')
    token_type = response.get('token_type')

    # Update the tokens
    create_or_update_tokens(
        session_id=session_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=token_type
    )

# Execute a Spotify API request
def spotify_requests_execution(session_id, endpoint):
    token = check_tokens(session_id)
    
    if not token:
        return {"error": "Token not found"}

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token.access_token}'
    }
    
    try:
        # Make the API request
        response = get(f"{BASE_URL}{endpoint}", headers=headers)
        
        # Check if the response is successful
        if response.status_code != 200:
            return {"error": f"API request failed with status code {response.status_code}"}
        
        # Return JSON data
        return response.json()
    
    except Exception as e:
        print(f"Error during API request: {e}")
        return {"error": "An error occurred while making the API request"}  