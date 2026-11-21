"""Trainers: parties (.party files), classes, pictures, battle sites, rematches
and the teams as the ROM fields them.

    tr = trainers.by_const("TRAINER_FALKNER_1_HNS")
    tr.id (402), tr.name ("Falk"), tr.class_const ("TRAINER_CLASS_LEADER_HNS"), tr.class_name ("Arenaleiter"),
    tr.money (class money factor), tr.pic ("leader_falkner_hns", file name in assets/trainer),
    tr.pic_png / tr.pic_pal (repo paths), tr.double, tr.items ([item ids]), tr.source (.party file),
    tr.mons -> [TrainerMon(species, level, item, ability, nature, moves, ivs, evs, nickname, gender, shiny)]
               ivs: always all six stats (31 where the file names none, as the build does;
               ivs_given tells whether the file has an IVs line); evs: None without EVs
    trainers.all_trainers()          -> {const: Trainer} (trainers_hns/frlg/emerald .party, file order)
    trainers.battles(const)          -> [Battle(map_id, command, file, label, leader_flag, rematch_row,
                                                opponents, partner)]
                                        where the game starts the fight (phone tiers via gRematchTable);
                                        multi battles (multi_2_vs_2 / multi_2_vs_1) name both opponents
                                        and the PARTNER_ constant
    trainers.party_count(tr, command)-> Pokémon the trainer fields (BATTLE_TYPE_TWO_OPPONENTS: 3)
    trainers.partner_team(partner_const, map_id) -> [EffMon] of the in-game partner (FillPartnerParty)
    trainers.battle_mode(tr, battle) -> "normal" | "phone" | "leader"
    trainers.rematch_rows()          -> [RematchRow(index, const, trainer_consts, map_id, special)]
    trainers.is_phone_rematch(const, command) -> bool  (IsNormalPhoneRematchBattle)
    trainers.effective_team(tr, map_id, mode="normal"|"phone"|"leader", steps=None, count=None)
        -> Team: .mons [EffMon(slot, species, level or None, level_range, data_level, mon)], .dynamic, .band
           "normal": fixed levels (RemapTrainerLevel) and species (ScaleTrainerMonSpecies);
           "phone"/"leader": the rematch band - levels depend on progress (see levels.band_*),
           .mons[i].level is None and .level_range = (min, max) over all 30 progress steps;
           .by_step = [(BandStep, [EffMon...])] gives every step exactly.
    trainers.partners()              -> {const: Trainer} of src/data/battle_partners.party
    trainers.level_span()            -> {(region, entry): (lowest, highest)} fixed levels (normal battles,
                                        unlocked maps; rematch bands not included), keys as encounters.level_span

Species, move, item, ability and class names in the .party files are
converted to constants exactly like tools/trainerproc/main.c (fprint_species,
fprint_constant) and resolved with the build's constants.

Language: all_trainers, partners, by_const, classes and class_name take lang="de"|"en"
(None = the process language). Teams are the same in both builds. Names: the .party
files may carry both languages ("Name: DE_EN(Falk, FALKNER)", resolved by cpp in the
build); English names and class names otherwise come from the tree of the English
version when one is configured (entext.py). tr.name / tr.class_name are in the site's
name style (namestyle.py), tr.name_game / tr.class_name_game as the game writes them;
tr.text_lang["name"] tells the language the name is really written in. tr.lang is the
build; tr.nature_name(mon) gives a Pokémon's nature as the game names it.
"""
import functools
import os
import re
import sys

from . import repo_path
from . import tu as TU
from . import text
from . import entext
from . import namestyle
from . import maps
from . import levels

