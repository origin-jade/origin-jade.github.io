"""Data of the location pages (pages/world.py): what is where.

Language neutral: ids, constants and numbers; the page looks names up in its language.
Everything is indexed once by map and then grouped by location (gamedata.locations).

Mirrors, through the data layer:
  * wild tables, time of day, slot rates: gamedata.encounters (levels: ScaleWildMonLevel);
  * Headbutt vs. Rock Smash on the rock_smash table: gamedata.wild_maps.field_spots;
  * Feebas (src/wild_encounter.c sWildFeebas, CheckFeebas);
  * battles: the map scripts with resolved conditionals (gamedata.trainers,
    trainers_scriptdb) - which battle is a fixed-level battle, a Kanto leader rematch
    (IsKantoLeaderRematchBattle) or a phone rematch (gRematchTable);
  * teams: trainers.effective_team (ScaleTrainerMonLevel / ScaleTrainerMonSpecies);
    ability slot as CreateNPCTrainerPartyWithId + GetAbilityBySpecies; empty move
    lists as GiveBoxMonInitialMoveset;
  * prize money: GetTrainerMoneyToGive (src/battle_script_commands.c): 4 x level of the
    last Pokémon fielded x class factor (x 2 in a double battle);
  * items, shops, berry trees: gamedata.trainers_items;
  * gifts, static encounters, trades, roamers: gamedata.wild_statics.
"""
import functools
import re

from gamedata import encounters as E
from gamedata import levels
from gamedata import locations as LOC
from gamedata import locations_services as LS
from gamedata import maps
from gamedata import species as SP
from gamedata import trainers as T
from gamedata import trainers_items as TI
from gamedata import trainers_rematch as RM
from gamedata import trainers_scriptdb as SDB
from gamedata import tu
from gamedata import wild_maps as WM
from gamedata import wild_statics as WS

TIME_ID = {"TIME_MORNING": "morning", "TIME_DAY": "day", "TIME_EVENING": "evening", "TIME_NIGHT": "night"}
# Classes whose battle name is the rival name the player chose (BattleStringGetOpponentName,
# src/battle_message.c), plus every trainer named {B_RIVAL_NAME}.
RIVAL_NAME_CLASSES = ("TRAINER_CLASS_RIVAL_EARLY_FRLG", "TRAINER_CLASS_RIVAL_LATE_FRLG", "TRAINER_CLASS_CHAMPION_FRLG")
STARTERS = ("BULBASAUR", "CHARMANDER", "SQUIRTLE", "CHIKORITA", "CYNDAQUIL", "TOTODILE", "TREECKO", "TORCHIC",
            "MUDKIP")
_STARTER = re.compile(r"_(%s)(?:_\d+)?(?:_HNS)?$|_(%s)_\d+_HNS$" % ("|".join(STARTERS), "|".join(STARTERS)))
LEAGUE_CHANGE_SCRIPT = "PokemonLeague_EventScript_CheckLeagueChanged"
LEAGUE_CHANGE_STEP = 18   # 8 Johto badges (data/scripts/pokemon_league.inc)
ROLE_CLASSES = {
    "leader": ("TRAINER_CLASS_LEADER", "TRAINER_CLASS_LEADER_FRLG", "TRAINER_CLASS_LEADER_HNS",
               "TRAINER_CLASS_LEADER_KANTO_HNS"),
    "e4": ("TRAINER_CLASS_ELITE_FOUR", "TRAINER_CLASS_ELITE_FOUR_FRLG", "TRAINER_CLASS_ELITE_FOUR_HNS"),
    "champion": ("TRAINER_CLASS_CHAMPION", "TRAINER_CLASS_CHAMPION_FRLG", "TRAINER_CLASS_CHAMPION_HNS"),
    "rival": ("TRAINER_CLASS_RIVAL", "TRAINER_CLASS_RIVAL_EARLY_FRLG", "TRAINER_CLASS_RIVAL_LATE_FRLG",
              "TRAINER_CLASS_RIVAL_HNS"),
    "boss": ("TRAINER_CLASS_BOSS_FRLG", "TRAINER_CLASS_AQUA_LEADER", "TRAINER_CLASS_MAGMA_LEADER"),
}
_ROLE = {c: r for r, cs in ROLE_CLASSES.items() for c in cs}


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, ", ".join("%s=%r" % kv for kv in sorted(self.__dict__.items())))


