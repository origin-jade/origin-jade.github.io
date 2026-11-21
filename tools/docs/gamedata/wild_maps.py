"""Map facts the wild-encounter pages need beyond the encounter tables.

    wild_maps.field_spots(map_id)  -> Spots(trees, rocks)
        trees: metatiles of the map's layout whose behaviour is a headbutt tree
               (MetatileBehavior_IsHeadbuttTree; src/field_control_avatar.c
               GetInteractedMetatileScript -> EventScript_Headbutt, IS_HNS)
        rocks: object events running EventScript_RockSmash
        Both scripts end in `special RockSmashWildEncounter`
        (data/scripts/field_move_scripts_hns.inc), which rolls the map's
        rock_smash_mons table (src/wild_encounter.c RockSmashWildEncounter).
    wild_maps.overworld_mons(map_id) -> [OwMon(species_const, when)]
        Visible Pokemon of a map: object events with a species sprite
        (OBJ_EVENT_GFX_MON_BASE+SPECIES_*) and no script (rule of
        tools/check_regions.py). when: "always" (flag 0), "day"
        (FLAG_DAY_POKEMON: set at night), "night" (FLAG_NIGHT_POKEMON: set by
        day) - src/overworld.c UpdateTimeOfDay, IS_HNS branch - or "flag"
        (any other flag: shown or hidden by the story).
    wild_maps.floor_name(code, lang) -> floor label of the game ("EG", "1S",
        "U1S" ...: gText_1F ... in src/strings.c; English build "1F", "2F",
        "B1F") or None; lang "de"|"en", None = the process language
    wild_maps.emerge_target(map_id) -> map id the "emerge" connection leads to
        (dive areas), or None
    wild_maps.time_hours()         -> {"TIME_MORNING": (begin, end), ...}
        (include/constants/rtc.h as preprocessed for this build)

Reads oj_world's layout helpers (tools/oj_world.py: Behaviors, Tilesets,
Grid) - the same code the repository's map checks use.
"""
import functools
import json
import os
import re
import sys

from . import repo_path
from . import tu as TU
from . import maps

_MON_GFX = re.compile(r"OBJ_EVENT_GFX_MON_BASE\s*\+\s*(SPECIES_\w+)")


class Spots:
    def __init__(self, trees, rocks):
        self.trees = trees
        self.rocks = rocks

    def __repr__(self):
        return "Spots(trees=%d, rocks=%d)" % (self.trees, self.rocks)


class OwMon:
    def __init__(self, species_const, when, flag):
        self.species_const = species_const
        self.when = when
        self.flag = flag

    def __repr__(self):
        return "OwMon(%s, %s)" % (self.species_const, self.when)


@functools.lru_cache(maxsize=None)
def _world():
    tools = repo_path("tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import oj_world
    return oj_world


@functools.lru_cache(maxsize=None)
def _behaviors():
    return _world().Behaviors()


@functools.lru_cache(maxsize=None)
def _tilesets():
    return _world().Tilesets()


@functools.lru_cache(maxsize=None)
def _layouts():
    data = json.load(open(repo_path("data", "layouts", "layouts.json"), encoding="utf-8"))
    return {l["id"]: l for l in data["layouts"] if "id" in l}


@functools.lru_cache(maxsize=None)
def field_spots(map_id):
    m = maps.by_id(map_id)
    trees = 0
    layout = _layouts().get(m.data.get("layout"))
    if layout and os.path.exists(repo_path(layout["blockdata_filepath"])):
        grid = _world().Grid(layout, _tilesets())
        tree_mb = _behaviors().preds.get("IsHeadbuttTree", set())
        for i in range(grid.w * grid.h):
            if grid.behavior_of_metatile(grid.blocks[i] & 0x3FF) in tree_mb:
                trees += 1
    rocks = sum(1 for o in m.data.get("object_events", []) if o.get("script") == "EventScript_RockSmash")
    return Spots(trees, rocks)


def overworld_mons(map_id):
    m = maps.by_id(map_id)
    out = []
    for o in m.data.get("object_events", []):
        g = _MON_GFX.search(o.get("graphics_id", ""))
        if not g or o.get("script") != "NULL":
            continue
        flag = o.get("flag", "0")
        when = {"0": "always", "FLAG_DAY_POKEMON": "day", "FLAG_NIGHT_POKEMON": "night"}.get(flag, "flag")
        out.append(OwMon(g.group(1), when, flag))
    return out


@functools.lru_cache(maxsize=None)
def _floor_strings(lang):
    text = TU.load("src/strings.c", lang=lang).text
    return dict(re.findall(r"\bgText_(B?\d+F|Rooftop)\s*\[\s*\]\s*=\s*\{?\s*([^;]*?)\s*\}?\s*;", text))


def floor_name(code, lang=None):
    """Floor code of a map name ("1F", "B2F") -> the game's own label in that build."""
    raw = _floor_strings(TU.lang(lang)).get(code)
    if raw is None:
        return None
    # preprocessed _("EG") becomes a string literal or a byte list; take the literal text
    m = re.search(r'"([^"]*)"', raw)
    if m:
        return m.group(1)
    return None


def emerge_target(map_id):
    m = maps.by_id(map_id)
    for c in m.data.get("connections") or []:
        if c.get("direction") == "emerge":
            return c.get("map")
    return None


@functools.lru_cache(maxsize=None)
def time_hours():
    t = TU.load("src/rtc.c")
    out = {}
    for name in ("MORNING", "DAY", "EVENING", "NIGHT"):
        b, e = t.const(name + "_HOUR_BEGIN"), t.const(name + "_HOUR_END")
        if b is not None and e is not None and b != e:
            out["TIME_" + name] = (b, e)
    return out
