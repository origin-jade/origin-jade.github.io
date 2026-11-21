"""Python mirror of the runtime level rules (src/level_scaling.c, LEVEL_REMAP == TRUE).

The ROM does not use the levels written in the data for Johto and Hoenn: it
remaps them on the fly (include/config/level_remap.h). Every level the site
shows goes through these functions. Each one names the C function it mirrors;
check_mirror() fails the build when those functions or their tables change,
so the docs cannot drift silently.

    levels.remap_region("MAP_VIOLET_CITY_GYM_HNS")       -> "JOHTO"   (GetRemapRegion)
    levels.remap_level("JOHTO", 8, "MAPSEC_VIOLET_CITY")  -> 47       (RemapLevel)
    levels.trainer_level(map_id, "TRAINER_CLASS_LEADER_HNS", 8) -> 47 (RemapTrainerLevel)
    levels.wild_level(map_id, 3)                          -> ...      (ScaleWildMonLevel)
    levels.static_level(level)                            -> level    (ScaleStaticMonLevel)
    levels.partner_level(map_id, level)                   -> ...      (ScalePartnerMonLevel)
    levels.band_steps()   -> [BandStep(step, region, badges, title, player_level, reachable, game_step, titles)]
                             (30 table entries; the game never is at 9 and 19, see reachable_steps())
    levels.apply_band(level, ace, step, low, high)        -> int      (ApplyRematchLevelBand)
    levels.phone_band(), levels.leader_band()             -> (low, high) offsets to P
    levels.band_party(eff_levels, eff_ace, band)          -> [(step, [levels])] for all 30 steps
    levels.scale_species(species_id, level, trainer_id, party_index, map_id, phone_rematch=False)
                                                          -> species id (ScaleTrainerMonSpecies)
    levels.trainer_evo_hash(trainer_id, party_index, step) (TrainerEvoHash)
    levels.exp_percent(map_id, receiver_level, opponent_level, has_badge3) (GetRemapExpPercent)
"""
import functools
import hashlib
import os
import re

from . import repo_path
from . import tu as TU
from . import maps

SRC = "src/level_scaling.c"
KANTO, JOHTO, HOENN, NONE = "KANTO", "JOHTO", "HOENN", "NONE"
STEPS_PER_REGION = 10  # REMATCH_BAND_STEPS_PER_REGION: badges 0-8, title

