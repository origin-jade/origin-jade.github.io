"""Locations: the grouping of maps into the places the site has pages for.

A location is one region map section (MAPSEC_*): all active maps of the section -
floors, rooms, houses, gates - belong to it. Language neutral (constants and ids only);
names come from gamedata.maps in the language of the page.

    locations.all_locations()        -> [Location] in travel order (Kanto, Johto, Hoenn)
    locations.by_key(key)            -> Location or None
    locations.key_of_map(map_id)     -> key of the location a map belongs to, or None when the
                                        map has no page (locked, never reachable, link rooms)
    locations.anchor_of_mapsec(sec)  -> (location key, fragment) for a map section that is shown
                                        as a part of another location (dive spots), else None
    locations.in_region(region)      -> [Location] of "kanto" | "johto" | "hoenn"

Location fields:
    key        registry key: the MAPSEC_* constant; for the ferry of gamedata.maps.DYNAMIC_PLACES
               the id of its first map (MAP_SS_TIDAL_CORRIDOR)
    mapsec     the map section (the ferry: MAPSEC_DYNAMIC)
    region     "kanto" | "johto" | "hoenn" (the hub page the location is listed on)
    kind       "town" | "route" | "dungeon" | "special"
    map_ids    every map of the location: outdoor maps first, then map group order
    content_ids  the maps whose trainers, items and events are shown (map_ids without
               alternative layouts and copies the play-through model never reaches)
    parts      [(map section, fragment, [map ids])] sections shown as a part of this location
    order      position in the travel order (all regions)
    wave       first wave of the play-through model

Which sections get a page:
  * locked areas (maps.locked_mapsec: Alola, Sinjoh) - none;
  * sections of which the play-through model reaches no map (locations_order.SECTION_ORDER:
    Navel Rock, Faraway Island, Southern Island, Embedded Tower, secret bases, the truck) - none.
    The Lilycove ferry script offers no event-ticket island (data/maps/LilycoveCity_Harbor);
  * the link rooms (MAPSEC_SPECIAL_AREA and the MAPSEC_DYNAMIC rooms) - none;
  * MAPSEC_DYNAMIC: only the ferry (maps.DYNAMIC_PLACES "SSTidal") - the contest halls have
    no content of their own;
  * dive maps (MAPSEC_UNDERWATER_*) are a part of the location their "emerge" connection
    leads to (Route 124, Sootopolis City, Seafloor Cavern ...).
"""
import functools
import re

from . import maps
from . import levels
from . import locations_order as ORDER

REGIONS = ("kanto", "johto", "hoenn")
_REGION = {"Kanto": "kanto", "Johto": "johto", "Hoenn": "hoenn"}
# Sections without a page although the model reaches a map (link rooms).
NO_PAGE = ("MAPSEC_SPECIAL_AREA", "MAPSEC_SECRET_BASE", "MAPSEC_INSIDE_OF_TRUCK", "MAPSEC_NONE")
# MAPSEC_DYNAMIC families (maps.DYNAMIC_PLACES prefix) with a page of their own.
DYNAMIC_PAGES = ("SSTidal",)
_ROUTE = re.compile(r"^MAPSEC_ROUTE_\d+$")
_TOWN = re.compile(r"^MAPSEC_\w+_(TOWN|CITY)$")
# Kinds that the name of the section does not give.
KIND = {
    "MAPSEC_CINNABAR_ISLAND": "town",
    "MAPSEC_SAFARI_ZONE_GATE": "special",
    "MAPSEC_KANTO_SAFARI_ZONE": "special",
    "MAPSEC_SAFARI_ZONE": "special",
    "MAPSEC_NATIONAL_PARK": "special",
    "MAPSEC_INDIGO_PLATEAU": "special",
    "MAPSEC_POKEMON_LEAGUE": "special",
    "MAPSEC_BATTLE_FRONTIER": "special",
    "MAPSEC_TRAINER_HILL": "special",
    "MAPSEC_BIRTH_ISLAND": "special",
    "MAPSEC_LAKE_OF_RAGE": "dungeon",
    "MAPSEC_MT_CHIMNEY": "dungeon",
    "MAPSEC_JAGGED_PASS": "dungeon",
    "MAPSEC_POWER_PLANT": "dungeon",
    "MAPSEC_POKEMON_MANSION": "dungeon",
    "MAPSEC_POKEMON_TOWER": "dungeon",
}
# Places outside the three region maps: the region whose harbour the ship to them leaves from
# (Birth Island: data/maps/OlivineCity_PortInside_hns/scripts.inc).
REGION = {
    "MAPSEC_BIRTH_ISLAND": "johto",
}
# Dive maps without an "emerge" connection (the game surfaces through a warp): the section they belong to.
PART_OF = {
    "MAPSEC_UNDERWATER_SOOTOPOLIS": "MAPSEC_SOOTOPOLIS_CITY",
    "MAPSEC_UNDERWATER_SEAFLOOR_CAVERN": "MAPSEC_SEAFLOOR_CAVERN",
    "MAPSEC_UNDERWATER_SEALED_CHAMBER": "MAPSEC_SEALED_CHAMBER",
    "MAPSEC_UNDERWATER_MARINE_CAVE": "MAPSEC_MARINE_CAVE",
}
_SUFFIX = re.compile(r"_(Frlg|hns)$")
_VARIANT = re.compile(r"(Day|Night|LowTide|HighTide)$")


