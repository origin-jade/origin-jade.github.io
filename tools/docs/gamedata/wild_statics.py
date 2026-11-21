"""Gifts, eggs, static encounters, trades and roamers, read from the scripts.

    wild_statics.entries() -> [Entry] in a stable order (map group/number, then line)
    wild_statics.entries("en") -> the same entries with the trade nickname and OT name of the
                                  English build (sIngameTrades has `#if GERMAN` branches);
                                  everything else is the same in both builds

Entry fields:
    kind      "gift" | "egg" | "static" | "static_shiny" | "trade" | "roamer"
    species   species id
    levels    sorted list of script levels (trades: [] - the level of the Pokémon given)
    map_id    map of the script (roamers: None)
    sources   [(file, line)] of every script line merged into this entry
    shiny     "roll" (normal shiny roll), "never", "always", "preview" (starter: shiny
              exactly when the selection preview was: SHINY_MODE_ALWAYS/NEVER branches),
              "fixed" (trade: the OT id and personality are fixed, see trade_shiny_value)
    items     held item ids (static battles / givemon with an item)
    price     coin price (game corner prize rooms: setvar VAR_TEMP_2 after the species)
    trade     dict(nickname, ot_name, requested, held_item, ot_id, personality) for trades
    roamer    dict(level, release_flag, table, maps) for roamers
    labels    script labels the lines belong to (for notes)

Commands and the C code they run (effective level = ScaleStaticMonLevel, which keeps the
script level under LEVEL_REMAP, src/level_scaling.c; gamedata.levels.static_level):
    givemon      ScrCmd_createmon -> ScriptGiveMonParameterized (shinyMode argument,
                 default SHINY_MODE_RANDOM = normal roll); level as written (no scaling)
    giveegg      ScriptGiveEgg -> CreateEgg (normal roll when the egg is made)
    setwildbattle ScrCmd_setwildbattle -> ScaleStaticMonLevel -> CreateScriptedWildMon
                 (player OT id: normal roll)
    setwildbattleshiny CreateShinyScriptedMon (personality forced shiny: always)
    seteventmon  CreateEnemyEventMon -> ScaleStaticMonLevel -> CreateEventMon (normal roll)
    ingame_trade / special CreateInGameTradePokemon: sIngameTrades (src/data/trade.h),
                 level = level of the Pokémon handed over, OT id + personality fixed
    roamers      src/roamer.c InitRoamer (IS_HNS) and src/legendaries_oj.c sLegendaries
                 (roamerLevel, releaseFlag; TryRaiseRoamerLevel keeps at least that level)
Variable species (givemon VAR_TEMP_1 ...) are resolved to every `setvar VAR, SPECIES_*`
of the same script file (.equ aliases followed). Maps of locked areas (Alola, Sinjoh) and
retired maps are left out; data/scripts/debug.inc is never part of the game.
"""
import functools
import os
import re

from . import repo_path
from . import tu as TU
from . import namestyle
from . import maps
from . import species as SP
from . import items as IT

CMD = re.compile(r"^\s*(givemon|giveegg|setwildbattle|setwildbattleshiny|seteventmon)\s+([^\n@]*)", re.M)
TRADE = re.compile(r"\b(INGAME_TRADE_\w+)")
LABEL = re.compile(r"^(\w+)::?", re.M)
GIVEMON_ARGS = ("species", "level", "item", "ball", "nature", "abilityNum", "gender", "hpEv", "atkEv", "defEv",
                "speedEv", "spAtkEv", "spDefEv", "hpIv", "atkIv", "defIv", "speedIv", "spAtkIv", "spDefIv",
                "move1", "move2", "move3", "move4", "shinyMode")
SHARED_SCRIPTS = ("data/scripts/kecleon.inc", "data/scripts/gift_pichu.inc")


class Entry:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Entry(%s %s %s %s)" % (self.kind, self.species, self.levels, self.map_id)