class Battle(Obj):
    """const, map_id, mode ("normal" | "leader" | "phone" | "special"), steps (progress steps of
    the dynamic modes), states, row (rematch row), stage (stage numbers), command, opponents,
    partner, league_change, order."""


def role_of(tr):
    return _ROLE.get(tr.class_const)


def starter_of(const):
    m = _STARTER.search(const)
    return (m.group(1) or m.group(2)) if m else None


def person_key(const):
    """One key for the battles that differ only by the starter chosen (rival teams)."""
    st = starter_of(const)
    return const.replace("_" + st, "_*", 1) if st else const


def rival_named(tr):
    return tr.class_const in RIVAL_NAME_CLASSES or "{B_RIVAL_NAME}" in (tr.name or "")


# ------------------------------------------------------------------ battles
@functools.lru_cache(maxsize=None)
def _league_change_maps():
    d = SDB.db()
    out = set()
    for ins in d.instrs:
        if ins.cmd == "call" and LEAGUE_CHANGE_SCRIPT in ins.args:
            mid = SDB.map_of_file(ins.file)
            if mid:
                out.add(mid)
    return out


@functools.lru_cache(maxsize=None)
def battles():
    """[Battle] of every battle on a map with a location page."""
    allt = T.all_trainers("de")
    order = {c: i for i, c in enumerate(allt)}
    rows = T.rematch_rows()
    in_row = {}
    for r in rows:
        for c in r.trainer_consts:
            in_row.setdefault(c, r)
    out, seen = [], set()
    lc_maps = _league_change_maps()
    for const, tr in allt.items():
        for b in T.battles(const):
            if not b.map_id or LOC.key_of_map(b.map_id) is None or b.rematch_row:
                continue
            if b.label and LS.closed_label(b.label):
                continue   # only reachable with a story state of a locked area
            row = in_row.get(const)
            if row and b.command in T.REMATCH_COMMANDS and row.trainer_consts[0] == const:
                continue   # the rematch call: handled through the row below
            key = (const, b.map_id, b.label)
            if key in seen:
                continue
            seen.add(key)
            states = SDB.states_for(const, b.file, b.label)
            mode, steps = "normal", None
            if T.is_kanto_leader_class(tr) and any(st[3] for st in states):
                mode = "leader"
                lo = LEAGUE_CHANGE_STEP if b.map_id in lc_maps else 0
                steps = SDB.title_steps([st for st in states if st[3]], lo=lo)
            elif T.is_league_rematch(const):
                mode = "leader"            # league rematch teams and Red: possible from the Johto title on
                steps = list(range(levels.TITLE_STEPS[1], levels.TITLE_STEPS[2] + 1))
            out.append(Battle(const=const, map_id=b.map_id, mode=mode, steps=steps, states=states, row=None,
                              daily=bool(b.label and LS.daily_label(b.label)),
                              stage=None, order=(order[const], 0), league_change=mode == "leader" and
                              b.map_id in lc_maps, command=b.command, opponents=b.opponents, partner=b.partner))
    for r in rows:
        first = r.trainer_consts[0]
        calls = [b for b in T.battles(first) if b.command in T.REMATCH_COMMANDS
                 and b.map_id and LOC.key_of_map(b.map_id) is not None]
        if not calls:
            continue
        sites = []
        for b in calls:
            if b.map_id not in [s.map_id for s in sites]:
                sites.append(b)
        stages = RM.row_stages(r)
        done = []
        for st in stages:
            if st.const in done or st.const not in allt:
                continue
            same = [x for x in stages if x.const == st.const]
            done.append(st.const)
            steps = sorted({s for x in same for s in x.steps})
            for b in sites:
                out.append(Battle(const=st.const, map_id=b.map_id, mode="special" if r.special else "phone",
                                  steps=steps, states=set(), row=r, stage=[x.index for x in same], daily=False,
                                  order=(order.get(first, 0), st.index), league_change=False,
                                  command=b.command, opponents=(st.const,), partner=None))
    return tuple(out)


