"""Natures (src/pokemon.c: gNaturesInfo).

    natures.all_natures()            -> [Nature] in id order (NATURE_HARDY = 0 ...)
    natures.by_const("NATURE_ADAMANT"), natures.by_id(3)
    natures.by_party_name("Adamant") -> the nature a .party line "Adamant Nature" names
                                        (tools/trainerproc: NATURE_ + upper case)

Nature fields: id, const, name (as the summary screen shows it), up / down (STAT_*
constant names of the raised and lowered stat; equal = neutral nature), neutral (bool),
lang, text_lang["name"].
Language: every function takes lang="de"|"en" (None = the process language).
"""
import functools

from . import tu as TU
from . import text
from . import entext
from . import namestyle

SRC = "src/pokemon.c"


class Nature:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Nature(%s %s)" % (self.const, self.name)


@functools.lru_cache(maxsize=None)
def _load(lang):
    t = TU.load(SRC, lang=lang)
    de_t = TU.load(SRC, lang="de")
    de_table = de_t.table("gNaturesInfo") if lang != "de" else {}
    names = t.names("NATURE_")
    stats = t.names("STAT_")
    out = []
    for nid, e in sorted(t.table("gNaturesInfo").items()):
        const = names.get(nid, "NATURE_%d" % nid)
        raw = {"name": t.text_field(e, "name")}
        raw_de = raw if lang == "de" else {"name": de_t.text_field(de_table.get(nid), "name")}
        if lang == "en":
            raw = entext.resolve("nature", const, raw, raw_de)
        written = text.written_in(raw["name"], raw_de["name"], lang)
        up, down = t.field(e, "statUp", 0), t.field(e, "statDown", 0)
        out.append(Nature(id=nid, const=const, name=namestyle.show(text.name(raw["name"], written), written, "nature", lang),
                          name_game=text.name(raw["name"], written),
                          up=stats.get(up, up), down=stats.get(down, down), neutral=up == down,
                          lang=lang, text_lang={"name": written}, entry=e))
    return out


def all_natures(lang=None):
    return list(_load(TU.lang(lang)))


def by_id(nid, lang=None):
    for n in _load(TU.lang(lang)):
        if n.id == nid:
            return n
    return None


def by_const(const, lang=None):
    for n in _load(TU.lang(lang)):
        if n.const == const:
            return n
    return None


def by_party_name(name, lang=None):
    """Nature of a .party line ("Adamant Nature" -> NATURE_ADAMANT)."""
    if not name:
        return None
    return by_const("NATURE_" + name.strip().upper().replace(" ", "_"), lang)
