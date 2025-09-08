#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import logging
import time

OUT_DIR = os.path.expanduser('~/eink/logs')
os.makedirs(OUT_DIR, exist_ok=True)
LOG_FILE = os.path.join(OUT_DIR, 'clock.log')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[
                        logging.FileHandler(LOG_FILE),
                        logging.StreamHandler(sys.stdout)
                    ]
                    )

def run_clock():
    logging.info("Starting E-Ink clock")

    epd = epd7in5_V2.EPD()
    logging.debug("Initializing display")


    epd.init()
    epd.Clear()

    # Pick a font and size you like
    font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 120)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)

    try:
        while True:
            # Create a new blank image (white background)
            logging.debug("Creating new frame")

            image = Image.new('1', (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(image)

            # Get current time
            now = datetime.now() + timedelta(minutes=1)
            now = now.strftime("%H:%M")
            date = datetime.now().strftime("%d.%m.%Y")

            logging.info(f"Updating display with time {now} and date {date}")

            # Center the text on screen
            w, h = draw.textsize(now, font=font_big)
            time_x = (epd.width - w) // 2
            time_y = (epd.height - h) // 2

            draw.text((time_x, time_y), now, font=font_big, fill=0)

            dw, dh = draw.textsize(date, font=font_small)
            date_x = (epd.width - dw) // 2
            date_y = epd.height - dh - 20   # 20px margin from bottom
            draw.text((date_x, date_y), date, font=font_small, fill=0)

            # Display
            epd.display(epd.getbuffer(image))

            logging.info("Done. Going to sleep 60 seconds")
            # Wait until the next full minute
            time.sleep(60)

    except KeyboardInterrupt:
        logging.warning("Interrupted by user, clearing display")
        epd.init()
        epd.Clear()
        epd.sleep()
        logging.info("Exiting cleanly")

if __name__ == "__main__":
    run_clock()
