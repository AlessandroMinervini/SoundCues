from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from os import getenv

from loguru import logger
from .classes import Status, Error, Response


sp_client = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=getenv("SPOTIFY_CLIENT_ID"),
        client_secret=getenv("SPOTIFY_CLIENT_SECRET"),
    )
)


def sp_search(query, limit=10):
    try:
        response = sp_client.search(q=query, limit=limit, type="playlist")

        playlists = response["playlists"]["items"]

        cleaned_playlists = [item for item in playlists if item is not None]

        playlist = cleaned_playlists[0]

        result = {
            "query": query,
            "name": playlist.get("name"),
            "link": playlist.get("external_urls", {}).get("spotify"),
            "cover": playlist.get("images", [{}])[0].get("url"),
        }

        return result

    except Error as e:
        logger.error(f"{e}")

        return Response(
            status=Status.NOT_FOUND,
            status_message=e.status_message,
        )
