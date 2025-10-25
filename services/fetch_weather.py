import requests
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

def fetch_weather():
    api_key = os.getenv('OPEN_WEATHER_API_KEY')
    if not api_key:
        raise ValueError("OPEN_WEATHER_API_KEY environment variable not set")

    # "Warsaw,PL"
    lon = 21.017532
    lat = 52.237049

    url = f"https://api.openweathermap.org/data/2.5/forecast?lon={lon}&lat={lat}&appid={api_key}&units=metric&lang=pl"

    response = requests.get(url)
    response.raise_for_status()  # Raise error for bad status codes

    data = response.json()

    forecast_list = data.get('list', [])
    if not forecast_list:
        raise ValueError("No forecast data")

    # Treat first item as current weather
    first = forecast_list[0]
    current = {
        "temp": round(first['main']['temp']),
        "description": first['weather'][0]['description'],
        "icon": first['weather'][0]['icon']
    }

    # Process forecast for midday and midnight
    grouped = defaultdict(dict)
    for item in forecast_list:
        dt = datetime.fromisoformat(item['dt_txt'])
        date_str = dt.date().isoformat()
        hour = dt.hour
        if hour == 12:  # Midday
            grouped[date_str]['midday'] = {
                'temp': round(item['main']['temp']),
                'icon': item['weather'][0]['icon']
            }
        elif hour == 0:  # Midnight
            grouped[date_str]['midnight'] = {
                'temp': round(item['main']['temp']),
                'icon': item['weather'][0]['icon']
            }

    # Build forecast for next 5 days
    forecast = []
    today = datetime.now().date()
    for i in range(1, 6):  # Days 1-5
        target_date = (today + timedelta(days=i)).isoformat()
        if target_date in grouped and 'midday' in grouped[target_date] and 'midnight' in grouped[target_date]:
            forecast.append({
                'date': target_date,
                'midday': grouped[target_date]['midday'],
                'midnight': grouped[target_date]['midnight']
            })

    weather_info = {
        'current': current,
        'forecast': forecast
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, '..', 'data', 'weather.json')
    with open(data_file, 'w') as f:
        json.dump(weather_info, f, indent=2)

try:
    fetch_weather()
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
