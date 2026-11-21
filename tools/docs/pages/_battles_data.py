"""Battle data for the battle pages: every battle the game can start, who fights
it, where, under which level rule and at which progress steps.

Language neutral (constants, ids, numbers); names are looked up by the page in
its language. Mirrors, through the data layer:
  * teams: the .party files (gamedata.trainers);
  * where and when a battle happens: the map scripts with resolved conditionals
    (gamedata.trainers_scriptdb) - only active, unlocked maps;
  * levels and species: ScaleTrainerMonLevel / ScaleTrainerMonSpecies
    (src/level_scaling.c via gamedata.levels, trainers.effective_team);
  * PokéCom rematch stages: gRematchTable, GetMaxRematchStageForBadges,
    HasEnoughBadgesForRematchOf (src/battle_setup.c via gamedata.trainers_rematch);
  * Kanto leader rematches: IsKantoLeaderRematchBattle (script flag set by the gym
    script, class of the Kanto rematch leaders); the progress steps come from the
    title flags the script tests and, for the leaders that only appear after the
    league change, the league-change check of data/scripts/pokemon_league.inc;
  * ability: CreateNPCTrainerPartyWithId takes the slot of the ability written in
    the data (of the data species) or slot 0, GetAbilityBySpecies reads it on the
    fielded species;
  * empty movesets: GiveBoxMonInitialMoveset (src/pokemon.c): the last four
    level-up moves up to the effective level, of the fielded species.
"""
import functools
import re

from gamedata import levels, maps, species as SP, trainers as T
from gamedata import trainers_rematch as RM
from gamedata import trainers_scriptdb as SDB

from pages import _battles_order as ORDER

# Trainer classes with a role - by class constant.
ROLES = {
    "leader": ("TRAINER_CLASS_LEADER", "TRAINER_CLASS_LEADER_FRLG", "TRAINER_CLASS_LEADER_HNS",
               "TRAINER_CLASS_LEADER_KANTO_HNS"),
    "e4": ("TRAINER_CLASS_ELITE_FOUR", "TRAINER_CLASS_ELITE_FOUR_FRLG", "TRAINER_CLASS_ELITE_FOUR_HNS"),
    "champion": ("TRAINER_CLASS_CHAMPION", "TRAINER_CLASS_CHAMPION_FRLG", "TRAINER_CLASS_CHAMPION_HNS"),
    "rival": ("TRAINER_CLASS_RIVAL", "TRAINER_CLASS_RIVAL_EARLY_FRLG", "TRAINER_CLASS_RIVAL_LATE_FRLG",
              "TRAINER_CLASS_RIVAL_HNS"),
    "boss": ("TRAINER_CLASS_BOSS_FRLG", "TRAINER_CLASS_AQUA_LEADER", "TRAINER_CLASS_MAGMA_LEADER"),
    "admin": ("TRAINER_CLASS_ROCKET_ADMIN_HNS", "TRAINER_CLASS_AQUA_ADMIN", "TRAINER_CLASS_MAGMA_ADMIN"),
    "grunt": ("TRAINER_CLASS_TEAM_ROCKET_FRLG", "TRAINER_CLASS_TEAM_ROCKET_HNS", "TRAINER_CLASS_TEAM_AQUA",
              "TRAINER_CLASS_TEAM_MAGMA"),
    "kimono": ("TRAINER_CLASS_KIMONO_GIRL_HNS",),
}
_ROLE_OF = {c: r for r, cs in ROLES.items() for c in cs}
# Classes whose battle name is the rival name the player chose (BattleStringGetOpponentName,
# src/battle_message.c), plus every trainer named {B_RIVAL_NAME}.
RIVAL_NAME_CLASSES = ("TRAINER_CLASS_RIVAL_EARLY_FRLG", "TRAINER_CLASS_RIVAL_LATE_FRLG", "TRAINER_CLASS_CHAMPION_FRLG")
# One rival person over several classes (one person per starter variant).
RIVAL_FAMILY = {"TRAINER_CLASS_RIVAL_EARLY_FRLG": "rival_kanto", "TRAINER_CLASS_RIVAL_LATE_FRLG": "rival_kanto",
                "TRAINER_CLASS_CHAMPION_FRLG": "rival_kanto", "TRAINER_CLASS_RIVAL_HNS": "rival_johto"}
STARTERS = ("BULBASAUR", "CHARMANDER", "SQUIRTLE", "CHIKORITA", "CYNDAQUIL", "TOTODILE", "TREECKO", "TORCHIC",
            "MUDKIP")
