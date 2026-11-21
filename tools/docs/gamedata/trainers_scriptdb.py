"""Event scripts with resolved #if/.if branches and a small control-flow walk.

Used by the trainers and items pages (both read what the map scripts do).

    db = trainers_scriptdb.db()             # tools/oj_world.py ScriptDB: data/event_scripts.s with
                                            # every .include inlined and every #if/.if evaluated
    trainers_scriptdb.label_at(idx)         # label an instruction belongs to
    trainers_scriptdb.map_of_file(path)     # map id of data/maps/<dir>/scripts.inc (active maps only)
    trainers_scriptdb.callers(label)        # map ids whose events/scripts reach a shared label
    trainers_scriptdb.battle_states()       # {(trainer const, file, label): {State}}
    trainers_scriptdb.title_steps(states)   # progress steps (levels.band_steps) those states allow
    trainers_scriptdb.text_db("en")         # the same database with the English build's branches
    trainers_scriptdb.script_text(label, lang)      # raw text of a text label in that build
    trainers_scriptdb.script_text_clean(label, lang) # one display line (text.clean rules of the
                                            # language the text is written in)
    trainers_scriptdb.nontext_diff()        # [] when the scripts of both builds differ in text only

Language: the scripts of the two builds differ only in their .string lines (nontext_diff(),
checked by selftest), so everything about what scripts do is read from one database, db()
(German branches). Texts are read per language with script_text().

The walk follows goto/call/goto_if_*/call_if_* from every script entry
(map.json events, map_script tables, labels no script jumps to). It only
tracks the three region titles (FLAG_IS_KANTO/JOHTO/HOENN_CHAMPION) and
FLAG_TEMP_KANTO_LEADER_REMATCH, the flag IsKantoLeaderRematchBattle
(src/battle_setup.c) reads. Every other condition is taken both ways.
A State is (kanto, johto, hoenn, leader): None = not tested on the way,
True/False = the branch the script took.
"""
import functools
import os
import re
import sys

from . import repo_path
from . import maps

TITLE_FLAGS = ("FLAG_IS_KANTO_CHAMPION", "FLAG_IS_JOHTO_CHAMPION", "FLAG_IS_HOENN_CHAMPION")
LEADER_FLAG = "FLAG_TEMP_KANTO_LEADER_REMATCH"
# First progress step (levels.band_steps) at which each title is held:
# GetRematchProgressStep gives Kanto badges 0-8, with the Kanto title 10 + Johto badges,
# with the Johto title 20 + Hoenn badges, with the Hoenn title 29 (never 9 or 19).
TITLE_STEP = (10, 20, 29)
_UNREACHABLE = (9, 19)
_STOP = ("end", "return", "goto", "releaseall_end")