def _battle_rank(b, allt):
    """Order of the battles on one map: trainers, then the leader, then rematches."""
    if b.mode in ("leader", "special"):
        return 2
    tr = allt.get(b.const)
    return 1 if tr is not None and role_of(tr) == "leader" else 0


@functools.lru_cache(maxsize=None)
def battles_by_location():
    """{location key: [Battle]} on the maps whose content the page shows; one battle per
    trainer constant and mode, in map order of the location, then trainer order."""
    by_map = {}
    for b in battles():
        by_map.setdefault(b.map_id, []).append(b)
    allt = T.all_trainers("de")
    out = {}
    for loc in LOC.all_locations():
        lst, seen = [], set()
        for mi, mid in enumerate(loc.content_ids):
            for b in sorted(by_map.get(mid, ()), key=lambda b: (_battle_rank(b, allt), b.order)):
                k = (b.const, b.mode)
                if k in seen:
                    continue
                seen.add(k)
                lst.append(b)
        if lst:
            out[loc.key] = lst
    return out


@functools.lru_cache(maxsize=None)
def trainer_home():
    """{trainer const: (location key, anchor const)}: where the anchor of a trainer lives.
    The first location in travel order with a fixed-level battle; trainers that only appear
    as a rematch stage point to the card of the first trainer of their rematch row."""
    out = {}
    bl = battles_by_location()
    for loc in LOC.all_locations():
        lst = bl.get(loc.key, ())
        for b in lst:
            if b.mode in ("normal", "leader", "special") and b.const not in out:
                out[b.const] = (loc.key, b.const)
        for b in lst:
            if b.mode == "phone" and b.const not in out:
                first = b.row.trainer_consts[0]
                if any(x.const == first and x.mode == "normal" for x in lst):
                    out[b.const] = (loc.key, first)
    return out


def frag(const):
    return "trainer-" + const[len("TRAINER_"):].lower().replace("_", "-")


def default_moves(sp, level):
    """GiveBoxMonInitialMoveset: level-up moves up to the level (level 0 = evolution moves
    skipped), no duplicates, the last four."""
    out = []
    for lv, mv in sp.levelup:
        if lv > level:
            break
        if lv == 0 or mv in out:
            continue
        if len(out) < 4:
            out.append(mv)
        else:
            out = out[1:] + [mv]
    return out


def ability_of(mon, eff_species_id):
    """CreateNPCTrainerPartyWithId (abilityNum) + GetAbilityBySpecies on the fielded species."""
    data_sp = SP.by_id(mon.species)
    num = 0
    if mon.ability and data_sp is not None and mon.ability in data_sp.abilities:
        num = data_sp.abilities.index(mon.ability)
    eff = SP.by_id(eff_species_id)
    ab = eff.abilities[num] if num < len(eff.abilities) else 0
    if not ab and num >= 2:
        ab = next((a for a in eff.abilities[2:] if a), 0)
    if not ab:
        ab = next((a for a in eff.abilities if a), 0)
    return ab


def has_detail(tr):
    """True when the data sets moves, items, abilities or natures for the team."""
    return any(any(m.moves) or m.item or m.ability or m.nature for m in tr.mons)


def reward(tr, last_level, two_opponents=False):
    """GetTrainerMoneyToGive: 4 x last level x class factor (default 5), doubled in a double battle."""
    money = tr.money or 5
    r = 4 * last_level * money
    if tr.double and not two_opponents:
        r *= 2
    return r


# ------------------------------------------------------------------ wild Pokémon
@functools.lru_cache(maxsize=None)
def time_groups(mid):
    return tuple(E.time_groups(mid))


def _signature(mid):
    sig = []
    for tms, tabs in time_groups(mid):
        sig.append((tms, tuple((a, tuple((r.species, r.pct, r.eff_min, r.eff_max) for r in tabs[a]))
                               for a in E.AREAS)))
    return tuple(sig)


