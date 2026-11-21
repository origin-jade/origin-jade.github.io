"""How English names are written on the site (site_config.EN_NAME_STYLE).

The English game writes every name in capitals (BULBASAUR, POUND, POKé BALL,
LITTLEROOT TOWN). The site can show them like that ("game") or in natural
capitalisation ("title", the default): Bulbasaur, Pound, Poké Ball, Littleroot Town.

    namestyle.style()                 -> "title" | "game"
    namestyle.show(s, written, kind)  -> the name as the site shows it; written = the
                                         language the string is written in ("de": untouched)
    namestyle.title(s)                -> the conversion itself, whatever the setting

Only names go through this - never descriptions or dialogue. Loaders keep the game's
spelling next to it (obj.name_game), for search keywords and for style "game".

The conversion is one rule plus two reviewed lists:
  * a name is converted only when it has no lower-case letter of its own (the "é" of
    POKé and plural endings such as "TMs" do not count), so mixed-case names of the
    game (categories, "Rusty") stay as they are;
  * each word: first letter upper case, rest lower case; parts of a hyphenated word
    likewise (Double-Edge, Ho-Oh, Porygon-Z); after an apostrophe lower case
    (Farfetch'd, King's Shield); small words inside a name lower case (Lake of Rage);
  * WORDS: single words that are written differently (acronyms: HP, PP, TM; the
    game's own compounds: PokéManiac, Pokémon; Roman numerals);
  * NAMES: whole names that no rule gets right (U-turn, Jangmo-o, Type: Null).
Both lists were made by going through every name of every table of the English
version (species, moves, abilities, items, types, natures, trainer classes, trainer
names, places, pockets, menu labels); selftest.py checks that no name falls through.
"""
import functools
import os
import re

ENV = "OJ_DOCS_EN_NAME_STYLE"
STYLES = ("title", "game")

# Words kept or written in a fixed way, wherever they occur in a name (key: the game's capitals).
WORDS = {
    # acronyms and symbols that stay in capitals
    "HP": "HP", "PP": "PP", "TM": "TM", "HM": "HM", "TMS": "TMs", "HMS": "HMs", "PC": "PC", "TV": "TV",
    "ID": "ID", "OT": "OT", "KO": "KO", "PKMN": "PKMN", "GS": "GS", "DNA": "DNA", "RKS": "RKS",
    "RTC": "RTC", "UI": "UI", "EV": "EV", "IV": "IV", "EVS": "EVs", "IVS": "IVs", "XL": "XL", "XS": "XS",
    "VS": "Vs", "NPC": "NPC", "GB": "GB", "SP": "Sp", "BST": "BST", "LR": "LR",
    "II": "II", "III": "III", "VI": "VI", "VII": "VII", "VIII": "VIII", "IX": "IX",
    # the game's own compounds
    "POKéMON": "Pokémon", "POKé": "Poké", "POKéDEX": "Pokédex", "POKéNAV": "PokéNav", "POKéGEAR": "Pokégear",
    "POKéBLOCK": "Pokéblock", "POKéBLOCKS": "Pokéblocks", "POKéMANIAC": "PokéManiac", "POKéFAN": "PokéFan",
    "POKéKID": "Poké Kid", "POKéMART": "Poké Mart", "POKéCENTER": "Pokécenter", "POKéBALL": "Poké Ball",
    "POKéMONCENTER": "Pokémon Center", "PKMNCENTER": "PKMN Center",
}
# Small words that are lower case inside a name (not at its start).
SMALL = {"OF": "of", "THE": "the", "AND": "and", "IN": "in", "ON": "on", "AT": "at", "TO": "to", "A": "a",
         "AN": "an", "AS": "as", "FOR": "for", "WITH": "with", "FROM": "from", "OR": "or"}
# Whole names no rule gets right (key: the game's spelling).
NAMES = {
    "U-TURN": "U-turn", "V-CREATE": "V-create", "TRICK-OR-TREAT": "Trick-or-Treat",
    "JANGMO-O": "Jangmo-o", "HAKAMO-O": "Hakamo-o", "KOMMO-O": "Kommo-o",
    "TYPE: NULL": "Type: Null", "FLABéBé": "Flabébé",
    # compounds the capitals hide (the spelling the games themselves use in mixed case)
    "SECRETPOTION": "SecretPotion", "SQUIRTBOTTLE": "SquirtBottle",
}
# Kinds whose names are people: no small words ("Al", "An" are first names).
PEOPLE = ("trainer", "person")

