"""Species data (src/pokemon.c: gSpeciesInfo and its learnsets).

    sp = species.by_const("SPECIES_BULBASAUR")
    sp.name, sp.stats["hp"], sp.bst, sp.types (type ids), sp.abilities ([a1, a2, hidden] ids, 0 = none)
    sp.levelup  -> [(level, move_id), ...]   (the learnset the ROM uses, P_LVL_UP_LEARNSETS)
    sp.teachable -> [move_id, ...]           (TM, HM and tutor moves; split with moves.tm_hm_moves())
    sp.egg_moves -> [move_id, ...]
    sp.evolutions -> [Evolution(method, param, target, conditions)]
    species.all_species()            -> {id: Species} incl. forms, without SPECIES_NONE/SPECIES_EGG
    species.by_name("Bisasam")       -> Species (first match; forms share names)
    species.dex("national"|"kanto"|"johto"|"hoenn"|"obtainable") -> [(number, Species), ...]
    species.dex_blocks()             -> {"Kanto": (first, last), ...} of the obtainable dex
    species.evolves_from(id)         -> [(Species, Evolution), ...]
    species.forms(id)                -> [Species, ...] (formSpeciesIdTable; [] without forms)

Language: every function takes lang="de"|"en" as its last argument (None = the process
language, tu.LANG); species.by_const("SPECIES_BULBASAUR", "en").name is what the English
build shows. sp.lang is the build, sp.text_lang = {"name": .., "category": .., "description": ..}
says in which language each text is really written there ("de" when the English build
carries the German string). Numbers are the same objects' fields in both languages.
    species.gender(ratio)            -> ("genderless"|"female_only"|"male_only"|"mixed", female percent or None)
    species.gender_text(ratio, lang) -> "12,5 % weiblich" / "12.5% female"

Species fields: id, const, slug ("bulbasaur", file name in assets/mon and assets/icon),
name, category, description (one line), types, type_consts, stats (hp atk def spa spd spe),
bst, abilities, egg_groups (EGG_GROUP_* names), gender_ratio (0..254, 255 genderless),
catch_rate, exp_yield, ev_yield (same keys as stats), growth_rate (GROWTH_* name), egg_cycles,
friendship, height (dm), weight (hg), natdex, held_common/held_rare (item ids, 0 = none),
flags (every is*/cannot*/dex* field that is set), form_table (symbol or None),
gfx (front, front_female, palette, shiny_palette, icon, icon_pal_index; repo paths),
entry (the raw parsed initializer; read other fields with species.field(sp, "name")).
"""
import functools
import re

from . import repo_path
from . import tu as TU
from . import text
from . import entext
from . import namestyle
from . import cparse as C

SRC = "src/pokemon.c"
STAT_FIELDS = (("hp", "baseHP"), ("atk", "baseAttack"), ("def", "baseDefense"),
               ("spa", "baseSpAttack"), ("spd", "baseSpDefense"), ("spe", "baseSpeed"))
EV_FIELDS = (("hp", "evYield_HP"), ("atk", "evYield_Attack"), ("def", "evYield_Defense"),
             ("spa", "evYield_SpAttack"), ("spd", "evYield_SpDefense"), ("spe", "evYield_Speed"))
GENDERLESS = 255
FEMALE_ONLY = 254
MALE_ONLY = 0


class Evolution:
    def __init__(self, method, param, target, conditions):
        self.method = method            # EVO_* constant name
        self.param = param              # level / item id / ... (meaning depends on method)
        self.target = target            # species id
        self.conditions = conditions    # [(IF_* name, [args...]), ...]

    def __repr__(self):
        return "Evolution(%s, %r, %r, %r)" % (self.method, self.param, self.target, self.conditions)


class Species:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Species(%s %s)" % (self.const, self.name)


def _t(lang=None):
    return TU.load(SRC, lang=lang)


def _incbin_png(sym):
    """INCBIN path of a symbol -> the checked-in source PNG/PAL (repo relative)."""
    if not sym:
        return None
    p = _t("de").incbin.get(str(sym))
    if not p:
        return None
    p = re.sub(r"\.(4bpp|8bpp)(\.smol|\.lz)?$", ".png", p)
    p = re.sub(r"\.gbapal(\.lz)?$", ".pal", p)
    return p