@functools.lru_cache(maxsize=None)
def _wild_maps():
    out = set()
    for mid in E.map_ids():
        if any(tabs[a] for _, tabs in time_groups(mid) for a in E.AREAS):
            out.add(mid)
    return frozenset(out)


@functools.lru_cache(maxsize=None)
def wild_clusters(loc_key):
    """[[map ids with identical tables]] of a location, in map order."""
    loc = LOC.by_key(loc_key)
    variants, sigs = [], []
    wild = _wild_maps()
    for mid in loc.map_ids:
        if mid not in wild:
            continue
        s = _signature(mid)
        if s in sigs:
            variants[sigs.index(s)].append(mid)
        else:
            sigs.append(s)
            variants.append([mid])
    return variants


@functools.lru_cache(maxsize=None)
def existing_times():
    """Times of day this build really has (begin != end in the clock table)."""
    hrs = WM.time_hours()
    return tuple(t for t in TIME_ID if t in hrs)


def rock_spots(group):
    """(Headbutt trees, breakable rocks) on the maps of a cluster. The rock_smash table is
    only used at such a spot; a map without any cannot give these encounters."""
    return (sum(WM.field_spots(mid).trees for mid in group), sum(WM.field_spots(mid).rocks for mid in group))


def cluster_blocks(group):
    """[(area, times or None, rows)] of one cluster: one block per method; a method whose
    table changes with the time of day gets one block per time group. The rock_smash table
    is left out when the maps have neither a Headbutt tree nor a breakable rock."""
    groups = time_groups(group[0])
    have = existing_times()
    out = []
    for area in ("land", "water", "rock_smash", "old_rod", "good_rod", "super_rod"):
        if area == "rock_smash" and rock_spots(tuple(group)) == (0, 0):
            continue
        per = [(times, d.get(area)) for times, d in groups if d.get(area)]
        if not per:
            continue
        keys = {tuple((r.species, r.pct, r.eff_min, r.eff_max) for r in rows) for _t, rows in per}
        same = len(keys) == 1 and len(per) == len(groups)
        for times, rows in (per[:1] if same else per):
            shown = [TIME_ID[t] for t in times if t in have] or [TIME_ID[t] for t in times]
            out.append((area, None if same else shown, rows))
    return out


@functools.lru_cache(maxsize=None)
def feebas():
    """dict(species, lo, hi, spots, pct, map_id) of src/wild_encounter.c, or None."""
    t = tu.load("src/wild_encounter.c")
    m = re.search(r"sWildFeebas\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\w+)\s*\}", t.text)
    chk = re.search(r"Random\(\)\s*%\s*100\s*>\s*(\d+)", t.text)
    if not m or not chk:
        return None
    sp = SP.by_id(t.eval(m.group(3))) if m.group(3)[0].isdigit() else SP.by_const(m.group(3))
    if sp is None:
        return None
    mid = "MAP_ROUTE119"
    return dict(species=sp.id, lo=levels.wild_level(mid, int(m.group(1))), hi=levels.wild_level(mid, int(m.group(2))),
                spots=t.const("NUM_FEEBAS_SPOTS"), pct=100 - (int(chk.group(1)) + 1), map_id=mid)


def altering_extra(mid):
    """Further tables of the same map that only a special event switches to."""
    if mid != "MAP_ALTERING_CAVE":
        return 0
    return sum(1 for h in E.headers() if h.map_id == mid) - 1


@functools.lru_cache(maxsize=None)
def wild_species(loc_key):
    """Distinct species ids in the wild tables of a location."""
    out = []
    for group in wild_clusters(loc_key):
        for _area, _times, rows in cluster_blocks(tuple(group)):
            for r in rows:
                if r.species not in out:
                    out.append(r.species)
    return tuple(out)


@functools.lru_cache(maxsize=None)
def overworld(loc_key):
    """[(species id, when)] visible map Pokémon of a location; when: "always" | "day" | "night" | "flag"."""
    loc = LOC.by_key(loc_key)
    order, whens = [], {}
    for mid in loc.content_ids:
        for ow in WM.overworld_mons(mid):
            sp = SP.by_const(ow.species_const)
            if sp is None:
                continue
            if sp.id not in whens:
                order.append(sp.id)
                whens[sp.id] = set()
            whens[sp.id].add(ow.when)
    out = []
    for sid in order:
        w = whens[sid]
        if "always" in w or ("day" in w and "night" in w):
            when = "always"
        elif "day" in w:
            when = "day"
        elif "night" in w:
            when = "night"
        else:
            when = "flag"
        out.append((sid, when))
    return tuple(out)


