from pydantic import BaseModel
from typing import Annotated, Generic, TypeVar


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class SpotifyTokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str
    expires_in: int
    refresh_token: str | None = None


class SpotifyUser(BaseModel):
    country: str
    display_name: str
    email: str
    id: str
    images: list["SpotifyImage"]


class SpotifyImage(BaseModel):
    url: str
    height: int
    width: int


class Playlist(BaseModel):
    id: str
    name: str
    description: str | None = None
    owner_name: str
    total_tracks: int
    images: list[SpotifyImage] | None


class Album(BaseModel):
    id: str
    name: str
    # "album", "single", "compilation"
    album_type: str
    total_tracks: int
    release_date: str
    artists: list["Artist"]
    images: list["SpotifyImage"]


class Track(BaseModel):
    id: str
    name: str
    preview_url: Annotated[str | None,
                           'A link to a 30 second preview (MP3 format) of the track.'] = None
    artists: list["Artist"]
    album: Album | None = None
    duration_ms: int


class Artist(BaseModel):
    id: Annotated[str, "Artist spotify id"]
    name: str


class LoginResponse(BaseModel):
    user: SpotifyUser
    token_data: SpotifyTokenResponse


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    data: T
    message: str | None = None
