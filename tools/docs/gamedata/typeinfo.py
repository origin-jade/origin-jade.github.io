"""Types and the type chart (module typeinfo; "types" would shadow the stdlib) (src/battle_main.c: gTypesInfo, gTypeEffectivenessTable).

    typeinfo.all_types()        -> [Type]   (every TYPE_*, id order, incl. NONE/MYSTERY/STELLAR)
    typeinfo.battle_types()     -> [Type]   (the 18 shown in charts: isSpecialCaseType == 0)
    typeinfo.by_const("TYPE_FIRE"), typeinfo.by_id(10)
    typeinfo.effectiveness(atk_id, def_id) -> 0.0 / 0.5 / 1.0 / 2.0  (exact value /4096)

Type fields: id, const ("TYPE_FIRE"), slug ("fire", the English id used in file
names, CSS classes t-<slug> and search tokens type<slug>), name ("Feuer"),
palette (13..15), palette_tmhm (symbol), special (bool), icon_png, icon_pal.

Language: all_types, battle_types, by_id and by_const take lang="de"|"en" (None = the
process language); t.lang is the build, t.text_lang["name"] the language the name is written in.
"""
import functools

from . import tu as TU
from . import text
from . import entext
from . import namestyle

SRC = "src/battle_main.c"
# graphics/types/<file>.png differs from the slug for these
_ICON_FILE = {"fighting": "fight"}


class Type:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Type(%s %s)" % (self.const, self.name)


def _load(lang=None):
    return _load_lang(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _load_lang(lang):
    t = TU.load(SRC, lang=lang)
    de_t = TU.load(SRC, lang="de")
    de_table = de_t.table("gTypesInfo") if lang != "de" else {}
    names = t.names("TYPE_")
    out = []
    for tid, e in sorted(t.table("gTypesInfo").items()):
        const = names.get(tid)
        slug = const[5:].lower()
        f = _ICON_FILE.get(slug, slug)
        pal = t.field(e, "palette", 13)
        raw = {"name": t.text_field(e, "name"), "generic": t.text_field(e, "generic")}
        raw_de = raw if lang == "de" else {"name": de_t.text_field(de_table.get(tid), "name"),
                                           "generic": de_t.text_field(de_table.get(tid), "generic")}
        if lang == "en":
            raw = entext.resolve("type", const, raw, raw_de)
        text_lang = {k: text.written_in(raw[k], raw_de[k], lang) for k in raw}
        out.append(Type(
            id=tid, const=const, slug=slug,
            name=namestyle.show(text.name(raw["name"], text_lang["name"]), text_lang["name"], "type", lang),
            name_game=text.name(raw["name"], text_lang["name"]), lang=lang, text_lang=text_lang,
            generic=text.name(raw["generic"], text_lang["generic"]),
            palette=pal, palette_tmhm=str(t.field(e, "paletteTMHM") or ""),
            special=bool(t.field(e, "isSpecialCaseType", 0)),
            damage_category=t.field(e, "damageCategory"),
            icon_png="graphics/types/%s.png" % f,
            icon_pal="graphics/types/move_types_%d.pal" % (pal - 12),
        ))
    chart = {}
    for atk, row in t.table("gTypeEffectivenessTable").items():
        vals = t.value(row)
        for dfn, v in enumerate(vals):
            chart[(atk, dfn)] = v / 4096.0
    return out, chart


def all_types(lang=None):
    return list(_load(lang)[0])


def battle_types(lang=None):
    return [x for x in _load(lang)[0] if not x.special]


def by_id(tid, lang=None):
    for x in _load(lang)[0]:
        if x.id == tid:
            return x
    return None


def by_const(const, lang=None):
    for x in _load(lang)[0]:
        if x.const == const:
            return x
    return None


def effectiveness(atk, dfn):
    """Multiplier of attacking type atk on defending type dfn (ids)."""
    return _load()[1].get((atk, dfn), 1.0)
