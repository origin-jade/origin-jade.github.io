"""Moves (data/moves): the list and one page per move.

Listed: every move below the Z-moves that a Pokémon of the game learns, that a TM, HM or
move tutor teaches, or that a trainer's Pokémon uses. Sources: gMovesInfo (values, flags,
additional effect chances), the learnsets of gSpeciesInfo, FOREACH_TM / FOREACH_HM,
the tutor scripts of the maps (gamedata.locations_services), GetMoveType and
GetBattleMoveCategory for the two settings that change type or category.
"""
import functools

from common import html as H
from common import search
from gamedata import cparse as C
from gamedata import dex_options, items, locations, maps, moves, species, trainers, tu, typeinfo
from gamedata import locations_services as LS

INDEX = "data/moves/index"

STRINGS = {
    "de": {
        "lead": "Alle {n} Attacken, die im Spiel vorkommen: Typ, Kategorie, Stärke, Genauigkeit und AP. "
                "Jede Attacke hat eine eigene Seite mit allen Pokémon, die sie lernen.",
        "placeholder": "Attacke suchen …",
        "facet_cat": "Kategorie",
        "facet_how": "Erhältlich als",
        "how_tm": "TM oder VM",
        "how_tutor": "Attacken-Lehrer",
        "eyebrow": "Attacke",
        "sec_data": "Werte",
        "priority": "Priorität",
        "crit": "Volltreffer-Stufe",
        "effect_chance": "Chance auf Zusatzeffekt",
        "target": "Ziel",
        "props": "Eigenschaften",
        "never_misses": "trifft immer",
        "tm": "TM / VM",
        "fairy": "Typ mit „{opt}“ = {off}",
        "split": "Kategorie mit „{opt}“ = {off}",
        "sec_tutor": "Attacken-Lehrer",
        "tutor_intro": "Hier bringt jemand deinen Pokémon diese Attacke bei.",
        "col_place": "Ort",
        "col_cond": "Bedingung",
        "tutor_bp": "{n} Gewinnpunkte",
        "tutor_once": "einmalig",
        "sec_level": "Durch Level-Aufstieg",
        "sec_teach": "Durch TM, VM oder Attacken-Lehrer",
        "sec_egg": "Als Ei-Attacke",
        "level_intro": "Diese Pokémon lernen die Attacke auf dem angegebenen Level.",
        "teach_intro": "Diesen Pokémon kann die Attacke beigebracht werden.",
        "egg_intro": "Diese Pokémon können die Attacke von einem Elternteil erben.",
        "nobody": "Kein Pokémon lernt diese Attacke selbst. Sie kommt nur bei Pokémon von Trainern vor.",
        "count": "{n} Pokémon",
        "t_selected": "Ein Ziel nach Wahl",
        "t_user": "Anwender",
        "t_both": "Alle Gegner",
        "t_foes_and_ally": "Alle anderen Pokémon auf dem Feld",
        "t_field": "Ganzes Feld",
        "t_random": "Zufälliger Gegner",
        "t_ally": "Partner",
        "t_opponents_field": "Seite des Gegners",
        "t_all_battlers": "Alle Pokémon auf dem Feld",
        "t_user_and_ally": "Anwender und Partner",
        "t_user_or_ally": "Anwender oder Partner",
        "flag_makesContact": "Direkter Kontakt",
        "flag_soundMove": "Lärm-Attacke",
        "flag_punchingMove": "Schlag-Attacke",
        "flag_bitingMove": "Biss-Attacke",
        "flag_pulseMove": "Puls-Attacke",
        "flag_ballisticMove": "Ball- oder Bomben-Attacke",
        "flag_healingMove": "Heil-Attacke",
        "flag_slicingMove": "Schneide-Attacke",
        "flag_windMove": "Wind-Attacke",
        "flag_powderMove": "Pulver-Attacke",
        "flag_danceMove": "Tanz-Attacke",
        "flag_multiHit": "Trifft mehrmals",
        "flag_thawsUser": "Taut den Anwender auf",
        "flag_alwaysCriticalHit": "Immer ein Volltreffer",
        "flag_ignoresProtect": "Trifft trotz {move}",
        "flag_ignoresSubstitute": "Trifft trotz {move}",
        "flag_magicCoatAffected": "Wird von {move} zurückgeworfen",
        "flag_snatchAffected": "Kann mit {move} gestohlen werden",
    },
    "en": {
        "lead": "All {n} moves that appear in the game: type, category, power, accuracy and PP. "
                "Every move has its own page listing the Pokémon that learn it.",
        "placeholder": "Search move …",
        "facet_cat": "Category",
        "facet_how": "Available as",
        "how_tm": "TM or HM",
        "how_tutor": "Move Tutor",
        "eyebrow": "Move",
        "sec_data": "Data",
        "priority": "Priority",
        "crit": "Critical-hit stage",
        "effect_chance": "Chance of the added effect",
        "target": "Target",
        "props": "Properties",
        "never_misses": "never misses",
        "tm": "TM / HM",
        "fairy": "Type with “{opt}” = {off}",
        "split": "Category with “{opt}” = {off}",
        "sec_tutor": "Move Tutors",
        "tutor_intro": "Someone here teaches your Pokémon this move.",
        "col_place": "Place",
        "col_cond": "Condition",
        "tutor_bp": "{n} Battle Points",
        "tutor_once": "once",
        "sec_level": "By level-up",
        "sec_teach": "By TM, HM or Move Tutor",
        "sec_egg": "As an egg move",
        "level_intro": "These Pokémon learn the move at the level shown.",
        "teach_intro": "These Pokémon can be taught the move.",
        "egg_intro": "These Pokémon can inherit the move from a parent.",
        "nobody": "No Pokémon learns this move itself. Only trainers' Pokémon use it.",
        "count": "{n} Pokémon",
        "t_selected": "One target of your choice",
        "t_user": "User",
        "t_both": "All opponents",
        "t_foes_and_ally": "All other Pokémon on the field",
        "t_field": "Whole field",
        "t_random": "Random opponent",
        "t_ally": "Ally",
        "t_opponents_field": "Opponent's side",
        "t_all_battlers": "All Pokémon on the field",
        "t_user_and_ally": "User and ally",
        "t_user_or_ally": "User or ally",
        "flag_makesContact": "Makes contact",
        "flag_soundMove": "Sound move",
        "flag_punchingMove": "Punching move",
        "flag_bitingMove": "Biting move",
        "flag_pulseMove": "Pulse move",
        "flag_ballisticMove": "Ball or bomb move",
        "flag_healingMove": "Healing move",
        "flag_slicingMove": "Slicing move",
        "flag_windMove": "Wind move",
        "flag_powderMove": "Powder move",
        "flag_danceMove": "Dance move",
        "flag_multiHit": "Hits several times",
        "flag_thawsUser": "Thaws the user",
        "flag_alwaysCriticalHit": "Always a critical hit",
        "flag_ignoresProtect": "Hits through {move}",
        "flag_ignoresSubstitute": "Hits through {move}",
        "flag_magicCoatAffected": "Reflected by {move}",
        "flag_snatchAffected": "Can be stolen with {move}",
    },
}

