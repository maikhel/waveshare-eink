import requests

import common

SUMMARIES = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"


def fetch_steam():
    api_key = common.require_env('STEAM_API_KEY')
    friend_ids = common.require_env('STEAM_FRIEND_IDS')
    steamids = ",".join(part.strip() for part in friend_ids.split(","))

    response = requests.get(f"{SUMMARIES}?key={api_key}&steamids={steamids}")
    response.raise_for_status()

    statuses = {
        player['steamid']: {
            'personaname': player.get('personaname'),
            'personastate': player.get('personastate'),
            'gameextrainfo': player.get('gameextrainfo'),
        }
        for player in response.json()['response']['players']
    }

    return {'statuses': statuses}


common.run('steam', fetch_steam)