# The mirrored C functions, their exact signatures and a fingerprint of their
# bodies (comments and whitespace removed). If the C side changes, the build
# stops here: review this module against the new C code, then update the hash.
MIRRORED = {
    (SRC, "static bool32 IsFrlgKantoMap(void)"): "c93d641d2cae",
    (SRC, "static enum RemapRegion GetRemapRegion(void)"): "214925abe5e1",
    (SRC, "static u8 RemapLevel(enum RemapRegion region, u8 level)"): "3dbcfc1b2f4c",
    (SRC, "static u8 RemapTrainerLevel(const struct Trainer *trainer, u8 level)"): "89604e2ec8ca",
    (SRC, "static u32 GetRematchProgressStep(void)"): "04ff2e38646b",
    (SRC, "static u8 ApplyRematchLevelBand(u8 level, u8 ace, s32 low, s32 high)"): "edb2bfc296db",
    (SRC, "u32 GetRemapExpPercent(u8 receiverLevel, u8 opponentLevel)"): "2d5113b3c85f",
    (SRC, "u8 ScaleWildMonLevel(u8 level)"): "63496bb4e8d8",
    (SRC, "u8 ScaleStaticMonLevel(u8 level)"): "44c83068cb49",
    (SRC, "static u32 TrainerEvoHash(u16 trainerId, u8 partyIndex, u8 step)"): "2082056e35a7",
    (SRC, "u16 ScaleTrainerMonSpecies(u16 species, u8 scaledLevel, u16 trainerId, u8 partyIndex)"): "35bfc87469d8",
    (SRC, "u8 ScaleTrainerMonLevel(const struct Trainer *trainer, u16 trainerId, u8 level, u8 partyMaxLevel)"): "027c8b760a24",
    (SRC, "u8 ScalePartnerMonLevel(u8 level, u8 partyMaxLevel)"): "10e5ac21b81b",
    ("src/battle_setup.c", "bool32 IsNormalPhoneRematchBattle(u16 trainerId)"): "1e48591c4ace",
    ("src/battle_setup.c", "bool32 IsKantoLeaderRematchBattle(u16 trainerId)"): "9b4c8556676e",
}
# Every REMAP_*/REMATCH_*/LEADER_REMATCH_* constant of include/config/level_remap.h
# this module reads. A new constant there fails check_mirror() until it is handled.
CONSUMED = {
    "LEVEL_REMAP", "REMATCH_LEVEL_BAND",
    "REMAP_KANTO_FROM_LO", "REMAP_KANTO_FROM_HI", "REMAP_KANTO_TO_LO", "REMAP_KANTO_TO_HI",
    "REMAP_JOHTO_FROM_LO", "REMAP_JOHTO_FROM_HI", "REMAP_JOHTO_TO_LO", "REMAP_JOHTO_TO_HI",
    "REMAP_HOENN_FROM_LO", "REMAP_HOENN_FROM_HI", "REMAP_HOENN_TO_LO", "REMAP_HOENN_TO_HI",
    "REMAP_JOHTO_ENTRY_MIN",
    "REMATCH_BAND_BELOW", "REMATCH_BAND_ABOVE", "LEADER_REMATCH_BAND_LOW", "LEADER_REMATCH_BAND_HIGH",
    "REMATCH_BAND_PLAYER_LEVELS",
    "REMAP_EXP_KANTO_LOW_UNTIL", "REMAP_EXP_KANTO_LOW_PERCENT", "REMAP_EXP_KANTO_PERCENT",
    "REMAP_EXP_JOHTO_PERCENT", "REMAP_EXP_HOENN_PERCENT",
    "REMAP_EXP_SOFT_ABOVE", "REMAP_EXP_SOFT_ABOVE_PERCENT", "REMAP_EXP_SOFT_BELOW",
}
JOHTO_ENTRY_MAPSECS = ("MAPSEC_ROUTE_26", "MAPSEC_ROUTE_27", "MAPSEC_TOHJO_FALLS")  # IsJohtoEntryMapsec
HOENN_REMAP_EXTRA = ("MAPSEC_SOUTHERN_ISLAND", "MAPSEC_FARAWAY_ISLAND", "MAPSEC_BIRTH_ISLAND",
                     "MAPSEC_BATTLE_FRONTIER", "MAPSEC_NAVEL_ROCK")  # GetRemapRegion


class MirrorError(RuntimeError):
    pass


def _t():
    return TU.load(SRC)


def C(name):
    """A constant of level_scaling.c's TU (configs included)."""
    return _t().need(name)


def _function_body(src, signature):
    i = src.find(signature)
    if i < 0:
        return None
    j = src.index("{", i)
    depth = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[j:k + 1]
    return None


def fingerprint(body):
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    body = re.sub(r"\s+", "", body)
    return hashlib.sha1(body.encode()).hexdigest()[:12]


def current_fingerprints():
    """{(file, signature): fingerprint or None} of the mirrored C functions (first definition)."""
    srcs, out = {}, {}
    for f, sig in MIRRORED:
        if f not in srcs:
            srcs[f] = open(repo_path(f), encoding="utf-8").read()
        body = _function_body(srcs[f], sig)
        out[(f, sig)] = fingerprint(body) if body else None
    return out


