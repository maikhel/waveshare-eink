"""Steam screen: which friends are online and what they are playing."""
from .base import Screen
from .. import theme
from ..layout import truncate_chars

GAME_CHARS = 25
ONLINE = 0  # personastate greater than this means online in some form


class SteamScreen(Screen):
    id = 'steam'
    requires = ('steam',)

    def available(self, ctx):
        """Nobody online is nothing worth a slot in the rotation."""
        steam = ctx.load('steam')
        return steam is not None and bool(self._online_lines(steam))

    def render(self, canvas, rect, ctx):
        steam = ctx.load('steam')
        if steam is None:
            return

        icon = canvas.icon('steam', 'icon.png')
        icon_x = rect.x + theme.MARGIN
        icon_y = rect.y + theme.MARGIN
        canvas.paste(icon, (icon_x, icon_y))

        text_x = icon_x + theme.ICON + theme.ICON_GAP
        text_y = icon_y + theme.ICON_GAP

        lines = self._online_lines(steam) or ["No one’s online."]
        for line in lines:
            canvas.text((text_x, text_y), line, theme.BODY)
            text_y += theme.LINE_HEIGHT

    @staticmethod
    def _online_lines(steam):
        lines = []
        for status in steam.get('statuses', {}).values():
            if status.get('personastate', 0) <= ONLINE:
                continue
            nickname = status.get('personaname', 'Unknown')
            game = status.get('gameextrainfo')
            if game:
                lines.append(f"{nickname} plays {truncate_chars(game, GAME_CHARS, '...')}")
            else:
                lines.append(f"{nickname} is online")
        return lines
