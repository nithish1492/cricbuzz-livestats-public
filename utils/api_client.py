import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("CRICBUZZ_API_BASE_URL", "https://cricbuzz-cricket.p.rapidapi.com").rstrip("/")
API_HOST = os.getenv("CRICBUZZ_API_HOST", "cricbuzz-cricket.p.rapidapi.com")
API_KEY = os.getenv("CRICBUZZ_API_KEY", "").strip()
LIVE_PATH = os.getenv("CRICBUZZ_LIVE_MATCHES_PATH", "matches/v1/live")
SCORE_PATH = os.getenv("CRICBUZZ_LIVESCORE_PATH", "mcenter/v1/{match_id}/livescore")
CARD_PATH = os.getenv("CRICBUZZ_SCORECARD_PATH", "mcenter/v1/{match_id}/hscard")
SERIES_PATH = os.getenv("CRICBUZZ_SERIES_LIST_PATH", "series/v1/international")

def api_configuration():
    return {"base_url": BASE_URL, "host": API_HOST, "configured": bool(API_KEY and API_KEY != "PASTE_YOUR_RAPIDAPI_KEY_HERE")}

def fetch_endpoint(endpoint, params=None):
    if not API_KEY or API_KEY == "PASTE_YOUR_RAPIDAPI_KEY_HERE":
        raise RuntimeError("API key missing. Copy .env.example to .env and set CRICBUZZ_API_KEY.")
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    try:
        r = requests.get(url, headers={"x-rapidapi-host": API_HOST, "x-rapidapi-key": API_KEY, "Accept": "application/json"}, params=params, timeout=25)
    except requests.RequestException as e:
        raise RuntimeError(f"API connection failed: {e}") from e
    if not r.ok:
        detail = r.text[:350].replace(API_KEY, "[redacted]")
        raise RuntimeError(f"API HTTP {r.status_code}: {detail}")
    try:
        return r.json()
    except ValueError as e:
        raise RuntimeError("API returned invalid JSON.") from e

def fetch_live_matches():
    return fetch_endpoint(LIVE_PATH)

def fetch_livescore(match_id):
    return fetch_endpoint(SCORE_PATH.format(match_id=match_id))

def fetch_scorecard(match_id):
    return fetch_endpoint(CARD_PATH.format(match_id=match_id))

def fetch_series_list():
    return fetch_endpoint(SERIES_PATH)