PARTY_FILES = ("src/data/trainers_hns.party", "src/data/trainers_frlg.party", "src/data/trainers.party")
PARTNER_FILE = "src/data/battle_partners.party"
# Trainer header lines ("Name: Falk") come before the first Pokemon: "Key: value"
# with a capitalised key of words (tools/trainerproc/main.c parse_trainer).
_HEADER = re.compile(r"^([A-Z][A-Za-z ]*):\s*(.*)$")
# Language switch of the .party files (the build runs them through cpp): the macro
# DE_EN(german, english) defined at the top of a file, used in "Name:" lines.
_DE_EN_PREAMBLE = re.compile(r"^#\s*(?:ifdef\s+LANG_ENGLISH|define\s+DE_EN\(de,\s*en\)\s+(?:de|en)|else|endif)\s*$")
_DE_EN = re.compile(r"^DE_EN\(\s*(.*?)\s*,\s*([^,()]*?)\s*\)$")
REMATCH_COMMANDS = ("trainerbattle_rematch", "trainerbattle_rematch_double")
# Multi battles with an in-game partner (asm/macros/battle_frontier/battle_tower.inc):
# setmultitrainerbattle trainer1, text1, trainer2, text2, partner. multi_2_vs_2 starts
# SPECIAL_BATTLE_MULTI with BATTLE_TYPE_TWO_OPPONENTS (src/battle_special.c), multi_2_vs_1 without.
MULTI_COMMANDS = ("multi_2_vs_2", "multi_2_vs_1")
TWO_OPPONENT_COMMANDS = ("multi_2_vs_2",)
SRC = "src/battle_setup.c"   # gRematchTable, trainer ids, classes via its includes


def warn(msg):
    sys.stderr.write("trainers: %s\n" % msg)


# ------------------------------------------------------------------ trainerproc names
def constant(prefix, s):
    """fprint_constant(): PREFIX_ + upper-case letters/digits, ' dropped, every other byte '_'."""
    if s.startswith(prefix + "_"):
        return s
    out = []
    for c in s.encode("utf-8"):
        ch = chr(c)
        if "A" <= ch <= "Z" or "0" <= ch <= "9":
            out.append(ch)
        elif "a" <= ch <= "z":
            out.append(ch.upper())
        elif ch == "'":
            pass
        else:
            out.append("_")
    return prefix + "_" + ("".join(out) if out else "NONE")


def species_const(s):
    """fprint_species(): species name of a .party line -> SPECIES_ constant."""
    if s.startswith("SPECIES_"):
        return s
    out, us = [], False
    for ch in s:
        if ch.isascii() and ch.isalnum():
            if us:
                out.append("_")
            us = False
            out.append(ch.upper())
        elif ch in "'%’":
            pass
        elif ch == "♂":
            us = False
            out.append("_M")
        elif ch == "♀":
            us = False
            out.append("_F")
        elif ch == "é":
            if us:
                out.append("_")
            us = False
            out.append("E")
        else:
            us = True
    return "SPECIES_" + "".join(out)


# ------------------------------------------------------------------ objects
class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, ", ".join("%s=%r" % kv for kv in list(self.__dict__.items())[:4]))


class Trainer(Obj):
    pass


class TrainerMon(Obj):
    pass


class Battle(Obj):
    pass


class RematchRow(Obj):
    pass


class EffMon(Obj):
    pass


class Team(Obj):
    pass


def _t():
    return TU.load(SRC, lang="de")


