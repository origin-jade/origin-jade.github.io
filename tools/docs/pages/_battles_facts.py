"""Facts around the gym and league battles (language neutral: constants, ids, numbers).

  * obedience_levels()   GetObedienceLevel (src/battle_util.c): highest level of a traded
                         Pokémon that obeys, by badges - Kanto badges before the Kanto title,
                         Johto badges from the Kanto title on; GetAttackerObedienceForAction:
                         only Pokémon of another trainer can disobey, after the Johto title
                         every Pokémon obeys.
  * kanto_field_moves()  IsFieldMoveUnlocked_* (src/field_move.c): the badge a field move
                         needs on Kanto maps (the KantoRulesApply branch).
  * battle_rewards(map)  items a script hands out after a battle (giveitem*) with the region
                         title the script asks for first, if any.
  * order_conditions()   Johto gyms whose leader fields a different team depending on which
                         other gyms are already beaten (FLAG_DEFEATED_*_GYM tests on the
                         way to the trainerbattle).
  * league_change_badges()  Johto badges after which the Indigo Plateau changes its league.
  * prize_money(...)     GetTrainerMoneyToGive (src/battle_script_commands.c).
"""
import functools
import re

from gamedata import repo_path
from gamedata import items as IT
from gamedata import maps
from gamedata import tu as TU
from gamedata import trainers_scriptdb as SDB

TITLE_FLAGS = SDB.TITLE_FLAGS
_GYM_FLAG = re.compile(r"^FLAG_DEFEATED_\w+_GYM$")


class FactError(RuntimeError):
    pass


# ------------------------------------------------------------------ obedience
@functools.lru_cache(maxsize=None)
def obedience_levels():
    """{"Kanto": [level by Kanto badges 0..8], "Johto": [level by Johto badges 0..8]}."""
    t = TU.load("src/battle_util.c")
    out = {"Kanto": [int(x) for x in t.array("sKantoObedienceLevels")],
           "Johto": [int(x) for x in t.array("sJohtoObedienceLevels")]}
    src = open(repo_path("src", "battle_util.c"), encoding="utf-8").read()
    i = src.index("static u8 GetObedienceLevel(void)")
    body = src[i:src.index("\n}\n", i)]
    # the function this mirrors: Johto table once FLAG_IS_KANTO_CHAMPION is set, else the Kanto table
    if not re.search(r"if \(FlagGet\(FLAG_IS_KANTO_CHAMPION\)\)\s*\{[^}]*sJohtoObedienceLevels\[badgeCount\]", body) \
            or "return sKantoObedienceLevels[badgeCount];" not in body:
        raise FactError("GetObedienceLevel changed shape")
    j = src.index("enum Obedience GetAttackerObedienceForAction(void)")
    body2 = src[j:src.index("\n}\n", j)]
    if not re.search(r"if \(FlagGet\(FLAG_IS_JOHTO_CHAMPION\)\)\s*return OBEYS;", body2) \
            or "B_OBEDIENCE_MECHANICS < GEN_8 && !IsOtherTrainer" not in body2:
        raise FactError("GetAttackerObedienceForAction changed shape")
    if len(out["Kanto"]) != 9 or len(out["Johto"]) != 9:
        raise FactError("obedience tables: expected 9 entries")
    return out


# ------------------------------------------------------------------ field moves (Kanto)
_CAMEL = re.compile(r"(?<!^)(?=[A-Z])")


