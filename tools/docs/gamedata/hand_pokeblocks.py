"""Berries, Pokeblock colours and the Safari Zone feeder, read from the code.

    hand_pokeblocks.flavors()   -> [(FLAVOR_* const, word)] (gText_Spicy2 ... in src/strings.c)
    hand_pokeblocks.berries()   -> [Berry(item, flavors{const: n}, smoothness)] (gBerries, src/berry.c)
    hand_pokeblocks.colors()    -> [Color(const, slug, name)] (gPokeblockNames, src/pokeblock.c)
    hand_pokeblocks.icon(color) -> PIL image of the block in that colour
                                   (graphics/pokeblock/pokeblock.png + <colour>.pal)
    hand_pokeblocks.color_rules() -> facts of the blender's colour decision
                                   (src/berry_blender.c, the function returning PBLOCK_CLR_*)
    hand_pokeblocks.feeder()    -> Feeder(steps, feeders, whole_map, nature_percent, iv_sets, gold_sets,
                                          perfect, gold_perfect) (src/safari_zone.c, src/wild_encounter.c:
                                          TryApplyPokeblockBonus, PickWildMonNature)
    hand_pokeblocks.natures()   -> [(nature name, liked flavor const, disliked flavor const)]
                                   (gPokeblockFlavorCompatibilityTable, gNaturesInfo)

Language: flavors, berries, colors and natures take lang="de"|"en" (None = the process
language) and return the names of that build; the rules (color_rules, feeder) are the same.
"""
import functools
import os
import re

from . import repo_path
from . import tu as TU
from . import namestyle
from . import items as ITEMS
from . import graphics
from . import hand_facts as F

FLAVORS = ("FLAVOR_SPICY", "FLAVOR_DRY", "FLAVOR_SWEET", "FLAVOR_BITTER", "FLAVOR_SOUR")
FLAVOR_TEXT = {"FLAVOR_SPICY": "gText_Spicy2", "FLAVOR_DRY": "gText_Dry2", "FLAVOR_SWEET": "gText_Sweet2",
               "FLAVOR_BITTER": "gText_Bitter2", "FLAVOR_SOUR": "gText_Sour2"}
FIELDS = {"FLAVOR_SPICY": "spicy", "FLAVOR_DRY": "dry", "FLAVOR_SWEET": "sweet",
          "FLAVOR_BITTER": "bitter", "FLAVOR_SOUR": "sour"}
IV_LABEL = {"MON_DATA_HP_IV": "hp", "MON_DATA_ATK_IV": "atk", "MON_DATA_DEF_IV": "def",
            "MON_DATA_SPATK_IV": "spa", "MON_DATA_SPDEF_IV": "spd", "MON_DATA_SPEED_IV": "spe"}
WILD = "src/wild_encounter.c"


def _check_flavor_order():
    t = TU.load("src/pokeblock.c", lang="de")
    vals = [t.need(f) for f in FLAVORS]
    if vals != list(range(5)):
        raise TU.DataError("enum Flavor changed: %r" % vals)


