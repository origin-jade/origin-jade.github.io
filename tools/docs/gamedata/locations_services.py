"""Services a place offers that are read from the event scripts: move tutors and things a
script sells (for coins, money or Battle Points).

    locations_services.tutors() -> [Tutor]
        Tutor(move, map_ids, cost, currency, once)
        move      MOVE_* constant taught
        map_ids   active, unlocked maps with a person, sign or tile whose script leads there
        cost      Battle Points the script takes (the frontier tutors), else None
        currency  "bp" or None
        once      True when the script sets a "taught" flag (the tutor teaches one time only)

      Two script forms exist: the `move_tutor` macro (data/scripts/move_tutors.inc,
      asm/macros/event.inc: the flag argument makes it a one-time tutor) and scripts that
      put the move into VAR_0x8005 before the tutor menu (`setvar VAR_0x8005, MOVE_*`:
      data/scripts/move_tutors_frlg.inc, BattleFrontier_Lounge7_hns). The frontier form
      sets the price in VAR_0x8008 right before it and pays with TakeFrontierBattlePoints.

    locations_services.script_prices() -> {(map id, item id): (currency, amount)}
        Items a script sells, currency "coins" | "money". Two script forms:
        the item is handed out right after taking coins or money in the same script block
        (`removecoins N` / `removemoney N` followed by giveitem/additem ...; Goldenrod and
        Mauville Game Corner, the Seashore House), or the block of a menu choice sets item
        and price (`setvar VAR_TEMP_1, ITEM_X` + `setvar VAR_TEMP_2, N`) and the script file
        pays with `removecoins VAR_TEMP_2` (Celadon Game Corner prize room).

    locations_services.reaching_maps(label) -> [map id]
        Maps with an event (object, sign, trigger) from which the scripts reach the label.

    locations_services.closed_label(label) -> True when every jump to the script label tests a
        story variable for a value that only scripts of locked areas (maps.locked_mapsec:
        Sinjoh, Alola) ever set - e.g. the league teams behind
        `goto_if_ge VAR_SINJOH_STORYLINE, 13, ...`. Such a script cannot run in this build.

    locations_services.daily_label(label) -> True when the script block of the label, or the
        block that calls it, sets a FLAG_DAILY_* flag afterwards (cleared once a day by
        ClearDailyFlags, src/clock.c): a battle or gift that comes back every day.

All conditionals of the scripts are resolved as in the build (gamedata.trainers_scriptdb).
Locked areas and data/scripts/debug.inc are left out.
"""
import functools
import re

from . import items as IT
from . import maps
from . import repo_path
from . import trainers_scriptdb as SDB

SKIP_FILES = ("data/scripts/debug.inc",)
GIVE = ("giveitem", "giveitem_msg", "additem", "finditem", "giveitem_norandom", "giveitem_unless_owned")
_BLOCK_END = ("end", "return", "goto", "releaseall_end")


class Tutor:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Tutor(%s %s %s)" % (self.move, self.map_ids, self.cost)


def _open(mid):
    m = maps.by_id(mid)
    return m is not None and not maps.locked_mapsec(m.mapsec)


@functools.lru_cache(maxsize=None)
def reaching_maps(label):
    """Map ids with a map event whose script reaches `label` (walks every jump backwards)."""
    refs = SDB._event_refs()
    src = SDB._jump_sources()
    d = SDB.db()
    found, seen, todo = set(), set(), [label]
    while todo:
        lb = todo.pop()
        if lb in seen or lb is None:
            continue
        seen.add(lb)
        found.update(refs.get(lb, ()))
        for i in src.get(lb, ()):
            if d.instrs[i].file in SKIP_FILES:
                continue
            todo.append(SDB.label_at(i))
    return tuple(sorted(x for x in found if _open(x)))


def _block(i):
    """Indices of the instructions of the script block around instruction i (same label)."""
    d = SDB.db()
    lab = SDB.label_at(i)
    a = i
    while a > 0 and SDB.label_at(a - 1) == lab:
        a -= 1
    b = i
    n = len(d.instrs)
    while b + 1 < n and SDB.label_at(b + 1) == lab:
        b += 1
    return range(a, b + 1)


@functools.lru_cache(maxsize=None)
def tutors():
    d = SDB.db()
    out, seen = [], set()
    for i, ins in enumerate(d.instrs):
        if ins.file in SKIP_FILES:
            continue
        move, once, cost = None, False, None
        if ins.cmd == "move_tutor" and ins.args and ins.args[0].startswith("MOVE_"):
            move = ins.args[0]
            flag = ins.args[5] if len(ins.args) > 5 else "0"
            once = flag not in ("0", "")
        elif ins.cmd == "setvar" and len(ins.args) >= 2 and ins.args[0] == "VAR_0x8005" \
                and ins.args[1].startswith("MOVE_"):
            move = ins.args[1]
            blk = _block(i)
            for j in blk:
                x = d.instrs[j]
                if x.cmd == "setflag" and x.args and "TUTOR" in x.args[0]:
                    once = True
                if j < i and x.cmd == "setvar" and len(x.args) >= 2 and x.args[0] == "VAR_0x8008" \
                        and re.match(r"^\d+$", x.args[1]):
                    cost = int(x.args[1])
        if move is None:
            continue
        mids = reaching_maps(SDB.label_at(i))
        if not mids:
            continue
        key = (move, mids, cost)
        if key in seen:
            continue
        seen.add(key)
        out.append(Tutor(move=move, map_ids=mids, cost=cost, currency="bp" if cost is not None else None,
                         once=once))
    return tuple(out)


