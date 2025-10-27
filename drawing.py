import json
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

weather_icon_mapping = {
    "01d": "wi-day-sunny-big.png",      # clear sky day
    "01n": "wi-day-sunny-big.png",      # clear sky night (fallback to day)
    "02d": "wi-day-cloudy-big.png",     # few clouds day
    "02n": "wi-day-cloudy-big.png",     # few clouds night
    "03d": "wi-cloudy-big.png",         # scattered clouds
    "03n": "wi-cloudy-big.png",
    "04d": "wi-cloudy-big.png",         # broken clouds
    "04n": "wi-cloudy-big.png",
    "09d": "wi-showers-big.png",        # shower rain
    "09n": "wi-showers-big.png",
    "10d": "wi-rain-big.png",           # rain
    "10n": "wi-rain-big.png",
    "11d": "wi-storm-showers-big.png",  # thunderstorm
    "11n": "wi-storm-showers-big.png",
    "13d": "wi-snowflake-cold-big.png", # snow
    "13n": "wi-snowflake-cold-big.png",
    "50d": "wi-fog-big.png",            # mist
    "50n": "wi-fog-big.png"
}

day_mapping = {
    'Mon': 'Pon',
    'Tue': 'Wt',
    'Wed': 'Śr',
    'Thu': 'Czw',
    'Fri': 'Pt',
    'Sat': 'Sob',
    'Sun': 'Nie'
}

def draw_weather_info(image, full_width, full_height, font):
    # Load weather data
    with open('data/weather.json', 'r') as f:
        weather = json.load(f)

    current = weather['current']
    forecast = weather['forecast']

    # Draw current weather (top right)
    temp_text = f"{current['temp']}°C"
    icon_code = current['icon']
    icon_file = weather_icon_mapping.get(icon_code, 'wi-alien-big.png')
    icon_path = os.path.join('assets', 'weather', icon_file)
    icon_img = Image.open(icon_path).convert('RGBA')
    bg = Image.new('RGBA', icon_img.size, (255, 255, 255, 255))
    bg.paste(icon_img, (0, 0), icon_img)
    icon_img = bg.convert('1')
    icon_size = 64
    icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(image)
    font_small = ImageFont.truetype(font, 40)

    temp_bbox = draw.textbbox((0, 0), temp_text, font=font_small)
    temp_w = temp_bbox[2] - temp_bbox[0]
    total_w = icon_size + 10 + temp_w
    x_start = full_width - total_w - 20
    icon_x = x_start + 10
    temp_x = x_start + icon_size + 10
    temp_y = 20
    text_center_y = temp_y + (temp_bbox[1] + temp_bbox[3]) / 2
    icon_y = int(text_center_y - icon_size / 2)
    image.paste(icon_img, (icon_x, icon_y))
    draw.text((temp_x, temp_y), temp_text, font=font_small, fill=0)

    # Draw forecast (centered at bottom)
    forecast_y = full_height - 150
    icon_size = 48
    font_day = ImageFont.truetype(font, 24)
    font_temp = ImageFont.truetype(font, 32)
    item_width = 100
    total_width = len(forecast) * item_width + (len(forecast) - 1) * 60
    start_x = (full_width - total_width) // 2
    x = start_x
    for i, day in enumerate(forecast):
        day_of_week = datetime.fromisoformat(day['date']).strftime('%a')
        day_pl = day_mapping.get(day_of_week, day_of_week)
        # Day text
        day_bbox = draw.textbbox((0, 0), day_pl, font=font_day)
        day_w = day_bbox[2] - day_bbox[0]
        day_x = x + (item_width - day_w) // 2
        draw.text((day_x, forecast_y), day_pl, font=font_day, fill=0)
        # Icon
        icon_code = day['midday']['icon']
        icon_file = weather_icon_mapping.get(icon_code, 'wi-alien-big.png')
        icon_path = os.path.join('assets', 'weather', icon_file)
        icon_img = Image.open(icon_path).convert('RGBA')
        bg = Image.new('RGBA', icon_img.size, (255, 255, 255, 255))
        bg.paste(icon_img, (0, 0), icon_img)
        icon_img = bg.convert('1')
        icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        icon_x = x + (item_width - icon_size) // 2
        icon_y = forecast_y + 30
        image.paste(icon_img, (icon_x, icon_y))
        # Temps
        temp_text = f"{day['midday']['temp']}°/{day['midnight']['temp']}°"
        temp_bbox = draw.textbbox((0, 0), temp_text, font=font_temp)
        temp_w = temp_bbox[2] - temp_bbox[0]
        temp_x = x + (item_width - temp_w) // 2
        temp_y = icon_y + icon_size + 10
        draw.text((temp_x, temp_y), temp_text, font=font_temp, fill=0)
        # Draw vertical line between entries (except after last)
        if i < len(forecast) - 1:
            line_x = x + item_width + 30
            draw.line([line_x, forecast_y, line_x, forecast_y + 120], fill=0, width=1)
        x += item_width + 60

def draw_steam_friends(image, font):
    try:
        with open('data/steam.json', 'r') as f:
            steam_data = json.load(f)
    except FileNotFoundError:
        return  # Skip if no data

    statuses = steam_data.get('statuses', {})
    draw = ImageDraw.Draw(image)
    font_small = ImageFont.truetype(font, 20)

    # Load Steam icon
    icon_path = os.path.join('assets', 'steam', 'icon.png')
    icon_img = Image.open(icon_path).convert('RGBA')

    # Convert to 1-bit like weather icons
    bg = Image.new('RGBA', icon_img.size, (255, 255, 255, 255))
    bg.paste(icon_img, (0, 0), icon_img)
    icon_img = bg.convert('1')

    # Position icon at top-left
    icon_x = 20
    icon_y = 20
    image.paste(icon_img, (icon_x, icon_y))

    # Position text next to icon
    text_x = icon_x + 64 + 10
    text_y = icon_y + 10
    line_height = 25

    online_friends = []
    for steamid, status in statuses.items():
        personastate = status.get('personastate', 0)
        if personastate > 0:  # Online
            nickname = status.get('personaname', 'Unknown')
            game = status.get('gameextrainfo')
            if game:
                text = f"{nickname} plays {game}"
            else:
                text = f"{nickname} is online"
            online_friends.append(text)

    if online_friends:
        for text in online_friends:
            draw.text((text_x, text_y), text, font=font_small, fill=0)
            text_y += line_height
    else:
        draw.text((text_x, text_y), "Noone is having fun on Steam", font=font_small, fill=0)

def draw_date_and_time(full_width, full_height, font):
    font_big = ImageFont.truetype(font, 120)

    image = Image.new('1', (full_width, full_height), 255)
    draw = ImageDraw.Draw(image)

    now = datetime.now() + timedelta(minutes=1)
    time_str = now.strftime("%H:%M")

    # --- Time ---
    bbox = draw.textbbox((0, 0), time_str, font=font_big)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    time_x = (full_width - w) // 2
    time_y = (full_height - h) // 2 - 50

    # Draw border around time (with padding)
    border_padding = 20
    border_x1 = time_x - border_padding
    border_y1 = time_y + bbox[1] - border_padding  # Use bbox top offset
    border_x2 = time_x + w + border_padding
    border_y2 = time_y + bbox[3] + border_padding  # Use bbox bottom offset
    draw.rectangle([border_x1, border_y1, border_x2, border_y2], outline=0, width=3)

    draw.text((time_x, time_y), time_str, font=font_big, fill=0)

    return image
