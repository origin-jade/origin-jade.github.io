"""Breeding rules of this build, read from include/config/pokemon.h and src/daycare.c.

    hand_breeding.cfg("P_NATURE_INHERITANCE")  -> 8 (GEN_9); hand_facts.gen() for the label
    hand_breeding.compat()          -> [(const, percent, percent with Oval Charm)]
                                       (GetDaycareCompatibilityScore, ModifyBreedingScoreForOvalCharm)
    hand_breeding.egg_check_steps() -> 256 (TryProduceEgg: (steps & 0xFF) == 0xFF)
    hand_breeding.cycle_steps()     -> steps per egg cycle (TryProduceOrHatchEgg, P_EGG_CYCLE_LENGTH)
    hand_breeding.cycle_abilities() -> [ABILITY_*] that hatch eggs twice as fast (GetEggCyclesToSubtract)
    hand_breeding.destiny_knot()    -> (normal IVs, IVs with ITEM_DESTINY_KNOT) (InheritIVs)
    hand_breeding.daycares()        -> [(map, region)] active maps whose script hands out daycare eggs
    hand_breeding.odd_egg()         -> OddEgg(map_dir, shiny_percent, rows=[(species, [words])])
                                       (Route34_DayCare_hns script, sOddEggSpecies and
                                        GiveOddEgg_Internal in src/scrcmd.c, sInterviewPasswords
                                        in src/easy_chat.c, word texts from the Easy Chat tables)

Language: daycares, odd_egg, incense_babies, special_moves, items_with_hold_effect and
compat_texts take lang="de"|"en" (None = the process language) and return the names and
texts of that build; the rules are the same in both.
"""
import functools
import glob
import re

from . import repo_path
from . import tu as TU
from . import maps
from . import species as SPECIES
from . import levels
from . import hand_facts as F

DAYCARE_C = "src/daycare.c"


def cfg(name):
    return TU.load(DAYCARE_C, lang="de").need(name)


def _body(path, sig):
    """Body of the function *definition* (a prototype `sig;` is skipped)."""
    src = open(repo_path(path), encoding="utf-8").read()
    m = re.search(re.escape(sig) + r"\s*\{", src)
    if not m:
        raise TU.DataError("%s: %s missing" % (path, sig))
    return levels._function_body(src[m.start():], sig)


def compat():
    t = TU.load(DAYCARE_C, lang="de")
    oval = dict((int(a), int(b)) for a, b in re.findall(
        r"case (\d+):\s*return (\d+);", _body(DAYCARE_C, "static u8 ModifyBreedingScoreForOvalCharm(u8 score)")))
    out = []
    for c in ("PARENTS_LOW_COMPATIBILITY", "PARENTS_MED_COMPATIBILITY", "PARENTS_MAX_COMPATIBILITY"):
        v = t.need(c)
        out.append((c, v, oval.get(v, v)))
    return out


def egg_check_steps():
    body = _body(DAYCARE_C, "static void TryProduceEgg(struct DayCare *daycare)")
    if "(daycare->mons[1].steps & 0xFF) == 0xFF" not in body:
        raise TU.DataError("TryProduceEgg: egg check interval changed")
    return 256


def cycle_steps():
    """TryProduceOrHatchEgg: 256 (<= Gen 3, Gen 7), 255 (Gen 4), 257 (Gen 5/6), 128 (Gen 8+)."""
    F.require(DAYCARE_C, r"P_EGG_CYCLE_LENGTH >= GEN_8 && daycare->stepCounter >= 128")
    g = cfg("P_EGG_CYCLE_LENGTH")
    G = lambda n: n - 1
    if g <= G(3) or g == G(7):
        return 256
    if g == G(4):
        return 255
    if g in (G(5), G(6)):
        return 257
    return 128


def cycle_abilities():
    return re.findall(r"ABILITY_\w+", _body("src/egg_hatch.c", "u8 GetEggCyclesToSubtract(void)"))


def destiny_knot():
    body = _body(DAYCARE_C, "static void InheritIVs(struct Pokemon *egg, struct DayCare *daycare)")
    a = re.search(r"u8 howManyIVs = (\d+);", body)
    b = re.search(r"ITEM_DESTINY_KNOT\)\s*howManyIVs = (\d+);", body)
    if not (a and b):
        raise TU.DataError("InheritIVs changed")
    return int(a.group(1)), int(b.group(1))


