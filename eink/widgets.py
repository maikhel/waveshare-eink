"""Small drawing pieces shared between screens."""
from . import theme
from .layout import Rect

HEADER_HEIGHT = 46
RULE_OFFSET = 34
ICON_GAP = 10


def section_header(canvas, rect, title, count=None, icon=None, icon_size=28,
                   rule=True):
    """Draw a centred band heading with an optional count, and return the rect below.

    An `icon` is centred together with the title as one group, so the pair stays
    balanced whatever the heading says.
    """
    title_w = canvas.text_width(title, theme.SECTION)
    group_w = title_w + (icon_size + ICON_GAP if icon else 0)
    x = rect.center_x_for(group_w)

    if icon:
        canvas.paste(canvas.icon(*icon, size=icon_size), (x, rect.y - 4))
        x += icon_size + ICON_GAP

    canvas.text((x, rect.y), title, theme.SECTION)

    if count is not None:
        canvas.text_right(rect, rect.y + 2, str(count), theme.COUNT)

    if rule:
        y = rect.y + RULE_OFFSET
        canvas.line([rect.x, y, rect.right, y])

    return Rect(rect.x, rect.y + HEADER_HEIGHT, rect.w, rect.h - HEADER_HEIGHT)


def marker(canvas, x, y, shape, size=16):
    """A small status glyph, drawn rather than typed.

    Colour emoji cannot be used: the panel is 1-bit, and Raspberry Pi OS ships
    no emoji font. Monochrome Unicode symbols would work, but coverage differs
    between the Pi's DejaVu and a desktop preview's Arial, and a missing glyph
    renders as a box only on the device -- where it is hardest to notice.
    Drawing them keeps both renderers honest.
    """
    if shape == 'check':
        canvas.line([(x, y + size * 0.52),
                     (x + size * 0.36, y + size * 0.86),
                     (x + size, y + size * 0.08)], width=3)

    elif shape == 'bang':
        # Exclamation mark: a tapering bar over a separate dot.
        canvas.rectangle([x + size * 0.34, y, x + size * 0.66, y + size * 0.62], fill=0)
        canvas.rectangle([x + size * 0.34, y + size * 0.78,
                          x + size * 0.66, y + size], fill=0)

    elif shape == 'circle':
        canvas.ellipse([x + 1, y + 1, x + size - 1, y + size - 1], fill=None, outline=0, width=2)

    elif shape == 'dot':
        canvas.ellipse([x + 3, y + 3, x + size - 3, y + size - 3], fill=0)

    elif shape == 'square':
        canvas.rectangle([x + 1, y + 1, x + size - 1, y + size - 1], outline=0, width=2)
