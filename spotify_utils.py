# spotify_utils.py

import os
import re
import requests
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)




def extract_spotify_id(url: str):
    pattern = r"spotify\.com/(track|album)/([A-Za-z0-9]+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Invalid Spotify URL.")
    return match.group(1), match.group(2)


def get_spotify_metadata(spotify_url: str):
    try:
        kind, sid = extract_spotify_id(spotify_url)

        if kind == "track":
            data = sp.track(sid)
        elif kind == "album":
            data = sp.album(sid)
        else:
            raise ValueError("Unsupported Spotify content type.")

        title = data["name"]
        artist = ", ".join(a["name"] for a in data["artists"])
        cover_url = data["album"]["images"][0]["url"] if kind == "track" else data["images"][0]["url"]
        track_id = spotify_url.split("/")[-1].split("?")[0]

        # Do not validate — just generate the Spotify Code image URL
        code_url = f"https://scannables.scdn.co/uri/plain/png/000000/FFFFFF/800/spotify:{kind}:{sid}"

        return {
            "song_id": track_id, 
            "title": title,
            "artist": artist,
            "cover_url": cover_url,
            "code_url": code_url,
        }

    except Exception as e:
        print("⚠️ Error fetching metadata:", e)
        return None
