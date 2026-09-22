"""Weather: current conditions, a temperature curve for the day, and the week."""
from datetime import datetime

from .base import Screen
from .. import theme, widgets
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

DAILY_HEIGHT = 158
LEFT_WIDTH = 330
COLUMN_GAP = 24

# Graph geometry
GRAPH_TOP_PAD = 22      # room for the temperature labels above the curve
GRAPH_BOTTOM_PAD = 26   # room for the hour labels under the axis
GRAPH_SIDE_PAD = 20
POINT_RADIUS = 3


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
        top, daily = body.split_bottom(DAILY_HEIGHT)
        left, right = top.split_left(LEFT_WIDTH)
        right = Rect(right.x + COLUMN_GAP, right.y, right.w - COLUMN_GAP, right.h)

        self._draw_current(canvas, left, weather['current'])

        hourly = weather.get('hourly') or []
        if len(hourly) >= 2:
            self._draw_graph(canvas, right, hourly)

        if weather.get('forecast'):
            canvas.line([body.x, daily.y, body.right, daily.y])
            self._draw_daily(canvas, daily, weather['forecast'])

    def _draw_current(self, canvas, rect, current):
        """Icon and temperature, the description, then a list of details."""
        icon_y = rect.y + 2
        canvas.paste(_icon(canvas, current['icon'], theme.ICON_HERO), (rect.x, icon_y))

        temp_text = f"{current['temp']}°"
        temp_bbox = canvas.text_bbox(temp_text, theme.HERO_TEMP)
        temp_x = rect.x + theme.ICON_HERO + 10
        temp_y = icon_y + (theme.ICON_HERO - (temp_bbox[3] - temp_bbox[1])) // 2 - temp_bbox[1]
        canvas.text((temp_x, temp_y), temp_text, theme.HERO_TEMP)

        description = current.get('description', '')
        if description:
            canvas.text((rect.x, rect.y + 130),
                        canvas.fit_text(description.capitalize(), theme.HERO_DESC, rect.w),
                        theme.HERO_DESC)

        rows = [
            ("Feels like", f"{current['feels_like']}°"),
            ("Humidity", f"{current['humidity']}%"),
            ("Sunrise", current.get('sunrise', '--:--')),
            ("Sunset", current.get('sunset', '--:--')),
        ]
        y = rect.y + 160
        for label, value in rows:
            canvas.text((rect.x, y), label, theme.DETAIL)
            canvas.text_right(rect, y, value, theme.DETAIL)
            y += 25

    def _draw_graph(self, canvas, rect, hourly):
        """Temperature over the coming day, as a simple line chart."""
        plot = widgets.section_header(canvas, rect, "NEXT 24H")

        temps = [step['temp'] for step in hourly]
        low, high = min(temps), max(temps)
        span = high - low or 1  # a flat day would divide by zero

        top = plot.y + GRAPH_TOP_PAD
        bottom = plot.bottom - GRAPH_BOTTOM_PAD
        left = plot.x + GRAPH_SIDE_PAD
        step_x = (plot.w - 2 * GRAPH_SIDE_PAD) / (len(hourly) - 1)

        points = [
            (int(left + i * step_x), int(bottom - (temp - low) / span * (bottom - top)))
            for i, temp in enumerate(temps)
        ]

        canvas.line([plot.x, bottom + 6, plot.right, bottom + 6])
        canvas.line(points, width=2)

        for (x, y), step in zip(points, hourly):
            canvas.ellipse([x - POINT_RADIUS, y - POINT_RADIUS,
                            x + POINT_RADIUS, y + POINT_RADIUS], fill=0)

            label = f"{step['temp']}°"
            label_x = x - canvas.text_width(label, theme.GRAPH_LABEL) // 2
            canvas.text((label_x, y - 22), label, theme.GRAPH_LABEL)

            hour = step['time'][:2]
            hour_x = x - canvas.text_width(hour, theme.GRAPH_LABEL) // 2
            canvas.text((hour_x, bottom + 10), hour, theme.GRAPH_LABEL)

    def _draw_daily(self, canvas, rect, forecast):
        """One column per day: name, icon, high/low and rain chance."""
        columns = rect.columns(len(forecast))
        for i, (column, day) in enumerate(zip(columns, forecast)):
            canvas.text_centered(column, rect.y + 8,
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
