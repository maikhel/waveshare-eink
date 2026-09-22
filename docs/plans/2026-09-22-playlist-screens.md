# Playlist of Screens — Architecture Plan

**Date:** 2026-09-22
**Branch:** `playlist-screens`
**Status:** all four steps done

## Goal

Replace the single fixed layout with a *playlist* of purpose-built screens that
rotate on the panel, inspired by TRMNL. The 7.5" 800×480 panel cannot show
everything at once, so instead of cramming, each screen gets the room to show one
topic properly.

Initial screens:

| id        | content |
|-----------|---------|
| `work`    | GitHub PRs (mine + review queue). Calendar deferred — see "Deferred". |
| `weather` | Detailed current conditions + 5-day forecast |
| `steam`   | Friends playing now, my recent playtime, wishlist |
| `extra`   | Rotating quote (local file) |

The existing split — **fetchers write JSON, renderer reads JSON, neither knows
about the other** — is kept and made more explicit. That is the property that
makes this whole thing work; nothing in this plan couples the two.

## Decisions taken

These were settled during design discussion and are not open for re-litigation
during implementation:

1. **Persistent header strip**, not a clock screen. ~56px at the top of every
   screen: `HH:MM`, Polish weekday + date, rotation dots. Body gets 424px.
2. **Pillow + a small layout primitive layer.** No headless Chromium, despite the
   Pi 4/5 having headroom for it — the screens are structured rather than
   free-form, and keeping the render loop at milliseconds preserves the current
   simple refresh behaviour.
3. **Relaxed data freshness.** Fetchers run on generous cron cadences (weather
   ~3h, Steam ~1h, GitHub ~15m). Data being old is the *normal* state, not a
   problem to surface. See "Data contract".
4. **Google Calendar deferred.** The `work` screen is built GitHub-only but laid
   out so calendar slots in without a rewrite.

## Target structure

```
eink/
  config.py        # loads playlist.yaml + .env
  store.py         # reads data/*.json, envelope parsing, age reporting
  layout.py        # Rect, split/row/column, text+truncate, icon cache
  theme.py         # font sizes, paddings, rules — one place to retune density
  render.py        # draws header strip, delegates body to the active screen
  playlist.py      # eligibility filter, round-robin, dwell tracking
  screens/
    __init__.py    # registry: {"work": WorkScreen(), ...}
    base.py        # Screen protocol
    work.py
    weather.py
    steam.py
    extra.py
services/
  common.py        # atomic write_data(), env loading, shared error handling
  fetch_github.py
  fetch_weather.py
  fetch_steam.py
  fetch_quote.py   # (optional — quotes may just be a static asset)
assets/quotes.json
data/              # json cache (already gitignored)
example_data/      # fixtures for demo.py
playlist.yaml
clock.py           # e-ink lifecycle ONLY
demo.py            # renders every screen to PNG, no hardware
```

### The central refactor

`clock.py` keeps only the e-ink lifecycle: init, refresh policy, night mode,
sleep, error recovery. Everything about *what* is drawn moves behind a single
`render.draw(ctx) -> Image` call.

Today the composition is spelled out in `clock.py` (`draw_date_and_time` →
`draw_weather_info` → `draw_steam_or_github`) *and* duplicated in `demo.py`, so
the two can drift. After the refactor both call the same `render.draw()`, giving
real parity between the Mac preview and the panel.

## Screen contract

```python
class Screen(Protocol):
    id: str
    requires: list[str]                 # data sources, e.g. ["github"]

    def available(self, ctx: Context) -> bool:
        """False → the playlist skips this screen entirely this cycle."""

    def render(self, canvas: Canvas, ctx: Context) -> None:
        """Draw into the body rect. The header is not this screen's business."""
```

`available()` is what makes rotation feel alive rather than mechanical: the Steam
screen returns `False` when nobody is online, so it is skipped instead of burning
three minutes displaying "No one's online."

**Eligibility is evaluated only at rotation boundaries.** Without this, a friend
going online mid-dwell can make screens flicker in and out of the cycle. Decide
the next screen once, at the moment of rotation, then leave it alone.

## Playlist configuration

`playlist.json` (JSON rather than YAML, to keep the Pi dependency-free):

```json
{
  "tick_seconds": 60,
  "header": { "clock": true, "indicator": true },
  "screens": [
    { "id": "work", "dwell": "10m",
      "when": [{ "days": "weekdays", "hours": [8, 18] }] },
    { "id": "weather", "dwell": "6m" },
    { "id": "steam", "dwell": "6m",
      "when": [{ "days": "weekdays", "hours": [17, 24] },
               { "days": "weekends" }] }
  ]
}
```

