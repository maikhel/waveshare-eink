import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Get API key from environment
api_key = os.getenv('OPEN_WEATHER_API_KEY')
if not api_key:
    raise ValueError("OPEN_WEATHER_API_KEY environment variable not set")

city = "Warsaw,PL"

# Construct API URL
url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=pl"

# Make request
response = requests.get(url)
response.raise_for_status()  # Raise error for bad status codes

# Parse response
data = response.json()

# Extract and format data
weather_info = {
    "last_updated": datetime.fromtimestamp(data['dt']).isoformat(),
    "temp": round(data['main']['temp']),
    "description": data['weather'][0]['description'],
    "icon": data['weather'][0]['icon']
}

# Save to file
script_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(script_dir, '..', 'data', 'weather.json')
with open(data_file, 'w') as f:
    json.dump(weather_info, f, indent=2)
