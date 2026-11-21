"""Where items come from: item balls, hidden items, script gifts, shops and berry trees.

All read from the active, unlocked maps (map.json) and the event scripts with
resolved #if/.if (gamedata.trainers_scriptdb, tools/oj_world.py ScriptDB).

    trainers_items.sources() -> {item id: [Source]}
    Source(kind, item, map_id, amount, price, detail)
        kind "ball"    object event whose script runs finditem (Common_EventScript_FindItem:
                       item = trainer_sight_or_berry_tree_id, amount = movement_range_x or 1,
                       GetItemBallIdAndAmountFromTemplate in src/item_ball.c); detail = "object"
                       when the object is not drawn as a ball (graphics_id not in BALL_GFX, e.g. a fossil)
             "hidden"  bg_event "hidden_item" (item, quantity; underfoot)
             "gift"    giveitem / giveitem_msg / additem / finditem in a script that is not
                       an item ball (NPC gifts, prizes, events; detail = the command); map = the map of the script
                       file or, for shared scripts, every map whose events reach it
             "shop"    pokemart <list>: the .2byte item list up to ITEM_NONE (price = gItemsInfo
                       price, GetItemPrice); "pokemart 0" = the Johto-badge marts of src/shop.c
                       SetShopItemsForSale (IS_HNS: sShopInventories[GetJohtoBadgeCount()]),
                       detail = badges needed
             "random"  a script that hands out the item by chance (`random N` + call_if_eq,
                       e.g. EventScript_EndSmash after Rock Smash): detail = (percent, caller label)
             "berry"   berry tree object (OBJ_EVENT_GFX_BERRY_TREE) whose tree gets a berry in
                       data/scripts/new_game.inc (setberrytree)
    trainers_items.unresolved() -> [(file:line, command)] script item commands with a variable item
    trainers_items.badge_mart() -> [(badges, [item ids])] (sShopInventories)
Battle Pyramid balls (BattlePyramid_FindItemBall*) are random (not listed); data/scripts/debug.inc
is not part of the game.
"""
import functools
import re

from . import tu as TU
from . import maps
from . import items as IT
from . import trainers_scriptdb as SDB

GIFT_COMMANDS = ("giveitem", "giveitem_msg", "additem", "finditem", "giveitem_norandom", "giveitem_unless_owned")
# debug.inc is not part of the game; cable_club.inc hands out the Eon Ticket only after a
# distribution over the link (ShouldDistributeEonTicket), never in normal play.
SKIP_FILES = ("data/scripts/debug.inc", "data/scripts/cable_club.inc")
BALL_GFX = ("OBJ_EVENT_GFX_ITEM_BALL", "OBJ_EVENT_GFX_ITEM_BALL_HNS", "OBJ_EVENT_GFX_POKE_BALL")
SKIP_SCRIPTS = ("BattlePyramid_FindItemBall", "BattlePyramid_FindItemBall_hns")


class Source:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Source(%s %s %s)" % (self.kind, self.item, self.map_id)


def _maps():
    return [m for m in maps.all_maps().values() if not maps.locked_mapsec(m.mapsec)]


def _item_id(name):
    it = IT.by_const(name) if name and name.startswith("ITEM_") else None
    return it.id if it else None


def _int(v, default=1):
    try:
        return int(str(v), 0)
    except (TypeError, ValueError):
        return default


@functools.lru_cache(maxsize=None)
def _ball_scripts():
    """Script labels of item-ball objects -> (item const, amount) when the script itself
    runs `finditem ITEM_X[, n]` (straight line, gotos followed)."""
    d = SDB.db()
    out = {}

    def scan(label):
        i = d.labels.get(label)
        steps = 0
        while i is not None and i < len(d.instrs) and steps < 40:
            ins = d.instrs[i]
            steps += 1
            if ins.cmd == "finditem" and ins.args and ins.args[0].startswith("ITEM_"):
                return ins.args[0], _int(ins.args[1]) if len(ins.args) > 1 else 1, i
            if ins.cmd in ("end", "return"):
                return None
            if ins.cmd == "goto" and ins.args and ins.args[-1] in d.labels:
                i = d.labels[ins.args[-1]]
                continue
            if ins.cmd.startswith("."):
                return None
            i += 1
        return None
    for m in _maps():
        for o in m.data.get("object_events") or []:
            s = o.get("script")
            if s and s not in out and s != "Common_EventScript_FindItem":
                r = scan(s)
                if r:
                    out[s] = r
    return out


@functools.lru_cache(maxsize=None)
def badge_mart():
    """sShopInventories (src/shop.c, IS_HNS): [(Johto badges, [item ids])]."""
    t = TU.load("src/shop.c")
    out = []
    for n, sym in enumerate(t.array("sShopInventories")):
        lst = [x for x in t.array(str(sym)) if x]
        out.append((n, lst))
    return out


@functools.lru_cache(maxsize=None)
def _setberry():
    """{BERRY_TREE_*: item const} of setberrytree in the new-game script."""
    d = SDB.db()
    out = {}
    for ins in d.instrs:
        if ins.cmd == "setberrytree" and len(ins.args) >= 2:
            found = [x for x in re.findall(r"\b(ITEM_\w+)", ins.args[1]) if x != "ITEM_TO_BERRY"]
            if found:
                out[ins.args[0]] = found[-1]
    return out