# Flag -> move whose name the text uses (None: plain text).
FLAGS = (("makesContact", None), ("soundMove", None), ("punchingMove", None), ("bitingMove", None),
         ("pulseMove", None), ("ballisticMove", None), ("healingMove", None), ("slicingMove", None),
         ("windMove", None), ("powderMove", None), ("danceMove", None), ("multiHit", None),
         ("thawsUser", None), ("alwaysCriticalHit", None), ("ignoresProtect", "MOVE_PROTECT"),
         ("ignoresSubstitute", "MOVE_SUBSTITUTE"), ("magicCoatAffected", "MOVE_MAGIC_COAT"),
         ("snatchAffected", "MOVE_SNATCH"))
# Flags that only say something for a move aimed at another Pokémon.
AIMED_ONLY = ("ignoresProtect", "ignoresSubstitute")
AIMED = ("TARGET_SELECTED", "TARGET_BOTH", "TARGET_FOES_AND_ALLY", "TARGET_RANDOM")
TARGETS = {"TARGET_SELECTED": "t_selected", "TARGET_USER": "t_user", "TARGET_BOTH": "t_both",
           "TARGET_FOES_AND_ALLY": "t_foes_and_ally", "TARGET_FIELD": "t_field", "TARGET_RANDOM": "t_random",
           "TARGET_ALLY": "t_ally", "TARGET_OPPONENTS_FIELD": "t_opponents_field",
           "TARGET_ALL_BATTLERS": "t_all_battlers", "TARGET_USER_AND_ALLY": "t_user_and_ally",
           "TARGET_USER_OR_ALLY": "t_user_or_ally"}


@functools.lru_cache(maxsize=None)
def _machines():
    """{move id: (kind, number)}"""
    return {mid: (kind, num) for kind, num, mid in moves.tm_hm_moves()}


@functools.lru_cache(maxsize=None)
def _tutors():
    """{move id: [Tutor]} tutors on maps that have a page."""
    out = {}
    t = tu.load("src/move.c")
    for x in LS.tutors():
        if any(locations.key_of_map(mid) for mid in x.map_ids):
            out.setdefault(t.need(x.move), []).append(x)
    return out