@functools.lru_cache(maxsize=None)
def _file_consts(path):
    """{name: int} of the `.set NAME, N` / `.equ NAME, N` lines of a script file."""
    out = {}
    try:
        src = open(repo_path(path), encoding="utf-8").read()
    except OSError:
        return out
    for m in re.finditer(r"^\s*\.(?:set|equ)\s+(\w+)\s*,\s*(\d+)\s*$", src, re.M):
        out[m.group(1)] = int(m.group(2))
    return out


def _amount(ins):
    if not ins.args:
        return None
    a = ins.args[0]
    if re.match(r"^\d+$", a):
        return int(a)
    return _file_consts(ins.file).get(a)


@functools.lru_cache(maxsize=None)
def script_prices():
    d = SDB.db()
    out = {}
    for i, ins in enumerate(d.instrs):
        if ins.cmd not in ("removecoins", "removemoney") or ins.file in SKIP_FILES:
            continue
        amount = _amount(ins)
        if not amount:
            continue
        lab = SDB.label_at(i)
        j = i + 1
        while j < len(d.instrs) and SDB.label_at(j) == lab:
            x = d.instrs[j]
            if x.cmd in GIVE:
                arg = next((a for a in x.args if a.startswith("ITEM_")), None)
                it = IT.by_const(arg) if arg else None
                if it is not None:
                    mid = SDB.map_of_file(ins.file)
                    mids = [mid] if mid else list(reaching_maps(lab))
                    for m in mids:
                        if m and _open(m):
                            out.setdefault((m, it.id), ("coins" if ins.cmd == "removecoins" else "money", amount))
                break
            if x.cmd in _BLOCK_END:
                break
            j += 1
    # menu form: item and price set in the block of the choice
    pays = {x.file for x in d.instrs if x.cmd == "removecoins" and x.args and x.args[0] == "VAR_TEMP_2"}
    for i, ins in enumerate(d.instrs):
        if ins.file not in pays or ins.cmd != "setvar" or len(ins.args) < 2 or ins.args[0] != "VAR_TEMP_1" \
                or not ins.args[1].startswith("ITEM_"):
            continue
        it = IT.by_const(ins.args[1])
        mid = SDB.map_of_file(ins.file)
        if it is None or not mid or not _open(mid):
            continue
        for j in _block(i):
            x = d.instrs[j]
            if x.cmd == "setvar" and len(x.args) >= 2 and x.args[0] == "VAR_TEMP_2" and re.match(r"^\d+$", x.args[1]):
                out.setdefault((mid, it.id), ("coins", int(x.args[1])))
    return out


_VAR_TESTS = ("goto_if_ge", "call_if_ge", "goto_if_eq", "call_if_eq", "goto_if_gt", "call_if_gt")


@functools.lru_cache(maxsize=None)
def _open_var_max():
    """{VAR: highest value a script outside the locked areas sets} (None: changed by addvar
    or copied there, so no bound is known)."""
    d = SDB.db()
    out = {}
    for ins in d.instrs:
        if ins.cmd not in ("setvar", "addvar", "copyvar", "subvar") or len(ins.args) < 2:
            continue
        var = ins.args[0]
        if not var.startswith("VAR_"):
            continue
        mid = SDB.map_of_file(ins.file)
        if ins.file.startswith("data/maps/"):
            if mid is None:
                continue                      # retired map
            m = maps.by_id(mid)
            if m is None or maps.locked_mapsec(m.mapsec):
                continue
        if ins.cmd != "setvar" or not re.match(r"^\d+$", ins.args[1]):
            out[var] = None
            continue
        if var not in out:
            out[var] = int(ins.args[1])
        elif out[var] is not None:
            out[var] = max(out[var], int(ins.args[1]))
    return out


@functools.lru_cache(maxsize=None)
def _locked_set_vars():
    """Variables that a script of a locked area sets."""
    d = SDB.db()
    out = set()
    for ins in d.instrs:
        if ins.cmd == "setvar" and ins.args and ins.args[0].startswith("VAR_"):
            mid = SDB.map_of_file(ins.file)
            m = maps.by_id(mid) if mid else None
            if m is not None and maps.locked_mapsec(m.mapsec):
                out.add(ins.args[0])
    return out


@functools.lru_cache(maxsize=None)
def closed_label(label):
    d = SDB.db()
    src = SDB._jump_sources().get(label, ())
    if not src or label in SDB._event_refs():
        return False
    top = _open_var_max()
    locked = _locked_set_vars()
    for i in src:
        ins = d.instrs[i]
        if ins.cmd not in _VAR_TESTS or len(ins.args) < 3 or ins.args[0] not in locked \
                or not re.match(r"^\d+$", ins.args[1]):
            return False
        var, need = ins.args[0], int(ins.args[1])
        if ins.cmd.endswith("_gt"):
            need += 1
        have = top.get(var, 0)
        if have is None or have >= need:
            return False
    return True


@functools.lru_cache(maxsize=None)
def daily_label(label):
    d = SDB.db()
    start = d.labels.get(label)
    if start is None:
        return False

    def sets_daily(indices):
        return any(d.instrs[j].cmd == "setflag" and d.instrs[j].args
                   and d.instrs[j].args[0].startswith("FLAG_DAILY_") for j in indices)

    if sets_daily(_block(start)):
        return True
    for i in SDB._jump_sources().get(label, ()):
        if d.instrs[i].cmd.startswith("call") and sets_daily([j for j in _block(i) if j > i]):
            return True
    return False
