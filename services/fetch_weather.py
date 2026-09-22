import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import common

# Warsaw, PL
LON = 21.017532
LAT = 52.237049

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

MIDDAY_HOUR = 15
NIGHT_HOUR = 3        # usually the coolest point
FORECAST_DAYS = 5
HOURLY_STEPS = 5      # 3h apart, so the rest of today plus a little


def _local_time(unix_seconds, shift_seconds):
    """Format an API timestamp in the forecast location's own timezone."""
    moment = datetime.fromtimestamp(unix_seconds, tz=timezone.utc) + timedelta(seconds=shift_seconds)
    return moment.strftime('%H:%M')


def fetch_current(api_key):
    params = {'lat': LAT, 'lon': LON, 'appid': api_key, 'units': 'metric', 'lang': 'pl'}
    response = requests.get(CURRENT_URL, params=params)
    response.raise_for_status()
    data = response.json()

    shift = data.get('timezone', 0)
    return {
        'temp': round(data['main']['temp']),
        'feels_like': round(data['main']['feels_like']),
        'humidity': data['main']['humidity'],
        'description': data['weather'][0]['description'],
        'icon': data['weather'][0]['icon'],
        'sunrise': _local_time(data['sys']['sunrise'], shift),
        'sunset': _local_time(data['sys']['sunset'], shift),
    }


def fetch_forecast(api_key):
    """Returns (hourly, daily) from the same 3-hourly series."""
    params = {'lat': LAT, 'lon': LON, 'appid': api_key, 'units': 'metric', 'lang': 'pl'}
    response = requests.get(FORECAST_URL, params=params)
    response.raise_for_status()

    steps = response.json().get('list', [])
    if not steps:
        raise ValueError("No forecast data")

    hourly = [
        {
            'time': datetime.fromisoformat(step['dt_txt']).strftime('%H:%M'),
            'temp': round(step['main']['temp']),
            'icon': step['weather'][0]['icon'],
            'pop': round(step.get('pop', 0) * 100),
        }
        for step in steps[:HOURLY_STEPS]
    ]

    grouped = defaultdict(dict)
    for step in steps:
        at = datetime.fromisoformat(step['dt_txt'])
        slot = {'midday': MIDDAY_HOUR, 'midnight': NIGHT_HOUR}
        for name, hour in slot.items():
            if at.hour == hour:
                grouped[at.date().isoformat()][name] = {
                    'temp': round(step['main']['temp']),
                    'icon': step['weather'][0]['icon'],
                    'pop': round(step.get('pop', 0) * 100),
                }

    daily = []
    today = datetime.now().date()
    for offset in range(1, FORECAST_DAYS + 1):
        date = (today + timedelta(days=offset)).isoformat()
        day = grouped.get(date, {})
        if 'midday' in day and 'midnight' in day:
            daily.append({'date': date, 'midday': day['midday'], 'midnight': day['midnight']})

    return hourly, daily


def fetch_weather():
    api_key = common.require_env('OPEN_WEATHER_API_KEY')
    hourly, daily = fetch_forecast(api_key)
    return {
        'current': fetch_current(api_key),
        'hourly': hourly,
        'forecast': daily,
    }


common.run('weather', fetch_weather)