@functools.lru_cache(maxsize=None)
def region_wild_levels(region):
    """(lowest, highest) effective level in the wild tables of a region's places, or None."""
    lo = hi = None
    for loc in LOC.in_region(region):
        for group in wild_clusters(loc.key):
            for _area, _times, rows in cluster_blocks(tuple(group)):
                for r in rows:
                    lo = r.eff_min if lo is None else min(lo, r.eff_min)
                    hi = r.eff_max if hi is None else max(hi, r.eff_max)
    return (lo, hi) if lo is not None else None


# ------------------------------------------------------------------ items
@functools.lru_cache(maxsize=None)
def _items_by_map():
    out = {}
    for iid, lst in sorted(TI.sources().items()):
        for s in lst:
            if s.map_id:
                out.setdefault(s.map_id, []).append(s)
    return out


@functools.lru_cache(maxsize=None)
def items_of(loc_key):
    """Obj(found, gifts, bought, berries, shops): sources of a location.
    found: [(map id, Source, count)] item balls and hidden items;
    gifts: [(map id, Source, 1)] one entry per item a script of the map hands out (a script
           often has the same gift in several branches - that is still one gift);
    bought: [(map id, Source, (currency, amount))] gifts a script sells for coins or money;
    berries: [(item id, count)]; shops: [(map id, [Source])]."""
    loc = LOC.by_key(loc_key)
    bm = _items_by_map()
    found, gifts, shops, bought = [], [], [], []
    berries, border = {}, []
    prices = LS.script_prices()
    for mid in loc.content_ids:
        srcs = bm.get(mid, ())
        agg, order = {}, []
        for s in srcs:
            if s.kind in ("ball", "hidden"):
                k = (s.kind, s.item, s.amount or 1, s.detail)
            elif s.kind == "gift":
                k = ("gift", s.item, None, None)
            else:
                continue
            if k not in agg:
                agg[k] = [s, 0]
                order.append(k)
            agg[k][1] += 1
        sold = set()
        for k in order:
            s, n = agg[k]
            if s.kind != "gift":
                found.append((mid, s, n))
            elif (mid, s.item) in prices:
                sold.add(s.item)
                bought.append((mid, s, prices[(mid, s.item)]))
            else:
                gifts.append((mid, s, 1))
        for (pm, iid), price in prices.items():     # sales whose item the script keeps in a variable
            if pm == mid and iid not in sold:
                bought.append((mid, TI.Source(kind="gift", item=iid, map_id=mid, amount=1, price=None,
                                              detail="script"), price))
        for s in srcs:
            if s.kind == "berry":
                if s.item not in berries:
                    berries[s.item] = 0
                    border.append(s.item)
                berries[s.item] += 1
        shop = [s for s in srcs if s.kind == "shop"]
        if shop:
            uniq, seen = [], set()
            for s in shop:
                if s.item not in seen:
                    seen.add(s.item)
                    uniq.append(s)
            shops.append((mid, uniq))
    return Obj(found=found, gifts=gifts, bought=bought, berries=[(i, berries[i]) for i in border], shops=shops)


@functools.lru_cache(maxsize=None)
def tutors_of(loc_key):
    """[(map id, Tutor)] move tutors on the maps of a location (gamedata.locations_services)."""
    loc = LOC.by_key(loc_key)
    out = []
    for t in LS.tutors():
        for mid in loc.content_ids:
            if mid in t.map_ids:
                out.append((mid, t))
                break
    pos = {mid: i for i, mid in enumerate(loc.content_ids)}
    out.sort(key=lambda x: pos[x[0]])
    return tuple(out)


