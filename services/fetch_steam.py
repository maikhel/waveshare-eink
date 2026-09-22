import requests

import common

SUMMARIES_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
RECENT_URL = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"

MAX_RECENT = 5


def fetch_friends(api_key):
    friend_ids = common.require_env('STEAM_FRIEND_IDS')
    steamids = ",".join(part.strip() for part in friend_ids.split(","))

    response = requests.get(SUMMARIES_URL, params={'key': api_key, 'steamids': steamids})
    response.raise_for_status()

    return {
        player['steamid']: {
            'personaname': player.get('personaname'),
            'personastate': player.get('personastate'),
            'gameextrainfo': player.get('gameextrainfo'),
        }
        for player in response.json()['response']['players']
    }


def fetch_recent(api_key):
    """My own playtime over the last two weeks.

    Returns an empty list rather than failing: this needs the profile's game
    details to be public, and it is not worth losing the friends list over.
    """
    steam_id = common.require_env('STEAM_USER_ID')

    response = requests.get(RECENT_URL, params={'key': api_key, 'steamid': steam_id,
                                                'count': MAX_RECENT})
    response.raise_for_status()

    games = response.json().get('response', {}).get('games', [])
    return [
        {'name': game.get('name'), 'minutes': game.get('playtime_2weeks', 0)}
        for game in games if game.get('name')
    ]


def fetch_steam():
    api_key = common.require_env('STEAM_API_KEY')
    return {
        'statuses': fetch_friends(api_key),
        'recent': fetch_recent(api_key),
    }


common.run('steam', fetch_steam)
