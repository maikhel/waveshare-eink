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

FULL_REFRESH_EVERY = 10  # partials between full refreshes
NIGHT_START_HOUR = 0     # 00:00 inclusive
NIGHT_END_HOUR = 7       # 07:00 exclusive

def is_night(now):
    return NIGHT_START_HOUR <= now.hour < NIGHT_END_HOUR

def run_clock():
    logging.info("Starting E-Ink clock")

    epd = epd7in5_V2.EPD()
    logging.debug("Initializing display")

    epd.init()
    epd.Clear()
    epd.sleep()

    partials_since_full = FULL_REFRESH_EVERY  # force a full refresh on first draw
    sleeping_for_night = False

    try:
        while True:
            now = datetime.now()

            if is_night(now):
                if not sleeping_for_night:
                    logging.info("Entering night mode: clearing and sleeping display")
                    epd.init()
                    epd.Clear()
                    epd.sleep()
                    sleeping_for_night = True
                time.sleep(60)
                continue

            if sleeping_for_night:
                logging.info("Exiting night mode")
                sleeping_for_night = False
                partials_since_full = FULL_REFRESH_EVERY  # force full refresh on wake

            logging.debug("Drawing current date and time")
            image = drawing.draw_date_and_time(epd.width, epd.height, font)
            drawing.draw_weather_info(image, epd.width, epd.height, font)
            drawing.draw_steam_or_github(image, font)

            buf = epd.getbuffer(image)

            if partials_since_full >= FULL_REFRESH_EVERY:
                logging.info("Full refresh")
                epd.init_fast()
                epd.display(buf)
                partials_since_full = 0
            else:
                logging.info("Partial refresh (%d/%d)", partials_since_full + 1, FULL_REFRESH_EVERY)
                epd.init_fast()
                epd.display_Partial(buf, 0, 0, epd.width, epd.height)
                partials_since_full += 1

            epd.sleep()

            logging.info("Done. Going to sleep 60 seconds")
            time.sleep(60)

    except KeyboardInterrupt:
        logging.warning("Interrupted by user, clearing display")
        epd.init()
        epd.Clear()
        epd.sleep()
        logging.info("Exiting cleanly")
    except Exception as e:
        logging.error("Fatal error occured: %s", e, exc_info=True)
        try:
            epd.init()
            epd.Clear()
            epd.sleep()
        except Exception:
            pass
        logging.info("Exiting cleanly")

if __name__ == "__main__":
    run_clock()
