#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2
from datetime import datetime, timedelta
import logging
import time

import drawing

OUT_DIR = os.path.expanduser('~/eink/logs')
os.makedirs(OUT_DIR, exist_ok=True)
LOG_FILE = os.path.join(OUT_DIR, 'clock.log')

font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

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

    epd.init_fast()
    epd.Clear()


    last_full_refresh = datetime.now()

    try:
        while True:
            # Create a new blank image (white background)
            logging.debug("Creating new frame")

            logging.debug("Drawing current date and time")
            image = drawing.draw_date_and_time(epd.width, epd.height, font)
            drawing.draw_weather_info(image, epd.width, epd.height, font)

             # Decide refresh type
            if (datetime.now() - last_full_refresh).seconds >= 300:  # 5 minutes
                epd.init_fast()
                logging.info("Full refresh")
                epd.display(epd.getbuffer(image))
                last_full_refresh = datetime.now()
            else:
                logging.info("Partial refresh")
                epd.init_fast()
                buf = epd.getbuffer(image)
                epd.display_Partial(buf, 0, 0, epd.width, epd.height)

            # Wait until the next full minute
            logging.info("Done. Going to sleep 60 seconds")
            time.sleep(60)

    except Exception as e:
        logging.error("Fatal error occured: %s", e, exc_info=True)
        epd.init_fast()
        epd.Clear()
        epd.sleep()
        logging.info("Exiting cleanly")
    except KeyboardInterrupt:
        logging.warning("Interrupted by user, clearing display")
        epd.init()
        epd.Clear()
        epd.sleep()
        logging.info("Exiting cleanly")

if __name__ == "__main__":
    run_clock()
