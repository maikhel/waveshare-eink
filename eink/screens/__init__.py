"""Screen registry. Adding a screen means importing it here."""
from .base import Context, Screen
from .steam import SteamScreen
from .weather import WeatherScreen
from .work import WorkScreen

REGISTRY = {
    screen.id: screen
    for screen in (WorkScreen(), WeatherScreen(), SteamScreen())
}


def get(screen_id):
    return REGISTRY[screen_id]


__all__ = ['Context', 'Screen', 'REGISTRY', 'get']
