"""Weather: current conditions, the next few hours, and the coming days."""
from datetime import datetime

from .base import Screen
from .. import theme
from ..dates import day_abbr
from ..layout import Rect

ICON_MAPPING = {
    "01d": "wi-day-sunny-big.png",      # clear sky day
    "01n": "wi-day-sunny-big.png",      # clear sky night (fallback to day)
    "02d": "wi-day-cloudy-big.png",     # few clouds day
    "02n": "wi-day-cloudy-big.png",     # few clouds night
    "03d": "wi-cloudy-big.png",         # scattered clouds
    "03n": "wi-cloudy-big.png",
    "04d": "wi-cloudy-big.png",         # broken clouds
    "04n": "wi-cloudy-big.png",
    "09d": "wi-showers-big.png",        # shower rain
    "09n": "wi-showers-big.png",
    "10d": "wi-rain-big.png",           # rain
    "10n": "wi-rain-big.png",
    "11d": "wi-storm-showers-big.png",  # thunderstorm
    "11n": "wi-storm-showers-big.png",
    "13d": "wi-snowflake-cold-big.png", # snow
    "13n": "wi-snowflake-cold-big.png",
    "50d": "wi-fog-big.png",            # mist
    "50n": "wi-fog-big.png",
}

UNKNOWN_ICON = 'wi-alien-big.png'

# Below this, printing a percentage costs more attention than it repays.
POP_THRESHOLD = 20

HERO_HEIGHT = 150
HOURLY_HEIGHT = 116
BAND_GAP = 8


def _icon(canvas, code, size):
    return canvas.icon('weather', ICON_MAPPING.get(code, UNKNOWN_ICON), size=size)


def _pop_label(pop):
    return f"{pop}%" if pop and pop >= POP_THRESHOLD else None


class WeatherScreen(Screen):
    id = 'weather'
    requires = ('weather',)

    def render(self, canvas, rect, ctx):
        weather = ctx.load('weather')
        if weather is None:
            return

        body = Rect(rect.x + theme.MARGIN, rect.y, rect.w - 2 * theme.MARGIN, rect.h)
        hero, rest = body.split_top(HERO_HEIGHT)
        hourly, daily = rest.split_top(HOURLY_HEIGHT)

        self._draw_hero(canvas, hero, weather['current'])

        if weather.get('hourly'):
            canvas.line([body.x, hourly.y, body.right, hourly.y])
            self._draw_hourly(canvas, hourly, weather['hourly'])

        if weather.get('forecast'):
            canvas.line([body.x, daily.y, body.right, daily.y])
            self._draw_daily(canvas, daily, weather['forecast'])

    def _draw_hero(self, canvas, rect, current):
        """Big icon and temperature on the left, a rail of details on the right."""
        left, right = rect.split_left(380)

        icon_y = rect.y + 6
        canvas.paste(_icon(canvas, current['icon'], theme.ICON_HERO), (left.x, icon_y))

        temp_text = f"{current['temp']}°"
        temp_bbox = canvas.text_bbox(temp_text, theme.HERO_TEMP)
        temp_x = left.x + theme.ICON_HERO + 12
        temp_y = icon_y + (theme.ICON_HERO - (temp_bbox[3] - temp_bbox[1])) // 2 - temp_bbox[1]
        canvas.text((temp_x, temp_y), temp_text, theme.HERO_TEMP)

        description = current.get('description', '')
        if description:
            available = left.w - theme.ICON_HERO - 12
            canvas.text((temp_x, icon_y + theme.ICON_HERO - 34),
                        canvas.fit_text(description.capitalize(), theme.HERO_DESC, available),
                        theme.HERO_DESC)

        rows = [
            ("Odczuwalna", f"{current['feels_like']}°"),
            ("Wilgotność", f"{current['humidity']}%"),
            ("Wschód", current.get('sunrise', '--:--')),
            ("Zachód", current.get('sunset', '--:--')),
        ]
        y = rect.y + 14
        for label, value in rows:
            canvas.text((right.x, y), label, theme.DETAIL)
            canvas.text_right(right, y, value, theme.DETAIL)
            y += 33

    def _draw_hourly(self, canvas, rect, hourly):
        """The next few 3-hourly steps."""
        for column, step in zip(rect.columns(len(hourly)), hourly):
            canvas.text_centered(column, rect.y + 4, step['time'], theme.HOUR_LABEL)
            canvas.paste(_icon(canvas, step['icon'], theme.ICON_HOUR),
                         (column.center_x_for(theme.ICON_HOUR), rect.y + 22))

            canvas.text_centered(column, rect.y + 64, f"{step['temp']}°", theme.HOUR_TEMP)

            pop = _pop_label(step.get('pop'))
            if pop:
                canvas.text_centered(column, rect.y + 94, pop, theme.POP)

    def _draw_daily(self, canvas, rect, forecast):
        """One column per day: name, icon, high/low and rain chance."""
        columns = rect.columns(len(forecast))
        for i, (column, day) in enumerate(zip(columns, forecast)):
            canvas.text_centered(column, rect.y + BAND_GAP,
                                 day_abbr(datetime.fromisoformat(day['date'])),
                                 theme.FORECAST_DAY)

            canvas.paste(_icon(canvas, day['midday']['icon'], theme.ICON_DAY),
                         (column.center_x_for(theme.ICON_DAY), rect.y + 34))

            canvas.text_centered(column, rect.y + 88,
                                 f"{day['midday']['temp']}°/{day['midnight']['temp']}°",
                                 theme.FORECAST_TEMP)

            pop = _pop_label(day['midday'].get('pop'))
            if pop:
                canvas.text_centered(column, rect.y + 124, pop, theme.POP)

            if i < len(columns) - 1:
                line_x = (column.right + columns[i + 1].x) // 2
                canvas.line([line_x, rect.y + 4, line_x, rect.bottom - 6])
