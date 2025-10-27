import os
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

MY_STEAM_ID = "76561198074362405"
FRIEND_IDS = [
        "76561198209263173", # Zulvik
        "76561198199870599", # Gwyner
        "76561198210702621", # Nyethan
        "76561198937135504", # Aristeion
        "76561198011464277", # Szaffran
        MY_STEAM_ID
        ]

load_dotenv()

def get_friends_status():
    api_key = os.getenv('STEAM_API_KEY')
    if not api_key:
        raise ValueError("STEAM_API_KEY not set")

    steamids = ",".join(FRIEND_IDS)
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
