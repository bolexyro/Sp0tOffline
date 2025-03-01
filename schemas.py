from pydantic import BaseModel
from typing import Annotated, Generic, TypeVar


class SpotifyTokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str
    expires_in: int
    refresh_token: str


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
    images: list[SpotifyImage] | None
    name: str


class Track(BaseModel):
    id: str
    name: str
    preview_url: Annotated[str | None,
                           'A link to a 30 second preview (MP3 format) of the track.'] = None
    artists: list["Artist"]
    album: "Album"
    duration_ms: int


class Artist(BaseModel):
    id: Annotated[str, "Artist spotify id"]
    name: str


class Album(BaseModel):
    id: str
    name: str
    images: list["SpotifyImage"]


class PlaylistTrack(BaseModel):
    pass


class LoginResponse(BaseModel):
    user: SpotifyUser
    token_data: SpotifyTokenResponse


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    data: T
