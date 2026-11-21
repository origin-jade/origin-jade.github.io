"""Game text -> plain site text, for German and English game strings.

The game strings carry hard line breaks (\\n), scroll/paragraph codes (\\l, \\p),
hyphens at line ends ("Geg-\\nner") and placeholders ({PKMN}). The site shows
them as one flowing line; the wording stays exactly as in the game.

    text.clean(s)             German rules (default)
    text.clean(s, "en")       English rules
    text.clean_as(s, s_de, lang)  rules of the language the string is really written in:
                              the English build still carries many German strings
                              (move, ability and most Pokédex texts); a string that is
                              identical in both builds is treated as German text
    text.name(s, lang)        names: placeholders only
    text.is_german(s_en, s_de) -> True when the English build shows the German string

Line-end hyphens:
  German text hyphenates words at line ends, so the hyphen is dropped before a
  lower-case continuation ("bestimm-\\nten" -> "bestimmten"), kept before a
  capital or digit ("Feuer-\\nAttacke" -> "Feuer-Attacke") and kept with a space
  before a conjunction ("Dies-\\nund" -> "Dies- und").
  English game text never splits a word; a hyphen at a line end is always the
  hyphen of a compound ("Psychic-\\ntype" -> "Psychic-type", "sea-\\ndwelling" ->
  "sea-dwelling"), so it is always kept and the lines are joined without a space.

Placeholders are glyph ligatures of the game font (charmap.txt). The font is the
same in both builds, so they read the same in both languages: {POKEBLOCK} is drawn
as "POKéRIEGEL" in the English build too (graphics/fonts/latin_*.png).
"""
import re

LANGS = ("de", "en")

# Placeholders that are glyph ligatures in the game font (charmap.txt).
PLACEHOLDERS = {
    "{PKMN}": "Pokémon",
    "{POKEBLOCK}": "Pokériegel",
    "{LV}": "Lv.",
    "{PK}": "PK",
    "{NBSP}": " ",
}

# The English version has its own font graphics (graphics_en/fonts): there the
# {POKEBLOCK} ligature reads "POKéBLOCK". {PKMN} is the small "PKMN" sign in both; in
# English text it is written as that, German text keeps the readable "Pokémon".
PLACEHOLDERS_EN = dict(PLACEHOLDERS)
PLACEHOLDERS_EN.update({"{PKMN}": "PKMN", "{POKEBLOCK}": "POKéBLOCK"})


def placeholders(lang="de"):
    """The placeholder texts for a string written in `lang`. The English ones apply
    when English text is drawn with the English version's font (entext.english_font():
    texts from the English version's tree, or graphics_en/fonts in this repository)."""
    if lang == "en":
        from . import entext
        if entext.english_font():
            return PLACEHOLDERS_EN
    return PLACEHOLDERS


# A hyphen followed by a line break (real newline or the literal codes \n, \l, \p of the C strings).
_BR = r"-(?:\n|\\n|\\l|\\p)[ \t]*"
_ANY_BREAK = re.compile(r"(?:\n|\\l|\\p|\\n)")
_CODE = re.compile(r"\{[A-Z_0-9 ]+\}")
_DE_CONJ = re.compile(_BR + r"(?=(?:und|oder|bis|sowie|u\.)(?![a-zäöüß]))")
_DE_LOWER = re.compile(_BR + r"(?=[a-zäöüß])")
_DE_UPPER = re.compile(_BR + r"(?=[A-ZÄÖÜ0-9])")
_EN_ANY = re.compile(_BR + r"(?=\S)")


_HEX = re.compile(r"\{0x([0-9A-Fa-f]{2})\}")
_charmap = None


def _glyph(m):
    """A raw glyph code {0x5B} -> the character charmap.txt gives that byte ("%");
    codes without a single character are dropped."""
    global _charmap
    if _charmap is None:
        from . import repo_path
        _charmap = {}
        try:
            for line in open(repo_path("charmap.txt"), encoding="utf-8"):
                c = re.match(r"'(\\?.)'\s*=\s*([0-9A-Fa-f]{2})\s*(?:@.*)?$", line.strip())
                if c and (len(c.group(1)) == 1 or c.group(1) == "\\'"):   # not \n, \l, \p
                    _charmap.setdefault(int(c.group(2), 16), c.group(1)[-1])
        except OSError:
            pass
    return _charmap.get(int(m.group(1), 16), "")


def clean(s, lang="de"):
    """One-line display text of a game string (None stays None).

    lang is the language the string is written in ("de" or "en"), see module doc."""
    if s is None:
        return None
    if lang not in LANGS:
        raise ValueError("unknown language %r" % (lang,))
    s = str(s)
    for k, v in placeholders(lang).items():
        s = s.replace(k, v)
    if lang == "en":
        #   "Psychic-\ntype" -> "Psychic-type": the hyphen belongs to the compound
        s = _EN_ANY.sub("-", s)
    else:
        #   "Geg-\nner"      -> "Gegner"        (lower-case continuation: a split word)
        #   "Feuer-\nAttacke" -> "Feuer-Attacke" (upper case / digit: a compound keeps its hyphen)
        #   "Dies-\nund"     -> "Dies- und"     (a conjunction follows: a shortened compound)
        s = _DE_CONJ.sub("- ", s)
        s = _DE_LOWER.sub("", s)
        s = _DE_UPPER.sub("-", s)
    s = _ANY_BREAK.sub(" ", s)
    s = _HEX.sub(_glyph, s)    # raw glyph bytes ("CATCH{0x5B}" -> "CATCH%")
    s = _CODE.sub("", s)       # any other control code
    return re.sub(r"\s+", " ", s).strip()


def is_german(s, s_de):
    """True when a string of the English build is the German build's string
    (not translated, or the same in both languages)."""
    return s is not None and s_de is not None and str(s) == str(s_de)


def written_in(s, s_de, lang):
    """Language a string of build `lang` is written in: "de" for the German build
    and for English-build strings that equal the German one, else "en"."""
    if lang == "de" or is_german(s, s_de):
        return "de"
    return "en"


def clean_as(s, s_de, lang):
    """clean() with the rules of the language the string is really written in.
    s: the string of build `lang`; s_de: the same string in the German build."""
    return clean(s, written_in(s, s_de, lang))


def name(s, lang="de"):
    """Names (species, moves, items): placeholders only, no other change.
    lang: the language the name is written in."""
    if s is None:
        return None
    for k, v in placeholders(lang).items():
        s = s.replace(k, v)
    return s
