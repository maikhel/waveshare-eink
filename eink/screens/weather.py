"""Current conditions and the multi-day forecast."""
from datetime import datetime

from .base import Screen
from .. import theme
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

DAY_NAMES = {
    'Mon': 'Pon',
    'Tue': 'Wt',
    'Wed': 'Śr',
    'Thu': 'Czw',
    'Fri': 'Pt',
    'Sat': 'Sob',
    'Sun': 'Nie',
}

FORECAST_ICON = 48
FORECAST_ITEM_WIDTH = 100
FORECAST_ITEM_GAP = 60


def _icon(canvas, code, size):
    return canvas.icon('weather', ICON_MAPPING.get(code, UNKNOWN_ICON), size=size)


class WeatherScreen(Screen):
    id = 'weather'
    requires = ('weather',)

    def render(self, canvas, rect, ctx):
        weather = ctx.load('weather')
        if weather is None:
            return
        self._draw_current(canvas, rect, weather['current'])
        self._draw_forecast(canvas, rect, weather['forecast'])

    def _draw_current(self, canvas, rect, current):
        """Icon and temperature, aligned to the top-right corner."""
        temp_text = f"{current['temp']}°C"
        icon = _icon(canvas, current['icon'], theme.ICON)

        temp_bbox = canvas.text_bbox(temp_text, theme.CURRENT_TEMP)
        temp_w = temp_bbox[2] - temp_bbox[0]

        total_w = theme.ICON + theme.ICON_GAP + temp_w
        x_start = rect.right - total_w - theme.MARGIN
        temp_y = rect.y + theme.MARGIN

        # Centre the icon on the temperature's visual midline.
        text_center_y = temp_y + (temp_bbox[1] + temp_bbox[3]) / 2
        canvas.paste(icon, (x_start + theme.ICON_GAP,
                            int(text_center_y - theme.ICON / 2)))
        canvas.text((x_start + theme.ICON + theme.ICON_GAP, temp_y),
                    temp_text, theme.CURRENT_TEMP)

    def _draw_forecast(self, canvas, rect, forecast):
        """A centred row of day / icon / high-low columns."""
        if not forecast:
            return

        forecast_y = rect.bottom - 150
        stride = FORECAST_ITEM_WIDTH + FORECAST_ITEM_GAP
        total_width = len(forecast) * FORECAST_ITEM_WIDTH + (len(forecast) - 1) * FORECAST_ITEM_GAP
        x = rect.center_x_for(total_width)

        for i, day in enumerate(forecast):
            column = Rect(x, forecast_y, FORECAST_ITEM_WIDTH, 150)

            weekday = datetime.fromisoformat(day['date']).strftime('%a')
            canvas.text_centered(column, forecast_y,
                                 DAY_NAMES.get(weekday, weekday), theme.FORECAST_DAY)

            icon = _icon(canvas, day['midday']['icon'], FORECAST_ICON)
            icon_y = forecast_y + 30
            canvas.paste(icon, (column.center_x_for(FORECAST_ICON), icon_y))

            temp_text = f"{day['midday']['temp']}°/{day['midnight']['temp']}°"
            canvas.text_centered(column, icon_y + FORECAST_ICON + 10,
                                 temp_text, theme.FORECAST_TEMP)

            if i < len(forecast) - 1:
                line_x = x + FORECAST_ITEM_WIDTH + FORECAST_ITEM_GAP // 2
                canvas.line([line_x, forecast_y, line_x, forecast_y + 120])

            x += stride