def daycares(lang=None):
    return list(_daycares(TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _daycares(lang):
    """Active maps with the Day Care man (object script *_EventScript_DaycareMan, who hands
    over the egg); each region has its own Day Care (GetRegionDaycare, src/daycare.c)."""
    F.require(DAYCARE_C, r"return GetRegionDaycare\(GetCurrentRegion\(\)\);")
    F.require("data/scripts/day_care.inc", r"special GiveEggFromDaycare")
    out = []
    for path in sorted(glob.glob(repo_path("data", "maps", "*", "map.json"))):
        if not re.search(r'"script": "\w+_EventScript_DaycareMan"', open(path, encoding="utf-8").read()):
            continue
        m = maps.by_dir(path.split("/")[-2], lang)
        if m and m.active:
            out.append(m)
    order = {"Kanto": 0, "Johto": 1, "Hoenn": 2}
    return tuple(sorted(out, key=lambda m: (order.get(m.region, 9), m.display)))


class OddEgg:
    def __init__(self, map_dir, shiny_percent, rows, level):
        self.map_dir, self.shiny_percent, self.rows, self.level = map_dir, shiny_percent, rows, level


def _ec_word(t, value, groups):
    bits = t.need("EC_MASK_BITS")
    mask = t.need("EC_MASK_INDEX")
    g, i = value >> bits, value & mask
    sym = groups.get(g)
    if not sym:
        raise TU.DataError("easy chat group %d has no word table" % g)
    entry = t.table(sym).get(i)
    if entry is None:
        raise TU.DataError("easy chat word %d/%d missing" % (g, i))
    raw = t.text_field(entry, "text")
    return F.clean(raw, t.lang, TU.written_in("src/easy_chat.c", raw, t.lang))


@functools.lru_cache(maxsize=None)
def _ec_groups():
    t = TU.load("src/easy_chat.c", lang="de")
    out = {}
    for g, entry in t.table("gEasyChatGroups").items():
        wd = dict(entry.items).get("wordData")
        if wd is None or not hasattr(wd, "items"):
            continue
        for k, v in wd.items:
            if k == "words":
                out[g] = [x for x in v if x not in ("(", ")", "&")][0]
    return out


def odd_egg(lang=None):
    return _odd_egg(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _odd_egg(lang):
    path = "data/maps/Route34_DayCare_hns/scripts.inc"
    src = F.raw(path)
    F.require(path, r"setvar VAR_0x8004, EASY_CHAT_TYPE_INTERVIEW")
    cases = dict((int(n), lbl) for n, lbl in re.findall(r"case (\d+), (\w+)", src))
    s = TU.load("src/scrcmd.c", lang="de")
    species_tab = s.array("sOddEggSpecies")
    body = _body("src/scrcmd.c", "static bool8 GiveOddEgg_Internal(u16 species, bool8 forceShiny, bool8 allow14PercentShiny)")
    shiny = re.search(r"\(Random\(\) % 100\) < (\d+)", body)
    lvl = re.search(r"CreateBoxMon\(&mon->box, species, (\d+),", body)
    if not (shiny and lvl):
        raise TU.DataError("GiveOddEgg_Internal changed")
    e = TU.load("src/easy_chat.c", lang=lang)
    pw = e.value(e.init("sInterviewPasswords"))
    groups = _ec_groups()
    names = s.names("SPECIES_")
    rows = []
    for idx, words in enumerate(pw, start=1):       # EvaluateInterviewPassword: i + 1
        lbl = cases.get(idx)
        m = lbl and re.search(r"^%s::\n\tgiveoddegg (\d+)" % re.escape(lbl), src, re.M)
        if not m:
            raise TU.DataError("%s: answer %d has no giveoddegg" % (path, idx))
        sp = SPECIES.by_id(species_tab[int(m.group(1))], lang)
        if sp is None:
            raise TU.DataError("odd egg species %s unknown" % names.get(species_tab[int(m.group(1))]))
        rows.append((sp, [_ec_word(e, w, groups) for w in words]))
    return OddEgg("Route34_DayCare_hns", int(shiny.group(1)), rows, int(lvl.group(1)))


def _table_rows(path, sym):
    src = F.raw(path)
    i = src.index(sym + "[] =")
    blk = src[i:src.index("};", i)]
    return re.findall(r"\{\s*(\w+),\s*(\w+),\s*(\w+)\s*\}", blk)


def incense_babies(lang=None):
    """sIncenseBabyTable: [(regular Species, incense Item, baby Species)]."""
    from . import items as ITEMS
    out = []
    for reg, it, baby in _table_rows(DAYCARE_C, "sIncenseBabyTable"):
        out.append((SPECIES.by_const(reg, lang), ITEMS.by_const(it, lang), SPECIES.by_const(baby, lang)))
    if not out or any(None in r for r in out):
        raise TU.DataError("sIncenseBabyTable changed")
    return out


def special_moves(lang=None):
    """sBreedingSpecialMoveItemTable: [(offspring Species, Item, Move)] (GiveMoveIfItem)."""
    from . import items as ITEMS
    from . import moves as MOVES
    out = []
    for sp, it, mv in _table_rows(DAYCARE_C, "sBreedingSpecialMoveItemTable"):
        out.append((SPECIES.by_const(sp, lang), ITEMS.by_const(it, lang), MOVES.by_const(mv, lang)))
    if not out or any(None in r for r in out):
        raise TU.DataError("sBreedingSpecialMoveItemTable changed")
    return out


def items_with_hold_effect(const, lang=None):
    """Items whose holdEffect is `const` (e.g. HOLD_EFFECT_PREVENT_EVOLVE, HOLD_EFFECT_POWER_ITEM)."""
    from . import items as ITEMS
    return [it for it in ITEMS.all_items(lang).values() if it.hold_effect == const]


def compat_texts(lang=None):
    """[(score const, daycare message)] as SetDaycareCompatibilityString picks them."""
    body = _body(DAYCARE_C, "void SetDaycareCompatibilityString(void)")
    pairs = re.findall(r"if \(relationshipScore == (PARENTS_\w+)\)\s*whichString = (\d+);", body)
    src = F.raw(DAYCARE_C)
    i = src.index("sCompatibilityMessages[] =")
    msgs = re.findall(r"(gDaycareText_\w+)", src[i:src.index("};", i)])
    return [(c, F.c_string("src/strings.c", msgs[int(n)], lang)) for c, n in pairs]