**`when` is structured, not an expression string.** Each clause is
`{days, hours}` with `days` in `all`/`weekdays`/`weekends` and `hours` a
`[start, end)` pair; a list of clauses means *any of these*. This avoids
`eval()` entirely, is trivially unit-testable, and maps one-to-one onto V2
playlists — which was the whole point of keeping the condition thin.

**`skip_if_empty` was dropped.** It duplicated `available()`. A screen alone
knows whether it has anything worth a slot — the Steam screen reports
unavailable when no friends are online — so there is one mechanism, not two.

Engine: filter by `when` + `available()`, round-robin the survivors, advance when
dwell expires. Adding a screen is one file plus four lines of YAML; reordering the
day never touches Python.

This replaces the hardcoded weekday/work-hours `if` in `drawing.py`
(`draw_steam_or_github`).

## Data contract

Every fetcher writes the same envelope:

```json
{
  "source": "github",
  "fetched_at": "2026-09-22T09:15:00+00:00",
  "data": { }
}
```

**The `ok` flag was dropped.** A fetch that fails now writes nothing at all and
leaves the previous result in place, so there is no `ok: false` state to
represent — and stale data beats a vanished screen at these cadences. Readers
also accept pre-envelope files (the whole document is the payload, age unknown),
so a freshly deployed renderer keeps working until cron rewrites `data/`.

Renderer rules, tuned for the relaxed-freshness decision:

- **Missing or unreadable file** → source unavailable → screens requiring it
  report `available() == False` → skipped.
- **Present and `ok: true`** → render it, however old it is. Old data is expected
  and is not decorated with warnings; a three-hour-old weather reading is simply
  the weather.
- `fetched_at` is still recorded, because a couple of screens want to *phrase*
  age as content (e.g. "friends online as of 14:00") and because it is
  indispensable when debugging a silently dead cron job.

No TTL-based hiding, no staleness badges in the header. If a source breaks
outright the file stops being valid and its screen quietly drops out of the
rotation, which is the right amount of signal.

### Fixes to fold in

Three existing issues in `services/` that this layer resolves:

1. **Non-atomic writes.** All three fetchers `json.dump` directly into the live
   file, so `clock.py` can read a half-written file. `write_data()` must write to
   a temp file and `os.replace()` it.
2. **Inconsistent paths.** `fetch_steam.py` writes to a *relative*
   `data/steam.json` while the other two resolve from `__file__` — that breaks
   under cron depending on the working directory. `common.py` centralises it.
3. **Duplicated boilerplate.** Env loading, the `try/except → print → exit(1)`
   tail, and the timestamp are copy-pasted three times.

## Refresh policy

Rotation changes the whole panel; a plain tick changes only the header clock.

- **Rotation** → full refresh (`init_fast` + `display`). This also flushes
  ghosting, conveniently on the same cadence as content changes.

  Because full refreshes now follow content rather than a timer, the dwell times
  set the flashing rate: 10m/6m/6m gives 8 full refreshes an hour on a weekday
  and 10 in the evening. Shorter dwells were tried first (5m/3m/3m) and gave 15
  an hour during work hours, which is a visible flash every few minutes in a
  room you are sitting in. None of this data changes fast enough to justify it.
- **In-dwell tick** → partial refresh.
- `FULL_REFRESH_EVERY = 10` becomes: full refresh **on rotation, or after 10
  partials, whichever comes first.**

**Night mode interaction:** after the 00:00–07:00 blank, the playlist must resume
at the first eligible screen rather than mid-cycle. Reset playlist state when
exiting night mode, alongside the existing forced full refresh.

## Screen designs (424px body)

### Work

Two columns across the 424px body, with a vertical divider:

- **Left — my open PRs.** A drawn status marker (filled = approved, triangle =
  changes requested, hollow = waiting, square = draft), the title truncated to
  the column width, and a meta line of review state + CI status.
- **Right — the review queue.** Title, then repo + CI status, with a `+N more`
  line when the queue overflows the column.

This needed the fetcher rewritten as a single GraphQL query: the REST search API
cannot return `reviewDecision` or check status at all. One call now replaces the
two REST searches and returns strictly more.

Status markers are **drawn, not typed.** The Pi renders with DejaVu and a
desktop preview with Arial, and symbol coverage differs between them — a missing
glyph would show up as a box only on the device, where it is hardest to notice.