class Location:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Location(%s %s %s, %d maps)" % (self.key, self.region, self.kind, len(self.map_ids))


def base_dir(d):
    """Map folder without the build suffix (_Frlg, _hns)."""
    return _SUFFIX.sub("", d)


def _twin_name(d):
    """Folder name without the build suffix and without the marker of an alternative layout."""
    parts = base_dir(d).split("_")
    return "_".join(_VARIANT.sub("", p) or p for p in parts)


def _outdoor(m):
    return m.map_type not in ("MAP_TYPE_INDOOR", "MAP_TYPE_UNDERGROUND", "MAP_TYPE_UNDERWATER",
                              "MAP_TYPE_SECRET_BASE")


def _emerge(m):
    for c in m.data.get("connections") or []:
        if c.get("direction") == "emerge":
            return c.get("map")
    return None


@functools.lru_cache(maxsize=None)
def _build():
    allm = [m for m in maps.all_maps(lang="de").values() if not maps.locked_mapsec(m.mapsec)]
    allm.sort(key=lambda m: (m.group_index, m.map_num))
    by_id = {m.id: m for m in allm}
    unreached = ORDER.UNREACHED_MAPS
    reached_twins = {}
    for m in allm:
        if m.dir not in unreached:
            reached_twins.setdefault((m.mapsec, _twin_name(m.dir)), []).append(m.id)
    rank = {s: i for i, s in enumerate(ORDER.SECTION_ORDER)}
    groups, order_keys = {}, []          # key -> [Map]

    def add(key, m):
        if key not in groups:
            groups[key] = []
            order_keys.append(key)
        groups[key].append(m)

    parts = {}                           # host mapsec -> {mapsec: [map ids]}
    for m in allm:
        sec = m.mapsec
        if sec in NO_PAGE:
            continue
        if sec == "MAPSEC_DYNAMIC":
            dyn = maps.dynamic_place(m.dir, "de")
            if dyn and dyn[2] in DYNAMIC_PAGES and m.dir in _reached_dirs():
                add(("dyn", dyn[2]), m)
            continue
        if sec not in rank:
            continue                     # the model reaches no map of this section
        if sec.startswith("MAPSEC_UNDERWATER"):
            tgt = by_id.get(_emerge(m) or "")
            host = PART_OF.get(sec) or (tgt.mapsec if tgt is not None else None)
            if host in rank and not host.startswith("MAPSEC_UNDERWATER") and host not in NO_PAGE:
                parts.setdefault(host, {}).setdefault(sec, []).append(m.id)
                continue
        add(sec, m)
    # travel-order rank of every group
    locs = []
    waves = _waves()
    for key in order_keys:
        ms = groups[key]
        if isinstance(key, tuple):
            host = maps.host_mapsec(ms[0].id)
            lkey, mapsec = ms[0].id, "MAPSEC_DYNAMIC"
            pos = (rank.get(host, len(rank)), 1)
        else:
            lkey, mapsec = key, key
            pos = (rank[key], 0)
        extra = parts.get(mapsec, {}) if not isinstance(key, tuple) else {}
        ms = sorted(ms, key=lambda m: (0 if _outdoor(m) and "_" not in base_dir(m.dir) else 1,
                                       m.group_index, m.map_num))
        part_list = []
        for sec in sorted(extra, key=lambda s: rank.get(s, len(rank))):
            part_list.append((sec, "underwater" if len(extra) == 1 else "underwater-%d" % (len(part_list) + 1),
                              list(extra[sec])))
        map_ids = [m.id for m in ms] + [x for _s, _f, ids in part_list for x in ids]
        content = []
        for mid in map_ids:
            m = by_id[mid]
            if m.dir in unreached and reached_twins.get((m.mapsec, _twin_name(m.dir))):
                continue                 # an unreached copy or alternative layout of a reached map
            content.append(mid)
        locs.append(Location(key=lkey, mapsec=mapsec, region=None, kind=None, map_ids=map_ids,
                             content_ids=content, parts=part_list, pos=pos,
                             wave=min([waves[by_id[x].dir] for x in map_ids if by_id[x].dir in waves] or [10 ** 6])))
    locs.sort(key=lambda l: l.pos)
    # region and kind
    for l in locs:
        m0 = by_id[l.map_ids[0]]
        reg = REGION.get(l.mapsec) or _REGION.get(m0.region) or _REGION.get(levels.reader_region(m0.id))
        l.region = reg
        l.kind = _kind(l, [by_id[x] for x in l.map_ids])
    for i, l in enumerate(locs):
        if l.region is None:             # a place outside the regions: the region of its neighbours in the order
            near = [x.region for x in locs[max(0, i - 3):i] if x.region] or \
                   [x.region for x in locs[i + 1:i + 4] if x.region]
            l.region = max(set(near), key=near.count) if near else "hoenn"
    locs.sort(key=lambda l: (REGIONS.index(l.region), l.pos))
    for i, l in enumerate(locs):
        l.order = i
    return tuple(locs)


