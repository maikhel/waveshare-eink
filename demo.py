"""Render the panel to preview.png on a desktop, without the e-ink hardware.

Uses example_data/ so it works without the fetchers having run.
"""
from datetime import datetime

from eink import render, theme
from eink.screens import Context

WIDTH, HEIGHT = 800, 480  # 7.5'' screen size


def draw_demo():
    ctx = Context(now=datetime.now(), fonts=theme.Fonts(), data_dir='example_data')
    image = render.draw(ctx, WIDTH, HEIGHT)

    image.show()
    image.save("preview.png")


draw_demo()
