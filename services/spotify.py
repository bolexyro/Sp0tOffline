from fastapi import HTTPException
import requests
from schemas import Album, SpotifyTokenResponse, SpotifyUser, Playlist, Track, ApiResponse
import os
from dotenv import load_dotenv

import aiohttp
from utils.common import encode_to_base64

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')


def get_access_token(authorization_code: str, redirect_uri: str):
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
    return SpotifyTokenResponse(**response.json())


def get_profile_details(access_token: str) -> SpotifyUser:
    response = requests.get("https://api.spotify.com/v1/me",
                            headers={"Authorization": f"Bearer {access_token}"})
    return SpotifyUser(**response.json())


async def get_user_playlists(access_token: str) -> ApiResponse[list[Playlist]]:
    # TODO make use of the offset and range
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}

    playlists = []

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, headers=headers) as response:
            if response.status != 200:
                return ApiResponse[list[Playlist]](status_code=response.status, data=[])

            data = await response.json()
            next_url = data['next']

            for playlist in data['items']:
                playlists.append(Playlist(**playlist))

            while next_url:
                async with session.get(url=next_url, headers=headers) as response:
                    if response.status != 200:
                        return ApiResponse[list[Playlist]](status_code=response.status, data=[])

                    data = await response.json()
                    next_url = data['next']
                    for playlist in data['items']:
                        playlists.append(Playlist(**playlist))

    # return [Playlist(**playlist) for playlist in response.json()["items"]]
    return ApiResponse[list[Playlist]](status_code=200, data=playlists)


async def get_liked_songs(access_token: str) -> ApiResponse[list[Track]]:
    url = 'https://api.spotify.com/v1/me/tracks?limit=50'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    tracks = []
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, headers=headers) as response:
            if response.status != 200:
                return ApiResponse[list[Track]](status_code=response.status, data=[])

            data = await response.json()
            next_url = data['next']

            for track in data['items']:
                tracks.append(Track(**track['track']))
            while next_url:
                async with session.get(url=next_url, headers=headers) as response:
                    if response.status != 200:
                        return ApiResponse[list[Track]](status_code=response.status, data=[])

                    data = await response.json()
                    next_url = data['next']
                    for track in data['items']:
                        tracks.append(Track(**track['track']))
    return ApiResponse[list[Track]](status_code=response.status, data=tracks)


async def get_playlist_items(playlist_id: str, access_token: str) -> ApiResponse[list[Track]]:
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers = {'Authorization': f'Bearer {access_token}'}
    tracks = []

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, headers=headers) as response:
            if response.status != 200:
                print(await response.text())
                return ApiResponse[list[Track]](status_code=response.status, data=[])

            data = await response.json()
            next_url = data['next']

            for track in data['items']:
                tracks.append(Track(**track['track']))

            while next_url:
                async with session.get(url=next_url, headers=headers) as response:
                    if response.status != 200:
                        return ApiResponse[list[Track]](status_code=response.status, data=[])

                    data = await response.json()
                    next_url = data['next']
                    for track in data['items']:
                        tracks.append(Track(**track['track']))
    return ApiResponse[list[Track]](status_code=response.status, data=tracks)


async def get_user_albums(access_token: str) -> ApiResponse[list[Album]]:
    url = "https://api.spotify.com/v1/me/albums"
    headers = {"Authorization": f"Bearer {access_token}"}

    albums = []

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, headers=headers) as response:
            if response.status != 200:
                return ApiResponse[list[Album]](status_code=response.status, data=[])

            data = await response.json()
            next_url = data['next']

            for item in data['items']:
                albums.append(Album(**item["album"]))

            while next_url:
                async with session.get(url=next_url, headers=headers) as response:
                    if response.status != 200:
                        return ApiResponse[list[Album]](status_code=response.status, data=[])

                    data = await response.json()
                    next_url = data['next']
                    for item in data['items']:
                        albums.append(Album(**item["album"]))

    return ApiResponse[list[Album]](status_code=200, data=albums)


async def get_album_items(album_id: str, access_token: str) -> ApiResponse[list[Track]]:
    url = f'https://api.spotify.com/v1/albums/{album_id}/tracks'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    tracks = []

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, headers=headers) as response:
            if response.status != 200:
                print(await response.text())
                return ApiResponse[list[Track]](status_code=response.status, data=[])

            data = await response.json()
            next_url = data['next']

            for track in data['items']:
                tracks.append(Track(**track))

            while next_url:
                async with session.get(url=next_url, headers=headers) as response:
                    if response.status != 200:
                        return ApiResponse[list[Track]](status_code=response.status, data=[])

                    data = await response.json()
                    next_url = data['next']
                    for track in data['items']:
                        tracks.append(Track(**track))
    return ApiResponse[list[Track]](status_code=response.status, data=tracks)


async def refresh_token(refresh_token: str) -> ApiResponse[SpotifyTokenResponse] | None:
    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        'Authorization': 'Basic ' + encode_to_base64(f"{CLIENT_ID}:{CLIENT_SECRET}")
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url=url, data=data) as response:
            if response.status != 200:
                return ApiResponse[SpotifyTokenResponse | None](
                    status_code=response.status,
                    data=None,
                    message=await response.text()
                )

            response_data = await response.json()
            print(response_data)

            return ApiResponse(
                status_code=200,
                data=SpotifyTokenResponse(**response_data)
            )