# ------------------------------------------------------------------ special Pokémon
@functools.lru_cache(maxsize=None)
def statics_by_location(lang):
    """{location key: [(Entry, map id or None)]}: gifts, eggs, static encounters and trades on
    the maps of a location, plus the roamers of the routes they visit."""
    out = {}
    content = {}
    for loc in LOC.all_locations():
        for mid in loc.content_ids:
            content[mid] = loc.key
    for e in WS.entries(lang):
        if e.kind == "roamer":
            keys = []
            for mid in e.roamer["maps"]:
                k = content.get(mid)
                if k and k not in keys:
                    keys.append(k)
            for k in keys:
                out.setdefault(k, []).append((e, None))
            continue
        mids = [e.map_id] if e.map_id else list(getattr(e, "callers", ()))
        done = set()
        for mid in mids:
            k = content.get(mid)
            if k and (k, e.species, e.kind) not in done:
                done.add((k, e.species, e.kind))
                out.setdefault(k, []).append((e, mid))
    return out


def static_group(e):
    if e.kind == "roamer":
        return "roamer"
    if e.kind in ("static", "static_shiny"):
        return "legendary" if e.legendary else "static"
    return e.kind


def script_money(path):
    """Price a script takes for a gift (.equ ...PRICE... with removemoney), or None."""
    from gamedata import repo_path
    src = open(repo_path(path), encoding="utf-8").read()
    m = re.search(r"^\s*\.equ\s+\w*PRICE\w*\s*,\s*(\d+)", src, re.M)
    return int(m.group(1)) if m and "removemoney" in src else None


# ------------------------------------------------------------------ neighbours
_DIRS = {"up": "north", "down": "south", "left": "west", "right": "east"}


@functools.lru_cache(maxsize=None)
def neighbours(loc_key):
    """([(direction, location key)], [location key]): map connections of the outdoor maps and
    the other locations the warps of this location lead to."""
    loc = LOC.by_key(loc_key)
    conn, warps = [], []
    for mid in loc.map_ids:
        m = maps.by_id(mid)
        for c in m.data.get("connections") or []:
            d = _DIRS.get(c.get("direction"))
            k = LOC.key_of_map(c.get("map"))
            if d and k and k != loc_key and (d, k) not in conn:
                conn.append((d, k))
    linked = {k for _d, k in conn}
    for mid in loc.content_ids:
        m = maps.by_id(mid)
        for w in m.data.get("warp_events") or []:
            k = LOC.key_of_map(w.get("dest_map"))
            if k and k != loc_key and k not in linked and k not in warps:
                warps.append(k)
    return tuple(conn), tuple(warps)


# ------------------------------------------------------------------ facilities
FACILITY_TOKENS = (("center", ("PokemonCenter",)), ("mart", ("Mart", "DepartmentStore")), ("gym", ("Gym",)),
                   ("daycare", ("DayCare", "PokemonDayCare")), ("gamecorner", ("GameCorner",)))


@functools.lru_cache(maxsize=None)
def facilities(loc_key):
    """Keys of the facilities a location has: "center", "mart", "gym", "daycare", "gamecorner",
    "relearner", "deleter" (map folder names; move relearner/deleter from their scripts)."""
    from gamedata import dex_relearner
    loc = LOC.by_key(loc_key)
    toks = set()
    for mid in loc.content_ids:
        toks.update(LOC.base_dir(maps.by_id(mid).dir).split("_")[1:])
    out = [k for k, names in FACILITY_TOKENS if toks & set(names)]
    for kind in ("relearner", "deleter"):
        if any(LOC.key_of_map(mid) == loc_key for mid in dex_relearner.place_maps(kind)):
            out.append(kind)
    if tutors_of(loc_key):
        out.append("tutor")
    return tuple(out)


# ------------------------------------------------------------------ counts
@functools.lru_cache(maxsize=None)
def counts(loc_key):
    """Obj(wild, trainers, items) for the hub tiles."""
    it = items_of(loc_key)
    bl = battles_by_location().get(loc_key, ())
    people = {person_key(b.const) for b in bl if b.mode in ("normal", "leader")}
    return Obj(wild=len(wild_species(loc_key)), trainers=len(people),
               items=sum(n for _m, _s, n in it.found) + len(it.gifts))
