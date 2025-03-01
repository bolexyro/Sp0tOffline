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


async def get_playlist_items(access_token: str, playlist_id: str) -> ApiResponse[list[Track]]:
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


async def get_album_items(access_token: str, album_id: str) -> ApiResponse[list[Track]]:
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


def refresh_token(refresh_token: str):
    # The refresh token contained in the response, can be used to request new tokens. Depending on the grant used to get the initial refresh token,
    # a refresh token might not be included in each response. When a refresh token is not returned, continue using the existing token.
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(url=url, headers=headers, data=data)
    if response.status_code == 200:
        return SpotifyTokenResponse(**response.json())
    raise HTTPException(status_code=response.status_code, detail=response.text)
