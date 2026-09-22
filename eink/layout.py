"""Layout primitives for composing screens.

Rect describes a region; Canvas draws into one. Screens are handed a Rect and
should stay inside it rather than computing absolute panel coordinates.
"""
import os
from dataclasses import dataclass
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y + self.h

    def inset(self, pad):
        """Shrink by `pad` on every side."""
        return Rect(self.x + pad, self.y + pad, self.w - 2 * pad, self.h - 2 * pad)

    def split_top(self, height):
        """Cut a strip off the top; returns (strip, remainder)."""
        return Rect(self.x, self.y, self.w, height), \
            Rect(self.x, self.y + height, self.w, self.h - height)

    def split_left(self, width):
        """Cut a column off the left; returns (column, remainder)."""
        return Rect(self.x, self.y, width, self.h), \
            Rect(self.x + width, self.y, self.w - width, self.h)

    def center_x_for(self, width):
        """Left edge that centres something `width` wide inside this rect."""
        return self.x + (self.w - width) // 2

    def center_y_for(self, height):
        return self.y + (self.h - height) // 2


_icon_cache = {}


def load_icon(path, size=None):
    """Load an icon as a 1-bit image, flattening transparency onto white.

    Results are cached; callers must treat the returned image as read-only
    (pasting from it is fine, drawing into it is not).
    """
    key = (path, size)
    if key in _icon_cache:
        return _icon_cache[key]

    icon = Image.open(path).convert('RGBA')
    background = Image.new('RGBA', icon.size, (255, 255, 255, 255))
    background.paste(icon, (0, 0), icon)
    icon = background.convert('1')
    if size is not None:
        icon = icon.resize((size, size), Image.Resampling.LANCZOS)

    _icon_cache[key] = icon
    return icon


def truncate_chars(text, limit, suffix=""):
    """Character-count truncation. Pixel-aware truncation comes later."""
    if len(text) <= limit:
        return text
    return text[:limit] + suffix


class Canvas:
    """A PIL image plus the drawing helpers screens need."""

    def __init__(self, image, fonts):
        self.image = image
        self.fonts = fonts
        self.draw = ImageDraw.Draw(image)

    @classmethod
    def blank(cls, width, height, fonts):
        return cls(Image.new('1', (width, height), 255), fonts)

    @property
    def bounds(self):
        return Rect(0, 0, self.image.width, self.image.height)

    def font(self, size):
        return self.fonts.at(size)

    def text_bbox(self, text, size):
        return self.draw.textbbox((0, 0), text, font=self.font(size))

    def text_width(self, text, size):
        bbox = self.text_bbox(text, size)
        return bbox[2] - bbox[0]

    def text(self, xy, text, size, fill=0):
        self.draw.text(xy, text, font=self.font(size), fill=fill)

    def text_centered(self, rect, y, text, size, fill=0):
        """Draw `text` horizontally centred within `rect` at vertical `y`."""
        x = rect.center_x_for(self.text_width(text, size))
        self.text((x, y), text, size, fill=fill)

    def icon(self, *parts, size=None):
        """Paste path is relative to the repo's assets/ directory."""
        return load_icon(os.path.join('assets', *parts), size=size)

    def paste(self, icon, xy):
        self.image.paste(icon, xy)

    def line(self, xy, fill=0, width=1):
        self.draw.line(xy, fill=fill, width=width)

    def rectangle(self, xy, outline=0, width=1):
        self.draw.rectangle(xy, outline=outline, width=width)

    def ellipse(self, xy, fill=None, outline=0, width=1):
        self.draw.ellipse(xy, fill=fill, outline=outline, width=width)
