"""The Screen contract and the render context handed to every screen."""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime

from ..theme import Fonts


@dataclass
class Context:
    """Everything a screen needs from the outside world.

    `now` is passed in rather than read from the clock so renders can be
    reproduced at a fixed moment for testing and previews.
    """
    now: datetime
    fonts: Fonts
    data_dir: str = 'data'
    _cache: dict = field(default_factory=dict, repr=False)

    def load(self, source):
        """Return the JSON written by `services/fetch_<source>.py`, or None.

        None covers a missing file and an unparseable one alike — the latter
        happens today because fetchers write in place and can be read mid-write.
        Either way the caller treats the source as unavailable rather than
        raising in the middle of a render.
        """
        if source in self._cache:
            return self._cache[source]

        path = os.path.join(self.data_dir, f'{source}.json')
        try:
            with open(path, 'r') as f:
                payload = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            payload = None

        self._cache[source] = payload
        return payload


class Screen:
    """One unit of the playlist: declares its data needs and draws itself."""

    id = ''
    requires = ()

    def available(self, ctx):
        """False means the playlist skips this screen entirely."""
        return all(ctx.load(source) is not None for source in self.requires)

    def render(self, canvas, rect, ctx):
        raise NotImplementedError
