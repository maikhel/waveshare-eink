#!/usr/bin/python
# -*- coding:utf-8 -*-

from waveshare_epd import epd7in5_V2

def shutdown_display():
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()
    epd.Clear()
    epd.Clear()
    epd.sleep()

if __name__ == "__main__":
    shutdown_display()
