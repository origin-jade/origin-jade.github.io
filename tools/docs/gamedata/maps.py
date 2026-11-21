"""Maps: id -> display name, map section, region, group.

    m = maps.by_id("MAP_ROUTE29_HNS")
    m.id, m.dir ("Route29_hns"), m.name (internal map name), m.mapsec ("MAPSEC_ROUTE_29"),
    m.mapsec_num (enum value), m.display ("Route 29", the in-game map section name),
    m.region ("Kanto"|"Johto"|"Hoenn"|"Alola"|"Hisui"|"Sonder", for display),
    m.group_index (index in data/maps/map_groups.json group_order = MAP_GROUP), m.map_num (MAP_NUM),
    m.map_type, m.active,
    m.data (the parsed map.json)
    maps.all_maps(active_only=True) -> {id: Map}
    maps.by_dir("Route29_hns")
    maps.mapsec_name("MAPSEC_ROUTE_29") -> "Route 29"
    maps.locked_mapsec(mapsec) -> True for areas the jade build keeps closed (Sinjoh, Alola)
    maps.host_mapsec(map_id) -> story anchor (MAPSEC_DYNAMIC maps: section of the map that warps there)
    MAPSEC_DYNAMIC maps (ferry, contest halls) get their name from DYNAMIC_PLACES.

Language: all_maps, by_id, by_dir, by_group_num, mapsec_name and dynamic_place take
lang="de"|"en" (None = the process language). The map section names come from
src/data/region_map/region_map_sections.json, which has one name per section and no
language switch: the English build shows the same (German) place names as the German
build. Only the DYNAMIC_PLACES names differ - they are quoted from dialogue, and dialogue
is translated. m.region is a key ("Kanto", "Johto", "Hoenn", "Alola", "Hisui", "Sonder"),
not display text; REGION_KEYS lists them.

Active maps are the ones with "game_version": "hns" (tools/oj_world.py ACTIVE_GAME_VERSION);
the others are retired and not in the game's map groups.

Two different region notions exist (DATA_MAP.md 4.4 / 6.1):
  * m.region  - where a place belongs for the reader (map section ranges, as
                tools/oj_world.py MapSections.region),
  * levels.remap_region(map_id) - the level rule of src/level_scaling.c GetRemapRegion.
"""
import functools
import json
import os

from . import repo_path
from . import tu as TU
from . import entext
from . import namestyle

ACTIVE_GAME_VERSION = "hns"
# Region ranges of the jade build (tools/oj_world.py MapSections)
_RANGES = (("Hisui", "MAPSEC_SNOWSWEPT_CAVERN", "MAPSEC_SINJOH_RUINS"),
           ("Johto", "MAPSEC_NEW_BARK_TOWN", "MAPSEC_WHIRL_ISLANDS"),
           ("Kanto", "MAPSEC_PALLET_TOWN", "MAPSEC_SPECIAL_AREA"),
           ("Alola", "MAPSEC_MELEMELE_ISLAND", "MAPSEC_ULAULA_CAVE_2"))
# Hoenn map sections inside the Johto/Kanto number range (src/level_scaling.c IsHoennMapsec)
HOENN_EXTRA = ("MAPSEC_VICTORY_ROAD", "MAPSEC_SAFARI_ZONE", "MAPSEC_ABANDONED_SHIP", "MAPSEC_LILYCOVE_CITY")
# Maps with region_map_section MAPSEC_DYNAMIC have no name of their own in
# gRegionMapEntries (the entry is empty). The place is named after the game
# text that names it: (map directory prefix, script text label, {language: name}).
# The name of each language occurs in that label's text of that build (checked by
# selftest). The reader region follows IsHoennMapsec (MAPSEC_DYNAMIC lies between
# MAPSEC_LITTLEROOT_TOWN and MAPSEC_NONE) and the story position is the section
# of the map whose script warps there (host_mapsec()).
DYNAMIC_PLACES = (
    ("SSTidal", "SSTidalCorridor_Text_BrineyWelcomeAboard", {"de": "MS Tide", "en": "S.S. TIDAL"}),
    ("ContestHall", "SlateportCity_Text_ScottLeavesContestHall", {"de": "Wettbewerbshalle", "en": "CONTEST HALL"}),
)
# Values of Map.region / display_region(): keys, not display text ("Sonder" = maps
# outside the regions: MAPSEC_DYNAMIC, MAPSEC_NONE and unknown sections).
REGION_KEYS = ("Kanto", "Johto", "Hoenn", "Alola", "Hisui", "Sonder")


