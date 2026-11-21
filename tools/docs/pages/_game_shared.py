"""Facts several pages of the section "Game" use: menu entries by their place in the
menus, the times of day, the rematch counts. Everything is read from the source; nothing
here is page text.
"""
import functools

from common import html as H
from gamedata import game_rules as G
from gamedata import hand_facts as F
from gamedata import hand_menus as M
from gamedata import levels
from gamedata import maps
from gamedata import namestyle
from gamedata import trainers
from gamedata import tu as TU


def challenge(ctx, tab_const, item_const):
    """Entry of the challenge menu in the page language."""
    return G.challenge_item(tab_const, item_const, ctx.lang)


@functools.lru_cache(maxsize=None)
def _option_pos(name_de):
    for ti, tab in enumerate(M.option_tabs("de")):
        for ii, item in enumerate(tab.items):
            if item.name_game == name_de:
                return ti, ii
    raise TU.DataError("option %s is not in the options menu" % name_de)


def option(ctx, name_de):
    """Entry of the options menu in the page language, found by its German name."""
    ti, ii = _option_pos(name_de)
    return M.option_tabs(ctx.lang)[ti].items[ii]


def choices_line(ctx, item):
    """"A / B / C" of an entry's choice names (HTML)."""
    return " / ".join(H.esc(c.name) for c in item.choices)


@functools.lru_cache(maxsize=None)
def day_hours():
    """[(begin hour, end hour)] of morning, day, evening, night."""
    r = TU.load("src/rtc.c")
    F.require("src/overworld.c", r"gTimeOfDay = TIME_EVENING;")
    return [(r.need("%s_HOUR_BEGIN" % k), r.need("%s_HOUR_END" % k)) for k in ("MORNING", "DAY", "EVENING", "NIGHT")]


def hours_text(ctx, span):
    if ctx.lang == "de":
        return "%d–%d Uhr" % span
    return "%02d:00–%02d:00" % span


@functools.lru_cache(maxsize=None)
def rematch_counts():
    """{region: number of trainers with phone rematches} (normal rows of the rematch table)."""
    count = {"Kanto": 0, "Johto": 0, "Hoenn": 0}
    for r in trainers.rematch_rows():
        if r.special or not r.map_id:
            continue
        m = maps.by_id(r.map_id)
        if m and m.region in count:
            count[m.region] += 1
    return count


def bands():
    """((low, high) of phone rematches below the reference level, (low, high) of the Kanto
    leaders above it) as positive numbers."""
    plow, phigh = levels.phone_band()
    return (-phigh, -plow), levels.leader_band()


def pc_entry(ctx):
    """Name of the PC menu entry that opens the challenge menu, in the site's name style."""
    game = F.c_string("src/strings.c", "gText_Challenges", ctx.lang)
    return namestyle.show(game, ctx.lang, "label", ctx.lang)
