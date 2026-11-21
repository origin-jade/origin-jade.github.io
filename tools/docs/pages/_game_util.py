"""Building blocks shared by the long-form pages (sections "Game" and "Guides").

Every page of pages/game.py and pages/guides.py lives in its own helper module
(_game_<page>.py, _guides_<page>.py) that exports

    PATH      the sitemap path it renders
    S         {"de": {...}, "en": {...}} its texts (keys carry the page prefix)
    render(ctx)

merge_strings() joins the S tables into the STRINGS of the page module. The
helpers below wrap the link helpers of common.html so that a sentence can be
written as a format string with linked names:

    U.fmt(ctx, "text_key", item=U.item(ctx, "ITEM_GS_BALL"), n=3)

Format values are HTML; the sentence itself is escaped first, so texts may
contain any character.
"""
import importlib
import re

from common import html as H
from gamedata import items as ITEMS
from gamedata import maps as MAPS
from gamedata import moves as MOVES
from gamedata import species as SPECIES
from gamedata import abilities as ABILITIES
from gamedata import trainers as TRAINERS

REGION_KEY = {"Kanto": "kanto", "Johto": "johto", "Hoenn": "hoenn"}


def load_pages(names):
    """Import the helper modules of a page module (pages._<name>)."""
    return [importlib.import_module("pages." + n) for n in names]


def merge_strings(mods):
    out = {"de": {}, "en": {}}
    for m in mods:
        for lang in out:
            for k, v in m.S[lang].items():
                if k in out[lang]:
                    raise ValueError("string key %r defined twice (%s)" % (k, m.__name__))
                out[lang][k] = v
    return out


# ------------------------------------------------------------------ sentences
_FIELD = re.compile(r"\{(\w+)\}")


def fmt(ctx, key, **kw):
    """Module string `key` with HTML values: the text is escaped, the values are not."""
    s = ctx.t(key)
    parts, pos = [], 0
    for m in _FIELD.finditer(s):
        parts.append(H.esc(s[pos:m.start()]))
        name = m.group(1)
        if name not in kw:
            raise KeyError("%s: value %r missing" % (key, name))
        parts.append(str(kw[name]))
        pos = m.end()
    parts.append(H.esc(s[pos:]))
    return "".join(parts)


def p(ctx, key, **kw):
    return "<p>%s</p>" % fmt(ctx, key, **kw)


def prose(ctx, *keys, **kw):
    """Paragraphs of the given string keys inside a prose block."""
    return H.prose("".join(p(ctx, k, **kw) for k in keys))


def ul(ctx, keys, **kw):
    return H.ul([fmt(ctx, k, **kw) for k in keys])


def b(html):
    return "<strong>%s</strong>" % html


def e(s):
    return H.esc(s)


def join(ctx, parts, last="and"):
    """"a, b and c" / "a, b und c" (parts are HTML)."""
    parts = [x for x in parts if x]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    word = {"and": ("und", "and"), "or": ("oder", "or")}[last][0 if ctx.lang == "de" else 1]
    return ", ".join(parts[:-1]) + " " + word + " " + parts[-1]


def quote(ctx, text):
    """Game text as a quotation in the page language's quotation marks."""
    return ("„%s“" if ctx.lang == "de" else "“%s”") % H.esc(text)


# ------------------------------------------------------------------ names with links
def sp_obj(ctx, const):
    return SPECIES.by_const(const, ctx.lang)


def species(ctx, const, icon=False):
    sp = const if hasattr(const, "const") else SPECIES.by_const(const, ctx.lang)
    return H.species_link(ctx, sp, icon=icon)


def item_obj(ctx, const):
    return ITEMS.by_const(const, ctx.lang)


def item(ctx, const, icon=False):
    it = const if hasattr(const, "const") else ITEMS.by_const(const, ctx.lang)
    return H.item_link(ctx, it, icon=icon)


def move(ctx, const):
    mv = const if hasattr(const, "const") else MOVES.by_const(const, ctx.lang)
    return H.move_link(ctx, mv)


def ability(ctx, const):
    ab = const if hasattr(const, "const") else ABILITIES.by_const(const, ctx.lang)
    return H.ability_link(ctx, ab)


def place(ctx, m, text=None):
    """A map (Map object, MAP_ id or map folder) as its linked place name."""
    if isinstance(m, str):
        m = MAPS.by_id(m, ctx.lang) if m.startswith("MAP_") else MAPS.by_dir(m, ctx.lang)
    name = text if text is not None else m.display
    if m.mapsec in ("MAPSEC_DYNAMIC", "MAPSEC_NONE"):
        return H.esc(name)
    return H.location_link(ctx, m.mapsec, name)


def mapsec(ctx, const):
    return H.location_link(ctx, const, MAPS.mapsec_name(const, ctx.lang))


def region_name(ctx, region):
    """"Kanto" | "Johto" | "Hoenn" (keys of gamedata.maps) -> the site's region name."""
    return ctx.ui("region_" + REGION_KEY[region])


def region_chip(ctx, region):
    return H.region_chip(ctx, REGION_KEY[region])


def trainer_name(ctx, const):
    tr = TRAINERS.by_const(const, ctx.lang)
    return tr.name if tr else ""


def trainer(ctx, const, text=None):
    tr = TRAINERS.by_const(const, ctx.lang)
    return H.link(ctx, "trainer", const, text if text is not None else (tr.name if tr else ""))


def page(ctx, path, text=None):
    return H.page_link(ctx, path, text)


def anchor_link(ctx, path, frag, text):
    """Link to a section of one of the long-form pages (plain text when the page is missing)."""
    url = ctx.url(path)
    if not url:
        return H.esc(text)
    return '<a href="%s#%s">%s</a>' % (url, frag, H.esc(text))


def faq(items):
    """[(question text, answer HTML)] as a list of folds."""
    return "".join(H.details(q, H.prose(a)) for q, a in items)