class Map:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Map(%s %s)" % (self.id, self.display)


def _t():
    # level_scaling.c includes constants/maps.h and constants/region_map_sections.h
    return TU.load("src/level_scaling.c", lang="de")


@functools.lru_cache(maxsize=None)
def _sections_json():
    return json.load(open(repo_path("src", "data", "region_map", "region_map_sections.json"), encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def _sections():
    """{MAPSEC_*: German name} (the "name" of hns_map_sections)."""
    return {s["id"]: s.get("name") for s in _sections_json()["hns_map_sections"]}


@functools.lru_cache(maxsize=None)
def _sections_en():
    """{MAPSEC_*: English name} where the JSON has one ("name_en": the English build's name)."""
    return {s["id"]: s["name_en"] for s in _sections_json()["hns_map_sections"] if s.get("name_en")}


@functools.lru_cache(maxsize=None)
def _mapsec_names(lang):
    """{MAPSEC_*: (name as the game shows it, language it is written in)}. English:
    the "name_en" of the JSON where it has one; with a tree of the English version
    configured, the "name_en" of that tree's JSON for the same section constant goes
    through the usual rule (entext.pick)."""
    src = entext.mapsec_names() if lang == "en" else {}
    own = _sections_en() if lang == "en" else {}
    out = {}
    for k, de in _sections().items():
        name = own.get(k, de)
        if lang == "en" and de is not None and entext.root():
            name = entext.pick("mapsec", k, name, de, src.get(k))
        out[k] = (name, "de" if lang == "de" or name == de else "en")
    return out


def mapsec_name(mapsec, lang=None):
    """Name of a map section (gRegionMapEntries, built from region_map_sections.json
    hns_map_sections). English: in the site's name style (namestyle.py)."""
    e = _mapsec_names(TU.lang(lang)).get(mapsec)
    if not e or not e[0]:
        return mapsec
    return namestyle.show(e[0], e[1], "place", TU.lang(lang))


def mapsec_name_game(mapsec, lang=None):
    """Name of a map section exactly as the game shows it (English: capitals)."""
    e = _mapsec_names(TU.lang(lang)).get(mapsec)
    return e[0] if e and e[0] else mapsec


def mapsec_num(mapsec):
    return _t().const(mapsec)


def is_hoenn_mapsec(mapsec):
    """src/level_scaling.c IsHoennMapsec."""
    t = _t()
    v = t.const(mapsec)
    if v is None:
        return False
    if t.need("MAPSEC_LITTLEROOT_TOWN") <= v < t.need("MAPSEC_NONE"):
        return True
    return mapsec in HOENN_EXTRA


def dynamic_place(map_dir, lang=None):
    """(name in that language, script text label, family prefix) for a MAPSEC_DYNAMIC
    map, or None."""
    lang = TU.lang(lang)
    for prefix, label, names in DYNAMIC_PLACES:
        if map_dir.startswith(prefix):
            return namestyle.show(names[lang], lang, "place", lang), label, prefix
    return None


def dynamic_place_game(map_dir, lang=None):
    """The name of dynamic_place() exactly as the game text writes it."""
    lang = TU.lang(lang)
    for prefix, label, names in DYNAMIC_PLACES:
        if map_dir.startswith(prefix):
            return names[lang]
    return None


def display_region(mapsec):
    t = _t()
    if mapsec in ("MAPSEC_DYNAMIC", "MAPSEC_NONE"):
        return "Sonder"
    v = t.const(mapsec)
    if v is None:
        return "Sonder"
    for name, lo, hi in _RANGES:
        if t.need(lo) <= v <= t.need(hi):
            return name
    if is_hoenn_mapsec(mapsec):
        return "Hoenn"
    return "Sonder"


def locked_mapsec(mapsec):
    """Areas the jade build keeps closed (LOCKED_MAPSECS in tools/check_text_width.py:
    Sinjoh and Alola)."""
    return display_region(mapsec) in ("Alola", "Hisui")


def _load(lang=None):
    return _load_lang(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _map_json(path):
    return json.load(open(path, encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def _load_lang(lang):
    groups = json.load(open(repo_path("data", "maps", "map_groups.json"), encoding="utf-8"))
    order = groups["group_order"]
    out = {}
    for gi, g in enumerate(order):
        for num, d in enumerate(groups[g]):
            p = repo_path("data", "maps", d, "map.json")
            if not os.path.exists(p):
                continue
            data = _map_json(p)
            mapsec = data.get("region_map_section", "MAPSEC_NONE")
            display, region = mapsec_name(mapsec, lang), display_region(mapsec)
            display_game = mapsec_name_game(mapsec, lang)
            dyn = dynamic_place(d, lang) if mapsec == "MAPSEC_DYNAMIC" else None
            if dyn:
                display, region = dyn[0], ("Hoenn" if is_hoenn_mapsec(mapsec) else region)
                display_game = dynamic_place_game(d, lang)
            m = Map(id=data["id"], dir=d, name=data.get("name", d), mapsec=mapsec,
                    mapsec_num=mapsec_num(mapsec), display=display, display_game=display_game, lang=lang,
                    region=region, group=g, group_index=gi, map_num=num,
                    map_type=data.get("map_type", ""),
                    active=data.get("game_version", ACTIVE_GAME_VERSION) == ACTIVE_GAME_VERSION,
                    data=data)
            if m.id in out and not m.active:
                continue
            out[m.id] = m
    return out


@functools.lru_cache(maxsize=None)
def host_mapsec(map_id):
    """Story anchor of a MAPSEC_DYNAMIC map: the map section of the first map (map
    group order) whose scripts.inc warps to a map of the same DYNAMIC_PLACES family.
    Other maps: their own map section."""
    m = by_id(map_id)
    dyn = dynamic_place(m.dir, "de") if m and m.mapsec == "MAPSEC_DYNAMIC" else None
    if not dyn:
        return m.mapsec if m else None
    family = {x.id for x in _load().values() if dynamic_place(x.dir, "de") == dyn}
    import re
    for x in sorted(_load().values(), key=lambda x: (x.group_index, x.map_num)):
        if x.id in family or not x.active:
            continue
        p = repo_path("data", "maps", x.dir, "scripts.inc")
        if not os.path.exists(p):
            continue
        targets = set(re.findall(r"\b(MAP_\w+)\b", open(p, encoding="utf-8").read()))
        if targets & family:
            return x.mapsec
    return m.mapsec


def all_maps(active_only=True, lang=None):
    return {k: v for k, v in _load(lang).items() if v.active or not active_only}


def by_id(map_id, lang=None):
    return _load(lang).get(map_id)


def by_dir(d, lang=None):
    for m in _load(lang).values():
        if m.dir == d:
            return m
    return None


def by_group_num(group, num, lang=None):
    """Map of MAP_GROUP()/MAP_NUM() values (as stored in gRematchTable etc.)."""
    for m in _load(lang).values():
        if m.group_index == group and m.map_num == num:
            return m
    return None


def group_index_of(map_id):
    return _load()[map_id].group_index
