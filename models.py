from pydantic import BaseModel


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
