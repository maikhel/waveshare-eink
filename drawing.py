import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

def draw_weather_info(image, full_width, full_height, font):
    # Load weather data
    with open('data/weather.json', 'r') as f:
        weather = json.load(f)

    # Format text
    temp_text = f"{weather['temp']}°C"
    desc_text = weather['description'].title()
    time_text = weather['last_updated'][11:16]  # Extract HH:MM from ISO timestamp

    # Use existing image draw
    draw = ImageDraw.Draw(image)
    font_small = ImageFont.truetype(font, 40)
    font_smaller = ImageFont.truetype(font, 20)

    # Calculate positions for top right
    temp_bbox = draw.textbbox((0, 0), temp_text, font=font_small)
    desc_bbox = draw.textbbox((0, 0), desc_text, font=font_smaller)
    time_bbox = draw.textbbox((0, 0), time_text, font=font_smaller)

    temp_w = temp_bbox[2] - temp_bbox[0]
    desc_w = desc_bbox[2] - desc_bbox[0]
    time_w = time_bbox[2] - time_bbox[0]
    max_w = max(temp_w, desc_w, time_w)

    desc_x = full_width - desc_w - 20
    time_x = desc_x + (desc_w - time_w) // 2
    temp_x = desc_x + (desc_w - temp_w) // 2
    temp_y = 20
    desc_y = temp_y + (temp_bbox[3] - temp_bbox[1]) + 10  # padding between temp and desc
    time_y = desc_y + (desc_bbox[3] - desc_bbox[1]) + 5   # padding between desc and time

    # Draw text
    draw.text((temp_x, temp_y), temp_text, font=font_small, fill=0)
    draw.text((desc_x, desc_y), desc_text, font=font_smaller, fill=0)
    draw.text((time_x, time_y), time_text, font=font_smaller, fill=0)

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
