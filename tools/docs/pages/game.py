"""Section "Game": what is new, getting started & FAQ, settings and game modes, the
level and EXP system, credits. Every page lives in its own helper module
(pages/_game_<page>.py: PATH, S, render); this module joins their texts and registers
and renders them.

The sitemap also has a page for updates (game/changelog). The repository holds no
list of changes per version, so that page is not registered here.
"""
from pages import _game_util as U

# "What's new" (_game_features) and "Settings & game modes" (_game_settings) are written but
# not built: the owner wants the site to stay a reference, and the menus explain themselves.
PAGES = U.load_pages(["_game_start"])
STRINGS = U.merge_strings(PAGES)

# page path -> key of its search keywords
KEYWORDS = {"game/features": "ft_keywords", "game/start": "st_keywords", "game/settings": "set_keywords"}


def register(ctx):
    for m in PAGES:
        ctx.add_page(m.PATH, keywords=ctx.t(KEYWORDS[m.PATH]))


def render(ctx):
    for m in PAGES:
        m.render(ctx)