# ------------------------------------------------------------------ .party parser
def parse_party(path):
    """{const: raw dict} of one .party file (header fields + "mons": [raw mon dicts])."""
    trainers, cur, mon = {}, None, None
    in_comment = False
    for n, raw in enumerate(open(repo_path(path), encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if in_comment:
            if "*/" in line:
                in_comment = False
            continue
        if line.lstrip().startswith("/*"):
            in_comment = "*/" not in line
            continue
        if line.startswith("#"):
            if not _DE_EN_PREAMBLE.match(line.strip()):
                warn("%s:%d: preprocessor line in .party file, not supported: %s" % (path, n, line))
            continue
        m = re.match(r"=== (\w+) ===\s*$", line)
        if m:
            cur = trainers[m.group(1)] = {"mons": [], "_line": n}
            mon = None
            continue
        if cur is None:
            continue
        if not line.strip():
            mon = None
            continue
        hm = _HEADER.match(line)
        if mon is None and not cur["mons"] and hm:
            k, v = hm.group(1).strip(), hm.group(2).strip()
            de_en = _DE_EN.match(v)
            if de_en:                       # "Name: DE_EN(Falk, FALKNER)": German, and English under "Name@en"
                v = de_en.group(1)
                cur[k + "@en"] = de_en.group(2)
            cur[k] = v
            if k == "Party Size" and v not in ("", "0"):
                warn("%s: party pools (Party Size) are not mirrored" % path)
            continue
        if mon is None:
            mon = {"moves": [], "_line": n}
            cur["mons"].append(mon)
            s = line
            if "@" in s:
                s, item = s.split("@", 1)
                mon["Item"] = item.strip()
            s = s.strip()
            g = re.search(r"\((M|F)\)\s*$", s)
            if g:
                mon["Gender"] = g.group(1)
                s = s[:g.start()].strip()
            nm = re.match(r"^(.*?)\s*\(([^()]+)\)\s*$", s)
            if nm:
                mon["Nickname"], mon["Species"] = nm.group(1).strip(), nm.group(2).strip()
            else:
                mon["Species"] = s
            continue
        if line.startswith("- "):
            mon["moves"].append(line[2:].strip())
        elif re.match(r"^\w+ Nature\s*$", line):
            mon["Nature"] = line.split()[0]
        elif ":" in line:
            k, v = line.split(":", 1)
            mon[k.strip()] = v.strip()
    return trainers


# tools/trainerproc/main.c: a Pokémon without an "IVs:" line gets default_ivs
# (31 in every stat; no .party file changes it with "#pragma trainerproc ivs"), and
# a line that names only some stats starts from the same default.
DEFAULT_IV = 31
_STAT_KEYS = ("hp", "atk", "def", "spa", "spd", "spe")


def _stats(s, default=None):
    """'12 HP / 12 Atk / ...' -> {hp, atk, def, spa, spd, spe}. Without default:
    only the stats the line names, None without a line (EVs: no line = no EVs).
    With default (IVs): every stat, the ones not named with the default."""
    if not s and default is None:
        return None
    keys = {"hp": "hp", "atk": "atk", "def": "def", "spa": "spa", "spd": "spd", "spe": "spe"}
    out = {} if default is None else {k: default for k in _STAT_KEYS}
    if not s:
        return out
    for part in s.split("/"):
        bits = part.split()
        if len(bits) == 2 and bits[1].lower() in keys:
            out[keys[bits[1].lower()]] = int(bits[0])
    return out


def _build(raw_trainers, source, lang):
    t = _t()
    classes = _classes(lang)
    classes_game = _class_names_game(lang)
    src_names = entext.trainer_names() if lang == "en" else {}
    sprites = _pics()
    out = {}
    for const, r in raw_trainers.items():
        mons = []
        # "Party Size: 0" (tools/trainerproc: .partySize = 0): the trainer fields nobody,
        # whatever is listed below it (PARTNER_DUMMY).
        listed = [] if r.get("Party Size", "").strip() == "0" else r["mons"]
        for m in listed:
            sc = species_const(m["Species"])
            sid = t.const(sc)
            if sid is None:
                warn("%s %s: unknown species %r -> %s" % (source, const, m["Species"], sc))
            mv = []
            for name in m["moves"]:
                mc = constant("MOVE", name)
                if t.const(mc) is None:
                    warn("%s %s: unknown move %r" % (source, const, name))
                mv.append(t.const(mc))
            item = t.const(constant("ITEM", m["Item"])) if m.get("Item") else 0
            ability = t.const(constant("ABILITY", m["Ability"])) if m.get("Ability") else None
            mons.append(TrainerMon(
                species=sid, species_const=sc, level=int(m.get("Level", "100")),
                item=item or 0, ability=ability, nature=m.get("Nature"), moves=mv,
                ivs=_stats(m.get("IVs"), DEFAULT_IV), ivs_given="IVs" in m,
                evs=_stats(m.get("EVs")), nickname=m.get("Nickname"),
                gender=m.get("Gender"), shiny=m.get("Shiny", "").lower() == "yes", raw=m))
        cls = constant("TRAINER_CLASS", r.get("Class", "Pkmn Trainer 1"))
        pic_const = constant("TRAINER_PIC_FRONT", r.get("Pic", ""))
        pic = sprites.get(pic_const, (None, None))
        items = [t.const(constant("ITEM", x.strip())) for x in r.get("Items", "").split("/") if x.strip()]
        # German name, and the English one where the file has it (DE_EN(Falk, FALKNER));
        # with a tree of the English version configured, its name for the same constant
        # goes through the usual rule (entext.pick).
        name_de = r.get("Name", "")
        name = r.get("Name@en", name_de) if lang == "en" else name_de
        if lang == "en" and entext.root():
            name = entext.pick("trainer.name", const, name, name_de, src_names.get(const))
        written = text.written_in(name, name_de, lang)
        out[const] = Trainer(
            const=const, id=t.const(const), name=namestyle.show(name, written, "trainer", lang), name_game=name,
            text_lang={"name": written}, class_const=cls, lang=lang,
            class_name=classes.get(cls, (None, None))[0], class_name_game=classes_game.get(cls),
            money=classes.get(cls, (None, None))[1],
            pic_const=pic_const, pic=pic_const[len("TRAINER_PIC_FRONT_"):].lower(),
            pic_png=pic[0], pic_pal=pic[1], gender=r.get("Gender"),
            double=r.get("Double Battle", "No").lower() == "yes", items=[x for x in items if x],
            music=r.get("Music"), source=source, line=r["_line"], mons=mons)
    return out


@functools.lru_cache(maxsize=None)
def _classes(lang):
    """{TRAINER_CLASS_*: (name, money factor)} from gTrainerClasses (positional:
    name, money, ball)."""
    return {c: (namestyle.show(name, written, "trainer_class", lang), money)
            for c, (name, written, money) in _classes_raw(lang).items()}


@functools.lru_cache(maxsize=None)
def _classes_raw(lang):
    """{TRAINER_CLASS_*: (name as the game shows it, language it is written in, money)}."""
    t = TU.load("src/battle_main.c", lang=lang)
    de_t = TU.load("src/battle_main.c", lang="de")
    de_table = de_t.table("gTrainerClasses")
    names = t.names("TRAINER_CLASS_")
    out = {}
    for cid, e in t.table("gTrainerClasses").items():
        pos = e.positional()
        const = names.get(cid, cid)
        raw = {"name": t.text_value(pos[0]) if pos else None}
        de_pos = de_table[cid].positional() if cid in de_table else []
        raw_de = {"name": de_t.text_value(de_pos[0]) if de_pos else None}
        if lang == "en":
            raw = entext.resolve("trainer_class", const, raw, raw_de)
        # { _("NAME") } without a money value: the member is zero in the ROM
        money = (t.value(pos[1]) if len(pos) > 1 else 0) or 0
        written = text.written_in(raw["name"], raw_de["name"], lang)
        out[const] = (text.name(raw["name"], written), written, money)
    return out


def _class_names_game(lang):
    return {c: v[0] for c, v in _classes_raw(lang).items()}


def classes(lang=None):
    """{TRAINER_CLASS_* const: (name, money factor)} of gTrainerClasses."""
    return dict(_classes(TU.lang(lang)))


def class_name(class_const, lang=None):
    """Name of a trainer class (English: in the site's name style, see namestyle.py)."""
    return _classes(TU.lang(lang)).get(class_const, (None, None))[0]


def class_name_game(class_const, lang=None):
    """Name of a trainer class exactly as the battle intro shows it."""
    return _class_names_game(TU.lang(lang)).get(class_const)


@functools.lru_cache(maxsize=None)
def _pics():
    """{TRAINER_PIC_FRONT_*: (png, pal or None)} via gTrainerSprites in src/graphics.c."""
    g = TU.load("src/graphics.c", lang="de")
    names = g.names("TRAINER_PIC_FRONT_")
    out = {}
    for pid, e in g.table("gTrainerSprites").items():
        fp = e.get("frontPic")
        pal = e.get("palette")
        pic_sym = str(g.value(fp.positional()[0])) if fp is not None else None
        pal_sym = str(g.value(pal.positional()[0])) if pal is not None else None

        def path(sym, exts):
            p = g.incbin.get(sym)
            if not p:
                return None
            for a, b in exts:
                if p.endswith(a):
                    p = p[:-len(a)] + b
            return p if os.path.exists(repo_path(p)) else None
        out[names.get(pid, pid)] = (path(pic_sym, ((".4bpp.smol", ".png"), (".4bpp.lz", ".png"), (".4bpp", ".png"))),
                                    path(pal_sym, ((".gbapal.lz", ".pal"), (".gbapal", ".pal"))))
    return out


@functools.lru_cache(maxsize=None)
def _parsed(path):
    return parse_party(path)


@functools.lru_cache(maxsize=None)
def _all_trainers(lang):
    out = {}
    for f in PARTY_FILES:
        out.update(_build(_parsed(f), f, lang))
    return out


def all_trainers(lang=None):
    return _all_trainers(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _partners(lang):
    return _build(_parsed(PARTNER_FILE), PARTNER_FILE, lang)


def partners(lang=None):
    return _partners(TU.lang(lang))


def by_const(const, lang=None):
    return all_trainers(lang).get(const)


def nature_name(mon, lang=None):
    """Name of a trainer Pokémon's nature as the game shows it (None: no nature set)."""
    from . import natures
    n = natures.by_party_name(mon.nature, lang)
    return n.name if n else None


# ------------------------------------------------------------------ battle sites
_BATTLE = re.compile(r"^\s*(trainerbattle\w*|%s)\b(.*)$" % "|".join(MULTI_COMMANDS))
_LABEL = re.compile(r"^(\w+)::?\s*$")


@functools.lru_cache(maxsize=None)
def _battle_index():
    """{trainer const: [Battle]} from active map scripts and data/scripts/*.inc.

    Map scripts give the map directly. A shared script (data/scripts/*.inc) gets
    the maps whose map.json events or scripts.inc refer to its label, directly or
    through goto/call chains of shared scripts; without any, map_id is None. Lines inside .if/#if branches are read as written."""
    out = {}
    active = maps.all_maps()

    def scan(path, map_id):
        label, flag = None, False
        found = []
        for line in open(repo_path(path), encoding="utf-8"):
            lm = _LABEL.match(line)
            if lm:
                label, flag = lm.group(1), False
                continue
            if re.match(r"\s*setflag\s+FLAG_TEMP_KANTO_LEADER_REMATCH\b", line):
                flag = True
            elif re.match(r"\s*clearflag\s+FLAG_TEMP_KANTO_LEADER_REMATCH\b", line):
                flag = False
            m = _BATTLE.match(line)
            if not m:
                continue
            opp = [tc for tc in re.findall(r"\b(TRAINER_\w+)\b", m.group(2))
                   if not tc.startswith("TRAINER_BATTLE_") and tc != "TRAINER_NONE"]
            pm = re.search(r"\b(PARTNER_\w+)\b", m.group(2)) if m.group(1) in MULTI_COMMANDS else None
            for tc in opp:
                found.append((tc, m.group(1), label, flag, tuple(opp), pm.group(1) if pm else None))
        return found

    for m in sorted(active.values(), key=lambda x: (x.group_index, x.map_num)):
        p = os.path.join("data", "maps", m.dir, "scripts.inc")
        if os.path.exists(repo_path(p)):
            for tc, cmd, label, flag, opp, partner in scan(p, m.id):
                out.setdefault(tc, []).append(Battle(map_id=m.id, command=cmd, file=p, label=label,
                                                     leader_flag=flag, rematch_row=None,
                                                     opponents=opp, partner=partner))
    # shared scripts: resolve the label's callers
    refs = {}
    for m in active.values():
        for o in m.data.get("object_events") or []:
            if o.get("script"):
                refs.setdefault(o["script"], set()).add(m.id)
        for kind in ("coord_events", "bg_events"):
            for o in m.data.get(kind) or []:
                if o.get("script"):
                    refs.setdefault(o["script"], set()).add(m.id)
        p = repo_path("data", "maps", m.dir, "scripts.inc")
        if os.path.exists(p):
            for word in set(re.findall(r"\b\w+\b", open(p, encoding="utf-8").read())):
                refs.setdefault(word, set()).add(m.id)
    sdir = repo_path("data", "scripts")
    shared = [os.path.join("data", "scripts", f) for f in sorted(os.listdir(sdir)) if f.endswith(".inc")]
    # label -> labels of shared scripts whose body names it (goto/call chains)
    callers = {}
    for p in shared:
        cur = None
        for line in open(repo_path(p), encoding="utf-8"):
            lm = _LABEL.match(line)
            if lm:
                cur = lm.group(1)
                continue
            if cur:
                for word in re.findall(r"\b[A-Za-z_]\w*_EventScript_\w+\b|\b[A-Z]\w*Script\w*\b", line):
                    callers.setdefault(word, set()).add(cur)

    def maps_of(label, depth=0, seen=None):
        seen = seen or set()
        if label in seen or depth > 5:
            return set()
        seen.add(label)
        found = set(refs.get(label, ()))
        if not found:
            for c in sorted(callers.get(label, ())):
                found |= maps_of(c, depth + 1, seen)
        return found

    for p in shared:
        for tc, cmd, label, flag, opp, partner in scan(p, None):
            where = sorted(maps_of(label)) or [None]
            for mid in where:
                out.setdefault(tc, []).append(Battle(map_id=mid, command=cmd, file=p, label=label,
                                                     leader_flag=flag, rematch_row=None,
                                                     opponents=opp, partner=partner))
    # Phone rematches name the row's first trainer; the game fields the tier
    # (gRematchTable). Every tier gets the battle sites of that call.
    for row in rematch_rows():
        if row.special:
            continue
        calls = [b for b in out.get(row.trainer_consts[0], []) if b.command in REMATCH_COMMANDS]
        for tc in row.trainer_consts:
            have = {(b.map_id, b.command, b.label) for b in out.get(tc, [])}
            for b in calls:
                if (b.map_id, b.command, b.label) not in have:
                    out.setdefault(tc, []).append(Battle(map_id=b.map_id, command=b.command, file=b.file,
                                                         label=b.label, leader_flag=False, rematch_row=row.const,
                                                         opponents=(tc,), partner=None))
                    have.add((b.map_id, b.command, b.label))
    return out


def battles(const):
    return list(_battle_index().get(const, []))


# ------------------------------------------------------------------ rematches
@functools.lru_cache(maxsize=None)
def rematch_rows():
    t = _t()
    names = t.names("REMATCH_")
    # Trainer ids are #defines that share their prefix with many other families
    # (TRAINER_ENCOUNTER_MUSIC_*, TRAINER_TOWER_FUNC_*): the names are the ones of the
    # .party files; ids nobody has a party for keep the first plain TRAINER_ define.
    tnames = dict(t.canonical("TRAINER_"))
    for c in all_trainers("de"):
        v = t.const(c)
        if v is not None:
            tnames[v] = c
    special = t.need("REMATCH_SPECIAL_TRAINER_START")
    rows = []
    for idx, e in sorted(t.table("gRematchTable").items()):
        ids = t.field(e, "trainerIds", [])
        g, n = t.field(e, "mapGroup"), t.field(e, "mapNum")
        mp = maps.by_group_num(g, n)
        rows.append(RematchRow(index=idx, const=names.get(idx, idx),
                               trainer_consts=[tnames.get(x, x) for x in ids],
                               map_id=mp.id if mp else None, special=idx >= special))
    return rows


@functools.lru_cache(maxsize=None)
def _normal_rematch_trainers():
    s = set()
    for r in rematch_rows():
        if not r.special:
            s.update(r.trainer_consts)
    return s


def is_phone_rematch(const, command):
    """IsNormalPhoneRematchBattle: a trainerbattle_rematch(_double) against a trainer
    of a gRematchTable row below REMATCH_SPECIAL_TRAINER_START."""
    return command in REMATCH_COMMANDS and const in _normal_rematch_trainers()


def battle_mode(tr, battle):
    """"phone" (IsNormalPhoneRematchBattle), "leader" (IsKantoLeaderRematchBattle:
    script set FLAG_TEMP_KANTO_LEADER_REMATCH and class LEADER_KANTO_HNS) or "normal"."""
    if is_phone_rematch(tr.const, battle.command):
        return "phone"
    if battle.leader_flag and is_kanto_leader_class(tr):
        return "leader"
    if is_league_rematch(tr.const):
        return "leader"
    return "normal"


@functools.lru_cache(maxsize=None)
def _league_rematch_consts():
    """Trainer constants of IsLeagueRematchBattle (src/battle_setup.c): the Johto league
    rematch teams and Red. Their levels follow the player's progress without an upper limit."""
    src = open(repo_path("src", "battle_setup.c"), encoding="utf-8").read()
    m = re.search(r"bool32 IsLeagueRematchBattle\(u16 trainerId\)\s*\{(.*?)\n\}", src, re.S)
    return frozenset(re.findall(r"case (TRAINER_\w+):", m.group(1))) if m else frozenset()


def is_league_rematch(const):
    return const in _league_rematch_consts()


def is_kanto_leader_class(tr):
    """IsKantoLeaderRematchBattle needs the class TRAINER_CLASS_LEADER_KANTO_HNS and
    the script flag FLAG_TEMP_KANTO_LEADER_REMATCH (set by the gym scripts)."""
    return tr.class_const == "TRAINER_CLASS_LEADER_KANTO_HNS"


# ------------------------------------------------------------------ effective teams
def party_count(tr, command):
    """CreateNPCTrainerPartyWithId: with BATTLE_TYPE_TWO_OPPONENTS a trainer fields at most
    PARTY_SIZE / 2 Pokémon (the first ones of the data), otherwise the whole party."""
    if command in TWO_OPPONENT_COMMANDS:
        return min(len(tr.mons), _t().need("PARTY_SIZE") // 2)
    return len(tr.mons)


def partner_team(partner_const, map_id):
    """FillPartnerParty (src/battle_partner.c): the first 3 Pokémon of the partner, level
    ScalePartnerMonLevel (= RemapLevel of the battle's region), species ScaleTrainerMonSpecies
    with trainerId TRAINER_PARTNER(partner) = MAX_TRAINERS_COUNT + partner."""
    p = partners().get(partner_const)
    if p is None:
        return None, []
    t = _t()
    tid = t.need("MAX_TRAINERS_COUNT") + t.need(partner_const)
    out = []
    for i, m in enumerate(p.mons[:3]):
        lv = levels.partner_level(map_id, m.level)
        sp = levels.scale_species(m.species, lv, tid, i, map_id)
        out.append(EffMon(slot=i, species=sp, level=lv, level_range=(lv, lv), data_level=m.level, mon=m))
    return p, out


def effective_team(tr, map_id, mode="normal", steps=None, count=None):
    """The team as the ROM builds it for a battle on map_id.

    mode: "normal", "phone" or "leader" (battle_mode()). steps: the progress steps
    (levels.band_steps()) at which this battle can happen; default all 30. Pages
    should pass the reachable ones (a Kanto leader rematch only after the Johto
    title, for example) so the shown range is honest.

    count: Pokémon fielded (party_count(); default the whole party) - the first ones.

    Mirrors ScaleTrainerMonLevel (RemapTrainerLevel, ApplyRematchLevelBand) and
    ScaleTrainerMonSpecies of src/level_scaling.c (see levels.py)."""
    levels.check_mirror()
    party = tr.mons if count is None else tr.mons[:count]
    data_levels = [m.level for m in party]
    party_max = max(data_levels) if data_levels else 0
    eff = [levels.trainer_level(map_id, tr.class_const, lv) for lv in data_levels]
    eff_ace = levels.trainer_level(map_id, tr.class_const, party_max)
    phone = mode == "phone"

    def mons_at(lvls):
        out = []
        for i, (m, lv) in enumerate(zip(party, lvls)):
            sp = levels.scale_species(m.species, lv, tr.id, i, map_id, phone_rematch=phone)
            out.append(EffMon(slot=i, species=sp, level=lv, level_range=(lv, lv), data_level=m.level, mon=m))
        return out

    if mode == "normal":
        return Team(mons=mons_at(eff), dynamic=False, band=None, by_step=None, region=levels.remap_region(map_id))
    if phone:
        band = levels.phone_band()
    elif is_league_rematch(tr.const):
        band = levels.league_band()
    else:
        band = levels.leader_band()
    by_step = [(s, mons_at(lv)) for s, lv in levels.band_party(eff, eff_ace, band)
               if steps is None or s.step in steps]
    rng = levels.band_range(eff, eff_ace, band, steps)
    mons = []
    for i, m in enumerate(party):
        species_seen = []
        for _, ms in by_step:
            if ms[i].species not in species_seen:
                species_seen.append(ms[i].species)
        mons.append(EffMon(slot=i, species=species_seen[0] if len(species_seen) == 1 else None,
                           species_options=species_seen, level=None, level_range=rng[i],
                           data_level=m.level, mon=m))
    return Team(mons=mons, dynamic=True, band=band, by_step=by_step, region=levels.remap_region(map_id))


@functools.lru_cache(maxsize=None)
def level_span():
    out = {}
    for const, tr in all_trainers().items():
        for b in battles(const):
            m = maps.by_id(b.map_id) if b.map_id else None
            if m is None or maps.locked_mapsec(m.mapsec) or b.rematch_row or is_phone_rematch(const, b.command):
                continue
            if b.leader_flag and is_kanto_leader_class(tr):
                continue
            key = (levels.reader_region(m.id), m.mapsec in levels.JOHTO_ENTRY_MAPSECS)
            for em in effective_team(tr, b.map_id, "normal", count=party_count(tr, b.command)).mons:
                lo, hi = out.get(key, (10 ** 6, 0))
                out[key] = (min(lo, em.level), max(hi, em.level))
    return out