@functools.lru_cache(maxsize=None)
def check_mirror():
    """Raise MirrorError when the mirrored C code or its constants changed."""
    problems = []
    for key, fp in current_fingerprints().items():
        if fp is None:
            problems.append("function missing or signature changed: %s: %s" % key)
        elif fp != MIRRORED[key]:
            problems.append("function body changed (fingerprint %s, mirrored %s): %s: %s"
                            % ((fp, MIRRORED[key]) + key))
    cfg = open(repo_path("include", "config", "level_remap.h"), encoding="utf-8").read()
    defined = set(re.findall(r"#define\s+((?:REMAP|REMATCH|LEADER_REMATCH|LEVEL_REMAP)\w*)", cfg))
    for name in sorted(defined - CONSUMED):
        problems.append("new constant in include/config/level_remap.h not handled: %s" % name)
    for name in sorted(CONSUMED - defined):
        problems.append("constant gone from include/config/level_remap.h: %s" % name)
    t = _t()
    for table in ("sJohtoCorridors", "sRematchBandPlayerLevels", "sTrainerEvoLevels", "sTrainerEvoExcluded"):
        if not t.has_symbol(table):
            problems.append("table missing: %s" % table)
    if C("LEVEL_REMAP") != 1:
        problems.append("LEVEL_REMAP is not TRUE: the docs mirror the fixed-level rules only")
    if len(band_player_levels()) != 3 * STEPS_PER_REGION:
        problems.append("REMATCH_BAND_PLAYER_LEVELS must have 30 entries")
    if problems:
        raise MirrorError("src/level_scaling.c and tools/docs/gamedata/levels.py differ:\n  "
                          + "\n  ".join(problems))
    return True


# ------------------------------------------------------------------ tables
@functools.lru_cache(maxsize=None)
def johto_corridor_mapsecs():
    t = _t()
    return [t.value(e.positional()[0]) for e in t.init("sJohtoCorridors").positional()]


@functools.lru_cache(maxsize=None)
def band_player_levels():
    return _t().array("sRematchBandPlayerLevels")


@functools.lru_cache(maxsize=None)
def trainer_evo_levels():
    t = _t()
    return {t.value(e.positional()[0]): t.value(e.positional()[1]) for e in t.init("sTrainerEvoLevels").positional()}


@functools.lru_cache(maxsize=None)
def trainer_evo_excluded():
    return set(_t().array("sTrainerEvoExcluded"))


# ------------------------------------------------------------------ regions
def is_frlg_kanto_map(map_id):
    """IsFrlgKantoMap: Kanto map section and a map group from MAP_LITTLEROOT_TOWN's on."""
    m = maps.by_id(map_id)
    v = m.mapsec_num
    if v is None or not (C("KANTO_MAPSEC_START") <= v <= C("KANTO_MAPSEC_END")):
        return False
    return m.group_index >= maps.by_id("MAP_LITTLEROOT_TOWN").group_index


def remap_region(map_id):
    """GetRemapRegion() for a battle on map_id."""
    if is_frlg_kanto_map(map_id):
        return KANTO
    m = maps.by_id(map_id)
    if m.mapsec_num in johto_corridor_mapsecs():          # FindCorridor(&sJohtoRules, ...)
        return JOHTO
    if maps.is_hoenn_mapsec(m.mapsec) or m.mapsec in HOENN_REMAP_EXTRA:
        return HOENN
    return NONE


def reader_region(map_id):
    """Region for statements to the reader: maps.Map.region for Kanto/Johto/Hoenn, else the
    level rule's region (GetRemapRegion), else "Sonder"."""
    m = maps.by_id(map_id)
    if m.region in ("Kanto", "Johto", "Hoenn"):
        return m.region
    return {KANTO: "Kanto", JOHTO: "Johto", HOENN: "Hoenn"}.get(remap_region(map_id), "Sonder")


def scaling_rules_region(map_id):
    """GetScalingRules() region for ScaleTrainerMonSpecies (no title flags needed:
    under LEVEL_REMAP the Kanto branch is handled by the caller)."""
    if is_frlg_kanto_map(map_id):
        return KANTO
    m = maps.by_id(map_id)
    if m.mapsec_num in johto_corridor_mapsecs():
        return JOHTO
    if maps.is_hoenn_mapsec(m.mapsec):
        return HOENN
    return NONE