@functools.lru_cache(maxsize=None)
def _trainer_moves():
    out = set()
    for tr in trainers.all_trainers().values():
        for mon in tr.mons:
            out.update(mon.moves or ())
    return out


@functools.lru_cache(maxsize=None)
def listed_ids():
    limit = tu.load("src/move.c").need("MOVES_COUNT")
    out = set()
    for m in moves.all_moves("de").values():
        if m.id >= limit:
            continue
        if any(moves.learners(m.id, "de").values()) or m.id in _machines() or m.id in _tutors() \
                or m.id in set(moves.tutor_moves()) or m.id in _trainer_moves():
            out.add(m.id)
    return frozenset(out)


def _sorted(lang):
    ids = listed_ids()
    return sorted((m for m in moves.all_moves(lang).values() if m.id in ids),
                  key=lambda m: (search.fold(m.name), m.id))


def _learners(lang, m):
    """(level [(Species, level)], teachable [Species], egg [Species]) in Pokédex order, one
    entry per name (forms that share the name of their base are listed once)."""
    L = moves.learners(m.id, lang)

    def key(sp):
        return (sp.natdex or 9999, sp.id)

    def uniq(lst, get=lambda x: x):
        seen, out = set(), []
        for x in lst:
            n = get(x).name
            if n not in seen:
                seen.add(n)
                out.append(x)
        return out
    lv = uniq(sorted(L["levelup"], key=lambda x: (key(x[0]), x[1])), lambda x: x[0])
    return lv, uniq(sorted(L["teachable"], key=key)), uniq(sorted(L["egg"], key=key))


def _chances(m):
    """additionalEffects[].chance values above 0, in order."""
    mt = tu.load("src/move.c")
    out = []

    def walk(v):
        if isinstance(v, C.Init):
            c = v.get("chance")
            if c is not None:
                val = mt.value(c)
                if isinstance(val, int) and val > 0:
                    out.append(val)
            for x in v.positional():
                walk(x)
    walk(m.entry.get("additionalEffects"))
    return out


def _flags(ctx, m):
    out = []
    for f, mv in FLAGS:
        if f not in m.flags or (f in AIMED_ONLY and m.target not in AIMED):
            continue
        if mv:
            other = moves.by_const(mv, ctx.lang)
            if other.id == m.id:
                continue
            out.append(ctx.t("flag_" + f, move=other.name))
        else:
            out.append(ctx.t("flag_" + f))
    return out


def _tm_item(ctx, m):
    mc = _machines().get(m.id)
    return items.by_tm(mc[0], mc[1], ctx.lang) if mc else None


def _tiles(ctx, sps, note=None):
    return H.ent_grid([H.species_tile(ctx, sp, number=sp.natdex or None, note=note(sp, x) if note else None)
                       for sp, x in sps])


def _tutor_section(ctx, m):
    t = ctx.t
    rows = []
    for x in _tutors().get(m.id, ()):
        seen = []
        for mid in x.map_ids:
            key = locations.key_of_map(mid)
            if key and key not in seen:
                seen.append(key)
        cond = []
        if x.cost is not None:
            cond.append(t("tutor_bp", n=ctx.num(x.cost)))
        if x.once:
            cond.append(t("tutor_once"))
        for key in seen:
            row = [H.location_link(ctx, key, ctx.title_of("location", key) or maps.mapsec_name(key, ctx.lang)),
                   H.esc(", ".join(cond)) if cond else None]
            if row not in rows:
                rows.append(row)
    if not rows:
        return ""
    cols = [(t("col_place"), "main"), t("col_cond")]
    if not any(r[1] for r in rows):
        cols, rows = cols[:1], [r[:1] for r in rows]
    return H.section(t("sec_tutor"), H.table(cols, rows), id="tutors", intro=H.esc(t("tutor_intro")))


