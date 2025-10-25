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

def draw_weather_info(image, full_width, full_height, font):
    # Load weather data
    with open('data/weather.json', 'r') as f:
        weather = json.load(f)

    # Format text
    temp_text = f"{weather['temp']}°C"

    # Get weather icon
    icon_code = weather['icon']
    icon_file = weather_icon_mapping.get(icon_code, 'wi-cloudy-big.png')
    icon_path = os.path.join('assets', 'weather', icon_file)
    icon_img = Image.open(icon_path).convert('RGBA')
    # Composite on white background to handle transparency
    bg = Image.new('RGBA', icon_img.size, (255, 255, 255, 255))
    bg.paste(icon_img, (0, 0), icon_img)
    icon_img = bg.convert('1')
    icon_size = 64
    icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    # Use existing image draw
    draw = ImageDraw.Draw(image)
    font_small = ImageFont.truetype(font, 40)

    # Calculate positions for top right: icon left of temp
    temp_bbox = draw.textbbox((0, 0), temp_text, font=font_small)
    temp_w = temp_bbox[2] - temp_bbox[0]
    temp_h = temp_bbox[3] - temp_bbox[1]
    total_w = icon_size + 10 + temp_w  # icon + padding + temp

    x_start = full_width - total_w - 20
    icon_x = x_start + 10
    temp_x = x_start + icon_size + 10
    temp_y = 20

    # Center icon vertically with text
    text_center_y = temp_y + (temp_bbox[1] + temp_bbox[3]) / 2
    icon_y = int(text_center_y - icon_size / 2)

    # Draw
    image.paste(icon_img, (icon_x, icon_y))
    draw.text((temp_x, temp_y), temp_text, font=font_small, fill=0)

def draw_date_and_time(full_width, full_height, font):
    font_big = ImageFont.truetype(font, 120)
    font_small = ImageFont.truetype(font, 40)

    image = Image.new('1', (full_width, full_height), 255)
    draw = ImageDraw.Draw(image)

    now = datetime.now() + timedelta(minutes=1)
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%d.%m.%Y")

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

    # --- Date ---
    bbox_date = draw.textbbox((0, 0), date_str, font=font_small)
    dw, dh = bbox_date[2] - bbox_date[0], bbox_date[3] - bbox_date[1]
    date_x = (full_width - dw) // 2
    date_y = full_height - dh - 20
    draw.text((date_x, date_y), date_str, font=font_small, fill=0)

    return image