# ------------------------------------------------------------------ levels
def _round_div(num, den):
    # C: (num >= 0 ? (num + den / 2) / den : -((-num + den / 2) / den)), integer division
    return (num + den // 2) // den if num >= 0 else -((-num + den // 2) // den)


def remap_level(region, level, mapsec=None):
    """RemapLevel(region, level); mapsec is the battle's map section (Johto entry rule)."""
    if region == KANTO:
        lo, hi, tlo, thi = C("REMAP_KANTO_FROM_LO"), C("REMAP_KANTO_FROM_HI"), C("REMAP_KANTO_TO_LO"), C("REMAP_KANTO_TO_HI")
    elif region == JOHTO:
        if mapsec in JOHTO_ENTRY_MAPSECS:
            return max(level, C("REMAP_JOHTO_ENTRY_MIN"))
        lo, hi, tlo, thi = C("REMAP_JOHTO_FROM_LO"), C("REMAP_JOHTO_FROM_HI"), C("REMAP_JOHTO_TO_LO"), C("REMAP_JOHTO_TO_HI")
    elif region == HOENN:
        lo, hi, tlo, thi = C("REMAP_HOENN_FROM_LO"), C("REMAP_HOENN_FROM_HI"), C("REMAP_HOENN_TO_LO"), C("REMAP_HOENN_TO_HI")
    else:
        return level
    if region == JOHTO and level > hi:
        # above the story range: fromHi..MAX_LEVEL -> toHi..MAX_LEVEL
        lo, tlo, hi, thi = hi, thi, C("MAX_LEVEL"), C("MAX_LEVEL")
    res = tlo + _round_div((level - lo) * (thi - tlo), hi - lo)
    return max(2, min(C("MAX_LEVEL"), res))


def trainer_level(map_id, trainer_class, level):
    """RemapTrainerLevel(trainer, level) for a battle on map_id (class: TRAINER_CLASS_* name)."""
    region = remap_region(map_id)
    mapsec = maps.by_id(map_id).mapsec
    if region == KANTO:
        if trainer_class == "TRAINER_CLASS_LEADER_KANTO_HNS":
            return remap_level(JOHTO, level, mapsec)
        return level
    if region in (JOHTO, HOENN):
        return remap_level(region, level, mapsec)
    return level


def wild_level(map_id, level):
    """ScaleWildMonLevel(level): Kanto keeps the JSON level, the rest is remapped."""
    region = remap_region(map_id)
    if region == KANTO:
        return level
    return remap_level(region, level, maps.by_id(map_id).mapsec)


@functools.lru_cache(maxsize=None)
def scripted_wild_exceptions():
    """Scripted Pokémon that do go through ScaleWildMonLevel although the rest keeps its level
    (ScaleStaticMonLevel): [(species const, data level, effective level, map id, source file)].
    Read from the C calls "SPECIES_X, [IS_HNS ? ]ScaleWildMonLevel(N)"; the map is the one whose
    scripts.inc calls the special (both are Petalburg events: StartWallyTutorialBattle,
    LoadWallyZigzagoon)."""
    import re
    from . import repo_path
    out = []
    for src, special in (("src/battle_setup.c", "StartWallyTutorialBattle"),
                         ("src/field_specials.c", "LoadWallyZigzagoon")):
        text = open(repo_path(src), encoding="utf-8").read()
        body = text[text.index("void %s(void)" % special):]
        body = body[:body.index("\n}\n")]
        m = re.search(r"(SPECIES_\w+),\s*(?:IS_HNS\s*\?\s*)?ScaleWildMonLevel\((\d+)\)", body)
        if not m:
            continue
        mid = None
        for x in sorted(maps.all_maps().values(), key=lambda x: (x.group_index, x.map_num)):
            p = repo_path("data", "maps", x.dir, "scripts.inc")
            if os.path.exists(p) and re.search(r"special\s+%s\b" % special, open(p, encoding="utf-8").read()):
                mid = x.id
                break
        if mid:
            out.append((m.group(1), int(m.group(2)), wild_level(mid, int(m.group(2))), mid, src))
    return out


def static_level(level):
    """ScaleStaticMonLevel(level): scripted encounters, gifts and roamers keep their level."""
    return level


def partner_level(map_id, level):
    """ScalePartnerMonLevel(level, partyMaxLevel) = RemapLevel(GetRemapRegion(), level)."""
    return remap_level(remap_region(map_id), level, maps.by_id(map_id).mapsec)


# ------------------------------------------------------------------ rematch band
# GetRematchProgressStep / GetBandBadgeStep: before the Kanto title the step is the
# number of Kanto badges (0-8, more than 8 count as 8); with the Kanto title it is
# 10 + Johto badges (10-18); with the Johto title 20 + Hoenn badges (20-28); with the
# Hoenn title 29. Indexes 9 and 19 of sRematchBandPlayerLevels ("title" in the table's
# comment) are never returned by the game: winning a title moves straight on to the
# next region's count. The list keeps 30 entries so that a step number is its index;
# the two unused ones carry reachable=False and game_step 10 / 20.
UNREACHABLE_STEPS = (9, 19)
# First step at which the title of each region is held (Kanto, Johto, Hoenn).
TITLE_STEPS = (10, 20, 29)


class BandStep:
    def __init__(self, step, region, badges, title, player_level, reachable=True, game_step=None, titles=0):
        self.step = step                    # 0..29 (index into sRematchBandPlayerLevels)
        self.region = region                # "Kanto" | "Johto" | "Hoenn": the region whose badges count
        self.badges = badges                # 0..8 badges of that region (8 also for more); None on a title entry
        self.title = title                  # True: the table's title entry of the region (9, 19, 29)
        self.player_level = player_level    # P the game uses in that situation
        self.reachable = reachable          # False: GetRematchProgressStep never returns this step (9, 19)
        self.game_step = step if game_step is None else game_step   # what the game returns in that situation
        self.titles = titles                # titles held at this step (0-3)

    def __repr__(self):
        return "BandStep(%d %s %s P=%d)" % (self.step, self.region, "title" if self.title else self.badges,
                                            self.player_level)


def game_step(step):
    """The step GetRematchProgressStep returns in the situation of table index `step`
    (9 -> 10 and 19 -> 20: holding a title means counting the next region's badges)."""
    return step + 1 if step in UNREACHABLE_STEPS else step


def reachable_steps():
    """The 28 step numbers the game can be at, in order."""
    return [s for s in range(3 * STEPS_PER_REGION) if s not in UNREACHABLE_STEPS]


def band_steps():
    """The 30 entries of sRematchBandPlayerLevels as progress steps (see above);
    player_level is the P of game_step. Pages iterate reachable_steps()."""
    out = []
    pl = band_player_levels()
    for r, region in enumerate(("Kanto", "Johto", "Hoenn")):
        for i in range(STEPS_PER_REGION):
            step = r * STEPS_PER_REGION + i
            title = i == STEPS_PER_REGION - 1
            g = game_step(step)
            out.append(BandStep(step, region, None if title else i, title, pl[g],
                                reachable=step not in UNREACHABLE_STEPS, game_step=g,
                                titles=sum(1 for t in TITLE_STEPS if g >= t)))
    return out


def phone_band():
    """Offsets of the phone rematch band: (-REMATCH_BAND_BELOW, -REMATCH_BAND_ABOVE)."""
    return (-C("REMATCH_BAND_BELOW"), -C("REMATCH_BAND_ABOVE"))


def leader_band():
    """Offsets of the Kanto leader rematch band: (LEADER_REMATCH_BAND_LOW, LEADER_REMATCH_BAND_HIGH)."""
    return (C("LEADER_REMATCH_BAND_LOW"), C("LEADER_REMATCH_BAND_HIGH"))


def league_band():
    """Offsets of the league rematch band (Johto league rematch teams and Red,
    IsLeagueRematchBattle): the ace is at least P + LEAGUE_REMATCH_BAND_LOW; the upper
    offset is MAX_LEVEL, which means no upper limit."""
    return (C("LEAGUE_REMATCH_BAND_LOW"), C("MAX_LEVEL"))


def apply_band(level, ace, step, low, high):
    """ApplyRematchLevelBand(level, ace, low, high) at progress step `step`
    (level, ace: the fixed levels after RemapTrainerLevel)."""
    p = band_player_levels()[game_step(step)]
    target = min(max(ace, p + low), p + high)
    return max(2, min(C("MAX_LEVEL"), target - (ace - level)))


def band_party(eff_levels, eff_ace, band):
    """[(BandStep, [level per party slot])] for all 30 steps."""
    low, high = band
    return [(s, [apply_band(lv, eff_ace, s.step, low, high) for lv in eff_levels]) for s in band_steps()]


def band_range(eff_levels, eff_ace, band, steps=None):
    """(lowest, highest) level of each party slot over the given steps (default: all)."""
    rows = band_party(eff_levels, eff_ace, band)
    if steps is not None:
        rows = [r for r in rows if r[0].step in steps]
    return [(min(r[1][i] for r in rows), max(r[1][i] for r in rows)) for i in range(len(eff_levels))]


# ------------------------------------------------------------------ species
def trainer_evo_hash(trainer_id, party_index, step):
    """TrainerEvoHash (lowbias32), u32 arithmetic."""
    h = (trainer_id | (party_index << 16) | (step << 24)) & 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 0x7FEB352D) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 0x846CA68B) & 0xFFFFFFFF
    h ^= h >> 16
    return h