def _data(ctx, m):
    t = ctx.t
    ty = typeinfo.by_id(m.type, ctx.lang)
    pairs = [
        (ctx.ui("type"), H.type_chip(ctx, ty)),
        (ctx.ui("category"), H.cat_chip(ctx, m.category)),
        (ctx.ui("power"), ctx.num(m.power) if m.power > 1 else H.dash(ctx)),
        (ctx.ui("accuracy"), H.esc(ctx.pct(m.accuracy) if m.accuracy else t("never_misses"))),
        (ctx.ui("pp"), ctx.num(m.pp)),
        (t("priority"), ("+%d" % m.priority if m.priority > 0 else "−%d" % -m.priority) if m.priority else None),
        (t("crit"), "+%d" % m.crit_stage if m.crit_stage else None),
    ]
    ch = _chances(m)
    pairs.append((t("effect_chance"), H.esc(" / ".join(ctx.pct(c) for c in ch)) if ch else None))
    tg = TARGETS.get(m.target)
    pairs.append((t("target"), H.esc(t(tg)) if tg else None))
    it = _tm_item(ctx, m)
    pairs.append((t("tm"), H.item_link(ctx, it, icon=True) if it else None))
    alt = dex_options.fairy_move_type(m)
    if alt is not None:
        o = dex_options.option("ITEM_MODE_FAIRY_TYPES", ctx.lang)
        pairs.append((t("fairy", opt=o.name, off=o.choices[0]), H.type_chip(ctx, typeinfo.by_id(alt, ctx.lang))))
    if m.category != "status":
        type_cat = {0: "physical", 1: "special"}.get(ty.damage_category)
        if type_cat and type_cat != m.category:
            o = dex_options.option("ITEM_MODE_SPLIT", ctx.lang)
            pairs.append((t("split", opt=o.name, off=o.choices[0]), H.cat_chip(ctx, type_cat)))
    body = H.kv(pairs)
    fl = _flags(ctx, m)
    if fl:
        body += H.sub(t("props"), H.chips([H.chip(x, "muted") for x in fl]))
    return H.section(t("sec_data"), body, id="data")


def register(ctx):
    ctx.add_page(INDEX)
    for m in _sorted(ctx.lang):
        ty = typeinfo.by_id(m.type, ctx.lang)
        ctx.add_entity("move", m.const, m.name, sub="%s · %s" % (ty.name, ctx.ui("cat_" + m.category)))


def render(ctx):
    t = ctx.t
    lang = ctx.lang
    alls = _sorted(lang)
    tutor_ids = set(_tutors()) | set(moves.tutor_moves())

    # ---- the list
    ctx.begin(INDEX)
    attrs = []
    for m in alls:
        how = []
        if m.id in _machines():
            how.append("tm")
        if m.id in tutor_ids:
            how.append("tutor")
        attrs.append(H.filter_attrs([m.name], type=[typeinfo.by_id(m.type, lang).slug], cat=m.category,
                                    how=how or None))
    bar = H.filter_bar(ctx, "moves", placeholder=t("placeholder"), facets=[
        H.type_facet(ctx),
        {"key": "cat", "label": t("facet_cat"),
         "options": [(c, ctx.ui("cat_" + c)) for c in ("physical", "special", "status")]},
        {"key": "how", "label": t("facet_how"), "options": [("tm", t("how_tm")), ("tutor", t("how_tutor"))]}])
    groups = H.letter_groups(
        [(m.name, (m, a)) for m, a in zip(alls, attrs)],
        lambda xs: H.move_table(ctx, [m for m, _a in xs], row_attrs=[a for _m, a in xs]), "moves")
    ctx.end(bar + groups,
            lead=H.esc(t("lead", n=ctx.num(len(alls)))))

    # ---- one page per move
    for i, m in enumerate(alls):
        ctx.begin("move", m.const)
        lv, teach, egg = _learners(lang, m)
        body = [_data(ctx, m), _tutor_section(ctx, m)]
        if lv:
            body.append(H.section(
                t("sec_level"),
                _tiles(ctx, lv, lambda sp, l: ctx.level(l) if l else ctx.ui("learn_evo")),
                id="level", intro=H.esc(t("level_intro"))))
        if teach:
            body.append(H.section(t("sec_teach"), _tiles(ctx, [(sp, None) for sp in teach]), id="teach",
                                  intro=H.esc(t("teach_intro"))))
        if egg:
            body.append(H.section(t("sec_egg"), _tiles(ctx, [(sp, None) for sp in egg]), id="egg",
                                  intro=H.esc(t("egg_intro"))))
        n = len({sp.name for sp, _ in lv} | {sp.name for sp in teach} | {sp.name for sp in egg})
        if not n:
            body.append(H.callout(ctx, "note", H.p(t("nobody"))))
        ty = typeinfo.by_id(m.type, lang)
        chips = [H.type_chip(ctx, ty), H.cat_chip(ctx, m.category)]
        if n:
            chips.append(H.chip(t("count", n=ctx.num(n)), "jade"))
        ctx.end("".join(body), eyebrow=t("eyebrow"), lead=H.esc(m.description) if m.description else None,
                chips=H.chips(chips),
                prev=("move", alls[i - 1].const) if i else None,
                next=("move", alls[i + 1].const) if i + 1 < len(alls) else None)
