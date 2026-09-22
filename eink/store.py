"""Reads what the fetch services left in data/.

Services write an envelope around their payload:

    {"source": ..., "fetched_at": <ISO 8601 UTC>, "data": {...}}

Data being old is normal here -- the services run on cron, as rarely as every
few hours -- so age is recorded but never a reason to hide a screen. Only a
missing or unreadable file makes a source unavailable.
"""
import json
import os
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Record:
    source: str
    data: object
    fetched_at: datetime = None  # None for files written before the envelope

    def age(self, now):
        """How long ago this was fetched, or None if unknown."""
        if self.fetched_at is None:
            return None

        fetched = self.fetched_at
        if fetched.tzinfo is not None and now.tzinfo is None:
            fetched = fetched.astimezone().replace(tzinfo=None)
        elif fetched.tzinfo is None and now.tzinfo is not None:
            fetched = fetched.replace(tzinfo=now.tzinfo)
        return now - fetched


def _parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def load(data_dir, source):
    """Return a Record, or None if the source is unreadable."""
    path = os.path.join(data_dir, f'{source}.json')
    try:
        with open(path, 'r') as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

    if isinstance(raw, dict) and 'data' in raw and 'source' in raw:
        return Record(source=source,
                      data=raw['data'],
                      fetched_at=_parse_timestamp(raw.get('fetched_at')))

    # Pre-envelope file: the whole document is the payload. Lets a freshly
    # deployed renderer keep working until cron rewrites data/.
    return Record(source=source, data=raw, fetched_at=None)
