"""Moves (src/move.c: gMovesInfo), TM/HM list, tutor moves.

    m = moves.by_const("MOVE_FLAMETHROWER")
    m.name, m.description, m.type (type id), m.category ("physical"|"special"|"status"),
    m.power, m.accuracy (0 = never misses), m.pp, m.priority, m.effect ("EFFECT_HIT"),
    m.target ("TARGET_SELECTED"), m.crit_stage, m.flags (set of boolean fields that are set,
    e.g. "makesContact"), m.entry (raw initializer; moves.field(m, "strikeCount"))
    moves.all_moves()      -> {id: Move} without MOVE_NONE and unnamed entries
    moves.by_name("Flammenwurf")
    moves.tm_hm_moves()    -> [("TM", 1, move_id), ..., ("HM", 1, move_id), ...]
                              (FOREACH_TM / FOREACH_HM of include/constants/tms_hms.h)
    moves.tutor_moves()    -> [move_id] (gTutorMoves, generated src/data/tutor_moves.h)
    moves.learners(move_id) -> {"levelup": [(Species, level)], "teachable": [Species], "egg": [Species]}

Language: all_moves, by_id, by_const, by_name and learners take lang="de"|"en" (None = the
process language). m.lang is the build, m.text_lang = {"name": .., "description": ..} the
language each text is really written in there ("de": the English build shows the German string).
"""
import functools

from . import tu as TU
from . import text
from . import entext
from . import namestyle
from . import cparse as C

SRC = "src/move.c"
CATEGORY = {0: "physical", 1: "special", 2: "status"}


class Move:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Move(%s %s)" % (self.const, self.name)


def _t(lang=None):
    return TU.load(SRC, lang=lang)


def _load(lang=None):
    return _load_lang(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _load_lang(lang):
    t = _t(lang)
    de_t = _t("de")
    de_table = de_t.table("gMovesInfo") if lang != "de" else {}
    names = t.canonical("MOVE_", "Move")
    effects = t.enum_names("BattleMoveEffects") or t.names("EFFECT_")
    targets = t.enum_names("MoveTarget") or t.names("TARGET_")
    out = {}
    for mid, e in t.table("gMovesInfo").items():
        if mid == 0:
            continue
        name = t.text_field(e, "name")
        if not name:
            continue
        raw = {"name": name, "description": t.text_field(e, "description")}
        de_e = de_table.get(mid)
        raw_de = raw if lang == "de" else {"name": de_t.text_field(de_e, "name"),
                                           "description": de_t.text_field(de_e, "description")}
        const = names.get(mid, "MOVE_%d" % mid)
        if lang == "en":
            raw = entext.resolve("move", const, raw, raw_de)
        text_lang = {k: text.written_in(raw[k], raw_de[k], lang) for k in raw}
        flags = set()
        for k, v in e.items:
            if k and not isinstance(v, C.Init) and k not in (
                    "power", "accuracy", "pp", "priority", "type", "category", "effect", "target",
                    "criticalHitStage", "name", "description", "contestEffect", "contestCategory",
                    "contestComboStarterId", "battleAnimScript", "strikeCount", "argument"):
                try:
                    val = t.value(v)
                except Exception:
                    continue
                if val is True or (isinstance(val, int) and not isinstance(val, C.Sym) and val == 1):
                    flags.add(k)
        out[mid] = Move(
            id=mid, const=const, name=namestyle.show(text.name(raw["name"], text_lang["name"]), text_lang["name"], "move", lang),
            name_game=text.name(raw["name"], text_lang["name"]), lang=lang, text_lang=text_lang,
            description=text.clean(raw["description"], text_lang["description"]),
            type=t.field(e, "type", 0), category=CATEGORY.get(t.field(e, "category", 0)),
            power=t.field(e, "power", 0), accuracy=t.field(e, "accuracy", 0),
            pp=t.field(e, "pp", 0), priority=t.field(e, "priority", 0),
            effect=effects.get(t.field(e, "effect", 0)), target=targets.get(t.field(e, "target", 0)),
            crit_stage=t.field(e, "criticalHitStage", 0), flags=flags, entry=e)
    return out


def all_moves(lang=None):
    return dict(_load(lang))


def by_id(mid, lang=None):
    return _load(lang).get(mid)


def by_const(const, lang=None):
    v = _t("de").const(const)
    return _load(lang).get(v) if v is not None else None


def by_name(name, lang=None):
    for m in sorted(_load(lang).values(), key=lambda x: x.id):
        if m.name == name:
            return m
    return None


def field(m, key, default=None):
    return _t(m.lang).field(m.entry, key, default)


@functools.lru_cache(maxsize=None)
def tm_hm_moves():
    t = _t("de")
    out = []
    for kind, macro in (("TM", "FOREACH_TM"), ("HM", "FOREACH_HM")):
        for i, m in enumerate(TU.x_macro("constants/tms_hms.h", macro), 1):
            out.append((kind, i, t.need("MOVE_" + m)))
    return out


@functools.lru_cache(maxsize=None)
def tutor_moves():
    t = TU.load("src/move_relearner.c", lang="de")
    return [x for x in t.array("gTutorMoves") if x not in (0, t.const("MOVE_UNAVAILABLE"))]


@functools.lru_cache(maxsize=None)
def _learners(lang):
    from . import species
    out = {}
    for sp in sorted(species.all_species(lang).values(), key=lambda s: s.id):
        for lv, mid in sp.levelup:
            out.setdefault(mid, {"levelup": [], "teachable": [], "egg": []})["levelup"].append((sp, lv))
        for mid in sp.teachable:
            out.setdefault(mid, {"levelup": [], "teachable": [], "egg": []})["teachable"].append(sp)
        for mid in sp.egg_moves:
            out.setdefault(mid, {"levelup": [], "teachable": [], "egg": []})["egg"].append(sp)
    return out


def learners(mid, lang=None):
    return _learners(TU.lang(lang)).get(mid, {"levelup": [], "teachable": [], "egg": []})
