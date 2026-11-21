"""Abilities (src/pokemon.c: gAbilitiesInfo).

    a = abilities.by_const("ABILITY_OVERGROW")   -> a.name "Notdünger", a.description
    abilities.all_abilities() -> {id: Ability} without ABILITY_NONE
    abilities.holders(aid)    -> {"regular": [Species], "hidden": [Species]}

Language: every function takes lang="de"|"en" (None = the process language). a.lang is the
build, a.text_lang = {"name": .., "description": ..} the language each text is written in there.
"""
import functools

from . import tu as TU
from . import text
from . import entext
from . import namestyle

SRC = "src/pokemon.c"


class Ability:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Ability(%s %s)" % (self.const, self.name)


def _t(lang=None):
    return TU.load(SRC, lang=lang)


def _load(lang=None):
    return _load_lang(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _load_lang(lang):
    t = _t(lang)
    de_t = _t("de")
    de_table = de_t.table("gAbilitiesInfo") if lang != "de" else {}
    names = t.canonical("ABILITY_", "Ability")
    out = {}
    for aid, e in t.table("gAbilitiesInfo").items():
        if aid == 0:
            continue
        name = t.text_field(e, "name")
        if not name:
            continue
        raw = {"name": name, "description": t.text_field(e, "description")}
        de_e = de_table.get(aid)
        raw_de = raw if lang == "de" else {"name": de_t.text_field(de_e, "name"),
                                           "description": de_t.text_field(de_e, "description")}
        const = names.get(aid, "ABILITY_%d" % aid)
        if lang == "en":
            raw = entext.resolve("ability", const, raw, raw_de)
        text_lang = {k: text.written_in(raw[k], raw_de[k], lang) for k in raw}
        out[aid] = Ability(id=aid, const=const,
                           name=namestyle.show(text.name(raw["name"], text_lang["name"]), text_lang["name"], "ability", lang),
                           name_game=text.name(raw["name"], text_lang["name"]),
                           description=text.clean(raw["description"], text_lang["description"]),
                           lang=lang, text_lang=text_lang, entry=e)
    return out


def all_abilities(lang=None):
    return dict(_load(lang))


def by_id(aid, lang=None):
    return _load(lang).get(aid)


def by_const(const, lang=None):
    v = _t("de").const(const)
    return _load(lang).get(v) if v is not None else None


def by_name(name, lang=None):
    for a in sorted(_load(lang).values(), key=lambda x: x.id):
        if a.name == name:
            return a
    return None


def field(a, key, default=None):
    return _t(a.lang).field(a.entry, key, default)


@functools.lru_cache(maxsize=None)
def _holders(lang):
    from . import species
    out = {}
    for sp in sorted(species.all_species(lang).values(), key=lambda s: s.id):
        for slot, aid in enumerate(sp.abilities[:3]):
            if not aid:
                continue
            d = out.setdefault(aid, {"regular": [], "hidden": []})
            lst = d["hidden"] if slot == 2 else d["regular"]
            if sp not in lst:
                lst.append(sp)
    return out


def holders(aid, lang=None):
    return _holders(TU.lang(lang)).get(aid, {"regular": [], "hidden": []})
