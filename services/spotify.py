from fastapi import HTTPException
import requests
from schemas import SpotifyTokenResponse, SpotifyUser, Playlist, Track
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


def get_user_playlists(access_token: str, user_id: str) -> list[Playlist]:
    # TODO make use of the offset and range
    response = requests.get(f"https://api.spotify.com/v1/users/{user_id}/playlists", headers={
                            "Authorization": f"Bearer {access_token}"})
    return [Playlist(**playlist) for playlist in response.json()["items"]]


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


async def get_liked_songs(access_token: str):
    url = 'https://api.spotify.com/v1/me/tracks?limit=50'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    tracks = []
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, headers=headers) as response:
            data = await response.json()
            next_url = data['next']

            while next_url:
                for track in data['items']:
                    tracks.append(Track(**track['track']))

                async with session.get(url=url, headers=headers) as response:
                    data = await response.json()
                    next_url = await response.json()['next']

    # response = requests.get(url=url, headers=headers)
    # next_url = response.json()['next']
    # while next_url:
    #     for track in response.json()['items']:
    #         tracks.append(Track(**track['track']))
    #     response = requests.get(url=next_url, headers=headers)
    #     next_url = response.json()['next']
    #     print(next_url)
    # print(len(tracks))
    return tracks


async def get_playlist_items(access_token: str, playlist_id: str):
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers = {'Authorization': f'Bearer {access_token}'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, headers=headers) as response:
            pass
