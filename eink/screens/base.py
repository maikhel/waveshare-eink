"""The Screen contract and the render context handed to every screen."""
from dataclasses import dataclass, field
from datetime import datetime

from .. import store
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

    def record(self, source):
        """The stored Record for a source, or None if it is unreadable."""
        if source not in self._cache:
            self._cache[source] = store.load(self.data_dir, source)
        return self._cache[source]

    def load(self, source):
        """The payload a screen draws, or None if the source is unavailable."""
        record = self.record(source)
        return record.data if record else None

    def age(self, source):
        """How old this source's data is, or None if unknown."""
        record = self.record(source)
        return record.age(self.now) if record else None


class Screen:
    """One unit of the playlist: declares its data needs and draws itself."""

    id = ''
    requires = ()

    def available(self, ctx):
        """False means the playlist skips this screen entirely."""
        return all(ctx.load(source) is not None for source in self.requires)

    def render(self, canvas, rect, ctx):
        raise NotImplementedError
