"""Steam: who is playing right now, and what I have been playing."""
from .base import Screen
from .. import theme, widgets
from ..layout import Rect

ONLINE = 0  # personastate above this counts as online in some form
ROW_HEIGHT = 32
ONLINE_BAND_HEIGHT = 190
NAME_WIDTH = 200


def format_playtime(minutes):
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h {minutes % 60:02d}m"


def online_friends(steam):
    """(nickname, game or None) for everyone currently online."""
    friends = []
    for status in (steam or {}).get('statuses', {}).values():
        if status.get('personastate', 0) <= ONLINE:
            continue
        friends.append((status.get('personaname', 'Unknown'), status.get('gameextrainfo')))
    return friends


class SteamScreen(Screen):
    id = 'steam'
    requires = ('steam',)

    def available(self, ctx):
        # "No one is online" is itself worth showing, so the screen stays in the
        # rotation whenever the data file is readable.
        return ctx.load('steam') is not None

    def render(self, canvas, rect, ctx):
        steam = ctx.load('steam')
        if steam is None:
            return

        body = Rect(rect.x + theme.MARGIN, rect.y + 10,
                    rect.w - 2 * theme.MARGIN, rect.h - 20)

        # Both bands always render, so the layout does not jump between
        # rotations as friends come and go.
        top, bottom = body.split_top(ONLINE_BAND_HEIGHT)
        self._draw_online(canvas, top, online_friends(steam))
        self._draw_recent(canvas, bottom, steam.get('recent', []))

    def _draw_online(self, canvas, rect, friends):
        rows = widgets.section_header(canvas, rect, "PLAYING NOW", len(friends),
                                      icon=('steam', 'icon.png'))
        if not friends:
            canvas.text((rows.x, rows.y), "No one is online.", theme.LIST)
            return

        for name, game, row in self._rows(rows, friends):
            canvas.text((row.x, row.y), canvas.fit_text(name, theme.LIST, NAME_WIDTH - 10),
                        theme.LIST)
            label = game or "online"
            canvas.text((row.x + NAME_WIDTH, row.y),
                        canvas.fit_text(label, theme.LIST, row.w - NAME_WIDTH), theme.LIST)

    def _draw_recent(self, canvas, rect, recent):
        rows = widgets.section_header(canvas, rect, "LAST 2 WEEKS")
        if not recent:
            canvas.text((rows.x, rows.y), "Nothing recent.", theme.LIST)
            return

        for game, row in self._rows(rows, recent):
            playtime = format_playtime(game.get('minutes', 0))
            available = row.w - canvas.text_width(playtime, theme.LIST) - 20
            canvas.text((row.x, row.y),
                        canvas.fit_text(game.get('name', ''), theme.LIST, available), theme.LIST)
            canvas.text_right(row, row.y, playtime, theme.LIST)

    @staticmethod
    def _rows(rect, items):
        capacity = max(rect.h // ROW_HEIGHT, 0)
        for i, item in enumerate(items[:capacity]):
            row = Rect(rect.x, rect.y + i * ROW_HEIGHT, rect.w, ROW_HEIGHT)
            yield (*item, row) if isinstance(item, tuple) else (item, row)