def _rules(region):
    pre = {KANTO: "KANTO", JOHTO: "JOHTO", HOENN: "HOENN"}[region]
    return dict(evolve=C(pre + "_SCALING_TRAINER_EVOLVE") == 1,
                other=C(pre + "_SCALING_EVO_OTHER_LEVEL"), skip=C(pre + "_SCALING_EVO_SKIP_PERCENT"),
                enabled=C(pre + "_LEVEL_SCALING") == 1)


def scale_species(species_id, scaled_level, trainer_id, party_index, map_id, phone_rematch=False):
    """ScaleTrainerMonSpecies(species, scaledLevel, trainerId, partyIndex) on map_id.

    phone_rematch: IsNormalPhoneRematchBattle(trainerId) (a trainerbattle_rematch of a
    normal gRematchTable row). Kanto keeps the written species except for those."""
    from . import species as SP
    t = _t()
    region = scaling_rules_region(map_id)
    if region == KANTO and not phone_rematch:
        return species_id
    if region == NONE:
        return species_id
    rules = _rules(region)
    if not rules["enabled"] or not rules["evolve"]:
        return species_id
    evo_levels = trainer_evo_levels()
    excluded = trainer_evo_excluded()
    lvl_methods = (t.const("EVO_LEVEL"), t.const("EVO_LEVEL_BATTLE_ONLY"))
    other_methods = (t.const("EVO_ITEM"), t.const("EVO_TRADE"))
    for step in range(2):
        sp = SP.by_id(species_id)
        if sp is None or not sp.evolutions:
            break
        cands = []
        for e in sp.evolutions:
            if len(cands) >= 8:
                break
            if e.target in excluded:
                continue
            method = t.const(e.method) if isinstance(e.method, str) else e.method
            if method in lvl_methods:
                thr = e.param if e.param else evo_levels.get(e.target, rules["other"])
            elif method in other_methods:
                thr = evo_levels.get(e.target, rules["other"])
            else:
                continue
            if scaled_level < thr:
                continue
            if e.target not in cands:
                cands.append(e.target)
        if not cands:
            break
        h = trainer_evo_hash(trainer_id, party_index, step)
        if (h & 0xFFFF) % 100 < rules["skip"]:
            break
        species_id = cands[(h >> 16) % len(cands)]
    return species_id


# ------------------------------------------------------------------ experience
def exp_percent(map_id, receiver_level, opponent_level, has_badge3=True):
    """GetRemapExpPercent(receiverLevel, opponentLevel) on map_id (has_badge3: FLAG_BADGE03_GET)."""
    region = remap_region(map_id)
    settled = True
    if region == KANTO:
        pct = C("REMAP_EXP_KANTO_LOW_PERCENT") if receiver_level <= C("REMAP_EXP_KANTO_LOW_UNTIL") \
            else C("REMAP_EXP_KANTO_PERCENT")
        settled = has_badge3
    elif region == JOHTO:
        pct = C("REMAP_EXP_JOHTO_PERCENT")
    else:
        pct = C("REMAP_EXP_HOENN_PERCENT")
    if receiver_level > opponent_level + C("REMAP_EXP_SOFT_ABOVE"):
        pct = pct * C("REMAP_EXP_SOFT_ABOVE_PERCENT") // 100
    elif settled and receiver_level + C("REMAP_EXP_SOFT_BELOW") < opponent_level:
        pct = 100
    return pct
