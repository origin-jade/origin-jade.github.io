"""Guides (section "guides"): one helper module per page (pages/_guides_<page>.py)."""
from pages import _game_util as U

PAGES = ("_guides_breeding", "_guides_shiny", "_guides_legendaries", "_guides_gifts", "_guides_completion", "_guides_keyitems")

_MODS = U.load_pages(PAGES)
STRINGS = U.merge_strings(_MODS)


def register(ctx):
    for m in _MODS:
        ctx.add_page(m.PATH)


def render(ctx):
    for m in _MODS:
        m.render(ctx)
