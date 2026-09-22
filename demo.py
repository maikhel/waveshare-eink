"""Render the panel to PNG on a desktop, without the e-ink hardware.

Writes preview.png for whichever screen the playlist picks right now, plus
preview_<id>.png for every configured screen so layouts can be compared
without waiting for a rotation. Uses example_data/ so it works before the
fetchers have ever run.
"""
from datetime import datetime

from eink import config as config_module
from eink import render, screens, theme
from eink.playlist import Playlist, Slide
from eink.screens import Context

WIDTH, HEIGHT = 800, 480  # 7.5'' screen size


def draw_demo():
    config = config_module.load(known_screens=screens.REGISTRY)
    ctx = Context(now=datetime.now(), fonts=theme.Fonts(), data_dir='example_data')

    slide = Playlist(config, screens).tick(ctx)
    image = render.draw(ctx, WIDTH, HEIGHT, slide, config)
    image.save("preview.png")
    print(f"preview.png -> {slide.entry.id if slide.entry else 'nothing eligible'}")

    # Every screen, regardless of schedule, for side-by-side comparison.
    for position, entry in enumerate(config.entries):
        screen = screens.get(entry.id)
        forced = Slide(screen=screen, entry=entry, rotated=True,
                       position=position, total=len(config.entries))
        name = f"preview_{entry.id}.png"
        render.draw(ctx, WIDTH, HEIGHT, forced, config).save(name)
        available = "" if screen.available(ctx) else "  (unavailable now)"
        print(f"{name}{available}")

    image.show()


draw_demo()
