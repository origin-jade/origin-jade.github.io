"""Challenge-menu options that change Pokédex, move and ability data, and the
alternative data the game uses when they are switched.

Mirrors (all read from the source, nothing copied by hand; option(const, lang) gives the
texts of the German or the English build, lang None = the process language):
  * src/challenge_menu.c sTabItems_Mode / sTabs: option name, tab name, choice
    names and descriptions; ApplyRecommendedPresets: the recommended choice.
  * src/pokemon.c GetSpeciesLevelUpLearnset / GetSpeciesEggMoves: with
    tx_Mode_Modern_Moves == 0 ("Gen 3") the game takes gLevelUpLearnsets_Gen3 /
    gEggMoves_Gen3 (src/data/pokemon/level_up_learnsets_gen3.c, egg_moves_gen3.c)
    when the species has an entry there, else the normal learnset.
  * src/pokemon.c GetAbilityBySpecies: with tx_Mode_Legendary_Abilities == 1 the
    first ability slot (abilityNum 0) of the species in sLegendaryCustomAbilities
    is replaced (not while the randomizer shuffles abilities).
  * src/pokemon.c GetSpeciesType: with tx_Mode_Fairy_Types == 0 the species in
    sPreFairyTypes get their pre-Gen-6 types.
  * src/pokemon.c GetMoveType: with tx_Mode_Fairy_Types == 0 a Fairy move takes
    its type from sFairyMoveAltTypes, every other Fairy move becomes Normal.
  * src/battle_util.c GetBattleMoveCategory: with "Phys./Spez.-Split" off
    (optionStyle == 1) the category comes from gTypesInfo[type].damageCategory.

    dex_options.option("ITEM_MODE_MODERN_MOVES") -> Option(name, tab, choices, descs, recommended)
    dex_options.gen3_levelup(species_id)  -> [(level, move_id)] or None (no own Gen-3 list)
    dex_options.gen3_egg_moves(species_id) -> [move_id] or None
    dex_options.legendary_abilities()     -> {species_id: ability_id}
    dex_options.pre_fairy_types()         -> {species_id: [type_id, type_id]}
    dex_options.fairy_move_types()        -> {move_id: type_id}; fairy_move_type(move) for any move
"""
import functools
import re

from . import repo_path
from . import tu as TU
from . import namestyle
from . import text
from . import cparse as C

MENU = "src/challenge_menu.c"
POKEMON = "src/pokemon.c"
GEN3_LEVELUP = "src/data/pokemon/level_up_learnsets_gen3.c"
GEN3_EGG = "src/data/pokemon/egg_moves_gen3.c"


class Option:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Option(%s %r)" % (self.const, self.name)


@functools.lru_cache(maxsize=None)
def _recommended():
    """{ITEM_MODE_*: choice index} from ApplyRecommendedPresets (raw source;
    the function only assigns constants)."""
    src = open(repo_path(*MENU.split("/")), encoding="utf-8").read()
    body = re.search(r"static void ApplyRecommendedPresets\(void\)\s*\{(.*?)\n\}", src, re.S)
    if not body:
        raise TU.DataError("%s: ApplyRecommendedPresets not found" % MENU)
    return {k: int(v) for k, v in re.findall(
        r"\*GetSelectionPtr\(TAB_MODE,\s*(ITEM_MODE_\w+)\)\s*=\s*(\d+)\s*;", body.group(1))}


def option(const, lang=None):
    """One option of the mode tab (sTabItems_Mode)."""
    return _option(const, TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _option(const, lang):
    t = TU.load(MENU, lang=lang)

    def cl(v):
        return TU.clean(MENU, t.text_value(v), lang)

    def label(v):       # names of tabs, options and choices: the site's name style
        raw = t.text_value(v)
        return namestyle.show(TU.clean(MENU, raw, lang), TU.written_in(MENU, raw, lang), "label", lang)
    item = t.table("sTabItems_Mode")[t.need(const)]
    tab = t.table("sTabs")[t.need("TAB_MODE")]
    name = label(item.get("name"))
    descs = [cl(x) for x in t.init(str(t.field(item, "descriptions"))).positional()]
    choices = [label(x) for x in t.init(str(t.field(item, "choiceNames"))).positional()]
    return Option(const=const, name=name, tab=label(tab.positional()[0]), choices=choices,
                  descs=descs, recommended=_recommended().get(const), lang=lang)


def _levelup_list(t, sym):
    out = []
    end = t.const("LEVEL_UP_END", 0xFFFF)
    for v in t.init(str(sym)).positional():
        if not isinstance(v, C.Init):
            continue
        mv = t.value(v.get("move")) if v.get("move") is not None else t.value(v.positional()[0])
        lv = t.value(v.get("level")) if v.get("level") is not None else t.value(v.positional()[1])
        if mv == end or lv == end:
            break
        out.append((lv, mv))
    return out


@functools.lru_cache(maxsize=None)
def _gen3_levelup():
    t = TU.load(GEN3_LEVELUP)
    out = {}
    for sid, sym in t.table("gLevelUpLearnsets_Gen3").items():
        name = str(t.value(sym))
        if t.has_symbol(name):
            out[sid] = _levelup_list(t, name)
    return out


@functools.lru_cache(maxsize=None)
def _gen3_egg():
    t = TU.load(GEN3_EGG)
    out = {}
    end = t.const("MOVE_UNAVAILABLE")
    for sid, sym in t.table("gEggMoves_Gen3").items():
        name = str(t.value(sym))
        if not t.has_symbol(name):
            continue
        lst = []
        for v in t.init(name).positional():
            x = t.value(v)
            if x == end:
                break
            lst.append(x)
        out[sid] = lst
    return out


def gen3_levelup(sid):
    """Level-up list with "Gen 3" chosen, or None when the game falls back to the normal one."""
    return _gen3_levelup().get(sid)


def gen3_egg_moves(sid):
    return _gen3_egg().get(sid)


@functools.lru_cache(maxsize=None)
def legendary_abilities():
    t = TU.load(POKEMON)
    out = {}
    for v in t.table("sLegendaryCustomAbilities").values():
        sp, ab = t.value(v)
        out[sp] = ab
    return out


@functools.lru_cache(maxsize=None)
def pre_fairy_types():
    t = TU.load(POKEMON)
    out = {}
    for v in t.table("sPreFairyTypes").values():
        sp, types = t.value(v)
        out[sp] = list(types)
    return out


@functools.lru_cache(maxsize=None)
def fairy_move_types():
    t = TU.load(POKEMON)
    out = {}
    for v in t.table("sFairyMoveAltTypes").values():
        mv, ty = t.value(v)
        out[mv] = ty
    return out


def fairy_move_type(move):
    """Type of a move with "Fee an" = Aus (GetMoveType); None if it stays the same."""
    t = TU.load(POKEMON)
    if move.type != t.need("TYPE_FAIRY"):
        return None
    return fairy_move_types().get(move.id, t.need("TYPE_NORMAL"))
