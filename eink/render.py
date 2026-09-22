"""Composes a full panel image: chrome plus the active screen.

This is the single entry point used by both `clock.py` (the device) and
`demo.py` (the desktop preview), so the two can never drift apart.
"""
from datetime import timedelta

from . import screens, theme
from .layout import Canvas

CLOCK_BORDER_PADDING = 20
CLOCK_BORDER_WIDTH = 3
CLOCK_Y_OFFSET = -50

WORK_START_HOUR = 7
WORK_END_HOUR = 18


def draw_clock(canvas, rect, ctx):
    """The big boxed HH:MM in the middle of the panel.

    Rounds up by a minute: the panel refresh lands closer to the next minute
    than the current one.
    """
    time_str = (ctx.now + timedelta(minutes=1)).strftime("%H:%M")

    bbox = canvas.text_bbox(time_str, theme.TIME)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = rect.center_x_for(w)
    y = rect.center_y_for(h) + CLOCK_Y_OFFSET

    pad = CLOCK_BORDER_PADDING
    canvas.rectangle(
        [x - pad, y + bbox[1] - pad, x + w + pad, y + bbox[3] + pad],
        outline=0, width=CLOCK_BORDER_WIDTH,
    )
    canvas.text((x, y), time_str, theme.TIME)


def active_screen_id(now):
    """Temporary stand-in for the playlist: work during the day, Steam after."""
    is_weekday = now.weekday() < 5
    is_work_time = WORK_START_HOUR <= now.hour < WORK_END_HOUR
    return 'work' if (is_weekday and is_work_time) else 'steam'


def draw(ctx, width, height):
    """Render one full panel image."""
    canvas = Canvas.blank(width, height, ctx.fonts)
    rect = canvas.bounds

    draw_clock(canvas, rect, ctx)

    weather = screens.get('weather')
    if weather.available(ctx):
        weather.render(canvas, rect, ctx)

    active = screens.get(active_screen_id(ctx.now))
    if active.available(ctx):
        active.render(canvas, rect, ctx)

    return canvas.image