def _list_until(t, sym, end_names):
    """Flat u16 list of a learnset symbol up to its terminator."""
    if not sym:
        return []
    out = []
    end = {t.const(n) for n in end_names}
    for v in t.init(str(sym)).positional():
        x = t.value(v)
        if x in end:
            break
        out.append(x)
    return out


def _load(lang=None):
    return _load_lang(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _load_lang(lang):
    t = _t(lang)
    # German strings of the same entries: tells which texts the English build really translates
    de_t = _t("de")
    de_table = de_t.table("gSpeciesInfo") if lang != "de" else {}
    names = t.canonical("SPECIES_")
    egg_groups = t.names("EGG_GROUP_")
    growth = t.names("GROWTH_")
    evo_names = t.names("EVO_")
    if_names = t.names("IF_")
    level_up_end = t.const("LEVEL_UP_END", 0xFFFF)
    out = {}
    egg = t.const("SPECIES_EGG")
    for sid, e in t.table("gSpeciesInfo").items():
        if sid in (0, egg):
            continue
        name = t.text_field(e, "speciesName")
        if not name:
            continue
        raw = {"name": name, "category": t.text_field(e, "categoryName"),
               "description": t.text_field(e, "description")}
        de_e = de_table.get(sid)
        raw_de = raw if lang == "de" else {
            "name": de_t.text_field(de_e, "speciesName"), "category": de_t.text_field(de_e, "categoryName"),
            "description": de_t.text_field(de_e, "description")}
        const = names.get(sid, "SPECIES_%d" % sid)
        if lang == "en":
            raw = entext.resolve("species", const, raw, raw_de)
        text_lang = {k: text.written_in(raw[k], raw_de[k], lang) for k in raw}
        stats = {k: t.field(e, f, 0) for k, f in STAT_FIELDS}
        ev = {k: t.field(e, f, 0) for k, f in EV_FIELDS}
        gr = t.field(e, "genderRatio", 0)
        # levelup: {.move = X, .level = N} until LEVEL_UP_END
        levelup = []
        lsym = t.field(e, "levelUpLearnset")
        if lsym and t.has_symbol(str(lsym)):
            for v in t.init(str(lsym)).positional():
                if not isinstance(v, C.Init):
                    continue
                mv = t.value(v.get("move")) if v.get("move") is not None else t.value(v.positional()[0])
                lv = t.value(v.get("level")) if v.get("level") is not None else t.value(v.positional()[1])
                if mv == level_up_end or lv == level_up_end:
                    break
                levelup.append((lv, mv))
        tsym = t.field(e, "teachableLearnset")
        esym = t.field(e, "eggMoveLearnset")
        evos = []
        ev_init = e.get("evolutions")
        if isinstance(ev_init, C.Init):
            for x in ev_init.positional():
                p = x.positional() if isinstance(x, C.Init) else []
                if len(p) < 3:
                    break
                method, param, target = (t.value(y) for y in p[:3])
                conds = []
                if len(p) > 3 and isinstance(p[3], C.Init):
                    for c in p[3].positional():
                        cv = t.value(c) if isinstance(c, C.Init) else [t.value(c)]
                        if not cv or cv[0] in (None, t.const("CONDITIONS_END")):
                            continue
                        conds.append((if_names.get(cv[0], cv[0]), cv[1:]))
                evos.append(Evolution(evo_names.get(method, method), param, target, conds))
        flags = {}
        for k, v in e.items:
            if k and (k.startswith("is") or k.startswith("cannot") or k.startswith("dex")
                      or k in ("perfectIVCount", "randomizerMode", "tmIlliterate")):
                val = t.value(v)
                if val:
                    flags[k] = val
        types_ = t.field(e, "types", [])
        out[sid] = Species(
            id=sid, const=const, slug=const[len("SPECIES_"):].lower(), lang=lang, text_lang=text_lang,
            name=namestyle.show(text.name(raw["name"], text_lang["name"]), text_lang["name"], "species", lang),
            name_game=text.name(raw["name"], text_lang["name"]),
            category=namestyle.show(text.name(raw["category"], text_lang["category"]), text_lang["category"],
                                    "category", lang),
            description=text.clean(raw["description"], text_lang["description"]),
            types=types_, type_consts=[t.names("TYPE_").get(x) for x in types_],
            stats=stats, bst=sum(stats.values()),
            abilities=list(t.field(e, "abilities", [0, 0, 0])) + [0] * (3 - len(t.field(e, "abilities", []))),
            egg_groups=[egg_groups.get(x, x) for x in t.field(e, "eggGroups", [])],
            gender_ratio=int(gr), catch_rate=t.field(e, "catchRate", 0),
            exp_yield=t.field(e, "expYield", 0), ev_yield=ev,
            growth_rate=growth.get(t.field(e, "growthRate", 0)),
            egg_cycles=t.field(e, "eggCycles", 0), friendship=t.field(e, "friendship", 0),
            height=t.field(e, "height", 0), weight=t.field(e, "weight", 0),
            natdex=t.field(e, "natDexNum", 0),
            held_common=t.field(e, "itemCommon", 0) or 0, held_rare=t.field(e, "itemRare", 0) or 0,
            levelup=levelup,
            teachable=_list_until(t, tsym, ("MOVE_UNAVAILABLE",)) if tsym and t.has_symbol(str(tsym)) else [],
            egg_moves=_list_until(t, esym, ("MOVE_UNAVAILABLE",)) if esym and t.has_symbol(str(esym)) else [],
            evolutions=evos, flags=flags,
            form_table=str(t.field(e, "formSpeciesIdTable")) if t.field(e, "formSpeciesIdTable") else None,
            gfx=dict(front=_incbin_png(t.field(e, "frontPic")),
                     front_female=_incbin_png(t.field(e, "frontPicFemale")),
                     palette=_incbin_png(t.field(e, "palette")),
                     shiny_palette=_incbin_png(t.field(e, "shinyPalette")),
                     icon=_incbin_png(t.field(e, "iconSprite")),
                     icon_pal_index=t.field(e, "iconPalIndex", 0)),
            entry=e,
        )
    return out


def all_species(lang=None):
    return dict(_load(lang))


def by_id(sid, lang=None):
    return _load(lang).get(sid)


def by_const(const, lang=None):
    sid = _t("de").const(const)
    return _load(lang).get(sid) if sid is not None else None


def by_slug(slug, lang=None):
    for sp in _load(lang).values():
        if sp.slug == slug:
            return sp
    return None


def by_name(name, lang=None):
    """First species (lowest id) with that name in the given build."""
    for sp in sorted(_load(lang).values(), key=lambda s: s.id):
        if sp.name == name:
            return sp
    return None


def by_natdex(num, lang=None):
    """The base form (lowest id) with that national number."""
    return _by_natdex(TU.lang(lang)).get(num)


@functools.lru_cache(maxsize=None)
def _by_natdex(lang):
    best = {}
    for sp in _load_lang(lang).values():
        if sp.natdex and (sp.natdex not in best or sp.id < best[sp.natdex].id):
            best[sp.natdex] = sp
    return best


def field(sp, key, default=None):
    """Any other gSpeciesInfo field of a species, evaluated."""
    return _t(sp.lang).field(sp.entry, key, default)


def forms(sid, lang=None):
    return list(_forms(sid, TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _forms(sid, lang):
    sp = by_id(sid, lang)
    if not sp or not sp.form_table:
        return ()
    t = _t(lang)
    ids = _list_until(t, sp.form_table, ("FORM_SPECIES_END",))
    return tuple(by_id(x, lang) for x in ids if by_id(x, lang))


@functools.lru_cache(maxsize=None)
def _evolves_from(lang):
    rev = {}
    for sp in sorted(_load_lang(lang).values(), key=lambda s: s.id):
        for e in sp.evolutions:
            rev.setdefault(e.target, []).append((sp, e))
    return rev


def evolves_from(sid, lang=None):
    return list(_evolves_from(TU.lang(lang)).get(sid, []))


@functools.lru_cache(maxsize=None)
def _regional(table, prefix):
    t = _t("de")
    out = []
    for k, v in sorted(t.table(table).items()):
        nat = t.value(v)
        out.append((k + 1, nat))
    return out


def dex(kind="obtainable", lang=None):
    """[(number, Species)] of a dex in its order.

    national: by natDexNum (base forms); kanto/johto/hoenn: the regional
    tables sKantoToNationalOrder/sJohtoToNationalOrder/sHoennToNationalOrder;
    obtainable: enum ObtainableDexOrder, the national dex the game shows.
    """
    return list(_dex(kind, TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _dex(kind, lang):
    t = _t("de")
    nat_map = _by_natdex(lang)
    if kind == "national":
        return tuple(sorted(nat_map.items()))
    if kind in ("kanto", "johto", "hoenn"):
        table = "s%sToNationalOrder" % kind.capitalize()
        return tuple((n, nat_map[nat]) for n, nat in _regional(table, kind.upper()) if nat in nat_map)
    if kind == "obtainable":
        out = []
        for v, n in sorted(t.names("OBTAINABLE_DEX_").items()):
            if v == 0 or not n.startswith("OBTAINABLE_DEX_"):
                continue
            nat = t.const("NATIONAL_DEX_" + n[len("OBTAINABLE_DEX_"):])
            if nat is None or v >= t.const("OBTAINABLE_DEX_COUNT", 1 << 30):
                continue
            sp = nat_map.get(nat)
            if sp:
                out.append((v, sp))
        return tuple(out)
    raise ValueError(kind)


@functools.lru_cache(maxsize=None)
def dex_blocks():
    """Region blocks of enum ObtainableDexOrder ({"Kanto": (first, last), ...}),
    read from the comments of include/constants/pokedex.h (cpp drops them),
    as tools/check_regions.py dex_order() does."""
    src = open(repo_path("include", "constants", "pokedex.h"), encoding="utf-8").read()
    body = re.search(r"enum ObtainableDexOrder\s*\{(.*?)\n\};", src, re.S)
    blocks, block, pos = {}, None, 0
    for line in body.group(1).splitlines():
        m = re.match(r"\s*//\s*(\w.*?)\s*$", line)
        if m:
            block = m.group(1)
            blocks[block] = [pos + 1, pos]
            continue
        for name in re.findall(r"\bOBTAINABLE_DEX_(\w+)\b", re.sub(r"//.*", "", line)):
            if name in ("NONE", "COUNT"):
                continue
            pos += 1
            if block in blocks:
                blocks[block][1] = pos
    return {k: tuple(v) for k, v in blocks.items()}


def gender(ratio):
    """(kind, female percent): kind "genderless", "female_only", "male_only" or "mixed";
    the percentage is ratio / 256 (None when genderless)."""
    if ratio == GENDERLESS:
        return "genderless", None
    if ratio == FEMALE_ONLY:
        return "female_only", 100.0
    if ratio == MALE_ONLY:
        return "male_only", 0.0
    return "mixed", ratio * 100.0 / 256


# Site wording of the gender line (not game text).
GENDER_TEXT = {
    "de": {"genderless": "Geschlechtslos", "female_only": "100 % weiblich", "male_only": "100 % männlich",
           "mixed": "%s %% weiblich", "decimal": ","},
    "en": {"genderless": "Genderless", "female_only": "100% female", "male_only": "100% male",
           "mixed": "%s%% female", "decimal": "."},
}


def gender_text(ratio, lang=None):
    """Gender line as the Pokédex page shows it ("12,5 % weiblich" / "12.5% female")."""
    S = GENDER_TEXT[TU.lang(lang)]
    kind, pct = gender(ratio)
    if kind != "mixed":
        return S[kind]
    # Display rounded to 0.1 like the usual 12.5 / 25 / 50 / 75 / 87.5 steps.
    s = ("%.1f" % pct).rstrip("0").rstrip(".").replace(".", S["decimal"])
    return S["mixed"] % s
