"""The two option screens of the game, read from their C tables.

    hand_menus.challenge_tabs() -> [Tab(name, items=[Item(name, choices=[Choice(name, desc)])])]
        src/challenge_menu.c: sTabs -> sTabItems_* -> .name / .choiceNames / .descriptions
        (menu "Herausforderungen" at the start of a new game and in the PC)
    hand_menus.option_tabs()    -> same shape, src/option_menu.c (start menu "Optionen")

Both screens use the same struct (name, descriptions[], numChoices, choiceNames[]).
An item with one description for all choices (descriptions shorter than the
choices) repeats that text; an item without choices ("Weiter", "Speichern")
is left out. Items whose choice names the code draws itself (choiceNames
NULL: type list, frame number) have .dynamic = True, .count and .descs only.
Texts are the strings of the requested build (challenge_tabs(lang), option_tabs(lang);
lang "de"|"en", None = the process language), cleaned with text.clean and the rules of the
language each string is written in. Most of the challenge menu has no English text: the
English build shows those entries in German.
"""
import functools
import re

from . import tu as TU
from . import hand_facts
from . import namestyle


class Choice:
    def __init__(self, name, desc, name_game=None):
        self.name, self.desc = name, desc
        self.name_game = name if name_game is None else name_game   # as the game writes it

    def __repr__(self):
        return "Choice(%r)" % self.name


class Item:
    def __init__(self, name, choices, desc, count, descs, name_game=None):
        self.name, self.choices, self.desc = name, choices, desc
        self.name_game = name if name_game is None else name_game
        self.count = count        # number of choices in the game
        self.descs = descs        # all description texts of the item
        self.dynamic = not choices  # choice names drawn by code (type list, frame number)

    def __repr__(self):
        return "Item(%r, %d)" % (self.name, len(self.choices))


class Tab:
    def __init__(self, name, items, name_game=None):
        self.name, self.items = name, items
        self.name_game = name if name_game is None else name_game

    def __repr__(self):
        return "Tab(%r, %d)" % (self.name, len(self.items))


def _sym(tokens):
    toks = [x for x in tokens if x not in ("(", ")", "&")]
    return toks[0] if len(toks) == 1 else None


def _named_string(t, name):
    """`static const u8 name[] = _("...")` in the preprocessed TU (the build's branch)."""
    m = re.search(r"\b%s\s*\[\s*\]\s*=\s*_?\(?\s*((?:\"(?:[^\"\\]|\\.)*\"\s*)+)" % re.escape(name), t.text)
    if not m:
        raise TU.DataError("%s: string %s missing" % (t.path, name))
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))).replace("\\n", "\n")


def _written(t, v):
    """Language a string of the TU is written in: a string of the English build that
    the German build has too is German text."""
    if v is not None and t.lang != "de":
        de = TU.load(t.path, lang="de")
        if v not in de.literals() and v.replace("\n", "\\n") not in de.text:
            return "en"
    return "de"


def _clean(t, v):
    """hand_facts.clean with the rules of the language the string is written in."""
    if v is None:
        return None
    return hand_facts.clean(v, t.lang, _written(t, v))


def _label(t, v):
    """(name in the site's name style, name as the game writes it) of a tab, an
    option or a choice (namestyle.py; descriptions never go through this)."""
    if v is None:
        return None, None
    game = _clean(t, v)
    return namestyle.show(game, _written(t, v), "label", t.lang), game


def _strings(t, sym, labels=False):
    """The strings of a string array; labels=True: [(shown, game)] names (_label)."""
    if not sym or sym == "NULL":
        return []
    out = []
    for tokens in t.init(sym).positional():
        if isinstance(tokens, list) and not any(str(x).startswith('"') for x in tokens):
            name = _sym(tokens)
            if not name:
                raise TU.DataError("%s: %s: cannot read %r" % (t.path, sym, tokens))
            v = _named_string(t, name)
        else:
            v = t.value(tokens)
        out.append(_label(t, v) if labels else _clean(t, v))
    return out


def _tabs(path, lang):
    t = TU.load(path, lang=lang)
    out = []
    for _, entry in sorted(t.table("sTabs").items()):
        pos = [v for _, v in entry.items]
        name, name_game = _label(t, t.value(pos[0]))
        items_sym = _sym(pos[1])
        items = []
        for _, it in sorted(t.table(items_sym).items()):
            n = t.field(it, "numChoices") or 0
            if not n:
                continue
            fields = dict(it.items)
            choices = _strings(t, _sym(fields.get("choiceNames", ["NULL"])), labels=True)
            descs = _strings(t, _sym(fields.get("descriptions", ["NULL"])))
            if choices and len(choices) < n:
                raise TU.DataError("%s: %s has %d choices, %d names" % (path, items_sym, n, len(choices)))
            rows = []
            for i in range(n if choices else 0):
                d = descs[i] if i < len(descs) else (descs[0] if len(descs) == 1 else None)
                rows.append(Choice(choices[i][0], d, choices[i][1]))
            item_name, item_game = _label(t, t.field(it, "name"))
            items.append(Item(item_name, rows, descs[0] if len(descs) == 1 else None, n, descs, item_game))
        out.append(Tab(name, items, name_game))
    return out


@functools.lru_cache(maxsize=None)
def _challenge_tabs(lang):
    return _tabs("src/challenge_menu.c", lang)


def challenge_tabs(lang=None):
    return _challenge_tabs(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _option_tabs(lang):
    return _tabs("src/option_menu.c", lang)


def option_tabs(lang=None):
    return _option_tabs(TU.lang(lang))
