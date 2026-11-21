"""Wild encounters (src/data/wild_encounters.json) as the ROM uses them.

Mirrors:
  * tools/wild_encounters/wild_encounters_to_header.py (WriteEncounters): which
    tables exist in the jade build (LeafGreen labels are not; Emerald, FireRed
    and _hns labels are) and the time of day of a table (its label contains
    Morning/Day/Evening/Night, otherwise OW_TIME_OF_DAY_FALLBACK);
  * GetCurrentMapWildMonHeaderId: the first header of a map counts;
  * GetTimeOfDayForEncounters (src/wild_encounter.c): if the current time has no
    table for that area, the OW_TIME_OF_DAY_FALLBACK table is used (GenConfigTimeOfDay
    of src/rtc.c otherwise);
  * ScaleWildMonLevel (src/level_scaling.c) via levels.wild_level: effective levels.

    encounters.AREAS                 -> ("land", "water", "rock_smash", "old_rod", "good_rod", "super_rod")
    encounters.times()               -> [("TIME_MORNING", "Morning"), ...]  (enum TimeOfDay)
    encounters.map_ids()             -> map ids with a header, in header (JSON) order, active maps only
    encounters.table(map_id, area, time) -> Table(rate, used_time, fallback, slots) or None
         slots: [Slot(index, species, min_level, max_level, eff_min, eff_max, rate)]
    encounters.summary(map_id, area, time) -> [Row(species, pct, eff_min, eff_max, slots)]
         same species merged, pct = summed slot rates, sorted by pct (highest first), then first slot;
         SPECIES_NONE slots and species missing from this build are left out (table() keeps them)
    encounters.time_groups(map_id)   -> [(times tuple, {area: summary})] times that show the same tables
    encounters.where(species_id)     -> [(map_id, area, times tuple, Row)] every place a species appears
    encounters.level_span()          -> {(region, entry): (lowest, highest)} effective levels of all shown
                                        rows on unlocked maps; region = levels.reader_region(), entry = the map
                                        section is one of levels.JOHTO_ENTRY_MAPSECS
"""
import functools
import json
import re

from . import repo_path
from . import tu as TU
from . import species as SP
from . import maps
from . import levels

JSON = "src/data/wild_encounters.json"
AREAS = ("land", "water", "rock_smash", "old_rod", "good_rod", "super_rod")
_FIELD = {"land": "land_mons", "water": "water_mons", "rock_smash": "rock_smash_mons",
          "old_rod": "fishing_mons", "good_rod": "fishing_mons", "super_rod": "fishing_mons"}


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, ", ".join("%s=%r" % kv for kv in self.__dict__.items()
                                                       if kv[0] != "slots"))


class Header(Obj):
    pass


class Table(Obj):
    pass


class Slot(Obj):
    pass


class Row(Obj):
    pass


def _t():
    return TU.load("src/wild_encounter.c")


