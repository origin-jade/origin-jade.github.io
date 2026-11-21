"""What "complete" means in this build: Trainer Card stars, diplomas, the
Pokedex rewards and Oak's aides, read from the code.

    hand_completion.check_mirror()   fingerprints of the mirrored C functions (build stops on change)
    hand_completion.stars()          -> [Star(kind, const)] in the order of GetHnSTrainerStars
                                        (src/trainer_card.c); kind "flag" or "trainer"
    hand_completion.dex_required(kind) -> [Species] a dex check needs caught
        kind "kanto"  HasAllKantoMons  (src/pokedex.c)
             "johto"  HasAllJohotoMons
             "hoenn"  HasAllHoennMons
             "national" HasAllMons (the obtainable dex the game shows)
    hand_completion.dex_problems(kind) -> [str] entries the check needs but the build cannot have
    hand_completion.dex_skipped(kind)  -> [(Species, reason)] entries the check skips
    hand_completion.oak_rewards()    -> [(check, item_const, flag)] from Oak's lab script
    hand_completion.diplomas()       -> [Diploma(map_dir, check, script)] (Special_ShowDiploma callers)
    hand_completion.aides()          -> [Aide(map_dir, required, counter, item_consts)] Oak's aides in Kanto

dex_required and dex_skipped take lang="de"|"en" (None = the process language) for the
Species objects they return; everything else is the same in both builds.

Mirrors (Python ports, one line each in the functions below):
    HasAllKantoMons, HasAllJohotoMons, HasAllHoennMons, HasAllMons (src/pokedex.c),
    GetSpeciesRegion (src/region_rule_oj.c), IsSpeciesEnabled (src/pokemon.c),
    GetFrlgPokedexCount (src/birch_pc.c: VAR_0x8004 2 = Kanto count, National with the species randomizer).
"""
import functools
import re

from . import repo_path
from . import tu as TU
from . import species as SPECIES
from . import levels
from . import hand_facts as F

MIRRORED = {
    ("src/pokedex.c", "bool16 HasAllKantoMons(void)"): "e61b61e19d37",
    ("src/pokedex.c", "bool16 HasAllJohotoMons(void)"): "b62d2120c721",
    ("src/pokedex.c", "bool16 HasAllHoennMons(void)"): "cc98b8691bdb",
    ("src/pokedex.c", "bool16 HasAllMons(void)"): "ef390ce671e0",
    ("src/pokedex.c", "bool16 HasAllRegionalMons(void)"): "e0b8442e122d",
    ("src/region_rule_oj.c", "enum Region GetSpeciesRegion(u16 species)"): "7fdeda4b37ff",
    ("src/trainer_card.c", "static u8 GetHnSTrainerStars(struct TrainerCard *trainerCard)"): "dddd2fbbbaee",
    ("src/birch_pc.c", "u16 GetFrlgPokedexCount(void)"): "4582598c5049",
    ("src/diploma.c", "static void DisplayDiplomaText(void)"): "8998cfd7f61e",
}


class MirrorError(RuntimeError):
    pass


def current_fingerprints():
    out, srcs = {}, {}
    for f, sig in MIRRORED:
        if f not in srcs:
            srcs[f] = open(repo_path(f), encoding="utf-8").read()
        body = levels._function_body(srcs[f], sig)
        out[(f, sig)] = levels.fingerprint(body) if body else None
    return out


def check_mirror():
    problems = []
    for key, fp in current_fingerprints().items():
        if fp is None:
            problems.append("function missing or signature changed: %s: %s" % key)
        elif fp != MIRRORED[key]:
            problems.append("function body changed (fingerprint %s, mirrored %s): %s: %s" % ((fp, MIRRORED[key]) + key))
    if problems:
        raise MirrorError("tools/docs/gamedata/hand_completion.py no longer matches the C code:\n  "
                          + "\n  ".join(problems))
    return True


def _body(path, sig):
    return levels._function_body(open(repo_path(path), encoding="utf-8").read(), sig)


# ------------------------------------------------------------------ stars
class Star:
    def __init__(self, kind, const):
        self.kind, self.const = kind, const

    def __repr__(self):
        return "Star(%s %s)" % (self.kind, self.const)


@functools.lru_cache(maxsize=None)
def stars():
    """One star per condition in GetHnSTrainerStars, in code order."""
    body = _body("src/trainer_card.c", "static u8 GetHnSTrainerStars(struct TrainerCard *trainerCard)")
    out = []
    for m in re.finditer(r"FlagGet\(\s*(TrainerIdToFlagId\(\s*(\w+)\s*\)|\w+)\s*\)", body):
        if m.group(2):
            out.append(Star("trainer", m.group(2)))
        elif m.group(1) == "FLAG_DEFEATED_RED":      # set by Red's script after either of his teams
            out.append(Star("trainer", "TRAINER_RED_HNS"))
        else:
            out.append(Star("flag", m.group(1)))
    if len(out) != body.count("stars++"):
        raise TU.DataError("GetHnSTrainerStars: %d conditions for %d stars" % (len(out), body.count("stars++")))
    return out


