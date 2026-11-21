"""Data of the Pokédex pages (pages/pokedex.py): which entries the Pokédex has,
which forms belong to them, where every Pokémon comes from and how it can be
obtained. Everything is derived from the loaders in gamedata; nothing is kept
by hand except the notes in SOURCE_NOTES of pages/pokedex.py.

Mirrors:
  * entries: enum ObtainableDexOrder (the national Pokédex the game shows,
    CreateMonDexNum -> NationalToObtainableOrder); every other species of
    gSpeciesInfo is a form of one entry (formSpeciesIdTable);
  * wild rows: gamedata.encounters.where (effective levels), merged per map
    section; locked areas and maps no warp leads to are left out;
  * scripted sources: gamedata.wild_statics (gifts, eggs, static battles,
    in-game trades, roamers), the Odd Egg (gamedata.hand_breeding.odd_egg) and
    the Feebas fishing spots (sWildFeebas, src/wild_encounter.c);
  * breeding: GetEggSpecies / DetermineEggSpeciesAndParentSlots (src/daycare.c):
    the egg holds the lowest stage of the mother's line (or of the parent that
    is not Ditto); with P_INCENSE_BREEDING >= GEN_9 no incense is needed.
"""
import functools
import os
import re

from gamedata import encounters, hand_breeding, maps, moves, repo_path, species, tu, wild_maps, wild_statics

REGION_ID = {"Kanto": "kanto", "Johto": "johto", "Hoenn": "hoenn"}
REGIONS = ("kanto", "johto", "hoenn")          # play order
TIME_ID = {"TIME_MORNING": "morning", "TIME_DAY": "day", "TIME_EVENING": "evening", "TIME_NIGHT": "night"}
TIME_ORDER = ("morning", "day", "evening", "night")
START_MAP = "MAP_PALLET_TOWN_PLAYERS_HOUSE_2F"
NO_EGGS = "EGG_GROUP_NO_EGGS_DISCOVERED"
DITTO_GROUP = "EGG_GROUP_DITTO"
# generations by national number (last number of each generation)
GEN_LAST = (151, 251, 386, 493, 649, 721, 809, 905, 1025)
_FLOOR = re.compile(r"^(B?\d+F|Rooftop)$")
_SUFFIX = re.compile(r"_(hns|Frlg)$", re.I)
_MAPRE = re.compile(r"\b(MAP_[A-Z0-9_]+)\b")


def generation(natdex):
    for i, last in enumerate(GEN_LAST):
        if natdex <= last:
            return i + 1
    return None


# ------------------------------------------------------------------ entries and forms
def entries(lang):
    """[(number, base Species)] in the order of the game's national Pokédex."""
    return species.dex("obtainable", lang)


def form_caption(base, f, index):
    """Label of a form: the game has no form names, so forms are numbered; the
    letters of Unown are the exception (they are what the form shows)."""
    suffix = f.const.split("_")[-1]
    special = {"EXCLAMATION": "!", "QUESTION": "?"}
    if base.const == "SPECIES_UNOWN":
        if f.id == base.id:
            return "A"
        if len(suffix) == 1 or suffix in special:
            return special.get(suffix, suffix)
    return None


# ------------------------------------------------------------------ reachable maps
# Event islands the Lilycove ferry used to sail to. Their warps are only in script labels of
# data/maps/LilycoveCity_Harbor/scripts.inc that nothing calls: the attendant goes straight
# to the "no event tickets" branch (checked below), and the tickets are not handed out.
# Birth Island is reached by the ships, but only its Johto-era copy (BirthIsland_*_hns).
_EVENT_ISLAND_PREFIXES = ("FarawayIsland_", "NavelRock_", "SouthernIsland_")
_EVENT_ISLAND_DIRS = ("BirthIsland_Exterior", "BirthIsland_Harbor")


@functools.lru_cache(maxsize=None)
def _ferry_has_no_event_islands():
    src = open(repo_path("data", "maps", "LilycoveCity_Harbor", "scripts.inc"), encoding="utf-8").read()
    m = re.search(r"^LilycoveCity_Harbor_EventScript_FerryAttendant::\n((?:[ \t].*\n|\n)*)", src, re.M)
    body = [l.split("@")[0].strip() for l in m.group(1).splitlines()] if m else []
    jumps = [l for l in body if l.startswith(("goto", "call"))]
    return (len(jumps) == 2 and jumps[0].startswith("goto_if_unset FLAG_IS_HOENN_CHAMPION")
            and jumps[1] == "goto LilycoveCity_Harbor_EventScript_NoEventTickets")


