# Waveshare E-ink Info Display

A Raspberry Pi–powered information display on a Waveshare 7.5" (V2) e-paper screen. It shows the current date and time, a weather forecast (OpenWeather), and — depending on the time of day — either my GitHub pull request status or my Steam friends' activity.

![Preview](assets/preview.png)

I wrote a blog series about building it:

1. [Informative e-ink display with Raspberry Pi — part 1](https://maikhel.github.io/blog/informative-e-ink-display-with-raspberry-pi-part-1/) — hardware setup and drawing on the screen
2. [Part 2](https://maikhel.github.io/blog/informative-e-ink-display-with-raspberry-pi-part-2/) — rendering the clock and weather layout
3. [Part 3](https://maikhel.github.io/blog/informative-e-ink-display-with-raspberry-pi-part-3/) — fetching live data from GitHub, Steam, and OpenWeather

The posts reference specific stages of this repo — the [`1.0`](../../tree/1.0) tag matches the state described in the series.

## How it works

- `clock.py` — main loop: renders the screen every minute, sleeps at night
- `drawing.py` — composes the image (time, weather, GitHub/Steam panels) with Pillow
- `services/` — fetch scripts for weather, GitHub PRs, and Steam friend statuses; each writes JSON to `data/` (run them from cron)
- `demo.py` — renders the layout to `preview.png` without the e-ink hardware, using `example_data/`
- `shutdown.py`, `deep_clean.py` — clear the panel safely / remove ghosting

## Setup

1. Install the [Waveshare e-Paper library](https://github.com/waveshareteam/e-Paper) on the Pi, plus `pillow`, `requests`, and `python-dotenv`
2. Copy `.env.example` to `.env` and fill in your API keys and Steam IDs
3. Schedule the `services/` scripts with cron and run `clock.py` (e.g. as a systemd service)