# ------------------------------------------------------------------ dex checks
def _t():
    return TU.load("src/pokedex.c", lang="de")


@functools.lru_cache(maxsize=None)
def _later_regions():
    """sLaterSpeciesRegions (src/region_rule_oj.c): national number -> region constant."""
    src = F.raw("src/region_rule_oj.c")
    t = TU.load("src/region_rule_oj.c", lang="de")
    out = {}
    for nat, reg in re.findall(r"\{\s*(NATIONAL_DEX_\w+)\s*,\s*(REGION_\w+)\s*\}", src):
        out[t.need(nat)] = reg
    return out


def species_region(sp):
    """GetSpeciesRegion: Kanto up to Mew, Johto up to Celebi, Hoenn up to Deoxys,
    later numbers from sLaterSpeciesRegions, else Hoenn."""
    t = _t()
    n = sp.natdex
    if not n:
        return "REGION_NONE"
    if n <= t.need("NATIONAL_DEX_MEW"):
        return "REGION_KANTO"
    if n <= t.need("NATIONAL_DEX_CELEBI"):
        return "REGION_JOHTO"
    if n <= t.need("NATIONAL_DEX_DEOXYS"):
        return "REGION_HOENN"
    return _later_regions().get(n, "REGION_HOENN")


def _not_required(sp):
    """dexNotRequired || (isMythical && !dexForceRequired)."""
    f = SPECIES.field
    return bool(f(sp, "dexNotRequired", 0)) or (bool(f(sp, "isMythical", 0)) and not f(sp, "dexForceRequired", 0))


def _entries(kind, lang):
    """(dex number, national number, Species or None) for i = 1 .. COUNT-1, as the C loops."""
    t = _t()
    if kind == "national":
        table = [(n, sp.natdex, sp) for n, sp in SPECIES.dex("obtainable", lang)]
        count = t.need("OBTAINABLE_DEX_COUNT")
        nums = {n for n, _, _ in table}
        missing = [n for n in range(1, count) if n not in nums]
        return table + [(n, None, None) for n in missing], count
    count = t.need("%s_DEX_COUNT" % kind.upper())
    raw = SPECIES._regional("s%sToNationalOrder" % kind.capitalize(), kind.upper())
    return [(n, nat, SPECIES.by_natdex(nat, lang)) for n, nat in raw if n < count], count


@functools.lru_cache(maxsize=None)
def _check(kind, lang):
    t = _t()
    entries, count = _entries(kind, lang)
    need, problems, skipped = [], [], []
    if len(entries) != count - 1:
        problems.append("%s: %d entries, the loop reads %d" % (kind, len(entries), count - 1))
    for n, nat, sp in entries:
        if kind == "national":
            if sp is None:            # IsSpeciesEnabled: disabled species do not count
                continue
        elif kind == "kanto" and nat > t.need("NATIONAL_DEX_MEW"):
            skipped.append((sp, "later"))
            continue                  # "only the 151"
        if sp is None:
            problems.append("%s #%d (national %s): species not in this build" % (kind, n, nat))
            continue
        if kind == "johto" and species_region(sp) == "REGION_HOENN":
            skipped.append((sp, "hoenn"))
            continue                  # Johto's Hoenn species are not needed
        if _not_required(sp):
            skipped.append((sp, "mythical" if SPECIES.field(sp, "isMythical", 0) else "not_required"))
            continue
        need.append(sp)
    return need, problems, skipped


def dex_required(kind, lang=None):
    return list(_check(kind, TU.lang(lang))[0])


def dex_problems(kind):
    return list(_check(kind, "de")[1])


def dex_skipped(kind, lang=None):
    """[(Species, reason)] entries of the dex the check skips: "later" (Kanto: national number
    above Mew), "hoenn" (Johto: Hoenn species), "mythical", "not_required" (dexNotRequired)."""
    return list(_check(kind, TU.lang(lang))[2])


# ------------------------------------------------------------------ rewards
OAK_LAB = "data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc"