@functools.lru_cache(maxsize=None)
def _waves():
    """{map folder: position of its section in the travel order} (a stand-in for the model's waves)."""
    rank = {s: i for i, s in enumerate(ORDER.SECTION_ORDER)}
    out = {}
    for m in maps.all_maps(lang="de").values():
        if m.dir not in ORDER.UNREACHED_MAPS and m.mapsec in rank:
            out[m.dir] = rank[m.mapsec]
    return out


@functools.lru_cache(maxsize=None)
def _reached_dirs():
    return frozenset(m.dir for m in maps.all_maps(lang="de").values() if m.dir not in ORDER.UNREACHED_MAPS)


def _kind(l, ms):
    sec = l.mapsec
    if sec in KIND:
        return KIND[sec]
    if _ROUTE.match(sec):
        return "route"
    if _TOWN.match(sec):
        return "town"
    if sec == "MAPSEC_DYNAMIC":
        return "special"
    types = {m.map_type for m in ms}
    from . import encounters
    wild = set(encounters.map_ids())
    if "MAP_TYPE_UNDERGROUND" in types or any(m.id in wild for m in ms):
        return "dungeon"
    return "special"


def all_locations():
    return list(_build())


@functools.lru_cache(maxsize=None)
def _index():
    by_key, by_map, anchors = {}, {}, {}
    for l in _build():
        by_key[l.key] = l
        for mid in l.map_ids:
            by_map[mid] = l.key
        for sec, frag, _ids in l.parts:
            anchors[sec] = (l.key, frag)
    return by_key, by_map, anchors


def by_key(key):
    return _index()[0].get(key)


def key_of_map(map_id):
    return _index()[1].get(map_id)


def anchor_of_mapsec(mapsec):
    return _index()[2].get(mapsec)


def in_region(region):
    return [l for l in _build() if l.region == region]
