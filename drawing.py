from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 120)
font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)

def draw_date_and_time(full_width, full_height):
    image = Image.new('1', (full_width, full_height), 255)
    draw = ImageDraw.Draw(image)

    # Get current time
    now = datetime.now() + timedelta(minutes=1)
    now = now.strftime("%H:%M")
    date = datetime.now().strftime("%d.%m.%Y")

    # Center the text on screen
    w, h = draw.textsize(now, font=font_big)
    time_x = (full_width - w) // 2
    time_y = (full_height - h) // 2

    draw.text((time_x, time_y), now, font=font_big, fill=0)

    dw, dh = draw.textsize(date, font=font_small)
    date_x = (full_width - dw) // 2
    date_y = full_height - dh - 20   # 20px margin from bottom
    draw.text((date_x, date_y), date, font=font_small, fill=0)

    return image