@functools.lru_cache(maxsize=None)
def oak_rewards():
    """[(dex check special, item const, received flag)] of
    PalletTown_ProfessorOaksLab_EventScript_TryGive*DexReward."""
    src = F.raw(OAK_LAB)
    F.require(OAK_LAB, r"^PalletTown_ProfessorOaksLab_EventScript_TryGiveDexRewards::")
    out = []
    for m in re.finditer(r"^PalletTown_ProfessorOaksLab_EventScript_TryGive(\w+)DexReward::\n(.*?)\n\treturn",
                         src, re.M | re.S):
        body = m.group(2)
        flag = re.search(r"goto_if_set (FLAG_\w+), Common_EventScript_NopReturn", body)
        check = re.search(r"specialvar VAR_RESULT, (\w+)", body)
        item = re.search(r"giveitem (ITEM_\w+)", body)
        if not (flag and check and item):
            raise TU.DataError("%s: reward script %s changed shape" % (OAK_LAB, m.group(1)))
        out.append((check.group(1), item.group(1), flag.group(1)))
    if not out:
        raise TU.DataError("%s: no dex rewards found" % OAK_LAB)
    return out


class Diploma:
    def __init__(self, map_dir, check, script):
        self.map_dir, self.check, self.script = map_dir, check, script


@functools.lru_cache(maxsize=None)
def diplomas():
    """Every map script that calls Special_ShowDiploma, with the dex check before it."""
    import glob
    out = []
    for path in sorted(glob.glob(repo_path("data", "maps", "*", "scripts.inc"))):
        src = open(path, encoding="utf-8").read()
        if "special Special_ShowDiploma" not in src:
            continue
        d = path.split("/")[-2]
        check = re.search(r"specialvar VAR_RESULT, (HasAll\w+)", src)
        out.append(Diploma(d, check.group(1) if check else None, "data/maps/%s/scripts.inc" % d))
    return out


class Aide:
    def __init__(self, map_dir, required, items, var4):
        self.map_dir, self.required, self.items, self.var4 = map_dir, required, items, var4


@functools.lru_cache(maxsize=None)
def aides():
    """Oak's aides that check the caught count (`.equ REQUIRED_*_MONS, N` +
    GetFrlgPokedexCount + goto_if_lt VAR_0x8006 = caught)."""
    import glob
    out = []
    for path in sorted(glob.glob(repo_path("data", "maps", "*", "scripts.inc"))):
        src = open(path, encoding="utf-8").read()
        m = re.match(r"\.equ (REQUIRED_\w+_MONS), (\d+)", src)
        if not m or "GetFrlgPokedexCount" not in src:
            continue
        if not re.search(r"goto_if_lt VAR_0x8006, %s," % m.group(1), src):
            raise TU.DataError("%s: aide no longer compares the caught count" % path)
        var4 = re.search(r"setvar VAR_0x8004, (\d+)\s*\n\s*specialvar VAR_RESULT, GetFrlgPokedexCount", src)
        its = re.findall(r"giveitem_msg \w+, (ITEM_\w+)", src)
        out.append(Aide(path.split("/")[-2], int(m.group(2)), its, int(var4.group(1)) if var4 else 0))
    return out


BIRCH_LAB = "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc"
HALL_OF_FAME = "data/scripts/hall_of_fame.inc"


@functools.lru_cache(maxsize=None)
def birch_johto_starter():
    """Prof. Birch's Johto starter: after the Hoenn title (Hall of Fame sets
    VAR_DEX_UPGRADE_JOHTO_STARTER_STATE to 3, IS_HNS branch) the lab checks HasAllHoennMons
    and then offers one of three species (givemon level). -> (check, [SPECIES_ consts], level)."""
    F.require(HALL_OF_FAME, r"^#if IS_HNS\n\tcall_if_eq VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 0, "
                            r"EverGrandeCity_HallOfFame_EventScript_SkipDexUpgradeEvent$")
    F.require(HALL_OF_FAME, r"^EverGrandeCity_HallOfFame_EventScript_SkipDexUpgradeEvent::\n"
                            r"\tsetvar VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 3$")
    F.require(BIRCH_LAB, r"goto_if_eq VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 3, "
                         r"LittlerootTown_ProfessorBirchsLab_EventScript_CheckReadyForJohtoStarter$")
    src = F.raw(BIRCH_LAB)
    m = re.search(r"^LittlerootTown_ProfessorBirchsLab_EventScript_CheckReadyForJohtoStarter::\n"
                  r"\tspecialvar VAR_RESULT, (HasAll\w+)\n\tgoto_if_eq VAR_RESULT, TRUE, "
                  r"LittlerootTown_ProfessorBirchsLab_EventScript_SetReadyForJohtoStarter$", src, re.M)
    if not m:
        raise TU.DataError("%s: Johto starter check changed shape" % BIRCH_LAB)
    species = []
    for c in re.findall(r"^\tsetvar VAR_TEMP_TRANSFERRED_SPECIES, (SPECIES_\w+)$", src, re.M):
        if c not in species:
            species.append(c)
    lv = re.search(r"^\tgivemon VAR_TEMP_TRANSFERRED_SPECIES, (\d+),", src, re.M)
    if not species or not lv:
        raise TU.DataError("%s: Johto starter species/level not found" % BIRCH_LAB)
    return m.group(1), species, int(lv.group(1))
