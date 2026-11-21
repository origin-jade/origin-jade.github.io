"""Small facts for the hand-written pages (features, FAQ, download, walkthrough):
config values, script checks and game strings, read from the source.

The prose of those pages is hand-written, but every number and name in it
comes from here, and every statement about how a script behaves is pinned to
the script by require(): if the script changes, the build stops with a
DataError instead of the page silently going stale.

    hand_facts.C("OW_REMATCH_BADGE_COUNT")          -> 3   (config value, German build)
    hand_facts.gen(hand_facts.C("P_EGG_HATCH_LEVEL")) -> "Gen 9"
    hand_facts.require("data/scripts/new_game.inc", r"additem ITEM_EXP_SHARE")
    hand_facts.inc_string("data/maps/X/scripts.inc", "X_Text_Label")  -> German text, one line
    hand_facts.c_string("src/main_menu.c", "gText_SaveFileOutdated")  -> German text, one line
    hand_facts.map_name("PalletTown_ProfessorOaksLab_Frlg")           -> in-game section name
    hand_facts.item("ITEM_HOENN_TICKET").name, hand_facts.trainer("TRAINER_STEVEN").name

Language: clean, inc_string, c_string, map_name, map_by_id, item, trainer and species take
lang="de"|"en" as their last argument (None = the process language) and return what that
build shows. Config values (C) and require() are the same for both builds.
"""
import functools
import re

from . import repo_path
from . import tu as TU
from . import text
from . import maps
from . import items as ITEMS
from . import trainers as TRAINERS
from . import species as SPECIES

# Translation unit used for config lookups: it includes include/config/*.h
# through global.h, so every #define of the configs is resolved there.
CONFIG_TU = "src/battle_main.c"


# Button and arrow glyphs of the game font, shown as their key names. The glyphs are
# pictures in the game; DPAD_NAME is the site's word for the D-pad picture (not game text).
DPAD_NAME = {"de": "Steuerkreuz", "en": "D-Pad"}
GLYPHS = {
    "{A_BUTTON}": "A", "{B_BUTTON}": "B", "{L_BUTTON}": "L", "{R_BUTTON}": "R",
    "{START_BUTTON}": "START", "{SELECT_BUTTON}": "SELECT",
    "{DPAD_UPDOWN}": DPAD_NAME, "{DPAD_LEFTRIGHT}": DPAD_NAME, "{DPAD_NONE}": DPAD_NAME,
    "{RIGHT_ARROW}": "→", "{LEFT_ARROW}": "←", "{UP_ARROW}": "↑", "{DOWN_ARROW}": "↓",
}


def clean(s, lang=None, written="de"):
    """text.clean, with button glyphs kept as key names (A, B, L, R, →).

    lang: the build (word for the D-pad glyph); written: the language the string is
    written in (line-end hyphen rules, see text.clean) - "de" unless the caller knows
    the English build translated this string (clean_pair does that comparison)."""
    if s is None:
        return None
    lang = TU.lang(lang)
    for k, v in GLYPHS.items():
        s = s.replace(k, v[lang] if isinstance(v, dict) else v)
    return text.clean(s, written)


def clean_pair(s, s_de, lang=None):
    """clean() of a string of build `lang`, given the German build's string at the same
    place: the rules of the language the string is really written in are used."""
    lang = TU.lang(lang)
    return clean(s, lang, text.written_in(s, s_de, lang))


def C(name, path=CONFIG_TU):
    """Numeric value of a config constant / enum (the same in both builds)."""
    return TU.load(path, lang="de").need(name)


def gen(value):
    """GEN_x constant value (GEN_1 == 0) -> "Gen x"."""
    return "Gen %d" % (int(value) + 1)


@functools.lru_cache(maxsize=None)
def raw(rel):
    with open(repo_path(rel), encoding="utf-8") as f:
        return f.read()


def require(rel, pattern, flags=re.M):
    """Regex match in a source file; DataError when the code no longer says so."""
    m = re.search(pattern, raw(rel), flags)
    if not m:
        raise TU.DataError("%s: expected %r - the page text relies on it, review the page" % (rel, pattern))
    return m


def count(rel, pattern):
    return len(re.findall(pattern, raw(rel), re.M))


_STR_LINE = re.compile(r'^\s*\.string\s+"((?:[^"\\]|\\.)*)"', re.M)


def _inc_raw(rel, label, lang):
    """Raw text of a script string label in build lang: from the script database (every
    #if resolved as in that build); for a label outside it, from the file with the
    `#if GERMAN ... #else ... #endif` branch of that language."""
    from . import trainers_scriptdb as SDB
    if SDB.script_text_file(label) == rel:
        return SDB.script_text(label, lang)
    src = raw(rel)
    m = re.search(r"^%s::?\s*$" % re.escape(label), src, re.M)
    if not m:
        raise TU.DataError("%s: label %s missing" % (rel, label))
    body = src[m.end():]
    nxt = re.search(r"^\w+::?\s*$", body, re.M)
    body = body[:nxt.start()] if nxt else body
    if "#if GERMAN" in body:
        de, _, rest = body.split("#if GERMAN", 1)[1].partition("#else")
        en = rest.split("#endif", 1)[0]
        body = de.split("#endif", 1)[0] if lang == "de" or not _STR_LINE.search(en) else en
    parts = _STR_LINE.findall(body)
    if not parts:
        raise TU.DataError("%s: label %s has no .string" % (rel, label))
    return "".join(parts).replace("$", "")


def inc_string(rel, label, lang=None):
    """Text of a script string label (`Label:` / `Label::`) in build lang, one line.
    Script texts carry `#if GERMAN ... #else ... #endif`; the branch of the build's
    language is taken. The text is cleaned like all game text (text.clean): line
    codes become spaces, placeholders are replaced."""
    lang = TU.lang(lang)
    s = _inc_raw(rel, label, lang)
    if s is None:
        raise TU.DataError("%s: label %s has no .string" % (rel, label))
    s_de = s if lang == "de" else _inc_raw(rel, label, "de")
    return clean_pair(s, s_de, lang)


def c_string(rel, symbol, lang=None):
    """Text of `symbol[] = _("...")` in a C file (preprocessed for build lang), one line."""
    lang = TU.lang(lang)
    s = TU.cstring(rel, symbol, lang)
    if s is None:
        raise TU.DataError("%s: string %s missing" % (rel, symbol))
    return clean_pair(s, s if lang == "de" else TU.cstring(rel, symbol, "de"), lang)


def map_name(map_dir, lang=None):
    """In-game name (map section) of a map folder in data/maps."""
    m = maps.by_dir(map_dir, lang)
    if m is None:
        raise TU.DataError("map folder %s unknown" % map_dir)
    return m.display


def map_by_id(map_id, lang=None):
    m = maps.by_id(map_id, lang)
    if m is None:
        raise TU.DataError("map %s unknown" % map_id)
    return m


def item(const, lang=None):
    it = ITEMS.by_const(const, lang)
    if it is None:
        raise TU.DataError("item %s unknown" % const)
    return it


def trainer(const, lang=None):
    tr = TRAINERS.by_const(const, lang)
    if tr is None:
        raise TU.DataError("trainer %s unknown" % const)
    return tr


def species(const, lang=None):
    sp = SPECIES.by_const(const, lang)
    if sp is None:
        raise TU.DataError("species %s unknown" % const)
    return sp
