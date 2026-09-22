# Playlist of Screens — Architecture Plan

**Date:** 2026-09-22
**Branch:** `playlist-screens`
**Status:** proposed

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

`playlist.yaml`:

```yaml
tick_seconds: 60
header:
  clock: true
  indicator: dots

screens:
  - id: work
    dwell: 5m
    when: "weekday and 8 <= hour < 18"
  - id: weather
    dwell: 3m
  - id: steam
    dwell: 3m
    when: "hour >= 17 or weekend"
    skip_if_empty: true
  - id: quote
    dwell: 2m
```

Engine: filter by `when` + `available()`, round-robin the survivors, advance when
dwell expires. Adding a screen is one file plus four lines of YAML; reordering the
day never touches Python.

This replaces the hardcoded weekday/work-hours `if` in `drawing.py`
(`draw_steam_or_github`).

`when` should be a small, explicitly-evaluated expression over a fixed set of
names (`hour`, `weekday`, `weekend`, `minute`) — not a bare `eval()` of arbitrary
config.

## Data contract

Every fetcher writes the same envelope:

```json
{
  "source": "github",
  "fetched_at": "2026-09-22T09:15:00+00:00",
  "ok": true,
  "data": { }
}
```

Renderer rules, tuned for the relaxed-freshness decision:

- **Missing file, or `ok: false`** → source unavailable → screens requiring it
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
- **In-dwell tick** → partial refresh.
- `FULL_REFRESH_EVERY = 10` becomes: full refresh **on rotation, or after 10
  partials, whichever comes first.**

**Night mode interaction:** after the 00:00–07:00 blank, the playlist must resume
at the first eligible screen rather than mid-cycle. Reset playlist state when
exiting night mode, alongside the existing forced full refresh.

## Screen designs (424px body)

### Work

Calendar is deferred, so GitHub gets the whole body — which means it should
finally be readable. Today `drawing.py` truncates PR titles to **10 characters**
and reduces the review queue to a bare count.

Two-column body (right column becomes the calendar later):

- **Left:** my open PRs, grouped by state (draft / open / changes requested),
  full-width titles with proper truncation.
- **Right:** review queue as an actual list — repo, title, age — not a number.

### Weather

- **Left ~40%:** big icon, temperature, feels-like, wind, humidity, description.
- **Right / bottom:** the existing 5-day midday/midnight strip.

Requires a fetcher change: `fetch_weather.py` currently derives "current" from
`forecast_list[0]` of the 3-hour forecast endpoint, which can be up to three hours
off and carries no feels-like, wind, or humidity. Add a second call to the current
weather endpoint and put it under `data.current`.

### Steam

Three bands, each independently skippable:

1. Friends online now — nickname, game, session length.
2. My recent playtime — `IPlayerService/GetRecentlyPlayedGames` (last 2 weeks).
3. Wishlist — titles and any price drops.

The wishlist endpoint is undocumented store JSON and has broken before; a wishlist
failure must degrade to hiding that band only, never to failing the screen.

### Extra

`assets/quotes.json`, indexed by day-of-year — deterministic, no network, no
failure mode. This is the slot to reuse for whatever comes next.

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
Only now: the richer weather fetch, the new Steam endpoints, the quotes screen,
and the redesigned Work layout.

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
    when: "weekday and 8 <= hour < 18"
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
delete. The fixed name set (`hour`, `weekday`, `weekend`, `minute`) is the
ceiling, not a starting point.

Open questions for V2: what happens when no playlist matches the current time
(fallback playlist, or blank panel?), and whether a screen may belong to more
than one playlist.