@functools.lru_cache(maxsize=None)
def kanto_field_moves():
    """{badge number: [MOVE_ constants]} for Kanto maps."""
    src = open(repo_path("src", "field_move.c"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"static bool32 IsFieldMoveUnlocked_(\w+)\(void\)\s*\{(.*?)\n\}", src, re.S):
        km = re.search(r"if \(KantoRulesApply\(\)\)\s*return FlagGet\(FLAG_BADGE0(\d)_GET\);", m.group(2))
        if km:
            const = "MOVE_" + _CAMEL.sub("_", m.group(1)).upper()
            out.setdefault(int(km.group(1)), []).append(const)
    if not out:
        raise FactError("src/field_move.c: no Kanto badge rules found")
    return out


# ------------------------------------------------------------------ script helpers
@functools.lru_cache(maxsize=None)
def _file_index():
    """{script file: [instruction index]} and {label: file}."""
    d = SDB.db()
    by_file = {}
    for i, ins in enumerate(d.instrs):
        by_file.setdefault(ins.file, []).append(i)
    return by_file


def _map_file(map_id):
    m = maps.by_id(map_id)
    return "data/maps/%s/scripts.inc" % m.dir


@functools.lru_cache(maxsize=None)
def battle_rewards(map_id):
    """{(trainer const, label of the battle): [(item const, title index or None)]}: the items
    the script hands out after winning that battle (giveitem* reached from the battle's
    continuation or its defeat script, before any other battle starts). title index
    (0 Kanto, 1 Johto, 2 Hoenn): the item is only reached through a positive test of that
    title flag."""
    d = SDB.db()
    idxs = _file_index().get(_map_file(map_id), [])
    if not idxs:
        return {}
    lo, hi = idxs[0], idxs[-1]
    out = {}
    for i0 in idxs:
        ins0 = d.instrs[i0]
        if not ins0.cmd.startswith("trainerbattle"):
            continue
        consts = [a for a in ins0.args if a.startswith("TRAINER_") and not a.startswith("TRAINER_BATTLE_")
                  and a != "TRAINER_NONE"]
        if not consts:
            continue
        found = []
        stack = [(i0 + 1, None)] + [(d.labels[a], None) for a in ins0.args if a in d.labels
                                    and lo <= d.labels[a] <= hi and "_Text_" not in a]
        visited = set()
        while stack:
            i, title = stack.pop()
            while lo <= i <= hi:
                if (i, title) in visited:
                    break
                visited.add((i, title))
                ins = d.instrs[i]
                cmd = ins.cmd
                if cmd.startswith(".") or cmd.startswith("trainerbattle"):
                    break
                tg = [a for a in ins.args if a in d.labels and lo <= d.labels[a] <= hi]
                if cmd.startswith("giveitem"):
                    item = next((a for a in ins.args if a.startswith("ITEM_")), None)
                    if item and (item, title) not in found:
                        found.append((item, title))
                    i += 1
                    continue
                if cmd in ("call_if_set", "goto_if_set") and ins.args and ins.args[0] in TITLE_FLAGS and tg:
                    stack.append((d.labels[tg[-1]], TITLE_FLAGS.index(ins.args[0])))
                    i += 1
                    continue
                if cmd == "goto":
                    if not tg:
                        break
                    i = d.labels[tg[-1]]
                    continue
                if cmd in ("end", "return", "releaseall_end"):
                    break
                if tg and (cmd.startswith("goto") or cmd.startswith("call") or cmd == "case"):
                    stack.append((d.labels[tg[-1]], title))
                i += 1
        # an item reached both with and without the title test is not title-gated
        plain = {it for it, t in found if t is None}
        res = [(it, t) for it, t in found if t is None or it not in plain]
        for c in consts:
            out[(c, SDB.label_at(i0))] = res
    return out


def reward_tms(map_id, const, label):
    """[(Item id, title index or None)]: the TMs/HMs of battle_rewards() for one battle."""
    out = []
    for item, title in battle_rewards(map_id).get((const, label), ()):
        it = IT.by_const(item)
        if it is not None and it.tm and (it.id, title) not in out:
            out.append((it.id, title))
    return out


@functools.lru_cache(maxsize=None)
def map_gift_tms(map_id):
    """[Item id] of the TMs/HMs a script of the map hands out (giveitem*), in script order."""
    d = SDB.db()
    out = []
    for i in _file_index().get(_map_file(map_id), []):
        ins = d.instrs[i]
        if not ins.cmd.startswith("giveitem"):
            continue
        item = next((a for a in ins.args if a.startswith("ITEM_")), None)
        it = IT.by_const(item) if item else None
        if it is not None and it.tm and it.id not in out:
            out.append(it.id)
    return out


def mapsec_gift_tms(map_id):
    """map_gift_tms over every map of the same map section (the place as a whole)."""
    sec = maps.by_id(map_id).mapsec
    out = []
    for m in sorted(maps.all_maps().values(), key=lambda x: (x.group_index, x.map_num)):
        if m.mapsec == sec:
            for x in map_gift_tms(m.id):
                if x not in out:
                    out.append(x)
    return out


# ------------------------------------------------------------------ gym order (Johto)
@functools.lru_cache(maxsize=None)
def _gym_flag_setters():
    """{FLAG_DEFEATED_*_GYM: map id of the script that sets it}."""
    d = SDB.db()
    out = {}
    for ins in d.instrs:
        if ins.cmd == "setflag" and ins.args and _GYM_FLAG.match(ins.args[0]):
            mid = SDB.map_of_file(ins.file)
            if mid:
                out.setdefault(ins.args[0], mid)
    return out


@functools.lru_cache(maxsize=None)
def order_conditions(map_id):
    """{trainer const: (beaten, [other gym map ids])} for the battles of a map that depend on
    how many of the named other gyms are already beaten (beaten: that number). Only when
    every path to the battle agrees on the number."""
    d = SDB.db()
    file = _map_file(map_id)
    idxs = _file_index().get(file, [])
    if not idxs:
        return {}
    lo, hi = idxs[0], idxs[-1]
    own = {f for f, mid in _gym_flag_setters().items() if mid == map_id}
    entries = set()
    m = maps.by_id(map_id)
    for kind in ("object_events", "coord_events", "bg_events"):
        for o in m.data.get(kind) or []:
            s = o.get("script")
            if s in d.labels:
                entries.add(s)
    found = {}
    visited = set()
    for entry in sorted(entries):
        stack = [(d.labels[entry], ())]
        while stack:
            i, st = stack.pop()
            while lo <= i <= hi:
                if (i, st) in visited:
                    break
                visited.add((i, st))
                ins = d.instrs[i]
                cmd = ins.cmd
                if cmd.startswith("."):
                    break
                tg = [a for a in ins.args if a in d.labels]
                if cmd.startswith("trainerbattle"):
                    for a in ins.args:
                        if a.startswith("TRAINER_") and not a.startswith("TRAINER_BATTLE_"):
                            found.setdefault(a, set()).add(st)
                    for t in tg:
                        stack.append((d.labels[t], st))
                    i += 1
                    continue
                if cmd in ("goto_if_set", "goto_if_unset", "call_if_set", "call_if_unset") and tg \
                        and ins.args and _GYM_FLAG.match(ins.args[0]) and ins.args[0] not in own:
                    taken = cmd.endswith("_set")
                    f = ins.args[0]
                    cur = dict(st)
                    if f in cur:                       # already decided on this path
                        if cur[f] == taken:
                            i = d.labels[tg[-1]]
                        else:
                            i += 1
                        continue
                    stack.append((d.labels[tg[-1]], tuple(sorted(dict(cur, **{f: taken}).items()))))
                    st = tuple(sorted(dict(cur, **{f: not taken}).items()))
                    i += 1
                    continue
                if cmd == "goto" and tg:
                    i = d.labels[tg[-1]]
                    continue
                if cmd in ("end", "return", "releaseall_end"):
                    break
                if tg and (cmd.startswith("goto") or cmd.startswith("call") or cmd == "case"):
                    stack.append((d.labels[tg[-1]], st))
                i += 1
    setters = _gym_flag_setters()
    flags = sorted({f for sts in found.values() for st in sts for f, _v in st})
    if not flags:
        return {}
    out = {}
    for const, sts in found.items():
        full = [st for st in sts if len(st) == len(flags)]
        if not full or len(full) != len(sts):
            # paths that never test the flags (the rematch after the title) carry no order rule
            if any(st for st in sts):
                continue
            continue
        counts = {sum(1 for _f, v in st if v) for st in full}
        if len(counts) == 1:
            out[const] = (counts.pop(), [setters[f] for f in flags if f in setters])
    return out


# ------------------------------------------------------------------ league change
LEAGUE_CHANGE_SCRIPT = "PokemonLeague_EventScript_CheckLeagueChanged"


@functools.lru_cache(maxsize=None)
def league_change_badges():
    """Johto badges the league-change check asks for (data/scripts/pokemon_league.inc)."""
    d = SDB.db()
    i = d.labels.get(LEAGUE_CHANGE_SCRIPT)
    if i is None:
        return None
    for ins in d.instrs[i:i + 12]:
        if ins.cmd.startswith("goto_if") or ins.cmd.startswith("call_if"):
            for a in ins.args:
                if a.isdigit():
                    return int(a)
    return None


# ------------------------------------------------------------------ prize money
@functools.lru_cache(maxsize=None)
def _money_check():
    src = open(repo_path("src", "battle_script_commands.c"), encoding="utf-8").read()
    i = src.index("static u32 GetTrainerMoneyToGive(u16 trainerId)")
    body = re.sub(r"\s+", " ", src[i:src.index("\n}\n", i)])
    need = ("trainerMoney = gTrainerClasses[GetTrainerClassFromId(trainerId)].money ?: 5;",
            "if (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS) moneyReward = 4 * lastMonLevel * "
            "gBattleStruct->moneyMultiplier * trainerMoney;",
            "else if (IsDoubleBattle()) moneyReward = 4 * lastMonLevel * gBattleStruct->moneyMultiplier * 2 * "
            "trainerMoney;",
            "else moneyReward = 4 * lastMonLevel * gBattleStruct->moneyMultiplier * trainerMoney;")
    for n in need:
        if n not in body:
            raise FactError("GetTrainerMoneyToGive changed shape")
    return True


def prize_money(class_money, last_level, double, two_opponents=False):
    """GetTrainerMoneyToGive without a prize-doubling item or move: 4 x level of the last
    Pokémon fielded x class money (0 counts as 5), doubled in a double battle against
    one trainer."""
    _money_check()
    money = class_money or 5
    return 4 * last_level * money * (2 if double and not two_opponents else 1)