@functools.lru_cache(maxsize=None)
def _json():
    return json.load(open(repo_path(JSON), encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def times():
    """[(TIME_*, label identifier)] of enum TimeOfDay (header converter's ParseTimeEnum)."""
    t = _t()
    out = []
    for name in t.consts.by_enum.get("TimeOfDay", []):
        if name.startswith("TIME_") and name not in ("TIME_COUNT",) and not name.startswith("TIMES_"):
            out.append((name, name.title().replace("Time_", "").replace("_", "")))
    return out


def fallback_time():
    """OW_TIME_OF_DAY_FALLBACK (include/config/overworld.h)."""
    src = open(repo_path("include", "config", "overworld.h"), encoding="utf-8").read()
    return re.search(r"#define OW_TIME_OF_DAY_FALLBACK\s+(\w+)", src).group(1)


def gen_config_time(time):
    """GenConfigTimeOfDay (src/rtc.c) for OW_TIMES_OF_DAY (include/config/overworld.h)."""
    t = _t()
    order = [n for n, _ in times()]
    gen = t.const("OW_TIMES_OF_DAY")
    i = order.index(time)
    if gen == t.const("GEN_3") and time in ("TIME_MORNING", "TIME_EVENING"):
        return order[i + 1]
    if gen in (t.const("GEN_2"), t.const("GEN_4")) and time == "TIME_EVENING":
        return order[i + 1]
    return time


def _flag(name):
    src = open(repo_path("include", "config", "overworld.h"), encoding="utf-8").read()
    return re.search(r"#define %s\s+(\w+)" % name, src).group(1) == "TRUE"


@functools.lru_cache(maxsize=None)
def _fields():
    grp = _json()["wild_encounter_groups"][0]
    return {f["type"]: f for f in grp["fields"]}


def _version(shared_label):
    if "FireRed" in shared_label:
        return "FIRERED"
    if "LeafGreen" in shared_label:
        return "LEAFGREEN"
    if "_Hns" in shared_label or "_hns" in shared_label:
        return "POKEMON_HNS"
    return "EMERALD"


@functools.lru_cache(maxsize=None)
def headers():
    """[Header(label, map_id, tables={TIME_*: json entry})] of gWildMonHeaders in the jade build."""
    grp = next(g for g in _json()["wild_encounter_groups"] if g.get("for_maps"))
    fb = fallback_time()
    tod = times()
    out, by_label = [], {}
    for e in grp["encounters"]:
        lab = e["base_label"]
        shared, time = lab, fb
        for tname, ident in tod:
            if ident in lab:
                time = tname
                shared = shared.replace("_" + ident, "")
        if _version(shared) == "LEAFGREEN":      # #ifdef LEAFGREEN: not in this build
            continue
        h = by_label.get(shared)
        if h is None:
            h = by_label[shared] = Header(label=shared, map_id=e["map"], tables={})
            out.append(h)
        h.tables[time] = e
    return out


@functools.lru_cache(maxsize=None)
def _first_header():
    first = {}
    for h in headers():
        first.setdefault(h.map_id, h)
    return first


def map_ids():
    """Map ids that have encounters, active maps only, in header order."""
    out = []
    for h in headers():
        m = maps.by_id(h.map_id)
        if m and m.active and h.map_id not in out and _first_header()[h.map_id] is h:
            out.append(h.map_id)
    return out


def _raw(h, field, time):
    e = h.tables.get(time)
    if e and field in e:
        return e[field]
    return None


def table(map_id, area, time):
    """The table the game uses on map_id for area at time (None: no encounters)."""
    h = _first_header().get(map_id)
    if h is None:
        return None
    field = _FIELD[area]
    used, data = time, _raw(h, field, time)
    if data is None and not _flag("OW_TIME_OF_DAY_DISABLE_FALLBACK"):
        used, data = fallback_time(), _raw(h, field, fallback_time())
    elif data is not None:
        used = gen_config_time(time)
        data = _raw(h, field, used)
    if data is None:
        return None
    rates = _fields()[field]["encounter_rates"]
    # The game picks slot indexes from the rate list only; extra JSON entries never appear.
    idx = range(min(len(data["mons"]), len(rates)))
    if field == "fishing_mons":
        idx = _fields()[field]["groups"][area]
    slots = []
    for i in idx:
        mon = data["mons"][i]
        lo, hi = sorted((mon["min_level"], mon["max_level"]))
        sp = SP.by_const(mon["species"])
        slots.append(Slot(index=i, species=sp.id if sp else None, species_const=mon["species"],
                          min_level=lo, max_level=hi,
                          eff_min=levels.wild_level(map_id, lo), eff_max=levels.wild_level(map_id, hi),
                          rate=rates[i]))
    return Table(rate=data["encounter_rate"], used_time=used, fallback=used != time, slots=slots)


def summary(map_id, area, time):
    tb = table(map_id, area, time)
    if tb is None:
        return []
    rows, order = {}, []
    for s in tb.slots:
        if not s.species:      # SPECIES_NONE (empty town tables) or a species not in this build
            continue
        r = rows.get(s.species)
        if r is None:
            r = rows[s.species] = Row(species=s.species, pct=0, eff_min=s.eff_min, eff_max=s.eff_max, slots=[])
            order.append(s.species)
        r.pct += s.rate
        r.eff_min = min(r.eff_min, s.eff_min)
        r.eff_max = max(r.eff_max, s.eff_max)
        r.slots.append(s.index)
    return sorted((rows[k] for k in order), key=lambda r: (-r.pct, order.index(r.species)))


def _key(rows):
    return tuple((r.species, r.pct, r.eff_min, r.eff_max) for r in rows)


def time_groups(map_id):
    """Group the times whose tables are identical in every area: [(times, {area: rows})].
    One group = no day/night split on this map."""
    groups = []
    for tname, _ in times():
        tabs = {a: summary(map_id, a, tname) for a in AREAS}
        key = tuple((a, _key(tabs[a])) for a in AREAS)
        for g in groups:
            if g[0] == key:
                g[1].append(tname)
                break
        else:
            groups.append((key, [tname], tabs))
    return [(tuple(g[1]), g[2]) for g in groups]


@functools.lru_cache(maxsize=None)
def _where():
    out = {}
    for mid in map_ids():
        for tms, tabs in time_groups(mid):
            for area in AREAS:
                for r in tabs[area]:
                    out.setdefault(r.species, []).append((mid, area, tms, r))
    return out


def where(species_id):
    return list(_where().get(species_id, []))


@functools.lru_cache(maxsize=None)
def level_span():
    out = {}
    for mid in map_ids():
        m = maps.by_id(mid)
        if maps.locked_mapsec(m.mapsec):
            continue
        key = (levels.reader_region(m.id), m.mapsec in levels.JOHTO_ENTRY_MAPSECS)
        for area in AREAS:
            for tm, _ in times():
                for r in summary(mid, area, tm) or []:
                    lo, hi = out.get(key, (10 ** 6, 0))
                    out[key] = (min(lo, r.eff_min), max(hi, r.eff_max))
    return out