def _event_island_copy(m):
    if not (m.dir.startswith(_EVENT_ISLAND_PREFIXES) or m.dir in _EVENT_ISLAND_DIRS):
        return False
    if not _ferry_has_no_event_islands():
        raise ValueError("the Lilycove ferry script changed: check which event islands can be reached")
    return True


@functools.lru_cache(maxsize=None)
def reachable_maps():
    """Ids of the active maps a player can walk or be warped to: everything
    connected to the start map through map connections, warps and the maps
    named in map scripts; maps named in shared scripts count as reachable.
    (Leaves out copies of event islands that no warp leads to.)"""
    am = maps.all_maps(True, "de")
    ids = {i for i, m in am.items() if not _event_island_copy(m)}
    edges = {}
    for m in am.values():
        tg = set()
        for c in m.data.get("connections") or []:
            tg.add(c.get("map"))
        for w in m.data.get("warp_events") or []:
            tg.add(w.get("dest_map"))
        p = repo_path("data", "maps", m.dir, "scripts.inc")
        if os.path.exists(p):
            tg |= set(_MAPRE.findall(open(p, encoding="utf-8").read()))
        edges[m.id] = tg & ids
    seen = set()
    shared = repo_path("data", "scripts")
    names = sorted(os.listdir(shared)) if os.path.isdir(shared) else []
    files = [os.path.join(shared, n) for n in names if n.endswith(".inc") and not n.startswith("debug")]
    files.append(repo_path("data", "event_scripts.s"))
    for p in files:
        if os.path.exists(p):
            seen |= set(_MAPRE.findall(open(p, encoding="utf-8").read())) & ids
    if START_MAP in ids:
        seen.add(START_MAP)
    stack = list(seen)
    while stack:
        x = stack.pop()
        for y in edges.get(x, ()):
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return frozenset(seen)


def map_ok(m):
    return m is not None and m.active and not maps.locked_mapsec(m.mapsec) and m.id in reachable_maps()


def region_of(m):
    return REGION_ID.get(m.region)


# ------------------------------------------------------------------ wild rows
def _floors(m, lang):
    names = []
    for tok in _SUFFIX.sub("", m.dir).split("_")[1:]:
        if _FLOOR.match(tok):
            n = wild_maps.floor_name(tok, lang)
            if n and n not in names:
                names.append(n)
    return names


@functools.lru_cache(maxsize=None)
def _spots(map_id):
    s = wild_maps.field_spots(map_id)
    return bool(s.trees), bool(s.rocks)


def _method(m, area):
    """Method key of a row: the encounter areas, split by what the map is."""
    if area == "land":
        if m.map_type == "MAP_TYPE_UNDERGROUND":
            return "cave"
        if m.map_type == "MAP_TYPE_INDOOR":
            return "indoor"
        return "land"
    if area == "water" and m.map_type == "MAP_TYPE_UNDERWATER":
        return "dive"
    if area == "rock_smash":
        trees, rocks = _spots(m.id)
        if trees and not rocks:
            return "headbutt"
        if trees and rocks:
            return "rock_head"
        return "rock_smash"
    return area


METHOD_ORDER = ("land", "cave", "indoor", "water", "dive", "headbutt", "rock_head", "rock_smash",
                "old_rod", "good_rod", "super_rod")


@functools.lru_cache(maxsize=None)
def wild_rows(sid, lang):
    """Merged wild rows of one species id:
    [dict(mapsec, name, region, method, times (tuple of ids or None), lo, hi, rate, floors, special)]
    One row per map section, method, level span and rate; the times of day of
    equal rows are joined, the floors of equal rows are collected."""
    all_times = len(encounters.times())
    rows, order = {}, []
    for mid, area, tms, row in encounters.where(sid):
        m = maps.by_id(mid, lang)
        if not map_ok(m):
            continue
        method = _method(m, area)
        if area == "rock_smash" and _spots(mid) == (False, False):
            continue                    # neither a headbutt tree nor a rock on this map
        special = "bug_contest" if "BUG_CONTEST" in mid else None
        key = (m.mapsec, m.display, method, row.eff_min, row.eff_max, row.pct, special)
        r = rows.get(key)
        if r is None:
            r = rows[key] = dict(mapsec=m.mapsec, name=m.display, region=region_of(m), method=method,
                                 lo=row.eff_min, hi=row.eff_max, rate=row.pct, special=special,
                                 _maps={}, _order=len(order))
            order.append(key)
        r["_maps"].setdefault(mid, set()).update(TIME_ID[t] for t in tms)
    out = []
    for key in order:
        r = rows[key]
        # split the maps of a row by their times of day
        by_times = {}
        for mid, ts in r["_maps"].items():
            tkey = tuple(t for t in TIME_ORDER if t in ts)
            by_times.setdefault(tkey, []).append(mid)
        for tkey, mids in by_times.items():
            floors = []
            for mid in mids:
                for f in _floors(maps.by_id(mid, lang), lang):
                    if f not in floors:
                        floors.append(f)
            d = dict(r)
            d.pop("_maps")
            d["times"] = None if len(tkey) == all_times else tkey
            d["floors"] = floors
            d["maps"] = tuple(mids)
            out.append(d)
    # floors only help where one place has several rows of the same method
    count = {}
    for d in out:
        count[(d["mapsec"], d["method"])] = count.get((d["mapsec"], d["method"]), 0) + 1
    all_floors = {}
    for d in out:
        all_floors.setdefault((d["mapsec"], d["method"]), set()).update(d["floors"])
    for d in out:
        k = (d["mapsec"], d["method"])
        if count[k] == 1 or len(all_floors[k]) <= 1:
            d["floors"] = []
    rank = {r: i for i, r in enumerate(REGIONS)}
    out.sort(key=lambda d: (rank.get(d["region"], 9), d["_order"]))
    return tuple(out)