def _split_args(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _named(args, names):
    """Positional + name=value macro arguments -> dict."""
    d = {}
    for i, a in enumerate(args):
        if "=" in a and re.match(r"^\w+\s*=", a):
            k, v = a.split("=", 1)
            d[k.strip()] = v.strip()
        elif i < len(names):
            d[names[i]] = a
    return d


@functools.lru_cache(maxsize=None)
def _consts():
    return TU.load("src/scrcmd.c", lang="de")


def _num(v):
    t = _consts()
    try:
        return int(t.eval(v))
    except Exception:
        return None


def _species(v):
    sp = SP.by_const(v.strip())
    return sp.id if sp else None


def _labels_at(src, pos):
    m = None
    for m2 in LABEL.finditer(src, 0, pos):
        m = m2
    return m.group(1) if m else None


def _resolve_var(src, var):
    """Species a script file writes into var (setvar var, SPECIES_X), with the coin price
    set right after it (setvar VAR_TEMP_2, N) when there is one."""
    aliases = dict(re.findall(r"^\s*\.equ\s+(\w+)\s*,\s*(\w+)", src, re.M))
    names = {var}
    real = aliases.get(var, var)
    names.add(real)
    names |= {k for k, v in aliases.items() if v == real}
    out = []
    lines = src.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^\s*setvar\s+(\w+)\s*,\s*(SPECIES_\w+)", line)
        if m and m.group(1) in names:
            price = None
            for nxt in lines[i + 1:i + 3]:
                p = re.match(r"^\s*setvar\s+VAR_TEMP_2\s*,\s*(\d+)", nxt)
                if p:
                    price = int(p.group(1))
            sid = _species(m.group(2))
            if sid and sid not in [x[0] for x in out]:
                out.append((sid, price))
    return out


def _script_files():
    """[(map or None, path)] of the active, unlocked maps plus shared gift scripts."""
    out = []
    for m in sorted(maps.all_maps().values(), key=lambda m: (m.group_index, m.map_num)):
        if maps.locked_mapsec(m.mapsec):
            continue
        p = os.path.join("data", "maps", m.dir, "scripts.inc")
        if os.path.exists(repo_path(p)):
            out.append((m, p))
    for p in SHARED_SCRIPTS:
        if os.path.exists(repo_path(p)):
            out.append((None, p))
    return out


def _legendary_flags(sp):
    return any(SP.field(sp, k) for k in ("isLegendary", "isMythical", "isSubLegendary", "isRestrictedLegendary"))


@functools.lru_cache(maxsize=None)
def _trade_table(lang="de"):
    t = TU.load("src/trade.c", lang=lang)
    return t, t.table("sIngameTrades")


def trade_shiny_value(ot_id, personality):
    """GET_SHINY_VALUE (include/pokemon.h): shiny when it is below the shiny odds."""
    return ((ot_id >> 16) ^ (ot_id & 0xFFFF) ^ (personality >> 16) ^ (personality & 0xFFFF))


def _string(init):
    s = str(init)
    m = re.search(r'"((?:[^"\\]|\\.)*)"', s)
    return re.sub(r"\\(['\"])", r"\1", m.group(1)) if m else s


def entries(lang=None):
    return list(_entries(TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _entries(lang):
    merged = {}
    order = []

    def add(key, **kw):
        e = merged.get(key)
        if e is None:
            e = merged[key] = Entry(levels=[], sources=[], items=[], labels=[], price=None, trade=None,
                                    roamer=None, shiny_modes=set(), **kw)
            order.append(key)
        return e

    for m, path in _script_files():
        src = open(repo_path(path), encoding="utf-8").read()
        mid = m.id if m else None
        for cm in CMD.finditer(src):
            cmd, raw = cm.group(1), cm.group(2).strip()
            line = src[:cm.start()].count("\n") + 1
            label = _labels_at(src, cm.start())
            args = _split_args(raw)
            if cmd == "givemon":
                a = _named(args, GIVEMON_ARGS)
                spec = a.get("species", "")
                cands = [(_species(spec), None)] if spec.startswith("SPECIES_") else _resolve_var(src, spec)
                lvl = _num(a.get("level", ""))
                mode = a.get("shinyMode", "SHINY_MODE_RANDOM") or "SHINY_MODE_RANDOM"
                item = a.get("item")
                for sid, price in cands:
                    if not sid:
                        continue
                    e = add(("gift", mid, path, sid), kind="gift", species=sid, map_id=mid)
                    e.shiny_modes.add(mode)
                    if lvl is not None and lvl not in e.levels:
                        e.levels.append(lvl)
                    if price:
                        e.price = price
                    if item and item not in ("ITEM_NONE", "0"):
                        iid = IT.by_const(item)
                        if iid and iid.id not in e.items:
                            e.items.append(iid.id)
                    e.sources.append((path, line))
                    e.labels.append(label)
            elif cmd == "giveegg":
                sid = _species(args[0]) if args else None
                if sid:
                    e = add(("egg", mid, path, sid), kind="egg", species=sid, map_id=mid)
                    e.shiny_modes.add("SHINY_MODE_RANDOM")
                    e.sources.append((path, line))
                    e.labels.append(label)
            else:
                a = _named(args, ("species", "level", "item", "species2", "level2", "item2"))
                pairs = [(a.get("species"), a.get("level"), a.get("item"))]
                if cmd == "setwildbattle" and a.get("species2") and a.get("species2") != "SPECIES_NONE":
                    pairs.append((a.get("species2"), a.get("level2"), a.get("item2")))
                for spec, lv, item in pairs:
                    sid = _species(spec or "")
                    if not sid:
                        continue
                    kind = "static_shiny" if cmd == "setwildbattleshiny" else "static"
                    e = add((kind, mid, path, sid), kind=kind, species=sid, map_id=mid)
                    e.shiny_modes.add("SHINY_MODE_ALWAYS" if kind == "static_shiny" else "SHINY_MODE_RANDOM")
                    lvl = _num(lv or "")
                    if lvl is not None and lvl not in e.levels:
                        e.levels.append(lvl)
                    if item and item not in ("ITEM_NONE", "0"):
                        it = IT.by_const(item)
                        if it and it.id not in e.items:
                            e.items.append(it.id)
                    e.sources.append((path, line))
                    e.labels.append(label)
        # trades
        if m is not None:
            t, table = _trade_table(lang)
            for tm in TRADE.finditer(src):
                const = tm.group(1)
                idx = t.const(const)
                line = src[:tm.start()].count("\n") + 1
                if idx is None or idx not in table or ("trade", mid, const) in merged:
                    continue
                row = table[idx]
                sp_ = SP.by_id(t.field(row, "species"))
                rq_ = SP.by_id(t.field(row, "requestedSpecies"))
                sid = sp_.id if sp_ else None
                req = rq_.id if rq_ else None
                if sid is None:
                    continue
                held = t.field(row, "heldItem")
                ot_id = t.field(row, "otId")
                pers = t.field(row, "personality")
                e = add(("trade", mid, const), kind="trade", species=sid, map_id=mid)
                e.shiny_modes.add("fixed")
                nick, ot = _string(row.get("nickname")), _string(row.get("otName"))
                # English: nickname and OT name in the site's name style (the game writes
                # them in capitals); *_game is the game's own spelling
                e.trade = dict(const=const,
                               nickname=namestyle.show(nick, lang, "person", lang), nickname_game=nick,
                               ot_name=namestyle.show(ot, lang, "person", lang), ot_name_game=ot,
                               requested=req, held_item=held, ot_id=ot_id, personality=pers)
                e.sources.append((path, line))
    callers = _shared_callers()
    out = []
    for k in order:
        e = merged[k]
        e.levels.sort()
        e.callers = []
        if e.map_id is None:
            e.callers = callers.get(e.sources[0][0], [])
            if not e.callers:
                continue          # shared script no active map calls (e.g. a Mystery Gift script)
        modes = e.shiny_modes
        if "fixed" in modes:
            e.shiny = "fixed"
        elif modes == {"SHINY_MODE_ALWAYS", "SHINY_MODE_NEVER"}:
            e.shiny = "preview"
        elif modes == {"SHINY_MODE_NEVER"}:
            e.shiny = "never"
        elif modes == {"SHINY_MODE_ALWAYS"}:
            e.shiny = "always"
        else:
            e.shiny = "roll"
        e.legendary = _legendary_flags(SP.by_id(e.species))
        out.append(e)
    out += roamers()
    return tuple(out)


@functools.lru_cache(maxsize=None)
def _shared_callers():
    """{shared script path: [map ids of active, unlocked maps that use one of its labels]}"""
    out = {}
    files = [(m, p) for m, p in _script_files() if m is not None]
    for path in SHARED_SCRIPTS:
        if not os.path.exists(repo_path(path)):
            continue
        labels = set(re.findall(r"^(\w+)::", open(repo_path(path), encoding="utf-8").read(), re.M))
        hits = []
        for m, p in files:
            text = open(repo_path(p), encoding="utf-8").read()
            mj = open(repo_path("data", "maps", m.dir, "map.json"), encoding="utf-8").read()
            if any(re.search(r"\b%s\b" % re.escape(l), text + mj) for l in labels):
                hits.append(m.id)
        out[path] = hits
    return out


def legendary_species():
    """Species consts that follow the one-time encounter rules of src/legendaries_oj.c
    (enum LEGENDARY_* of sLegendaries -> SPECIES_*; LEGENDARY_RED_GYARADOS -> Gyarados)."""
    t, table = _legendaries()
    out = set()
    for idx in table:
        name = t.names("LEGENDARY_").get(idx)
        if not name:
            continue
        base = name[len("LEGENDARY_"):]
        base = {"RED_GYARADOS": "GYARADOS"}.get(base, base)
        if SP.by_const("SPECIES_" + base):
            out.add("SPECIES_" + base)
    return out


def legendary_rules():
    """(flee cooldown days,) of src/legendaries_oj.c (FLEE_COOLDOWN_DAYS)."""
    t, _ = _legendaries()
    return t.const("FLEE_COOLDOWN_DAYS")


@functools.lru_cache(maxsize=None)
def _roamer_flags():
    """{species const: release flag name} from the ROAMING_LEGENDARY(...) rows (source text)."""
    src = open(repo_path("src", "legendaries_oj.c"), encoding="utf-8").read()
    return {m.group(1): m.group(2) for m in re.finditer(
        r"ROAMING_LEGENDARY\(\s*\w+\s*,\s*(SPECIES_\w+)\s*,\s*\d+\s*,\s*(\w+)", src)}


@functools.lru_cache(maxsize=None)
def _legendaries():
    """sLegendaries rows of src/legendaries_oj.c (IS_HNS)."""
    t = TU.load("src/legendaries_oj.c", lang="de")
    return t, t.table("sLegendaries")


def roamers():
    """Roaming Pokémon: sLegendaries entries with a roamer species."""
    t, table = _legendaries()
    rtab = TU.load("src/roamer.c", lang="de")
    out = []
    for idx in sorted(table):
        row = table[idx]
        sid = t.field(row, "roamerSpecies")
        if not sid:
            continue
        tab = t.field(row, "roamerTable")
        tname = {rtab.const("ROAMER_LOC_TABLE_JOHTO"): "johto", rtab.const("ROAMER_LOC_TABLE_HOENN"): "hoenn"}.get(tab)
        release = _roamer_flags().get(SP.by_id(sid).const)
        e = Entry(kind="roamer", species=sid, levels=[t.field(row, "roamerLevel")], map_id=None, sources=[
            ("src/legendaries_oj.c", 0)], items=[], labels=[], price=None, trade=None, shiny="roll",
            legendary=True, shiny_modes={"SHINY_MODE_RANDOM"},
            roamer=dict(level=t.field(row, "roamerLevel"), release_flag=release, table=tname,
                        maps=roamer_maps(tname)))
        out.append(e)
    return out


@functools.lru_cache(maxsize=None)
def roamer_maps(table_name):
    """Map ids of a roamer location table (first column of sRoamerLocationsJohto/Hoenn)."""
    if table_name is None:
        return ()
    src = open(repo_path("src", "roamer.c"), encoding="utf-8").read()
    sym = {"johto": "sRoamerLocationsJohto", "hoenn": "sRoamerLocationsHoenn"}[table_name]
    m = re.search(r"%s\[\]\[6\]\s*=\s*\{(.*?)\n\};" % sym, src, re.S)
    out = []
    for mid in re.findall(r"MAP_NUM\((MAP_\w+)\)", m.group(1) if m else ""):
        if mid not in out:
            out.append(mid)
    return tuple(out)
