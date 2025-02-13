# https://developer.spotify.com/documentation/web-api/tutorials/code-flow

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
import requests

from models import Playlist, SpotifyTokenResponse, SpotifyUser
from utils import encode_to_base64, generate_random_string

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
FASTAPI_AUTH_SECRET_KEY = os.getenv('FASTAPI_AUTH_SECRET_KEY')

redirect_uri = "http://127.0.0.1:8000/auth/callback"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=FASTAPI_AUTH_SECRET_KEY)


@app.get('/login')
def login(request: Request):
    scope = 'playlist-read-private playlist-read-collaborative user-read-private user-read-email'
    state = generate_random_string()
    request.session['state'] = state
    return RedirectResponse(f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&state={state}&scope={scope}')


@app.get(path='/auth/callback')
def auth_callback(request: Request):
    session_state = request.session.get('state', 'not_valid')
    query_param_state = request.query_params.get("state")

    # if not query_param_state or query_param_state != session_state:
    if not query_param_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    error = request.query_params.get("error")
    if error:
        # TODO redirect them to an error page
        raise HTTPException(
            status_code=400, detail=f"OAuth 2.0 Error: {error}")

    authorization_code = request.query_params.get("code")
    form = {
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + encode_to_base64(f"{CLIENT_ID}:{CLIENT_SECRET}")
    }
    response = requests.post(
        url="https://accounts.spotify.com/api/token", data=form, headers=headers)
    spotify_token_response = SpotifyTokenResponse(**response.json())

    user = get_profile_details(
        access_token=spotify_token_response.access_token)
    playlists = get_user_playlists(
        access_token=spotify_token_response.access_token, user_id=user.id)

    return [{"name": playlist.name} for playlist in playlists]


def get_profile_details(access_token: str) -> SpotifyUser:
    response = requests.get("https://api.spotify.com/v1/me",
                            headers={"Authorization": f"Bearer {access_token}"})
    return SpotifyUser(**response.json())


def get_user_playlists(access_token: str, user_id: str) -> list[Playlist]:
    # TODO make use of the offset and range
    response = requests.get(f"https://api.spotify.com/v1/users/{user_id}/playlists", headers={
                            "Authorization": f"Bearer {access_token}"})
    return [Playlist(**playlist) for playlist in response.json()["items"]]
