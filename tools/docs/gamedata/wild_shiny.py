"""Shiny rules of the jade build, read from the source.

    wild_shiny.odds_table()        -> [8, 16, 32, 64, 128]  sShinyOddsTable (src/pokemon.c GetShinyOdds:
                                      shiny when GET_SHINY_VALUE < odds, out of 65536)
    wild_shiny.default_odds()      -> SHINY_ODDS (include/constants/pokemon.h; used without a save)
    wild_shiny.charm_rolls()       -> I_SHINY_CHARM_ADDITIONAL_ROLLS (include/config/item.h)
    wild_shiny.chance(odds, extra) -> probability with `extra` re-rolls (CreateBoxMon: re-roll the
                                      personality while not shiny and rolls are left)
    wild_shiny.option(item_const, lang) -> Option(name, tab, choices, descriptions) of the challenge menu
                                      (src/challenge_menu.c sTabItems_*; e.g. "ITEM_FEATURES_SHINY_CHANCE");
                                      lang "de"|"en", None = the process language
    wild_shiny.flags()             -> {name: value} of the switches CreateBoxMon reads
                                      (P_ONLY_OBTAINABLE_SHINIES, P_NO_SHINIES_WITHOUT_POKEBALLS,
                                      P_FLAG_FORCE_SHINY, P_FLAG_FORCE_NO_SHINY, I_FISHING_CHAIN,
                                      DEXNAV_ENABLED, P_EGG_SHINY_ROLL_ON_PICKUP)
    wild_shiny.alt_palette_species() -> [Species] with gSpeciesInfo[].shinyPaletteModern (the
                                      "Shinyfarbe" option, GetMonSpritePalFromSpeciesIsEgg)
    wild_shiny.alt_palette(sp)     -> repo path of that palette
    wild_shiny.marts_selling(item_const) -> [map ids] whose pokemart lists contain the item
    wild_shiny.charm_givers()      -> [(map id, label)] of `giveitem ITEM_SHINY_CHARM` in active maps
"""
import functools
import os
import re

from . import repo_path
from . import tu as TU
from . import namestyle
from . import text
from . import maps
from . import species as SP


class Option:
    def __init__(self, **kw):
        self.__dict__.update(kw)


@functools.lru_cache(maxsize=None)
def _pk():
    return TU.load("src/pokemon.c")


def odds_table():
    return [int(x) for x in _pk().array("sShinyOddsTable")]


def default_odds():
    return _pk().const("SHINY_ODDS")


def charm_rolls():
    return _pk().const("I_SHINY_CHARM_ADDITIONAL_ROLLS")


def chance(odds, extra_rolls=0):
    p = odds / 65536.0
    return 1.0 - (1.0 - p) ** (1 + extra_rolls)


MENU = "src/challenge_menu.c"


def option(item_const, lang=None):
    return _option(item_const, TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _option(item_const, lang):
    t = TU.load(MENU, lang=lang)

    def cl(v):
        return TU.clean(MENU, t.text_value(v), lang)

    def label(v):       # names of tabs, options and choices: the site's name style
        raw = t.text_value(v)
        return namestyle.show(TU.clean(MENU, raw, lang), TU.written_in(MENU, raw, lang), "label", lang)
    idx = t.need(item_const)
    tab_const = {"ITEM_FEATURES_": "TAB_FEATURES", "ITEM_NUZLOCKE_": "TAB_NUZLOCKE"}
    tab = next(v for k, v in tab_const.items() if item_const.startswith(k))
    table = {"TAB_FEATURES": "sTabItems_Features", "TAB_NUZLOCKE": "sTabItems_Nuzlocke"}[tab]
    item = t.table(table)[idx]
    name = label(item.get("name"))
    descs = [cl(x) for x in t.init(str(t.field(item, "descriptions"))).positional()]
    choices = [label(x) for x in t.init(str(t.field(item, "choiceNames"))).positional()]
    tab_name = label(t.table("sTabs")[t.need(tab)].positional()[0])
    return Option(name=name, tab=tab_name, choices=choices, descriptions=descs, lang=lang)


def flags():
    t = _pk()
    out = {}
    for n in ("P_ONLY_OBTAINABLE_SHINIES", "P_NO_SHINIES_WITHOUT_POKEBALLS", "P_FLAG_FORCE_SHINY",
              "P_FLAG_FORCE_NO_SHINY", "P_EGG_SHINY_ROLL_ON_PICKUP"):
        out[n] = t.const(n)
    out["I_FISHING_CHAIN"] = TU.load("src/fishing.c").const("I_FISHING_CHAIN")
    dn = TU.load("src/dexnav.c") if os.path.exists(repo_path("src", "dexnav.c")) else t
    out["DEXNAV_ENABLED"] = dn.const("DEXNAV_ENABLED")
    return out


def alt_palette_species(lang=None):
    out = []
    for sp in SP.all_species(lang).values():
        if SP.field(sp, "shinyPaletteModern"):
            out.append(sp)
    return out


def alt_palette(sp):
    return SP._incbin_png(SP.field(sp, "shinyPaletteModern"))


def _active_scripts():
    for m in sorted(maps.all_maps().values(), key=lambda m: (m.group_index, m.map_num)):
        if maps.locked_mapsec(m.mapsec):
            continue
        p = repo_path("data", "maps", m.dir, "scripts.inc")
        if os.path.exists(p):
            yield m, open(p, encoding="utf-8").read()


def marts_selling(item_const):
    out = []
    for m, src in _active_scripts():
        for lst in re.findall(r"((?:\s*\.2byte\s+ITEM_\w+\s*\n)+)\s*pokemartlistend", src):
            if re.search(r"\b%s\b" % item_const, lst) and m.id not in out:
                out.append(m.id)
    return out


def charm_givers(item_const="ITEM_SHINY_CHARM"):
    out = []
    for m, src in _active_scripts():
        for mm in re.finditer(r"^\s*giveitem\s+%s\b" % item_const, src, re.M):
            labels = re.findall(r"^(\w+)::", src[:mm.start()], re.M)
            out.append((m.id, labels[-1] if labels else None))
    return out
