"""Small drawing pieces shared between screens."""
from . import theme
from .layout import Rect

HEADER_HEIGHT = 46
RULE_OFFSET = 34


def section_header(canvas, rect, title, count=None):
    """Draw a centred band heading with an optional count, and return the rect below."""
    canvas.text_centered(rect, rect.y, title, theme.SECTION)
    if count is not None:
        canvas.text_right(rect, rect.y + 2, str(count), theme.COUNT)

    y = rect.y + RULE_OFFSET
    canvas.line([rect.x, y, rect.right, y])

    return Rect(rect.x, rect.y + HEADER_HEIGHT, rect.w, rect.h - HEADER_HEIGHT)


def marker(canvas, x, y, shape, size=12):
    """A small status glyph, drawn rather than typed.

    The display fonts differ between the Pi (DejaVu) and a desktop preview
    (Arial), and symbol coverage differs with them -- a missing glyph renders as
    a blank or a box only on the device, where it is hardest to notice.
    """
    box = [x, y, x + size, y + size]
    if shape == 'filled':
        canvas.ellipse(box, fill=0)
    elif shape == 'hollow':
        canvas.ellipse(box, fill=None, outline=0)
    elif shape == 'square':
        canvas.rectangle(box, outline=0)
    elif shape == 'triangle':
        canvas.polygon([(x + size // 2, y), (x + size, y + size), (x, y + size)], fill=0)
