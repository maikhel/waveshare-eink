import os
import sys
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def get_friends_status():
    api_key = os.getenv('STEAM_API_KEY')
    if not api_key:
        raise ValueError("STEAM_API_KEY not set")

    friend_ids = os.getenv('STEAM_FRIEND_IDS')
    if not friend_ids:
        raise ValueError("STEAM_FRIEND_IDS not set")

    steamids = ",".join(id.strip() for id in friend_ids.split(","))
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steamids}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    statuses = {}
    for player in data['response']['players']:
        steamid = player['steamid']
        statuses[steamid] = {
            "personaname": player.get("personaname"),
            "personastate": player.get("personastate"),
            "gameextrainfo": player.get("gameextrainfo")
        }

    result = {
        "statuses": statuses,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

    with open("data/steam.json", "w") as f:
        json.dump(result, f, indent=2)

    return result

try:
    get_friends_status()
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