def flavors(lang=None):
    return list(_flavors(TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _flavors(lang):
    _check_flavor_order()
    return tuple((f, F.c_string("src/strings.c", FLAVOR_TEXT[f], lang)) for f in FLAVORS)


class Berry:
    def __init__(self, item, flavors, smoothness):
        self.item, self.flavors, self.smoothness = item, flavors, smoothness


def berries(lang=None):
    return list(_berries(TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _berries(lang):
    t = TU.load("src/berry.c", lang="de")
    first = t.need("FIRST_BERRY_INDEX")
    out = []
    for idx, entry in sorted(t.table("gBerries").items()):
        it = ITEMS.by_id(first + idx, lang)
        if it is None:
            continue
        fl = {f: int(t.field(entry, FIELDS[f], 0)) for f in FLAVORS}
        out.append(Berry(it, fl, int(t.field(entry, "smoothness", 0))))
    return out


class Color:
    def __init__(self, const, slug, name, name_game=None):
        self.const, self.slug, self.name = const, slug, name
        self.name_game = name if name_game is None else name_game


def colors(lang=None):
    return list(_colors(TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _colors(lang):
    t = TU.load("src/pokeblock.c", lang=lang)
    init = t.init("gPokeblockNames")
    out = []
    for key, tokens in init.items:
        if key is None:
            continue
        const = key if isinstance(key, str) else None
        if isinstance(key, (list, tuple)):
            const = [x for x in key if str(x).startswith("PBLOCK_CLR_")][0]
        if not const or const == "PBLOCK_CLR_NONE":
            continue
        slug = const[len("PBLOCK_CLR_"):].lower().replace("_", "")
        raw = t.text_value(tokens)
        written = TU.written_in("src/pokeblock.c", raw, lang)
        game = F.clean(raw, lang, written)
        out.append(Color(const, slug, namestyle.show(game, written, "label", lang), game))
    order = t.names("PBLOCK_CLR_")
    rank = {v: k for k, v in order.items()}
    return sorted(out, key=lambda c: rank.get(c.const, 99))


def icon(color, scale=2):
    """The Pokeblock sprite in `color` (Color.slug), scaled with NEAREST."""
    png = repo_path("graphics", "pokeblock", "pokeblock.png")
    pal = repo_path("graphics", "pokeblock", "%s.pal" % color.slug)
    if not os.path.exists(pal):
        raise TU.DataError("palette %s missing" % pal)
    return graphics.render(png, graphics.palette(pal, png), None, scale)


def _blender_color_body():
    src = F.raw("src/berry_blender.c")
    i = src.find("return PBLOCK_CLR_GOLD;")
    if i < 0:
        raise TU.DataError("berry blender colour function changed")
    j = src.rfind("\n{", 0, i)
    k = src.find("return PBLOCK_CLR_NONE;\n}", i)
    return src[j:k]


def color_rules():
    """Checks the blender rules the page states; returns the gold threshold."""
    body = _blender_color_body()
    for snippet in ("if (j == FLAVOR_COUNT || negativeFlavors > 3)\n        return PBLOCK_CLR_BLACK;",
                    "if (numFlavors > 3)\n        return PBLOCK_CLR_WHITE;",
                    "if (numFlavors == 3)\n        return PBLOCK_CLR_GRAY;",
                    "return PBLOCK_CLR_BLACK;"):
        if snippet not in body:
            raise TU.DataError("berry blender colour rule changed: %r" % snippet)
    gold = re.search(r"if \(flavors\[i\] > (\d+)\)\s*return PBLOCK_CLR_GOLD;", body)
    single = re.findall(r"numFlavors == 1 && flavors\[(FLAVOR_\w+)\] > 0\)\s*return (PBLOCK_CLR_\w+);", body)
    double = re.findall(r"if \(sPokeblockPresentFlavors\[0\] == (FLAVOR_\w+)\)\s*return \(sPokeblockPresentFlavors\[1\] << 16\) \| (PBLOCK_CLR_\w+);", body)
    if not gold or len(single) != 5 or len(double) != 5:
        raise TU.DataError("berry blender colour table changed")
    return {"gold_above": int(gold.group(1)), "single": dict(single), "double": dict(double)}


class Feeder:
    pass


@functools.lru_cache(maxsize=None)
def feeder():
    sz = TU.load("src/safari_zone.c", lang="de")
    w = TU.load(WILD, lang="de")
    fd = Feeder()
    fd.steps = sz.need("POKEBLOCK_FEEDER_STEPS")
    fd.feeders = sz.need("NUM_POKEBLOCK_FEEDERS")
    fd.whole_map = sz.need("POKEBLOCK_FEEDER_RANGE") == sz.need("POKEBLOCK_FEEDER_RANGE_WHOLE_MAP")
    nat = F.require(WILD, r"GetSafariZoneFlag\(\) == TRUE && Random\(\) % 100 < (\d+)")
    fd.nature_percent = int(nat.group(1))
    F.require(WILD, r"// The Hidden Ability is guaranteed no matter which Pokeblock was fed\.\n\s*"
                    r"if \(GetSpeciesAbility\(species, abilityNum\) != ABILITY_NONE\)")
    F.require(WILD, r"u8 abilityNum = 2;")
    fd.perfect = w.need("POKEBLOCK_PERFECT_IVS")
    fd.gold_perfect = w.need("POKEBLOCK_GOLD_PERFECT_IVS")
    src = F.raw(WILD)
    blk = src[src.index("sPokeblockColorIvs[][POKEBLOCK_PERFECT_IVS] ="):]
    blk = blk[:blk.index("};")]
    fd.iv_sets = [(c, [IV_LABEL[x] for x in ivs.split(",") for x in [x.strip()] if x])
                  for c, ivs in re.findall(r"\[(PBLOCK_CLR_\w+)\]\s*=\s*\{([^}]*)\}", blk) if c != "PBLOCK_CLR_NONE"]
    blk = src[src.index("sGoldPokeblockIvs[FLAVOR_COUNT][POKEBLOCK_GOLD_PERFECT_IVS] ="):]
    blk = blk[:blk.index("};")]
    fd.gold_sets = [(f, [IV_LABEL[x.strip()] for x in ivs.split(",") if x.strip()])
                    for f, ivs in re.findall(r"\[(FLAVOR_\w+)\]\s*=\s*\{([^}]*)\}", blk)]
    fd.white_link_only = "// Only reachable by blending with another player over a link." in src
    return fd


def natures(lang=None):
    return list(_natures(TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _natures(lang):
    from . import natures as NATURES
    p = TU.load("src/pokeblock.c", lang="de")
    table = p.array("gPokeblockFlavorCompatibilityTable")
    out = []
    for n in range(len(table) // 5):
        row = table[n * 5:(n + 1) * 5]
        like = [FLAVORS[i] for i, v in enumerate(row) if v > 0]
        dislike = [FLAVORS[i] for i, v in enumerate(row) if v < 0]
        out.append((NATURES.by_id(n, lang).name, like[0] if like else None, dislike[0] if dislike else None))
    return out
