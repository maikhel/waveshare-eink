#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2
from datetime import datetime
import logging
import time

from eink import config as config_module
from eink import render, screens, theme
from eink.playlist import Playlist
from eink.screens import Context

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

FULL_REFRESH_EVERY = 10  # partials between full refreshes
NIGHT_START_HOUR = 0     # 00:00 inclusive
NIGHT_END_HOUR = 7       # 07:00 exclusive

def is_night(now):
    return NIGHT_START_HOUR <= now.hour < NIGHT_END_HOUR

def describe_age(age):
    if age is None:
        return "age unknown"
    minutes = int(age.total_seconds() // 60)
    if minutes < 60:
        return f"{minutes}m old"
    return f"{minutes // 60}h{minutes % 60:02d}m old"

def run_clock():
    logging.info("Starting E-Ink clock")

    fonts = theme.Fonts()
    config = config_module.load(known_screens=screens.REGISTRY)
    playlist = Playlist(config, screens)
    logging.info("Playlist: %s", ", ".join(e.id for e in config.entries))

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
                time.sleep(config.tick_seconds)
                continue

            if sleeping_for_night:
                logging.info("Exiting night mode")
                sleeping_for_night = False
                partials_since_full = FULL_REFRESH_EVERY  # force full refresh on wake
                playlist.reset()  # resuming mid-cycle after hours of blank is arbitrary

            ctx = Context(now=now, fonts=fonts)
            slide = playlist.tick(ctx)
            if slide.rotated:
                if slide.is_empty:
                    logging.info("Showing screen: none eligible")
                else:
                    # Data age makes a silently dead cron job visible in the log.
                    ages = ", ".join(
                        f"{source} {describe_age(ctx.age(source))}"
                        for source in slide.screen.requires)
                    logging.info("Showing screen: %s (%s)", slide.entry.id, ages)
            image = render.draw(ctx, epd.width, epd.height, slide, config)

            buf = epd.getbuffer(image)

            # A rotation replaces the whole panel, so it gets a full refresh --
            # which doubles as the periodic ghosting flush.
            if slide.rotated or partials_since_full >= FULL_REFRESH_EVERY:
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

            logging.info("Done. Going to sleep %d seconds", config.tick_seconds)
            time.sleep(config.tick_seconds)

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