@functools.lru_cache(maxsize=None)
def feebas():
    """The special Feebas fishing spots (src/wild_encounter.c: sWildFeebas,
    CheckFeebas): dict(species id, lo, hi, spots, pct, map_id) or None."""
    t = tu.load("src/wild_encounter.c")
    m = re.search(r"sWildFeebas\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\w+)\s*\}", t.text)
    chk = re.search(r"Random\(\)\s*%\s*100\s*>\s*(\d+)", t.text)
    if not m or not chk:
        return None
    sp = species.by_id(t.eval(m.group(3))) if m.group(3)[0].isdigit() else species.by_const(m.group(3))
    mm = maps.by_id("MAP_ROUTE119", "de")
    if sp is None or not map_ok(mm):
        return None
    from gamedata import levels
    return dict(species=sp.id, lo=levels.wild_level("MAP_ROUTE119", int(m.group(1))),
                hi=levels.wild_level("MAP_ROUTE119", int(m.group(2))),
                spots=t.const("NUM_FEEBAS_SPOTS"), pct=int(chk.group(1)) + 1, map_id="MAP_ROUTE119")


# ------------------------------------------------------------------ scripted sources
@functools.lru_cache(maxsize=None)
def _referenced_labels():
    """Script labels that something refers to (map events or another script line)."""
    used = set()
    lab = re.compile(r"\b([A-Za-z]\w*_EventScript_\w+)\b")
    for m in maps.all_maps(True, "de").values():
        for name in ("map.json", "scripts.inc"):
            p = repo_path("data", "maps", m.dir, name)
            if not os.path.exists(p):
                continue
            src = open(p, encoding="utf-8").read()
            if name == "scripts.inc":
                src = re.sub(r"^\w+::?", "", src, flags=re.M)        # the definitions themselves
            used |= set(lab.findall(src))
    return frozenset(used)


@functools.lru_cache(maxsize=None)
def specials(lang):
    """{species id: [wild_statics Entry]}: gifts, eggs, static battles, trades and
    roamers a player can reach. Entries of a script nothing refers to and entries
    on maps without a way in are left out."""
    out = {}
    used = _referenced_labels()
    for e in wild_statics.entries(lang):
        if e.map_id is not None:
            if not map_ok(maps.by_id(e.map_id, lang)):
                continue
            labels = [l for l in e.labels if l]
            if e.kind in ("gift", "egg") and labels and not any(l in used for l in labels):
                continue
        out.setdefault(e.species, []).append(e)
    return out


@functools.lru_cache(maxsize=None)
def odd_egg(lang):
    """(Map of the Day Care that hands out the Odd Egg, {species id}) or (None, {})."""
    try:
        o = hand_breeding.odd_egg(lang)
    except Exception:
        return None, frozenset()
    m = maps.by_dir(o.map_dir, lang)
    if not map_ok(m):
        return None, frozenset()
    return m, frozenset(sp.id for sp, _w in o.rows)


# ------------------------------------------------------------------ breeding
@functools.lru_cache(maxsize=None)
def egg_species():
    """{species id: species id that hatches from its eggs} (GetEggSpecies: the
    first stage of the line), for every species that can lay eggs."""
    alls = species.all_species("de")
    prev = {}
    for sp in sorted(alls.values(), key=lambda s: s.id):
        for e in sp.evolutions:
            if e.target in alls and e.method != "EVO_SPLIT_FROM_EVO":
                prev.setdefault(e.target, sp.id)
    out = {}
    for sp in alls.values():
        if NO_EGGS in sp.egg_groups or DITTO_GROUP in sp.egg_groups:
            continue
        cur, seen = sp.id, set()
        while cur in prev and cur not in seen:
            seen.add(cur)
            cur = prev[cur]
        out[sp.id] = cur
    return out