Calendar, when it arrives, takes the right column and the review queue moves
beneath my PRs on the left.

### Weather

Two regions above the forecast strip:

- **Left (330px)** — 128px icon at native size, temperature, description, then
  feels-like, humidity, sunrise and sunset.
- **Right** — a line chart of temperature over the next 24 hours, one point per
  3-hourly step, each labelled with its temperature and hour.
- **Bottom (158px)** — the 5-day strip, unchanged apart from rain chance.

The chart is labelled *next 24h* rather than *today*: the forecast API only
returns future steps, so a "today" chart would shrink to one or two points by
evening. Rain chance is printed only above 20%; below that the percentage costs
more attention than it repays.

Needed a second API call: `current` was previously derived from `forecast[0]` of
the 3-hour series, so it could be three hours stale and carried no feels-like or
humidity.

### Steam

Two bands, each collapsing when empty so no heading is left stranded:

1. **Friends online now** — nickname and game, with room for the full title
   rather than clipping at 25 characters.
2. **My recent playtime** — `GetRecentlyPlayedGames`, last two weeks.

**The wishlist band was dropped.** It was the only undocumented endpoint in the
project and had broken before; the screen is better without that failure mode.

Because the recent-playtime band has content even when nobody is online, this
screen no longer drops out of the rotation as often as it did. `available()` is
now "either band has something".

### Extra

**Not built.** The quotes screen was dropped rather than filling the slot with
something decorative; the playlist stays at three screens until something earns
the fourth.

## Implementation order

Each step leaves the repo working and is verifiable on the Mac via `demo.py`.

**Step 1 — bones, no behaviour change.**
`layout.py`, `theme.py`, `screens/base.py`, the registry. Port the *existing*
weather / GitHub / Steam drawing code into screens unchanged. Output should be
identical to today's `preview.png`.

**Step 2 — rotation.**
`render.py` with the header strip, `playlist.py`, `playlist.yaml`. `clock.py`
slims to the lifecycle. Night-mode reset and the new refresh policy land here.
`demo.py` gains the ability to render every screen to `preview_<id>.png`.

**Step 3 — data layer.**
`services/common.py`, atomic writes, the envelope, `store.py`. Migrate the three
existing fetchers; update `example_data/` fixtures to the envelope shape.

**Step 4 — enrich.**
The richer weather fetch, the new Steam endpoints, and the redesigned Work
layout. Also fixed the icon pipeline: icons were converted to 1-bit (which
dithers) and *then* resampled, which smears the dither into broken strokes.
Resizing in greyscale and thresholding last, with dithering off, is visibly
cleaner — and matters more now that the weather hero icon is 128px.

Steps 1–2 carry all the risk and neither requires touching the Pi.

## Deferred

- **Google Calendar.** When added, the preferred route is the private `.ics`
  secret address from Calendar settings plus the `icalendar` library: no OAuth,
  no refresh token to babysit on a headless Pi. Read-only, and the URL is a
  bearer secret for `.env`. Full OAuth remains the fallback if richer data
  (colors, attendees, responses) turns out to be needed.
- Manual screen advance (GPIO button / web hook).
- Per-screen refresh hints (e.g. a screen that wants a full refresh every tick).

### V2 — named playlists

A *playlist* is a named group of screens that owns a time slot, e.g. a `work`
playlist running 08:00–18:00 on weekdays and a `home` playlist covering evenings
and weekends. Rotation happens within the active playlist.

```yaml
playlists:
  - id: work
    when: [{ days: weekdays, hours: [8, 18] }]
    screens: [work, weather]
  - id: home
    screens: [weather, steam, quote]
```

**Consequence for V1:** playlists would largely subsume the per-screen `when:`
field — if the Work playlist only runs during work hours, the `work` screen does
not need its own condition. Scheduling belongs to the playlist; membership
belongs to the screen.

Therefore **keep V1's `when:` deliberately thin.** It is a stand-in for playlists,
not a feature to grow. Resist building an expression language that V2 will
delete. The structured `{days, hours}` clause is the ceiling, not a starting
point.

Open questions for V2: what happens when no playlist matches the current time
(fallback playlist, or blank panel?), and whether a screen may belong to more
than one playlist.

## Interface language

All on-screen text is English. The display previously mixed Polish day names and
labels with English data from the APIs; OpenWeather is now asked for English
descriptions (`lang=en`) and weekday names come from `strftime('%a')`, which
follows the C locale rather than the system one.
