"""Loads and validates playlist.json.

Config is hand-edited and read on a headless device, so every problem is
reported as a ConfigError naming the offending entry rather than surfacing as
an AttributeError halfway through a render.
"""
import json
import os
import re
from dataclasses import dataclass, field

DEFAULT_PATH = 'playlist.json'
DEFAULT_TICK_SECONDS = 60
DEFAULT_DWELL_SECONDS = 180

DAY_SETS = ('all', 'weekdays', 'weekends')
_DURATION = re.compile(r'^(\d+)([sm])$')


class ConfigError(Exception):
    pass


def parse_duration(value, where):
    """Accepts 90, '90s' or '5m'; returns seconds."""
    if isinstance(value, bool):
        raise ConfigError(f"{where}: expected a duration, got a boolean")
    if isinstance(value, int):
        seconds = value
    elif isinstance(value, str):
        match = _DURATION.match(value.strip())
        if not match:
            raise ConfigError(
                f"{where}: cannot read duration {value!r}, expected e.g. 90, '90s' or '5m'")
        amount, unit = int(match.group(1)), match.group(2)
        seconds = amount * (60 if unit == 'm' else 1)
    else:
        raise ConfigError(f"{where}: cannot read duration {value!r}")

    if seconds <= 0:
        raise ConfigError(f"{where}: duration must be positive, got {value!r}")
    return seconds


@dataclass(frozen=True)
class WhenClause:
    """One scheduling condition. All of its fields must match."""
    days: str = 'all'
    hours: tuple = None  # (start, end), start inclusive, end exclusive

    def matches(self, now):
        if self.days == 'weekdays' and now.weekday() >= 5:
            return False
        if self.days == 'weekends' and now.weekday() < 5:
            return False
        if self.hours is not None:
            start, end = self.hours
            if not (start <= now.hour < end):
                return False
        return True

    @classmethod
    def parse(cls, raw, where):
        if not isinstance(raw, dict):
            raise ConfigError(f"{where}: each 'when' clause must be an object")

        unknown = set(raw) - {'days', 'hours'}
        if unknown:
            raise ConfigError(f"{where}: unknown key(s) {sorted(unknown)} in 'when'")

        days = raw.get('days', 'all')
        if days not in DAY_SETS:
            raise ConfigError(f"{where}: 'days' must be one of {list(DAY_SETS)}, got {days!r}")

        hours = raw.get('hours')
        if hours is not None:
            if (not isinstance(hours, list) or len(hours) != 2
                    or not all(isinstance(h, int) for h in hours)):
                raise ConfigError(f"{where}: 'hours' must be [start, end], got {hours!r}")
            start, end = hours
            if not (0 <= start < end <= 24):
                raise ConfigError(
                    f"{where}: 'hours' must satisfy 0 <= start < end <= 24, got {hours!r}")
            hours = (start, end)

        return cls(days=days, hours=hours)


@dataclass(frozen=True)
class Entry:
    """One screen's place in the playlist."""
    id: str
    dwell: int
    when: tuple = ()  # empty means always; otherwise any clause matching is enough

    def scheduled(self, now):
        return not self.when or any(clause.matches(now) for clause in self.when)

    @classmethod
    def parse(cls, raw, index):
        where = f"screens[{index}]"
        if not isinstance(raw, dict):
            raise ConfigError(f"{where}: must be an object")

        unknown = set(raw) - {'id', 'dwell', 'when'}
        if unknown:
            raise ConfigError(f"{where}: unknown key(s) {sorted(unknown)}")

        screen_id = raw.get('id')
        if not isinstance(screen_id, str) or not screen_id:
            raise ConfigError(f"{where}: 'id' is required and must be a non-empty string")

        dwell = parse_duration(raw.get('dwell', DEFAULT_DWELL_SECONDS), f"{where}.dwell")

        raw_when = raw.get('when', [])
        if isinstance(raw_when, dict):  # a single clause is allowed unwrapped
            raw_when = [raw_when]
        if not isinstance(raw_when, list):
            raise ConfigError(f"{where}: 'when' must be an object or a list of objects")
        when = tuple(WhenClause.parse(clause, f"{where}.when[{i}]")
                     for i, clause in enumerate(raw_when))

        return cls(id=screen_id, dwell=dwell, when=when)


@dataclass(frozen=True)
class Config:
    tick_seconds: int = DEFAULT_TICK_SECONDS
    show_clock: bool = True
    show_indicator: bool = True
    entries: tuple = field(default=())


def load(path=DEFAULT_PATH, known_screens=None):
    """Read and validate the playlist config."""
    try:
        with open(path, 'r') as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise ConfigError(f"{path}: not found")
    except json.JSONDecodeError as e:
        raise ConfigError(f"{path}: invalid JSON ({e})")

    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: top level must be an object")

    raw_screens = raw.get('screens')
    if not isinstance(raw_screens, list) or not raw_screens:
        raise ConfigError(f"{path}: 'screens' must be a non-empty list")

    entries = tuple(Entry.parse(entry, i) for i, entry in enumerate(raw_screens))

    if known_screens is not None:
        for entry in entries:
            if entry.id not in known_screens:
                raise ConfigError(
                    f"{path}: unknown screen {entry.id!r}, "
                    f"known screens are {sorted(known_screens)}")

    header = raw.get('header', {})
    if not isinstance(header, dict):
        raise ConfigError(f"{path}: 'header' must be an object")

    return Config(
        tick_seconds=parse_duration(raw.get('tick_seconds', DEFAULT_TICK_SECONDS),
                                    f"{path}.tick_seconds"),
        show_clock=bool(header.get('clock', True)),
        show_indicator=bool(header.get('indicator', True)),
        entries=entries,
    )
