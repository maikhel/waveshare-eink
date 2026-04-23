#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Deep-clean / ghost-removal routine for Waveshare 7.5" V2 e-ink panels.

Cycles the panel between solid black and solid white several times to shake
loose trapped particles that cause ghosting. Run this once when you notice
artifacts. If ghosting is gone after a few runs, the panel isn't permanently
damaged. If it remains after ~5 runs, the damage is likely permanent.

Usage:  python3 deep_clean.py
"""
import sys
import os
import time

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2
from PIL import Image

CYCLES = 5          # number of black/white flips
HOLD_SECONDS = 3    # how long to hold each solid colour

def run():
    epd = epd7in5_V2.EPD()
    print(f"Deep clean: {CYCLES} black/white cycles, {HOLD_SECONDS}s each")

    epd.init()
    epd.Clear()

    white = Image.new('1', (epd.width, epd.height), 255)
    black = Image.new('1', (epd.width, epd.height), 0)
    white_buf = epd.getbuffer(white)
    black_buf = epd.getbuffer(black)

    try:
        for i in range(CYCLES):
            print(f"Cycle {i + 1}/{CYCLES}")

            epd.init()
            epd.display(black_buf)
            time.sleep(HOLD_SECONDS)

            epd.init()
            epd.display(white_buf)
            time.sleep(HOLD_SECONDS)

        # Finish on white and put the panel to sleep
        epd.init()
        epd.Clear()
        epd.sleep()
        print("Done. Panel left blank and asleep.")

    except KeyboardInterrupt:
        epd.init()
        epd.Clear()
        epd.sleep()
        print("\nInterrupted. Panel cleared and asleep.")

if __name__ == "__main__":
    run()
