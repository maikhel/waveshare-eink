from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import drawing

WIDTH, HEIGHT = 800, 480  # 7.5'' screen size

def draw_demo():
    font = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    image = drawing.draw_date_and_time(WIDTH, HEIGHT, font)
    drawing.draw_weather_info(image, WIDTH, HEIGHT, font)
    # drawing.draw_steam_friends(image, font)
    drawing.draw_github_info(image, font)

    image.show()
    image.save("preview.png")


draw_demo()
