from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 120)
font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)

def draw_date_and_time(full_width, full_height):
    image = Image.new('1', (full_width, full_height), 255)
    draw = ImageDraw.Draw(image)

    now = datetime.now() + timedelta(minutes=1)
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%d.%m.%Y")

    # --- Time ---
    w, h = draw.textsize(time_str, font=font_big)
    time_x = (full_width - w) // 2
    time_y = (full_height - h) // 2 - 50

    # Draw border around time (with padding)
    border_padding = 20
    border_x1 = time_x - border_padding
    border_y1 = time_y - border_padding
    border_x2 = time_x + w + border_padding
    border_y2 = time_y + h + border_padding * 2
    draw.rectangle([border_x1, border_y1, border_x2, border_y2], outline=0, width=3)

    draw.text((time_x, time_y), time_str, font=font_big, fill=0)

    # --- Date ---
    dw, dh = draw.textsize(date_str, font=font_small)
    date_x = (full_width - dw) // 2
    date_y = full_height - dh - 20
    draw.text((date_x, date_y), date_str, font=font_small, fill=0)

    return image