# DetermineEggSpeciesAndParentSlots: an egg of the first species can also hold the second
# one and the other way round (P_NIDORAN_M_DITTO_BREED >= GEN_5).
EGG_PAIRS = (("SPECIES_NIDORAN_F", "SPECIES_NIDORAN_M"), ("SPECIES_ILLUMISE", "SPECIES_VOLBEAT"))


@functools.lru_cache(maxsize=None)
def egg_results():
    """{species id: (species ids that can hatch from its eggs)}."""
    pair = {}
    for a, b in EGG_PAIRS:
        sa, sb = species.by_const(a, "de"), species.by_const(b, "de")
        if sa and sb:
            pair[sa.id] = (sa.id, sb.id)
            pair[sb.id] = (sb.id, sa.id)
    return {sid: pair.get(baby, (baby,)) for sid, baby in egg_species().items()}


def needs_ditto(sp):
    """True when the species can only lay its own eggs together with Ditto
    (no females: the mother decides the species of the egg)."""
    kind, _pct = species.gender(sp.gender_ratio)
    return kind in ("genderless", "male_only")


# ------------------------------------------------------------------ availability
class Avail:
    """How one species id can be obtained.
    wild/special: it has rows of its own; evolves_from: [species id] it can be
    evolved from; parents: [species id] whose eggs hatch into it; regions: the
    regions with a source (direct or through an obtainable relative)."""
    def __init__(self):
        self.wild = False
        self.special = False
        self.evolves_from = []
        self.parents = []
        self.regions = set()
        self.direct_regions = set()
        self.other_place = False        # a source outside the three regions

    @property
    def obtainable(self):
        return bool(self.wild or self.special or self.evolves_from or self.parents)

    @property
    def kind(self):
        if self.wild:
            return "wild"
        if self.special:
            return "special"
        if self.evolves_from or self.parents:
            return "evo"
        return "none"


@functools.lru_cache(maxsize=None)
def availability():
    """{species id: Avail} for every species of the build (language neutral)."""
    alls = species.all_species("de")
    av = {sid: Avail() for sid in alls}
    spec = specials("de")
    fb = feebas()
    _om, odd = odd_egg("de")
    for sid in alls:
        a = av[sid]
        for r in wild_rows(sid, "de"):
            a.wild = True
            if r["region"]:
                a.direct_regions.add(r["region"])
            else:
                a.other_place = True
        if fb and fb["species"] == sid:
            a.wild = True
            a.direct_regions.add("hoenn")
        for e in spec.get(sid, ()):
            a.special = True
            if e.kind == "roamer":
                if e.roamer.get("table") in REGIONS:
                    a.direct_regions.add(e.roamer["table"])
                continue
            m = maps.by_id(e.map_id, "de") if e.map_id else None
            if m is None and getattr(e, "callers", None):
                m = maps.by_id(e.callers[0], "de")
            if m is not None and region_of(m):
                a.direct_regions.add(region_of(m))
            else:
                a.other_place = True
        if sid in odd:
            a.special = True
            a.direct_regions.add(region_of(_om))
        a.regions |= a.direct_regions
    eggs = egg_results()
    ditto = species.by_const("SPECIES_DITTO", "de")
    changed = True
    while changed:
        changed = False
        have_ditto = ditto is not None and av[ditto.id].obtainable
        for sid, sp in alls.items():
            a = av[sid]
            if not a.obtainable:
                continue
            for e in sp.evolutions:
                tg = av.get(e.target)
                if tg is None:
                    continue
                if sid not in tg.evolves_from:
                    tg.evolves_from.append(sid)
                    changed = True
                if not a.regions <= tg.regions:
                    tg.regions |= a.regions
                    changed = True
            if not (have_ditto or not needs_ditto(sp)):
                continue
            for baby in eggs.get(sid, ()):
                if baby == sid:
                    continue
                b = av[baby]
                if sid not in b.parents:
                    b.parents.append(sid)
                    changed = True
                if not a.regions <= b.regions:
                    b.regions |= a.regions
                    changed = True
    return av


# ------------------------------------------------------------------ learnsets
@functools.lru_cache(maxsize=None)
def machines():
    """{move id: (0 TM | 1 HM, number, kind)}"""
    out = {}
    for kind, num, mid in moves.tm_hm_moves():
        out.setdefault(mid, (0 if kind == "TM" else 1, num, kind))
    return out
