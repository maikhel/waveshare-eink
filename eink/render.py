"""Composes a full panel image: the header strip plus the active screen.

This is the single entry point used by both `clock.py` (the device) and
`demo.py` (the desktop preview), so the two can never drift apart.
"""
from . import theme
from .dates import header_date
from .layout import Canvas

NO_SCREEN_MESSAGE = "Nothing to show right now."


def _ink_centered_y(canvas, rect, text, size):
    """Vertical position that centres a string's ink inside `rect`."""
    bbox = canvas.text_bbox(text, size)
    return rect.center_y_for(bbox[3] - bbox[1]) - bbox[1]


def draw_header(canvas, rect, ctx, slide, config):
    """Time and date on the left, rotation dots on the right."""
    if config.show_clock:
        time_str = ctx.now.strftime("%H:%M")
        x = rect.x + theme.MARGIN
        canvas.text((x, _ink_centered_y(canvas, rect, time_str, theme.HEADER_TIME)),
                    time_str, theme.HEADER_TIME)

        x += canvas.text_width(time_str, theme.HEADER_TIME) + theme.HEADER_GAP
        date_str = header_date(ctx.now)
        canvas.text((x, _ink_centered_y(canvas, rect, date_str, theme.HEADER_DATE)),
                    date_str, theme.HEADER_DATE)

    if config.show_indicator and slide.total > 1:
        draw_indicator(canvas, rect, slide)

    canvas.line([rect.x, rect.bottom, rect.right, rect.bottom])


def draw_indicator(canvas, rect, slide):
    """One dot per eligible screen; the active one is filled."""
    size, gap = theme.DOT_DIAMETER, theme.DOT_GAP
    stride = size + gap
    total_w = slide.total * size + (slide.total - 1) * gap

    x = rect.right - theme.MARGIN - total_w
    y = rect.center_y_for(size)

    for i in range(slide.total):
        box = [x, y, x + size, y + size]
        canvas.ellipse(box, fill=0 if i == slide.position else None, outline=0)
        x += stride


def draw(ctx, width, height, slide, config):
    """Render one full panel image for the given slide."""
    canvas = Canvas.blank(width, height, ctx.fonts)
    header, body = canvas.bounds.split_top(theme.HEADER_HEIGHT)

    draw_header(canvas, header, ctx, slide, config)

    if slide.is_empty:
        canvas.text_centered(body, body.center_y_for(theme.BODY),
                             NO_SCREEN_MESSAGE, theme.BODY)
    else:
        slide.screen.render(canvas, body, ctx)

    return canvas.image
