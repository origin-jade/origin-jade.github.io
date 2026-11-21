#!/usr/bin/env python3
"""Check the Python mirror of the level rules against the game's C code.

    python3 -I -B tools/docs/verify/remap_check.py --dump dump_de.json [--work DIR]

The game changes levels (and trainer species) at run time: src/level_scaling.c
with include/config/level_remap.h. The docs use a Python mirror of those rules
(gamedata/levels.py, used by gamedata/trainers.py and gamedata/encounters.py).
Here the real C functions run on the PC and both sides are compared over the
complete domain:

  * every trainer battle the data layer knows (trainer x map x script command),
    all Pokemon fielded, at all 30 progress steps: level and species per slot,
    and which rule applies (phone rematch band / Kanto leader rematch band / fixed);
  * every in-game battle partner of those battles, at all 30 steps;
  * every wild table: all maps x 4 times of day x 6 areas: table chosen, time used,
    encounter rate, species, level range and effective level range of every slot;
  * the rematch band: progress step and player level of all 30 steps;
  * all levels 1..100 on every map through the trainer / wild / partner / scripted
    level functions (two trainer classes on every map, every class on one map per
    kind of map), and the experience percentage for all level pairs;
  * the hash that decides trainer evolutions, for every trainer, slot and step.

How the C side is built (nothing of the rules is typed by hand):
    remap_harness.c      state, stubs and the calling driver
    src/level_scaling.c  included as a whole
    remap_extracted.inc  functions cut verbatim from src/battle_setup.c,
                         src/wild_encounter.c, src/rtc.c, src/pokemon.c, src/difficulty.c
    remap_tables.h       tables of the compiled game from the ROM dump (rom_dump.py)

Exit status 1 if anything differs.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(DOCS))
CPPFLAGS = ["-iquote", "include", "-iquote", ".", "-Wno-trigraphs", "-DMODERN=1", "-DTESTING=0",
            "-DPOKEMON_HNS", "-std=gnu17"]
HOST_CC = os.environ.get("OJ_HOST_CC", "gcc")

# (file, first line of the definition) of what is cut out of the sources
EXTRACT = [
    ("src/battle_setup.c", "s32 TrainerIdToRematchTableId(const struct RematchTrainer *table, u16 trainerId)"),
    ("src/battle_setup.c", "bool32 IsNormalPhoneRematchBattle(u16 trainerId)"),
    ("src/battle_setup.c", "bool32 IsKantoLeaderRematchBattle(u16 trainerId)"),
    ("src/difficulty.c", "enum DifficultyLevel GetTrainerDifficultyLevel(u16 trainerId)"),
    ("src/pokemon.c", "bool32 IsSpeciesEnabled(u16 species)"),
    ("src/pokemon.c", "u16 SanitizeSpeciesId(u16 species)"),
    ("src/pokemon.c", "const struct Evolution *GetSpeciesEvolutions(u16 species)"),
    ("src/rtc.c", "enum TimeOfDay GenConfigTimeOfDay(enum TimeOfDay timeOfDay)"),
    ("src/wild_encounter.c", "u16 GetCurrentMapWildMonHeaderId(void)"),
    ("src/wild_encounter.c", "enum TimeOfDay GetTimeOfDayForEncounters(u32 headerId, enum WildPokemonArea area)"),
]
# The driver in remap_harness.c calls the rules like these lines of the game do.
CALL_SITES = [
    ("src/battle_main.c", "u8 scaledLvl = ScaleTrainerMonLevel(trainer, trainerId, partyData[monIndex].lvl, scalingPartyMaxLvl);"),
    ("src/battle_main.c", "u16 species = ScaleTrainerMonSpecies(partyData[monIndex].species, scaledLvl, trainerId, monIndex);"),
    ("src/battle_main.c", "if (trainer->party[monIndices[i]].lvl > scalingPartyMaxLvl)"),
    ("src/battle_main.c", "if (trainer->partySize > PARTY_SIZE / 2)"),
    ("src/battle_partner.c", "scaledLevels[i] = ScalePartnerMonLevel(partner->party[i].lvl, partyMaxLevel);"),
    ("src/battle_partner.c", "scaledSpecies[i] = ScaleTrainerMonSpecies(partner->party[i].species, scaledLevels[i], trainerId, i);"),
    ("src/battle_partner.c", "for (i = 0; i < 3 && i < partner->partySize; i++)"),
    ("src/wild_encounter.c", "level = ScaleWildMonLevel(ChooseWildMonLevel(wildMonInfo->wildPokemon, wildMonIndex, area));"),
    ("src/wild_encounter.c", "u8 level = ScaleWildMonLevel(ChooseWildMonLevel(wildMonInfo->wildPokemon, wildMonIndex, WILD_AREA_FISHING));"),
]
REGION_NAMES = {0: "NONE", 1: "KANTO", 2: "JOHTO", 3: "HOENN"}   # enum RemapRegion, checked below
AREAS_C = {"land": "land", "water": "water", "rock_smash": "rock_smash",
           "old_rod": "fishing", "good_rod": "fishing", "super_rod": "fishing"}


# ------------------------------------------------------------------ building the C side
def cut(repo, path, first_line):
    src = open(os.path.join(repo, path), encoding="utf-8").read()
    if first_line.startswith("#define"):
        m = re.search(r"^%s\b.*$" % re.escape(first_line), src, re.M)
        if not m:
            raise SystemExit("%s: '%s' not found" % (path, first_line))
        return m.group(0) + "\n"
    i = src.find("\n" + first_line + "\n{")
    if i < 0:
        raise SystemExit("%s: definition '%s' not found" % (path, first_line))
    j = src.index("{", i)
    depth = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return "// %s\n%s\n\n" % (path, src[i + 1:k + 1])
    raise SystemExit("%s: '%s' has no end" % (path, first_line))


def write_tables(dump, path):
    K = dump["constants"]
    o = []
    w = o.append
    w("// Tables of the compiled game (ROM dump), for the host harness.\n")
    # species: what IsSpeciesEnabled / GetSpeciesEvolutions read
    for sid, e in sorted((int(k), v) for k, v in dump["species"].items()):
        if e["evolutions"]:
            w("static const struct Evolution sEvo_%d[] = { %s { EVOLUTIONS_END } };\n" % (
                sid, " ".join("{ %d, %d, %d, NULL }," % (x["method"], x["param"], x["target"]) for x in e["evolutions"])))
    w("const struct SpeciesInfo gSpeciesInfo[NUM_SPECIES + 2] = {\n")
    for sid, e in sorted((int(k), v) for k, v in dump["species"].items()):
        w("    [%d] = { .baseHP = %d%s },\n" % (sid, e["stats"]["hp"],
                                                (", .evolutions = sEvo_%d" % sid) if e["evolutions"] else ""))
    w("};\n")
    for table, sym, dim in (("trainers", "gTrainers", "TRAINERS_COUNT"), ("partners", "gBattlePartners", "PARTNER_COUNT")):
        rows = sorted((int(k), v) for k, v in dump[table].items())
        if len(rows) != K[dim]:
            raise SystemExit("%s: %d entries in the dump, %s = %d" % (sym, len(rows), dim, K[dim]))
        for tid, e in rows:
            if e["party"]:
                w("static const struct TrainerMon s%s_%d[] = { %s };\n" % (
                    table, tid, " ".join("{ .species = %d, .lvl = %d }," % (m["species"], m["level"]) for m in e["party"])))
        w("const struct Trainer %s[DIFFICULTY_COUNT][%s] = {\n" % (sym, dim))
        for tid, e in rows:
            w("    [DIFFICULTY_NORMAL][%d] = { .trainerClass = %d, .partySize = %d%s },\n" % (
                tid, e["trainer_class"], e["party_size"], (", .party = s%s_%d" % (table, tid)) if e["party"] else ""))
        w("};\n")
    if len(dump["rematch"]) != K["REMATCH_TABLE_ENTRIES"]:
        raise SystemExit("gRematchTable: %d rows in the dump" % len(dump["rematch"]))
    w("const struct RematchTrainer gRematchTable[REMATCH_TABLE_ENTRIES] = {\n")
    for e in dump["rematch"]:
        w("    { { %s }, %d, %d },\n" % (", ".join(str(x) for x in e["trainers"]), e["group"], e["num"]))
    w("};\n")
    fields = {"land": "landMonsInfo", "water": "waterMonsInfo", "rock_smash": "rockSmashMonsInfo",
              "fishing": "fishingMonsInfo", "hidden": "hiddenMonsInfo"}
    need = {"land": K["LAND_WILD_COUNT"], "water": K["WATER_WILD_COUNT"], "rock_smash": K["ROCK_WILD_COUNT"],
            "fishing": K["FISH_WILD_COUNT"], "hidden": K.get("HIDDEN_WILD_COUNT", 0)}
    for h in dump["wild"]:
        for ti, tabs in enumerate(h["times"]):
            for area, t in tabs.items():
                if len(t["mons"]) < need[area]:
                    raise SystemExit("wild table %s has %d slots" % (t["symbol"], len(t["mons"])))
                name = "h%d_t%d_%s" % (h["index"], ti, area)
                w("static const struct WildPokemon sW_%s[] = { %s };\n" % (
                    name, " ".join("{ %d, %d, %d }," % tuple(m) for m in t["mons"])))
                w("static const struct WildPokemonInfo sI_%s = { %d, sW_%s };\n" % (name, t["rate"], name))
    w("const struct WildPokemonHeader gWildMonHeaders[] = {\n")
    for h in dump["wild"]:
        w("    { .mapGroup = %d, .mapNum = %d, .encounterTypes = {\n" % (h["group"], h["num"]))
        for ti, tabs in enumerate(h["times"]):
            if tabs:
                w("        [%d] = { %s },\n" % (ti, ", ".join(
                    ".%s = &sI_h%d_t%d_%s" % (fields[a], h["index"], ti, a) for a in sorted(tabs))))
        w("    } },\n")
    w("    { .mapGroup = MAP_GROUP(MAP_UNDEFINED), .mapNum = MAP_NUM(MAP_UNDEFINED) },\n};\n")
    with open(path, "w") as fh:
        fh.write("".join(o))


def build_harness(repo, dump, work):
    os.makedirs(work, exist_ok=True)
    problems = []
    for path, line in CALL_SITES:
        if line not in open(os.path.join(repo, path), encoding="utf-8").read():
            problems.append("%s no longer contains: %s" % (path, line))
    if problems:
        raise SystemExit("the game's call sites changed; review the driver in remap_harness.c:\n  " + "\n  ".join(problems))
    write_tables(dump, os.path.join(work, "remap_tables.h"))
    with open(os.path.join(work, "remap_extracted.inc"), "w") as fh:
        fh.write("// Cut verbatim out of the game's sources by remap_check.py.\n\n")
        for path, line in EXTRACT:
            fh.write(cut(repo, path, line))
    exe = os.path.join(work, "remap_harness")
    r = subprocess.run([HOST_CC, "-O1", "-w", *CPPFLAGS, "-I", work, os.path.join(HERE, "remap_harness.c"), "-o", exe],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("the harness does not compile:\n" + r.stderr[-6000:])
    return exe


ASSERTS = {}     # message of a game assertion that fired -> [command, ...]


def run_harness(exe, lines):
    """Results of the printing commands. A game assertion that fired during a command
    (" !message" at the end of its line) is collected in ASSERTS and cut off."""
    r = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("harness failed (%d): %s" % (r.returncode, r.stderr[-2000:]))
    out = []
    printing = [l for l in lines if l[:1] not in ("M", "P")]
    res = r.stdout.splitlines()
    if len(res) != len(printing):
        raise SystemExit("harness: %d results for %d commands" % (len(res), len(printing)))
    ctx = ""
    it = iter(res)
    for l in lines:
        if l[:1] == "M":
            ctx = l
            continue
        if l[:1] == "P":
            continue
        line = next(it)
        if " !" in line:
            line, msg = line.split(" !", 1)
            msg = re.sub(r"^.*?:\d+:_", "", msg).replace("_", " ")     # drop "file:line: "
            ASSERTS.setdefault(msg, []).append("%s / %s" % (ctx, l))
        out.append(line)
    return out


# ------------------------------------------------------------------ progress states
def state_of(step):
    """Game state of progress step 0..29 as the docs describe it: Kanto badges 0-8,
    Kanto title, Johto badges 0-8, Johto title, Hoenn badges 0-8, Hoenn title.
    -> (P command, step GetRematchProgressStep must give)"""
    r, i = divmod(step, 10)
    champ = [1 if x < r else 0 for x in range(3)]
    badges = [8 if x < r else 0 for x in range(3)]
    if i == 9:
        champ[r] = 1
        badges[r] = 8
    else:
        badges[r] = i
    return "P %d %d %d %d %d %d" % (*champ, *badges)


class Tally:
    def __init__(self):
        self.rows = []       # [name, compared, [diffs]]

    def start(self, name):
        self.cur = [name, 0, []]
        self.rows.append(self.cur)

    def eq(self, key, c_value, py_value, n=1):
        self.cur[1] += n
        if c_value != py_value:
            self.cur[2].append("%s: C %s, Python %s" % (key, c_value, py_value))
            return False
        return True

    def diff(self, text):
        self.cur[2].append(text)

    def total(self):
        return sum(len(r[2]) for r in self.rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dump", required=True, help="JSON of rom_dump.py (either language; the tables used are the same)")
    ap.add_argument("--work", default=None, help="folder for the generated C files and the harness (default: next to --dump)")
    ap.add_argument("--max", type=int, default=40, help="differences printed per section")
    a = ap.parse_args()
    dump = json.load(open(a.dump, encoding="utf-8"))
    K = dump["constants"]
    work = a.work or os.path.join(os.path.dirname(os.path.abspath(a.dump)), "remap")
    exe = build_harness(REPO, dump, work)

    sys.path.insert(0, DOCS)
    from gamedata import levels as LV, trainers as TR, encounters as EN, maps as MP

    for v, name in REGION_NAMES.items():
        src = open(os.path.join(REPO, "src/level_scaling.c"), encoding="utf-8").read()
        m = re.search(r"enum RemapRegion\s*\{([^}]*)\}", src)
        order = re.findall(r"REMAP_(\w+)", m.group(1))
        if order[v] != name:
            raise SystemExit("enum RemapRegion changed: %s" % order)
    LV.check_mirror()

    rom_maps = {(e["group"], e["num"]): e for e in dump["maps"]}
    T = Tally()

    def map_cmd(map_id):
        v = K[map_id]
        e = rom_maps[(v >> 8, v & 0xFF)]
        return "M %d %d %d" % (v >> 8, v & 0xFF, e["mapsec"])

    all_maps = sorted(MP.all_maps().values(), key=lambda m: (m.group_index, m.map_num))
    steps = LV.band_steps()

    # ---------------------------------------------------------------- 1. progress steps
    T.start("progress steps (GetRematchProgressStep, sRematchBandPlayerLevels)")
    out = run_harness(exe, [x for s in range(30) for x in (state_of(s), "S")])
    unreachable = []
    for s, line in zip(range(30), out):
        _, cstep, cp = line.split()
        T.eq("step %d %s: player level" % (s, steps[s]), int(cp), steps[s].player_level)
        T.eq("step %d %s: step the game is at" % (s, steps[s]), int(cstep), steps[s].game_step)
        T.eq("step %d %s: reachable" % (s, steps[s]), int(cstep) == s, steps[s].reachable)
        if int(cstep) != s:
            unreachable.append((s, int(cstep)))
    # badge counts above 8 before the title (C only: GetBandBadgeStep clamps)
    out = run_harness(exe, [x for b in range(9, 17) for x in ("P 0 0 0 %d 0 0" % b, "S", "P 1 0 0 8 %d 0" % b, "S")])
    clamp = sorted({int(l.split()[1]) for l in out})

    # ---------------------------------------------------------------- 2. all levels on every map
    T.start("levels 1-100 on every map (trainer, Kanto-leader class, wild, partner, scripted)")
    plain = K["TRAINER_CLASS_YOUNGSTER"] if "TRAINER_CLASS_YOUNGSTER" in K else 1
    leader = K["TRAINER_CLASS_LEADER_KANTO_HNS"]
    cmds = []
    for m in all_maps:
        cmds += [map_cmd(m.id), "A %d" % plain, "A %d" % leader]
    out = run_harness(exe, ["P 0 0 0 0 0 0"] + cmds)
    c_region = {}
    kinds = {}
    for i, m in enumerate(all_maps):
        for j, (cls, cname) in enumerate(((plain, None), (leader, "TRAINER_CLASS_LEADER_KANTO_HNS"))):
            parts = out[2 * i + j].split()
            reg = REGION_NAMES[int(parts[1])]
            vals = [tuple(int(x) for x in p.split(",")) for p in parts[2:]]
            if j == 0:
                c_region[m.id] = reg
                T.eq("%s remap region" % m.id, reg, LV.remap_region(m.id))
                kinds.setdefault((reg, tuple(v[1] for v in vals)), m.id)
            pyname = cname or dump["names"]["TRAINER_CLASS_"].get(str(plain))
            for lv, (ct, cw, cp, cs) in enumerate(vals, 1):
                T.eq("%s level %d trainer (%s)" % (m.id, lv, pyname), ct, LV.trainer_level(m.id, pyname, lv))
                if j == 0:
                    T.eq("%s level %d wild" % (m.id, lv), cw, LV.wild_level(m.id, lv))
                    T.eq("%s level %d partner" % (m.id, lv), cp, LV.partner_level(m.id, lv))
                    T.eq("%s level %d scripted" % (m.id, lv), cs, LV.static_level(lv))
    # every trainer class on one map of every kind (kind = region + how levels come out)
    T.start("levels 1-100, every trainer class, one map per kind of map")
    kind_maps = sorted(kinds.values())
    classes = sorted((int(k), v) for k, v in dump["names"]["TRAINER_CLASS_"].items() if int(k) < len(dump["trainer_classes"]))
    cmds = []
    for mid in kind_maps:
        cmds.append(map_cmd(mid))
        cmds += ["A %d" % cid for cid, _ in classes]
    out = run_harness(exe, ["P 0 0 0 0 0 0"] + cmds)
    k = 0
    for mid in kind_maps:
        for cid, cname in classes:
            vals = [int(p.split(",")[0]) for p in out[k].split()[2:]]
            k += 1
            for lv, ct in enumerate(vals, 1):
                T.eq("%s level %d trainer (%s)" % (mid, lv, cname), ct, LV.trainer_level(mid, cname, lv))

    # ---------------------------------------------------------------- 3. experience percent
    T.start("experience percent (GetRemapExpPercent), all level pairs, one map per kind")
    cmds = []
    for mid in kind_maps:
        for b3 in (0, 1):
            cmds += ["P 0 0 0 %d 0 0" % (3 if b3 else 2), map_cmd(mid), "X"]
    out = run_harness(exe, cmds)
    k = 0
    for mid in kind_maps:
        for b3 in (0, 1):
            vals = out[k].split()[1:]
            k += 1
            i = 0
            for r in range(1, 101):
                for o in range(1, 101):
                    T.eq("%s receiver %d opponent %d third badge %d" % (mid, r, o, b3), int(vals[i]),
                         LV.exp_percent(mid, r, o, bool(b3)))
                    i += 1

    # ---------------------------------------------------------------- 4. trainers
    T.start("trainer battles x 30 progress steps (level and species per slot, rule)")
    trainers = TR.all_trainers()
    battles = []          # (const, tr, battle, mode, count)
    no_map = 0
    seen = set()
    for const, tr in trainers.items():
        for b in TR.battles(const):
            if b.map_id is None:
                no_map += 1
                continue
            mode = TR.battle_mode(tr, b)
            count = TR.party_count(tr, b.command)
            key = (const, b.map_id, b.command, bool(b.leader_flag), count)
            if key in seen:
                continue
            seen.add(key)
            battles.append((const, tr, b, mode, count))
    with_battle = {x[0] for x in battles}
    cmds = []
    for s in range(30):
        cmds.append(state_of(s))
        for const, tr, b, mode, count in battles:
            cm = 1 if b.command == "trainerbattle_rematch" else 2 if b.command == "trainerbattle_rematch_double" else 0
            cmds += [map_cmd(b.map_id), "T %d %d %d %d" % (tr.id, cm, 1 if b.leader_flag else 0, count)]
    out = run_harness(exe, cmds)
    expected = {}
    slots = 0
    k = 0
    for s in range(30):
        for bi, (const, tr, b, mode, count) in enumerate(battles):
            parts = out[k].split()
            k += 1
            cphone, cleader, n = int(parts[1]), int(parts[2]), int(parts[3])
            cteam = [(int(parts[4 + 2 * i]), int(parts[5 + 2 * i])) for i in range(n)]
            if bi not in expected:
                team = TR.effective_team(tr, b.map_id, mode, count=count)
                if mode == "normal":
                    expected[bi] = [[(m.level, m.species) for m in team.mons]] * 30
                else:
                    by = {st.step: ms for st, ms in team.by_step}
                    expected[bi] = [[(m.level, m.species) for m in by[x]] for x in range(30)]
            key = "%s on %s (%s) step %d" % (const, b.map_id, b.command, s)
            cmode = "phone" if cphone else "leader" if cleader else "normal"
            T.eq(key + " rule", cmode, mode)
            T.eq(key + " team (level, species)", cteam, expected[bi][s], n=max(1, n))
            slots += n

    # ---------------------------------------------------------------- 5. partners
    T.start("battle partners x 30 progress steps")
    pairs = sorted({(b.partner, b.map_id, tr.id) for const, tr, b, mode, count in battles if b.partner})
    cmds = []
    for s in range(30):
        cmds.append(state_of(s))
        for pc, mid, opp in pairs:
            cmds += [map_cmd(mid), "Q %d %d" % (K[pc], opp)]
    out = run_harness(exe, cmds) if pairs else []
    k = 0
    for s in range(30):
        for pc, mid, opp in pairs:
            parts = out[k].split()
            k += 1
            n = int(parts[1])
            cteam = [(int(parts[2 + 2 * i]), int(parts[3 + 2 * i])) for i in range(n)]
            _, team = TR.partner_team(pc, mid)
            T.eq("%s on %s step %d" % (pc, mid, s), cteam, [(m.level, m.species) for m in team], n=max(1, n))

    # ---------------------------------------------------------------- 6. evolution hash
    T.start("trainer evolution hash (TrainerEvoHash), every trainer id, slot, step")
    cmds = ["H %d %d %d" % (tid, slot, st) for tid in range(len(dump["trainers"]) + 8) for slot in range(6) for st in range(2)]
    out = run_harness(exe, cmds)
    for c, line in zip(cmds, out):
        _, tid, slot, st = c.split()
        T.eq("hash %s" % c, int(line.split()[1]), LV.trainer_evo_hash(int(tid), int(slot), int(st)))

    # ---------------------------------------------------------------- 7. wild
    T.start("wild slots: every map x time of day x area (table, time used, rate, species, levels)")
    times = [t for t, _ in EN.times()]
    cmds = []
    for st in (0, 29):
        cmds.append(state_of(st))
        for m in all_maps:
            cmds.append(map_cmd(m.id))
            cmds += ["W %d" % K[t] for t in times]
    out = run_harness(exe, cmds)
    k = 0
    maps_with_wild = set()
    wild_slots = 0
    for st in (0, 29):
        for m in all_maps:
            for tname in times:
                line = out[k]
                k += 1
                c = {}
                if line != "W none":
                    parts = line.split()
                    i = 2
                    while i < len(parts):
                        area, tod = parts[i], int(parts[i + 1])
                        if parts[i + 2] == "-":
                            c[area] = None
                            i += 3
                            continue
                        rate = int(parts[i + 2])
                        i += 3
                        sl = []
                        while i < len(parts) and ":" in parts[i]:
                            sl.append(tuple(int(x) for x in parts[i].split(":")))
                            i += 1
                        c[area] = (tod, rate, sl)
                for area in EN.AREAS:
                    key = "%s %s %s (step %d)" % (m.id, tname, area, st)
                    tb = EN.table(m.id, area, tname)
                    ct = c.get(AREAS_C[area])
                    if tb is None and ct is None:
                        T.eq(key + " no table", None, None)
                        continue
                    if tb is None or ct is None:
                        T.diff("%s: table only in %s" % (key, "C" if tb is None else "Python"))
                        continue
                    maps_with_wild.add(m.id)
                    T.eq(key + " time used", ct[0], K[tb.used_time])
                    T.eq(key + " encounter rate", ct[1], tb.rate)
                    for s in tb.slots:
                        csl = ct[2][s.index]
                        T.eq(key + " slot %d (species, min, max, effective min, effective max)" % s.index, csl,
                             (K.get(s.species_const), s.min_level, s.max_level, s.eff_min, s.eff_max), n=5)
                        if s.species is not None and s.species != csl[0]:
                            T.diff("%s slot %d: species id %s, C %s" % (key, s.index, s.species, csl[0]))
                        if st == 0:
                            wild_slots += 1

    # ---------------------------------------------------------------- report
    print("C side: %s (host %s), tables from %s" % (os.path.relpath(exe, REPO) if exe.startswith(REPO) else exe, HOST_CC, a.dump))
    print("domain: %d trainers in the data layer, %d with a battle on a map, %d battles (trainer x map x command x party), "
          "%d fielded slots per step; %d battle sites without a map skipped; %d partner teams; "
          "%d maps, %d with wild tables, %d wild slots per pass"
          % (len(trainers), len(with_battle), len(battles), slots // 30, no_map, len(pairs), len(all_maps),
             len(maps_with_wild), wild_slots))
    for name, n, diffs in T.rows:
        print("%-88s %9d values compared, %d differences" % (name + ":", n, len(diffs)))
    print("total: %d differences" % T.total())
    print("kinds of maps (remap region by the C code): %s" % ", ".join(
        "%s e.g. %s" % (reg, mid) for (reg, _), mid in sorted(kinds.items(), key=lambda kv: kv[1])))
    if unreachable:
        print("note: GetRematchProgressStep never returns step %s: with the title it returns %s "
              "(the next region's 0 badges). The data layer models this (levels.band_steps: reachable, "
              "game_step); both are compared above."
              % (" / ".join(str(a) for a, _ in unreachable), " / ".join(str(b) for _, b in unreachable)))
    print("note: with 9-16 badges of a region before its title the C code stays at step(s) %s" % clamp)
    if ASSERTS:
        print("\n== assertions of the game's own code that fired (a development build shows its crash screen "
              "there; a release build goes on with the fallback) ==")
        tname = {t.id: c for c, t in trainers.items()}
        mname = {"%d %d" % (K[m.id] >> 8, K[m.id] & 0xFF): m.id for m in all_maps}
        for msg, where in sorted(ASSERTS.items()):
            sm = re.search(r"species: (\d+)", msg)
            if sm:
                msg += " (%s)" % dump["names"]["SPECIES_"].get(sm.group(1), "?")
            places = set()
            for w in where:
                mm = re.match(r"M (\d+ \d+) \d+ / (\w) (\d+)", w)
                if mm and mm.group(2) == "T":
                    places.add("%s on %s" % (tname.get(int(mm.group(3)), mm.group(3)), mname.get(mm.group(1), mm.group(1))))
                else:
                    places.add(w)
            print("  %s: %d commands; %s" % (msg, len(where), "; ".join(sorted(places)[:6])))
    without = sorted(set(trainers) - with_battle)
    print("note: %d trainers of the data layer have no battle on a map and are not part of this check" % len(without))
    for name, n, diffs in T.rows:
        if diffs:
            print("\n== %s: %d differences ==" % (name, len(diffs)))
            for d in diffs[:a.max]:
                print("  " + d)
            if len(diffs) > a.max:
                print("  ... %d more (use --max)" % (len(diffs) - a.max))
    sys.exit(1 if T.total() or ASSERTS else 0)


if __name__ == "__main__":
    main()