_STARTER = re.compile(r"_(%s)(?:_\d+)?(?:_HNS)?$|_(%s)_\d+_HNS$" % ("|".join(STARTERS), "|".join(STARTERS)))
REGION_ORDER = ("Kanto", "Johto", "Hoenn", "Sonder")
LEAGUE_CHANGE_SCRIPT = "PokemonLeague_EventScript_CheckLeagueChanged"
LEAGUE_CHANGE_STEP = 18   # 8 Johto badges (data/scripts/pokemon_league.inc)


class Entry:
    """One battle: const (trainer), map_id, mode ("normal"|"leader"|"phone"|"special"),
    steps (progress steps of the dynamic modes), states (title conditions of the script),
    row (rematch table row), stage ([stage index] of the row), command, opponents, partner."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Entry(%s %s %s)" % (self.const, self.map_id, self.mode)


def role_of(tr):
    return _ROLE_OF.get(tr.class_const)


def starter_of(const):
    m = _STARTER.search(const)
    return (m.group(1) or m.group(2)) if m else None


def valid_map(mid):
    m = maps.by_id(mid) if mid else None
    return m is not None and not maps.locked_mapsec(m.mapsec)


@functools.lru_cache(maxsize=None)
def league_change_maps():
    """Maps whose on-transition script asks the league-change check."""
    d = SDB.db()
    out = set()
    for ins in d.instrs:
        if ins.cmd == "call" and LEAGUE_CHANGE_SCRIPT in ins.args:
            mid = SDB.map_of_file(ins.file)
            if mid:
                out.add(mid)
    return out


@functools.lru_cache(maxsize=None)
def league_change_badges():
    """Johto badges the league-change check asks for (read from the script)."""
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


_TERMINATORS = ("goto", "end", "return", "releaseall_end")
# scratch variables carry no story state
_SCRATCH_VARS = ("VAR_0x", "VAR_RESULT", "VAR_TEMP_", "VAR_FACING", "VAR_LAST_TALKED")


@functools.lru_cache(maxsize=None)
def _var_ceiling():
    """{story variable: highest value a script of an unlocked map can set} for variables
    that scripts of locked maps set as well (areas this build keeps closed)."""
    d = SDB.db()
    locked, free = {}, {}
    for ins in d.instrs:
        if ins.cmd != "setvar" or len(ins.args) < 2 or not ins.args[1].strip().isdigit():
            continue
        mid = SDB.map_of_file(ins.file)
        if mid is None or ins.args[0].startswith(_SCRATCH_VARS):
            continue
        tgt = locked if maps.locked_mapsec(maps.by_id(mid).mapsec) else free
        v = int(ins.args[1])
        tgt[ins.args[0]] = max(tgt.get(ins.args[0], 0), v)
    return {var: free.get(var, 0) for var in locked}


@functools.lru_cache(maxsize=None)
def _jump_sources():
    d = SDB.db()
    out = {}
    for i, ins in enumerate(d.instrs):
        if ins.cmd.startswith("."):
            continue
        for a in ins.args:
            if a in d.labels:
                out.setdefault(a, []).append(i)
    return out


@functools.lru_cache(maxsize=None)
def unreachable_label(label):
    """True when a script label can only be entered through a jump that needs a story
    variable value no unlocked map can set (the story of a closed area)."""
    d = SDB.db()
    idx = d.labels.get(label)
    if idx is None:
        return False
    if idx > 0 and d.instrs[idx - 1].cmd not in _TERMINATORS and not d.instrs[idx - 1].cmd.startswith("."):
        return False            # entered by falling through
    srcs = _jump_sources().get(label, [])
    if not srcs:
        return False
    ceil = _var_ceiling()
    for i in srcs:
        ins = d.instrs[i]
        if ins.cmd in ("goto_if_ge", "goto_if_eq", "goto_if_gt", "call_if_ge", "call_if_eq", "call_if_gt") \
                and len(ins.args) >= 3 and ins.args[0] in ceil and ins.args[1].strip().isdigit():
            n = int(ins.args[1])
            top = ceil[ins.args[0]]
            if (ins.cmd.endswith("_gt") and n >= top) or (not ins.cmd.endswith("_gt") and n > top):
                continue
        return False
    return True


# ------------------------------------------------------------------ reachability
_SCRIPT_NAME = re.compile(r"\b[A-Za-z]\w*(?:EventScript|Script)\w*\b")
_WALK_STOP = ("end", "return", "releaseall_end")


@functools.lru_cache(maxsize=None)
def _reached():
    """bytearray: 1 for every script instruction the build can run.

    Roots: the scripts named by the events of the active maps (map.json), every label a
    data table names (map script tables, standard scripts) and every script label the C
    sources name. From there the walk follows each label an instruction names; an
    unconditional goto, end and return stop the straight run. What is left over is code
    behind an unconditional jump or a script nobody calls (for example the Hoenn rival
    battles of the choices this game does not offer)."""
    import glob
    from gamedata import repo_path
    d = SDB.db()
    labels = d.labels
    n = len(d.instrs)
    roots = set(x for x in SDB._event_refs() if x in labels)
    for ins in d.instrs:
        if ins.cmd.startswith(".") or ins.cmd.startswith("map_script"):
            for a in ins.args:
                if a in labels:
                    roots.add(a)
    for p in sorted(glob.glob(repo_path("src", "*.c"))):
        txt = open(p, encoding="utf-8", errors="replace").read()
        if "Script" not in txt:
            continue
        for w in set(_SCRIPT_NAME.findall(txt)):
            if w in labels:
                roots.add(w)
    seen = bytearray(n)
    stack = [labels[x] for x in sorted(roots)]
    while stack:
        i = stack.pop()
        while 0 <= i < n and not seen[i]:
            seen[i] = 1
            ins = d.instrs[i]
            cmd = ins.cmd
            if cmd.startswith("."):
                break
            tg = [a for a in ins.args if a in labels]
            if cmd == "goto" and tg:
                i = labels[tg[-1]]
                continue
            for t in tg:
                stack.append(labels[t])
            if cmd in _WALK_STOP:
                break
            i += 1
    return seen


def battle_index(const, file, label, command):
    """Index of the battle instruction in the script database (None: not in this build)."""
    d = SDB.db()
    start = d.labels.get(label)
    if start is None:
        return None
    for i in range(start, len(d.instrs)):
        if SDB.label_at(i) != label:
            break
        ins = d.instrs[i]
        if ins.cmd == command and const in ins.args and ins.file == file:
            return i
    return None


def battle_reachable(const, file, label, command):
    i = battle_index(const, file, label, command)
    return i is not None and bool(_reached()[i])


_TITLE_JUMPS = ("goto_if_set", "goto_if_unset", "call_if_set", "call_if_unset")


def _merge(base, over):
    """State tuple `base` with the decided values of `over` on top."""
    return tuple(o if o is not None else b for b, o in zip(base, over))


def _back(idx, depth, seen):
    """Title-flag states that hold when the script arrives at instruction idx: the tests on
    the way inside its label, then the jumps that lead to the label (4 levels up)."""
    d = SDB.db()
    label = SDB.label_at(idx)
    start = d.labels.get(label, idx)
    here = [None, None, None]
    for i in range(idx - 1, start - 1, -1):
        ins = d.instrs[i]
        if ins.cmd in ("goto_if_set", "goto_if_unset") and ins.args and ins.args[0] in SDB.TITLE_FLAGS:
            k = SDB.TITLE_FLAGS.index(ins.args[0])
            if here[k] is None:
                here[k] = ins.cmd.endswith("_unset")     # not jumped away
    here = tuple(here)
    if depth >= 4 or label in seen:
        return {here}
    srcs = [i for i in _jump_sources().get(label, []) if d.instrs[i].cmd != "trainerbattle"]
    falls = start > 0 and d.instrs[start - 1].cmd not in _TERMINATORS and not d.instrs[start - 1].cmd.startswith(".")
    if not srcs and not falls:
        return {here}
    out = set()
    if falls:
        for st in _back(start, depth + 1, seen | {label}) if SDB.label_at(start - 1) != label else {(None,) * 3}:
            out.add(_merge(st, here))
    for i in srcs:
        ins = d.instrs[i]
        own = [None, None, None]
        if ins.cmd in _TITLE_JUMPS and ins.args and ins.args[0] in SDB.TITLE_FLAGS:
            own[SDB.TITLE_FLAGS.index(ins.args[0])] = ins.cmd.endswith("_set")
        for st in _back(i, depth + 1, seen | {label}):
            out.add(_merge(_merge(st, tuple(own)), here))
    return out


@functools.lru_cache(maxsize=None)
def back_states(const, label):
    """States (title flags, leader flag False) of a battle the forward walk of the data
    layer does not reach (rooms entered through a map script table): read backwards from
    the battle command."""
    d = SDB.db()
    start = d.labels.get(label)
    if start is None:
        return frozenset()
    idx = None
    for i in range(start, min(start + 400, len(d.instrs))):
        ins = d.instrs[i]
        if i > start and SDB.label_at(i) != label:
            break
        if ins.cmd.startswith("trainerbattle") and const in ins.args:
            idx = i
            break
    if idx is None:
        return frozenset()
    sts = {st + (False,) for st in _back(idx, 0, frozenset())}
    if all(st[:3] == (None, None, None) for st in sts):
        return frozenset()
    return frozenset(sts)


@functools.lru_cache(maxsize=None)
def entries():
    """[Entry] of every battle on an active, unlocked map."""
    allt = T.all_trainers()
    order = {c: i for i, c in enumerate(allt)}
    rows = T.rematch_rows()
    in_row = {}
    for r in rows:
        for c in r.trainer_consts:
            in_row.setdefault(c, r)
    out = []
    seen = set()
    seen_sig = set()
    lc_maps = league_change_maps()
    for const, tr in allt.items():
        for b in T.battles(const):
            if not valid_map(b.map_id) or b.rematch_row:
                continue
            row = in_row.get(const)
            if row and b.command in T.REMATCH_COMMANDS and row.trainer_consts[0] == const:
                continue   # the rematch call: handled through the row below
            key = (const, b.map_id, b.label)
            if key in seen:
                continue
            seen.add(key)
            if b.label and unreachable_label(b.label):
                continue
            if not battle_reachable(const, b.file, b.label, b.command):
                continue
            states = SDB.states_for(const, b.file, b.label)
            if not states:
                states = back_states(const, b.label)
            sig = (const, b.map_id, tuple(sorted(states, key=repr)))
            if sig in seen_sig:
                continue   # the same battle offered by two scripts of the map
            seen_sig.add(sig)
            mode, steps = "normal", None
            if T.is_kanto_leader_class(tr) and any(st[3] for st in states):
                mode = "leader"
                lo = LEAGUE_CHANGE_STEP if b.map_id in lc_maps else 0
                steps = SDB.title_steps([st for st in states if st[3]], lo=lo)
            elif T.is_league_rematch(const):
                mode = "leader"            # league rematch teams and Red: possible from the Johto title on
                steps = list(range(levels.TITLE_STEPS[1], levels.TITLE_STEPS[2] + 1))
            out.append(Entry(const=const, map_id=b.map_id, mode=mode, steps=steps, states=states, row=None,
                             stage=None, order=(order[const], 0), league_change=mode == "leader" and
                             b.map_id in lc_maps, file=b.file, label=b.label, command=b.command,
                             pos=SDB.db().labels.get(b.label, 0),
                             opponents=b.opponents, partner=b.partner))
    for r in rows:
        first = r.trainer_consts[0]
        calls = [b for b in T.battles(first) if b.command in T.REMATCH_COMMANDS and valid_map(b.map_id)]
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
                out.append(Entry(const=st.const, map_id=b.map_id, mode="special" if r.special else "phone",
                                 steps=steps, states=set(), row=r, stage=[x.index for x in same],
                                 order=(order.get(first, 0), st.index), league_change=False,
                                 file=b.file, label=b.label, command=b.command, opponents=(st.const,),
                                 pos=0,
                                 partner=None))
    return out


class _UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def first_step(e):
    """Earliest progress step of a battle (story order of a person's battles)."""
    if e.steps:
        return min(e.steps)
    st = SDB.title_steps(e.states) if e.states else [0]
    return st[0] if st else 0


@functools.lru_cache(maxsize=None)
def _rank():
    return ORDER.rank()


def map_rank(mid):
    m = maps.by_id(mid)
    return (_rank().get(m.mapsec, 10 ** 6), m.group_index, m.map_num)


@functools.lru_cache(maxsize=None)
def groups():
    """Persons: [[Entry]] - a rematch row, a rival per starter, or the same class name
    and trainer name at the same first map. Battles of a person in story order."""
    ents = entries()
    allt = T.all_trainers("de")      # persons are told apart by their German names in both builds
    uf = _UF()
    first_map = {}
    for e in sorted(ents, key=lambda e: e.order):
        first_map.setdefault(e.const, e.map_id)
    rows = {}
    for e in ents:
        if e.row is not None:
            rows.setdefault(e.row.index, e.row)
    for r in rows.values():
        for c in r.trainer_consts:
            if c in allt:
                uf.union(("c", c), ("row", r.index))
    for c, mid in first_map.items():
        tr = allt[c]
        st = starter_of(c)
        if st and (tr.class_const in RIVAL_FAMILY or role_of(tr) == "rival" or "RIVAL" in c
                   or c.startswith(("TRAINER_BRENDAN_", "TRAINER_MAY_"))):
            fam = RIVAL_FAMILY.get(tr.class_const, tr.class_const + "|" + tr.name)
            uf.union(("c", c), ("starter", fam, st))
        else:
            uf.union(("c", c), ("id", tr.class_name, tr.name, mid))
    comp = {}
    for e in ents:
        comp.setdefault(uf.find(("c", e.const)), []).append(e)
    out = []
    for es in comp.values():
        es.sort(key=battle_sort_key)
        # the same battle offered at several places (the rival in Rustboro City or on
        # Route 104, the interviewers on three routes): one battle, the other maps as alt_maps
        merged, seen = [], {}
        for e in es:
            e.alt_maps = []
            key = (e.const, e.mode, tuple(e.steps or ()), tuple(sorted(e.states, key=repr)))
            if e.row is None and key in seen:
                if e.map_id != seen[key].map_id and e.map_id not in seen[key].alt_maps:
                    seen[key].alt_maps.append(e.map_id)
                continue
            seen[key] = e
            merged.append(e)
        out.append(merged)
    out.sort(key=person_sort_key)
    return out


def battle_sort_key(e):
    """Story order of a person's battles: progress step, then the fixed battles by level
    (rivals grow), leader battles in script order, rematch stages last in stage order."""
    if e.row is not None:
        k = (1, e.stage[0], 0)
    elif e.mode == "leader":
        k = (0, 0, e.pos)
    else:
        k = (0, 0, max_level(e))
    return (first_step(e),) + k + (e.order, map_rank(e.map_id))


def person_region(es):
    return maps.by_id(es[0].map_id).region


def person_sort_key(es):
    """Region, story order of the first battle's place, map, trainer order."""
    m = maps.by_id(es[0].map_id)
    region = m.region
    reg_i = REGION_ORDER.index(region) if region in REGION_ORDER else len(REGION_ORDER)
    host = maps.host_mapsec(es[0].map_id)
    rank = _rank()
    return (reg_i, rank.get(host, 10 ** 6), 1 if host != m.mapsec else 0, m.mapsec) + tuple(
        map_rank(es[0].map_id)) + (es[0].order,)


def missing_order_mapsecs():
    rank = _rank()
    return sorted({maps.by_id(es[0].map_id).mapsec for es in groups()} - set(rank))


def head_entry(es):
    """The entry that names the person (the first battle that is not a rematch stage)."""
    return next((e for e in es if e.row is None), es[0])


# ------------------------------------------------------------------ team helpers
def default_moves(sp, level):
    """GiveBoxMonInitialMoveset: level-up moves (level 1..level, level 0 = evolution moves
    skipped), no duplicates, the last four. Returns move ids."""
    out = []
    for lv, mv in sp.levelup:
        if lv > level:
            break
        if lv == 0:
            continue
        if mv in out:
            continue
        if len(out) < 4:
            out.append(mv)
        else:
            out = out[1:] + [mv]
    return out


def ability_of(mon, eff_species_id):
    """CreateNPCTrainerPartyWithId (abilityNum) + GetAbilityBySpecies on the fielded species.
    Returns an ability id (0: none)."""
    data_sp = SP.by_id(mon.species)
    num = 0
    if mon.ability:
        if mon.ability in data_sp.abilities:
            num = data_sp.abilities.index(mon.ability)
    eff = SP.by_id(eff_species_id)
    ab = eff.abilities[num] if num < len(eff.abilities) else 0
    if not ab and num >= 2:
        ab = next((a for a in eff.abilities[2:] if a), 0)
    if not ab:
        ab = next((a for a in eff.abilities if a), 0)
    return ab


def team_of(e):
    """trainers.Team of an entry as the game builds it."""
    tr = T.by_const(e.const)
    if e.mode == "phone":
        return T.effective_team(tr, e.map_id, "phone", steps=e.steps)
    if e.mode == "leader":
        return T.effective_team(tr, e.map_id, "leader", steps=e.steps)
    return T.effective_team(tr, e.map_id, "normal", count=T.party_count(tr, e.command))


def max_level(e):
    """Highest level of a battle (dynamic battles: the highest over the possible steps)."""
    team = team_of(e)
    lv = 0
    for m in team.mons:
        lv = max(lv, m.level if m.level is not None else m.level_range[1])
    return lv


def title_condition(e):
    """(after, before): region indexes (0 Kanto, 1 Johto, 2 Hoenn) of the latest title
    the script requires and the earliest title it excludes; None each when not tested."""
    cond = SDB.title_condition(e.states)
    after = [k for k, v in cond if v]
    before = [k for k, v in cond if not v]
    return (max(after) if after else None, min(before) if before else None)
