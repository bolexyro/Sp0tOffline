# https://developer.spotify.com/documentation/seb-api/tutorials/code-flow

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

from schemas import LoginResponse, TokenRefreshRequest
from services.spotify import get_access_token, get_album_items, get_liked_songs, get_playlist_items, get_profile_details, get_user_albums, get_user_playlists, refresh_token
from utils.common import generate_random_string, generate_spotify_redirecturl

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
FASTAPI_AUTH_SECRET_KEY = os.getenv('FASTAPI_AUTH_SECRET_KEY')


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=FASTAPI_AUTH_SECRET_KEY)

security = HTTPBearer()


@app.get('/login')
def login(request: Request):
    redirect_uri = request.url_for('auth_callback_route')
    scope = 'playlist-read-private playlist-read-collaborative user-read-private user-read-email user-library-read'
    state = generate_random_string()
    request.session['state'] = state
    return RedirectResponse(generate_spotify_redirecturl(CLIENT_ID, redirect_uri, scope, state))


@app.get(path='/auth/callback', name='auth_callback_route')
async def auth_callback(request: Request):
    redirect_uri = request.url_for('auth_callback_route')

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
    spotify_token_response = get_access_token(
        authorization_code=request.query_params.get("code"), redirect_uri=redirect_uri)

    user = get_profile_details(
        access_token=spotify_token_response.access_token)
    # playlists = get_user_playlists(
    #     access_token=spotify_token_response.access_token, user_id=user.id)
    # return await get_liked_songs(access_token=spotify_token_response.access_token)
    # return [{"name": playlist.name} for playlist in playlists]
    await manager.broadcast(LoginResponse(user=user, token_data=spotify_token_response).model_dump_json())
    return LoginResponse(user=user, token_data=spotify_token_response)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[id] = websocket

    def disconnect(self, id: str):
        del self.active_connections[id]

    async def send_personal_message(self, message: str, id: str):
        await self.active_connections[id].send_text(message)

    async def broadcast(self, message: str):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/token/{id}")
async def token_websocket(id: str, websocket: WebSocket):
    await manager.connect(id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(id)
        print("client disconnected")


# Function to validate the token
def extract_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return token


@app.get("/liked-songs")
async def liked_songs(access_token: str = Depends(extract_token)):
    api_response = await get_liked_songs(access_token=access_token)
    if api_response.status_code == 200:
        return api_response.data
    raise HTTPException(status_code=api_response.status_code,
                        detail="Bad or Expired Token")


@app.get("/playlists")
async def get_playlists(access_token: str = Depends(extract_token)):
    api_response = await get_user_playlists(access_token)
    if api_response.status_code == 200:
        return api_response.data
    raise HTTPException(status_code=api_response.status_code,
                        detail="Bad or Expired Token")


@app.get("/playlists/{playlist_id}/tracks")
async def get_playlist_tracks(playlist_id: str, access_token: str = Depends(extract_token)):
    api_response = await get_playlist_items(playlist_id, access_token)
    if api_response.status_code == 200:
        return api_response.data
    raise HTTPException(status_code=api_response.status_code,
                        detail="Bad or Expired Token")


@app.get("/albums")
async def get_albums(access_token: str = Depends(extract_token)):
    api_response = await get_user_albums(access_token)
    if api_response.status_code == 200:
        return api_response.data
    raise HTTPException(status_code=api_response.status_code,
                        detail="Bad or Expired Token")


@app.get("/albums/{album_id}/tracks")
async def get_playlist_tracks(album_id: str, access_token: str = Depends(extract_token)):
    api_response = await get_album_items(album_id, access_token)
    if api_response.status_code == 200:
        return api_response.data
    raise HTTPException(status_code=api_response.status_code,
                        detail="Bad or Expired Token")


@app.post("/auth/refresh-token")
async def refresh_access_token(request: TokenRefreshRequest):
    api_response = await refresh_token(refresh_token=request.refresh_token)
    if api_response.status_code == 200:
        return api_response.data
    raise HTTPException(status_code=api_response.status_code,
                        detail=api_response.message)
