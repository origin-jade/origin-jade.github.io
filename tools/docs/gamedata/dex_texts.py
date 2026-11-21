"""Labels the in-game Pokédex (src/pokedex_plus_hgss.c, POKEDEX_PLUS_HGSS) and
src/strings.c use, so the site says what the game says.

    dex_texts.string("sText_Stats_eggGroup_MONSTER")   -> "Monster"
    dex_texts.egg_group("EGG_GROUP_WATER_1")          -> "Wasser 1"        ("en": "WATER {CIRCLE_1}" as written)
    dex_texts.growth("GROWTH_MEDIUM_SLOW")            -> "Mittel-Langsam"
    dex_texts.catch_class(45)                         -> "Sehr schwer"
    dex_texts.no_evolution("Tauros")                  -> "Tauros hat keine Entwicklung."
    dex_texts.dex_title("regional"|"national")        -> "Johto Dex" / "Nationaler Dex"

catch_class mirrors the thresholds of PrintStatsScreen_Left (catchRate <= 15 /
45 / 90 / 150 / 200). The strings are read from the preprocessed TU of the
requested build, so `#if GERMAN` is resolved as in that ROM.

Language: every function takes lang="de"|"en" as its last argument (None = the process
language). string_lang(sym, path, lang) tells whether the English build translated a label.
"""
import functools
import re

from . import tu as TU
from . import text
from . import namestyle

DEX = "src/pokedex_plus_hgss.c"
STRINGS = "src/strings.c"
_CIRCLED = {"{CIRCLE_%d}" % i: str(i) for i in range(1, 10)}


@functools.lru_cache(maxsize=None)
def _raw_lang(path, sym, lang):
    s = TU.cstring(path, sym, lang)
    if s is None:
        raise TU.DataError("%s: string %s not found" % (path, sym))
    for k, v in _CIRCLED.items():
        s = s.replace(k, v)
    return s


def _raw(path, sym, lang=None):
    return _raw_lang(path, sym, TU.lang(lang))


def string_lang(sym, path=DEX, lang=None):
    """Language the label is written in in build lang ("de": the English build shows
    the German string)."""
    lang = TU.lang(lang)
    return text.written_in(_raw(path, sym, lang), _raw(path, sym, "de"), lang)


def string(sym, path=DEX, lang=None):
    return text.clean(_raw(path, sym, lang), string_lang(sym, path, lang))


def name(sym, path=DEX, lang=None):
    """A label or name of the Pokédex screens in the site's name style (the English
    game writes them in capitals: "MONSTER", "MED. SLOW" -> "Monster", "Med. Slow";
    namestyle.py). string() gives the game's own spelling."""
    return namestyle.show(string(sym, path, lang), string_lang(sym, path, lang), "label", TU.lang(lang))


def label(sym, lang=None):
    """A stats-screen label without its trailing colon ("Fangrate:" -> "Fangrate")."""
    return name(sym, DEX, lang).rstrip(":").strip()


def egg_group(const, lang=None):
    return name("sText_Stats_eggGroup_" + const[len("EGG_GROUP_"):], DEX, lang)


def growth(const, lang=None):
    return name("sText_Stats_" + const[len("GROWTH_"):], DEX, lang)


CATCH_CLASSES = ((15, "Legend"), (45, "VeryHard"), (90, "Difficult"), (150, "Medium"), (200, "Relaxed"))


def catch_class(rate, lang=None):
    """PrintStatsScreen_Left: the in-game wording of a catch rate."""
    for limit, sym in CATCH_CLASSES:
        if rate <= limit:
            return name("sText_Stats_CatchRate_" + sym, DEX, lang)
    return name("sText_Stats_CatchRate_Easy", DEX, lang)


def no_evolution(name, lang=None):
    return _raw(DEX, "sText_EVO_NONE", lang).replace("{STR_VAR_1}", name)


def dex_title(kind, lang=None):
    return name({"regional": "gText_DexHoennTitle", "national": "gText_DexNatTitle"}[kind], STRINGS, lang)