def _oj_world():
    tools = repo_path("tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import oj_world
    return oj_world


@functools.lru_cache(maxsize=None)
def _world():
    return _oj_world().World()


@functools.lru_cache(maxsize=None)
def text_db(lang="de"):
    """ScriptDB of one build. oj_world evaluates `#if GERMAN` with the macros of
    include/constants/global.h; for English the three language macros are set as
    -DLANG_ENGLISH sets them (GERMAN 0, ENGLISH 1, GAME_LANGUAGE LANGUAGE_ENGLISH)."""
    import copy
    if lang not in ("de", "en"):
        raise ValueError("unknown language %r" % (lang,))
    oj_world = _oj_world()
    macros = _world().macros
    if lang == "en":
        macros = copy.copy(macros)
        macros.defs = dict(macros.defs)
        macros._cache = {}
        if macros.defs.get("GERMAN") != "1" or macros.defs.get("ENGLISH") != "0":
            raise RuntimeError("include/constants/global.h: language macros changed shape")
        macros.defs.update({"GERMAN": "0", "ENGLISH": "1", "GAME_LANGUAGE": "(LANGUAGE_ENGLISH)",
                            "LANG_ENGLISH": "1"})
    return oj_world.ScriptDB(macros)


def db():
    """The database every script-logic function reads (German build; the English
    build has the same instructions apart from .string lines)."""
    return text_db("de")


def _dump(d):
    """Every instruction but the texts, with its labels."""
    starts = {}
    for name, idx in d.labels.items():
        starts.setdefault(idx, []).append(name)
    out = []
    for i, ins in enumerate(d.instrs):
        for name in sorted(starts.get(i, ())):
            out.append(name + ":")
        if ins.cmd in (".string", ".braille"):
            continue
        out.append("%s %s @ %s" % (ins.cmd, ", ".join(ins.args), ins.file))
    return out


@functools.lru_cache(maxsize=None)
def nontext_diff():
    """Script lines that differ between the German and the English build, texts
    (.string, .braille) left out: [(german, english)]; [] = text is the only difference."""
    import difflib
    a, b = _dump(text_db("de")), _dump(text_db("en"))
    if a == b:
        return []
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            out.append(("\n".join(a[i1:i2]), "\n".join(b[j1:j2])))
    return out


_STRING_LINE = re.compile(r'^\s*(?:\w+::?\s*)?\.string\s+"((?:[^"\\]|\\.)*)"')


@functools.lru_cache(maxsize=None)
def _texts(lang):
    """{label: (file, [string pieces])} of every label that is followed by .string lines.
    The pieces are read from the source line itself (ScriptDB splits arguments at commas)."""
    d = text_db(lang)
    starts = _starts_of(lang)
    files = {}
    out, cur = {}, ()
    for i, ins in enumerate(d.instrs):
        if i in starts:
            cur = starts[i]
        if ins.cmd != ".string":
            continue
        lines = files.get(ins.file)
        if lines is None:
            lines = files[ins.file] = open(repo_path(ins.file), encoding="utf-8").read().split("\n")
        m = _STRING_LINE.match(lines[ins.line - 1])
        if not m:
            continue
        for name in cur:
            out.setdefault(name, (ins.file, []))[1].append(m.group(1))
    return out


@functools.lru_cache(maxsize=None)
def _starts_of(lang):
    starts = {}
    for name, idx in text_db(lang).labels.items():
        starts.setdefault(idx, []).append(name)
    return starts


def script_text(label, lang=None):
    """Raw game text of a script text label in one build (codes \\n, \\l, \\p kept, the
    cut at the terminating $); None when the label has no text."""
    from . import tu as TU
    lang = TU.lang(lang)
    s = _script_text_build(label, lang)
    if lang == "en" and s is not None:
        from . import entext
        if entext.root():
            # the English version's wording of the same label (entext.pick: unless the
            # German text of this repository has moved on and has its own English)
            s = entext.pick("script", label, s, _script_text_build(label, "de"), entext.script_text(label))
    return s


def _script_text_build(label, lang):
    """The text of this repository's build `lang`."""
    e = _texts(lang).get(label)
    if e is None:
        return None
    # "$" ends a game string; a second, unlabelled string may follow in the file
    return "".join(e[1]).split("$", 1)[0]


def script_text_file(label):
    e = _texts("de").get(label)
    return e[0] if e else None


def script_text_lang(label, lang=None):
    """Language the text of `label` is written in in build lang ("de" when the English
    build carries the German text)."""
    from . import tu as TU
    from . import text
    lang = TU.lang(lang)
    return text.written_in(script_text(label, lang), script_text(label, "de"), lang)


def script_text_clean(label, lang=None):
    """One display line of a script text (text.clean with the rules of the language
    the text is written in)."""
    from . import text
    s = script_text(label, lang)
    return None if s is None else text.clean(s, script_text_lang(label, lang))


@functools.lru_cache(maxsize=None)
def _label_starts():
    d = db()
    starts = {}
    for name, idx in d.labels.items():
        starts.setdefault(idx, []).append(name)
    return starts


@functools.lru_cache(maxsize=None)
def _label_index():
    """label of every instruction (the last label defined at or before it)."""
    d = db()
    starts = _label_starts()
    out, cur = [], None
    for i in range(len(d.instrs)):
        if i in starts:
            cur = starts[i][-1]
        out.append(cur)
    return out


def label_at(idx):
    return _label_index()[idx]


@functools.lru_cache(maxsize=None)
def _file_maps():
    out = {}
    for m in maps.all_maps().values():
        out[os.path.join("data", "maps", m.dir, "scripts.inc")] = m.id
    return out


def map_of_file(path):
    """Map id of a map's own scripts.inc (None for shared data/scripts/*.inc)."""
    return _file_maps().get(path)


@functools.lru_cache(maxsize=None)
def _event_refs():
    """{script label: {map ids}} of every active map's object/coord/bg events."""
    refs = {}
    for m in maps.all_maps().values():
        for kind in ("object_events", "coord_events", "bg_events"):
            for o in m.data.get(kind) or []:
                s = o.get("script")
                if s and s != "0x0":
                    refs.setdefault(s, set()).add(m.id)
    return refs


def _targets(ins):
    labels = db().labels
    return [a for a in ins.args if a in labels]


@functools.lru_cache(maxsize=None)
def _jump_sources():
    """{label: [instruction index]} of instructions that name the label."""
    d = db()
    out = {}
    for i, ins in enumerate(d.instrs):
        if ins.cmd.startswith("."):
            continue
        for a in _targets(ins):
            out.setdefault(a, []).append(i)
    return out


@functools.lru_cache(maxsize=None)
def callers(label):
    """Map ids that reach `label`: map.json events naming it, scripts of a map's own
    scripts.inc that jump to it, or (recursively, 6 levels) such callers of the
    shared label that jumps to it."""
    found = set()
    seen = set()

    def walk(lb, depth):
        if lb in seen or depth > 6:
            return
        seen.add(lb)
        found.update(_event_refs().get(lb, ()))
        for i in _jump_sources().get(lb, ()):
            ins = db().instrs[i]
            mid = map_of_file(ins.file)
            if mid:
                found.add(mid)
            else:
                caller = label_at(i)
                if caller:
                    walk(caller, depth + 1)
    walk(label, 0)
    return sorted(found)


def _entries():
    d = db()
    jumped = set(_jump_sources())
    ent = set(_event_refs())
    for name in d.labels:
        if name not in jumped:
            ent.add(name)
    return sorted(x for x in ent if x in d.labels)


@functools.lru_cache(maxsize=None)
def battle_states():
    """{(trainer const, file, label): set of State} for every trainerbattle* the walk reaches."""
    d = db()
    n = len(d.instrs)
    flag_idx = {f: i for i, f in enumerate(TITLE_FLAGS)}
    out = {}
    visited = set()
    for entry in _entries():
        start = d.labels[entry]
        stack = [(start, (None, None, None, False), ())]
        while stack:
            i, st, calls = stack.pop()
            while 0 <= i < n:
                key = (i, st, calls[-1:] if calls else ())
                if key in visited:
                    break
                visited.add(key)
                ins = d.instrs[i]
                cmd = ins.cmd
                if cmd.startswith("."):
                    break
                if cmd.startswith("trainerbattle"):
                    for a in ins.args:
                        if a.startswith("TRAINER_") and not a.startswith("TRAINER_BATTLE_") and a != "TRAINER_NONE":
                            out.setdefault((a, ins.file, label_at(i)), set()).add(st)
                    for t in _targets(ins):
                        stack.append((d.labels[t], st, calls))
                    i += 1
                    continue
                if cmd in ("setflag", "clearflag") and ins.args:
                    f = ins.args[0]
                    val = cmd == "setflag"
                    if f in flag_idx:
                        s = list(st)
                        s[flag_idx[f]] = val
                        st = tuple(s)
                    elif f == LEADER_FLAG:
                        st = st[:3] + (val,)
                    i += 1
                    continue
                tg = _targets(ins)
                if cmd in ("goto_if_set", "goto_if_unset", "call_if_set", "call_if_unset") and len(ins.args) >= 2 \
                        and ins.args[0] in flag_idx and tg:
                    k = flag_idx[ins.args[0]]
                    taken = cmd.endswith("_set")
                    s_t, s_f = list(st), list(st)
                    s_t[k], s_f[k] = taken, not taken
                    if cmd.startswith("goto"):
                        stack.append((d.labels[tg[-1]], tuple(s_t), calls))
                    else:
                        stack.append((d.labels[tg[-1]], tuple(s_t), calls + (i + 1,)))
                    st = tuple(s_f)
                    i += 1
                    continue
                if cmd == "goto" and tg:
                    i = d.labels[tg[-1]]
                    continue
                if cmd == "call" and tg:
                    stack.append((d.labels[tg[-1]], st, calls + (i + 1,)))
                    break   # the return continues at i + 1
                if cmd == "return":
                    if calls:
                        i, calls = calls[-1], calls[:-1]
                        continue
                    break
                if cmd in _STOP:
                    break
                if tg and (cmd.startswith("goto") or cmd.startswith("call") or cmd == "case"):
                    if cmd.startswith("call"):
                        stack.append((d.labels[tg[-1]], st, calls + (i + 1,)))
                    else:
                        stack.append((d.labels[tg[-1]], st, calls))
                i += 1
    return out


def states_for(const, file, label):
    """States of one battle site (trainers.Battle file/label); falls back to every
    site of that trainer in the file."""
    bs = battle_states()
    if (const, file, label) in bs:
        return bs[(const, file, label)]
    out = set()
    for (c, f, _l), v in bs.items():
        if c == const and f == file:
            out |= v
    return out


def title_steps(states, lo=0, hi=29):
    """Progress steps (levels.reachable_steps: 0-8, 10-18, 20-29) a set of states allows."""
    steps = set()
    for st in states:
        for s in range(lo, hi + 1):
            if s in _UNREACHABLE:
                continue
            ok = True
            for k in range(3):
                if st[k] is not None and (s >= TITLE_STEP[k]) != st[k]:
                    ok = False
                    break
            if ok:
                steps.add(s)
    return sorted(steps)


def title_condition(states):
    """[(region index, True/False)] that hold on every path: True = after the
    region's title, False = before it."""
    if not states:
        return []
    out = []
    for k in range(3):
        vals = {st[k] for st in states}
        if len(vals) == 1 and None not in vals:
            out.append((k, vals.pop()))
    return out
