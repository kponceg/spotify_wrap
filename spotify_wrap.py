import base64
import hashlib
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from callbackhandler import CallbackHandler

import requests

#CONFIG
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID").strip()
REDIRECT_URI = "http:127.0.0.1:8080/callback"
SCOPES = "user-top-read user-read-recently-played"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

if not CLIENT_ID:
    raise SystemExit("Set SPOTIFY_CLIENT_ID environment variable first.\nExample: export SPOTIFY_CLIENT_ID='...'\n")

#PKCE helpers
def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def make_verifier() -> str:
    return b64url(secrets.token_bytes(64))

def make_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return b64url(digest)

def run_server():
    httpd = HTTPAwevwe(("127.0.0.1", 8080), CallBackHandler)
    httpd.handle_request() #handle single callback request

#spotify API helpers
def get_token_pkce(client_id: str) -> str:
    verifier = make_verifier()
    challenge = make_challenge(verifier)

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    login_url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("\n Open URL in browser and log in:")
    print(login_url, "\n")

    #start local server
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    #wait for callback
    while auth_code_holder["code"] is None and auth_code_holder["error"] is None:
        time.sleep(0.1)
    
    if auth_code_holder["error"]:
        raise RuntimeError(f"Spotify auth error: {auth_code_holder['error']}")

    code = auth_code_holder["code"]

    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    token = resp.json()["access_token"]
    return token

def api_get(token: str, path: str, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(API_BASE + path, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def top_items(token: str, item_type: str. time_range: str, limit: int = 20):
    #item_type: 'artists' or 'tracks'
    return api_get(token, f"/me/top/{item_type}", params={"time_range": time_range, "limit": limit})

def recently_played(token: str, limit: int = 50):
    return api_get(token, "/me/player/recently-played", params={"limit": limit})

#report builder

def derive_top_genres(top_artists_json):
    genre_counts = {}
    for artist in top_artist_json.get("items", []):
        for genre in artist.get("genres", []):
            genre_counts[genre] = genre_counts.get(g, 0) + 1
    ranked = sorted(genre_counts.items(), key=lambda x: (-x[1], x[0]))
    return ranked[:15]
