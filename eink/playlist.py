"""Rotation engine: decides which screen is on the panel right now.

Eligibility is deliberately evaluated only at rotation boundaries. Checking it
every tick would let a friend logging off mid-dwell reshuffle the rotation
underneath the viewer.
"""
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Slide:
    """The outcome of one tick."""
    screen: object = None       # None when nothing is eligible
    entry: object = None
    rotated: bool = False       # True when this tick changed the panel's content
    position: int = 0           # index among the eligible screens, for the indicator
    total: int = 0              # how many screens are eligible

    @property
    def is_empty(self):
        return self.screen is None


class Playlist:
    def __init__(self, config, registry):
        self._entries = config.entries
        self._registry = registry
        self.reset()

    def reset(self):
        """Forget rotation state, so the next tick starts from the top.

        Called on wake from night mode: resuming mid-cycle after a seven-hour
        blank is arbitrary.
        """
        self._active = -1
        self._expires_at = None
        self._eligible = ()

    def tick(self, ctx):
        if self._expires_at is None or ctx.now >= self._expires_at:
            return self._rotate(ctx)

        entry = self._entries[self._active]
        return Slide(
            screen=self._registry.get(entry.id),
            entry=entry,
            rotated=False,
            position=self._eligible.index(self._active),
            total=len(self._eligible),
        )

    def _rotate(self, ctx):
        eligible = tuple(
            i for i, entry in enumerate(self._entries) if self._is_eligible(entry, ctx)
        )

        if not eligible:
            # Nothing to show. Leave the deadline unset so the next tick retries.
            self._active = -1
            self._expires_at = None
            self._eligible = ()
            return Slide()

        # Round-robin: first eligible entry strictly after the current one, wrapping.
        order = ((self._active + 1 + step) % len(self._entries)
                 for step in range(len(self._entries)))
        self._active = next(i for i in order if i in eligible)

        entry = self._entries[self._active]
        self._eligible = eligible
        self._expires_at = ctx.now + timedelta(seconds=entry.dwell)

        return Slide(
            screen=self._registry.get(entry.id),
            entry=entry,
            rotated=True,
            position=eligible.index(self._active),
            total=len(eligible),
        )

    def _is_eligible(self, entry, ctx):
        if not entry.scheduled(ctx.now):
            return False
        screen = self._registry.get(entry.id)
        return screen is not None and screen.available(ctx)