_LOWER_OK = re.compile(r"é|(?<=[A-Z])s\b")       # lower case that capitals style itself uses
_TOKEN = re.compile(r"[^\s/&+()\[\]\"“”:,]+|[\s/&+()\[\]\"“”:,]+")
_INITIALS = re.compile(r"^(?:[A-Z]\.){2,}$")      # S.S.
_CODE = re.compile(r"^(?:(?:TM|HM)\d+|B?\d+F|\d[\d.,]*|[A-Z]?\d+[A-Z]?)$")    # TM01, B1F, 10,000,000, 2F


@functools.lru_cache(maxsize=None)
def style():
    v = os.environ.get(ENV)
    if v is None:
        from . import entext
        v = getattr(entext._site_config(), "EN_NAME_STYLE", "title")
    v = v.strip().lower()
    if v not in STYLES:
        raise ValueError("EN_NAME_STYLE %r: use %s" % (v, " or ".join(STYLES)))
    return v


def is_capitals(s):
    """True for a name written in the game's capitals style (no lower-case letter of
    its own and at least two capitals in a row somewhere)."""
    if not s or not re.search(r"[A-ZÀ-Þ]{2}", s):
        return False
    return not re.search(r"[a-zß-ÿ]", _LOWER_OK.sub("", s))


def _cap(part):
    """One hyphen-free piece: first letter upper case, rest lower case; after an
    apostrophe lower case."""
    if not part:
        return part
    out, first = [], True
    for ch in part:
        if ch.isalpha():
            out.append(ch.upper() if first else ch.lower())
            first = False
        else:
            out.append(ch)
    return "".join(out)


def _word(w, at_start, small=True):
    if w in WORDS:
        return WORDS[w]
    if w[-1:] == "s" and w[:-1] + "S" in WORDS:        # TMs, HMs
        return WORDS[w[:-1] + "S"]
    if _INITIALS.match(w) or _CODE.match(w):
        return w
    core = w.rstrip(".!?")
    tail = w[len(core):]
    if core in WORDS:
        return WORDS[core] + tail
    if small and not at_start and core in SMALL and not tail:
        return SMALL[core]
    if "-" in core:
        parts = core.split("-")
        return "-".join(WORDS.get(p) or (p if _CODE.match(p) else _cap(p)) for p in parts) + tail
    if "'" in core or "’" in core:
        # POKéMON'S, FARFETCH'D, DIGLETT'S: the part before the apostrophe by the rules
        i = min(x for x in (core.find("'"), core.find("’")) if x != -1)
        head = WORDS.get(core[:i]) or _cap(core[:i])
        return head + core[i:].lower() + tail
    return _cap(core) + tail


_BRACES = re.compile(r"(\{[^{}]*\})")


@functools.lru_cache(maxsize=None)
def title(s, kind=None):
    """Natural capitalisation of a name in game capitals; any other string unchanged
    (also constants and anything with an underscore). Placeholders in braces
    ({B_RIVAL_NAME}) are kept as they are."""
    if s is None or "_" in _BRACES.sub("", s) or not is_capitals(_BRACES.sub("", s)):
        return s
    if s in NAMES:
        return NAMES[s]
    out, start = [], True
    for piece in _BRACES.split(s):
        if piece.startswith("{") and piece.endswith("}"):
            out.append(piece)
            start = False
            continue
        for tok in _TOKEN.findall(piece):
            if not re.search(r"[^\s/&+()\[\]\"“”:,]", tok):
                out.append(tok)
                continue
            out.append(_word(tok, start, small=kind not in PEOPLE))
            start = False
    return "".join(out)


def game_spellings(lang):
    """{(kind, key): the name as the game writes it} for the entities the site
    registers by constant: species, move, ability, item, location (map section),
    trainer. Used for search keywords."""
    from . import abilities, items, maps, moves, species, trainers, tu
    lang = tu.lang(lang)
    out = {}
    for kind, objs in (("species", species.all_species(lang).values()), ("move", moves.all_moves(lang).values()),
                       ("ability", abilities.all_abilities(lang).values()), ("item", items.all_items(lang).values()),
                       ("trainer", trainers.all_trainers(lang).values())):
        for o in objs:
            if o.name_game and o.name_game != o.name:
                out[(kind, o.const)] = o.name_game
    for sec in maps._sections():
        g = maps.mapsec_name_game(sec, lang)
        if g != sec and g != maps.mapsec_name(sec, lang):
            out[("location", sec)] = g
    return out


def show(s, written, kind=None, lang=None):
    """A name as the site shows it. German names (written "de") and style "game":
    unchanged. English names with style "title": natural capitalisation.
    kind: species, move, item, place, trainer, ... ("trainer"/"person": no small words).
    lang="en": the name belongs to the English build - then a name in capitals is
    converted even if the German build has the very same string (AKALA CAVE)."""
    if s is None or style() != "title" or (written != "en" and lang != "en"):
        return s
    return title(s, kind)
