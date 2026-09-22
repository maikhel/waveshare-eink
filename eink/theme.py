"""Fonts and type sizes.

Every size the screens use lives here, so density can be retuned in one place
instead of hunting through draw calls.
"""
import os
from PIL import ImageFont

# Checked in order; first one that exists wins. The Pi has DejaVu, macOS has Arial.
FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
]

# Type scale
TIME = 120
CURRENT_TEMP = 40
FORECAST_DAY = 24
FORECAST_TEMP = 32
BODY = 20

# Header strip
HEADER_HEIGHT = 56
HEADER_TIME = 32
HEADER_DATE = 22
HEADER_GAP = 14
DOT_DIAMETER = 10
DOT_GAP = 10

# Spacing
MARGIN = 20
ICON = 64
ICON_GAP = 10
LINE_HEIGHT = 25


def default_font_path():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "No usable font found, tried: " + ", ".join(FONT_CANDIDATES)
    )


class Fonts:
    """Lazily loads and caches ImageFont instances for one typeface."""

    def __init__(self, path=None):
        self.path = path or default_font_path()
        self._cache = {}

    def at(self, size):
        if size not in self._cache:
            self._cache[size] = ImageFont.truetype(self.path, size)
        return self._cache[size]