@functools.lru_cache(maxsize=None)
def _collect():
    d = SDB.db()
    out = []
    unresolved = []
    ball_scripts = _ball_scripts()
    ball_instr = {r[2] for r in ball_scripts.values()}
    berries = _setberry()
    # map objects and hidden items
    for m in _maps():
        for o in m.data.get("object_events") or []:
            s = o.get("script") or ""
            if s in SKIP_SCRIPTS:
                continue
            if s == "Common_EventScript_FindItem":
                iid = _item_id(o.get("trainer_sight_or_berry_tree_id"))
                if iid:
                    amt = _int(o.get("movement_range_x"), 0) or 1
                    out.append(Source(kind="ball", item=iid, map_id=m.id, amount=amt, price=None,
                                      detail=None if o.get("graphics_id") in BALL_GFX else "object"))
            elif s in ball_scripts:
                c, amt, _i = ball_scripts[s]
                iid = _item_id(c)
                if iid:
                    out.append(Source(kind="ball", item=iid, map_id=m.id, amount=amt, price=None,
                                      detail=None if o.get("graphics_id") in BALL_GFX else "object"))
            if o.get("graphics_id") == "OBJ_EVENT_GFX_BERRY_TREE":
                tree = o.get("trainer_sight_or_berry_tree_id")
                iid = _item_id(berries.get(tree))
                if iid:
                    out.append(Source(kind="berry", item=iid, map_id=m.id, amount=None, price=None, detail=tree))
        for b in m.data.get("bg_events") or []:
            if b.get("type") == "hidden_item":
                iid = _item_id(b.get("item"))
                if iid:
                    out.append(Source(kind="hidden", item=iid, map_id=m.id, amount=_int(b.get("quantity"), 1),
                                      price=None, detail="underfoot" if b.get("underfoot") else None))
    # scripts: gifts and shops
    cur_label, dead = None, False
    for i, ins in enumerate(d.instrs):
        if ins.file in SKIP_FILES:
            continue
        # nothing runs after an unconditional end / return / goto until the next label
        lab_here = SDB.label_at(i)
        if lab_here != cur_label:
            cur_label, dead = lab_here, False
        was_dead = dead
        if ins.cmd in ("end", "return", "goto"):
            dead = True
        if was_dead:
            continue
        if ins.cmd in GIFT_COMMANDS:
            if i in ball_instr:
                continue
            arg = next((a for a in ins.args if a.startswith("ITEM_")), None)
            if ins.cmd == "giveitem_msg":
                arg = next((a for a in ins.args[1:] if a.startswith("ITEM_")), None)
            if arg is None:
                unresolved.append(("%s:%d" % (ins.file, ins.line), "%s %s" % (ins.cmd, ", ".join(ins.args))))
                continue
            iid = _item_id(arg)
            if not iid:
                continue
            idx = [a for a in ins.args if a.startswith("ITEM_")]
            rest = ins.args[ins.args.index(idx[0]) + 1:] if idx else []
            amt = _int(rest[0], 1) if rest and re.match(r"^\d+$", rest[0]) else 1
            where = _where(i, ins)
            if where == [None]:
                chance = _random_chance(i)
                if chance:
                    out.append(Source(kind="random", item=iid, map_id=None, amount=amt, price=None, detail=chance))
                continue    # shared script no active map reaches (e.g. retired Sevii scripts)
            for mid in where:
                out.append(Source(kind="gift", item=iid, map_id=mid, amount=amt, price=None, detail=ins.cmd))
        elif ins.cmd == "pokemart" and ins.args:
            lab = ins.args[0]
            where = _where(i, ins)
            if lab in ("0", "NULL"):
                first = {}
                for n, lst in badge_mart():
                    for iid in lst:
                        first.setdefault(iid, n)
                for iid, n in first.items():
                    for mid in where:
                        out.append(Source(kind="shop", item=iid, map_id=mid, amount=None,
                                          price=IT.by_id(iid).price, detail=n))
                continue
            j = d.labels.get(lab)
            while j is not None and j < len(d.instrs):
                x = d.instrs[j]
                if x.cmd == ".2byte":
                    stop = False
                    for a in x.args:
                        if a in ("ITEM_NONE", "0"):
                            stop = True
                            break
                        iid = _item_id(a)
                        if iid:
                            for mid in where:
                                out.append(Source(kind="shop", item=iid, map_id=mid, amount=None,
                                                  price=IT.by_id(iid).price, detail=None))
                    if stop:
                        break
                    j += 1
                    continue
                if x.cmd.startswith(".") and x.cmd != ".2byte":
                    j += 1
                    continue
                break
    return out, unresolved


def _where(i, ins):
    mid = SDB.map_of_file(ins.file)
    if mid:
        m = maps.by_id(mid)
        return [mid] if m and not maps.locked_mapsec(m.mapsec) else []
    if ins.file.startswith("data/maps/"):
        return []   # script of a retired (inactive) map
    label = SDB.label_at(i)
    res = []
    for x in SDB.callers(label) if label else []:
        m = maps.by_id(x)
        if m and not maps.locked_mapsec(m.mapsec):
            res.append(x)
    return res or [None]


def _random_chance(i):
    """(percent, caller label) when the script is called as `call_if_eq VAR_RESULT, k, label`
    after `random N` in the caller (e.g. EventScript_EndSmash: rock smash finds)."""
    d = SDB.db()
    label = SDB.label_at(i)
    for j in SDB._jump_sources().get(label, ()):
        x = d.instrs[j]
        if not x.cmd.startswith("call_if_eq") or not x.args or x.args[0] != "VAR_RESULT":
            continue
        k = j - 1
        caller = SDB.label_at(j)
        while k >= 0 and SDB.label_at(k) == caller:
            y = d.instrs[k]
            if y.cmd == "random" and y.args:
                n = _int(y.args[0], 0)
                if n:
                    return (100.0 / n, caller)
            k -= 1
    return None


def sources():
    out = {}
    for s in _collect()[0]:
        out.setdefault(s.item, []).append(s)
    return out


def unresolved():
    return list(_collect()[1])
