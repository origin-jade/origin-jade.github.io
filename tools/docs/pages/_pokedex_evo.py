"""Evolution wording of the Pokédex pages.

Reads gSpeciesInfo[].evolutions through gamedata.species (method, parameter,
target, IF_* conditions) and words every entry in the page language. The
checks follow GetEvolutionTargetSpecies / DoesMonMeetAdditionalConditions in
src/pokemon.c:
  * EVO_LEVEL with parameter 0 is "any level-up" (conditions decide);
  * EVO_TRADE works for link trades and in-game trades (src/trade.c);
  * EVO_ITEM: the item is used on the Pokémon;
  * EVO_SPLIT_FROM_EVO: a second Pokémon appears when the evolution into the
    parameter species happens and the party has a free slot (CreateShedinja,
    src/evolution_scene.c);
  * IF_TIME / IF_NOT_TIME compare GetTimeOfDay() (hours: include/constants/rtc.h);
  * IF_PID_* compare the personality value; the share of values that pass is
    shown as a percentage.
An entry that cannot be worded is left out and reported with ctx.todo.
"""
import re

from common import html as H
from gamedata import items, maps, moves, species, tu, wild_maps

S = {
    "de": {
        "e_levelup": "Levelaufstieg",
        "e_trade": "Tausch",
        "e_item": "{item} einsetzen",
        "e_split": "erscheint zusätzlich bei der Entwicklung zu {species}, wenn im Team ein Platz frei ist",
        "e_or": " oder ",
        "c_friendship": "Freundschaft ab {n}",
        "c_time": "{time} ({hours})",
        "c_not_time": "nicht {time} ({hours})",
        "tod_morning": "morgens", "tod_day": "tagsüber", "tod_evening": "abends", "tod_night": "nachts",
        "hours": "{a}–{b} Uhr",
        "c_hold": "trägt {item}",
        "c_knows": "kennt {move}",
        "c_place": "Ort: {places}",
        "c_used": "{move} {n}× eingesetzt",
        "c_male": "nur Männchen",
        "c_female": "nur Weibchen",
        "c_atk_gt_def": "{atk} höher als {df}",
        "c_atk_lt_def": "{atk} niedriger als {df}",
        "c_atk_eq_def": "{atk} gleich {df}",
        "c_random": "zufällig ({pct})",
        "c_party": "{species} im Team",
        "c_bag": "{n}× {item} im Beutel (wird verbraucht)",
        "c_beauty": "Schönheit ab {n}",
        "evo_from": "Von",
        "evo_to": "Zu",
        "evo_how": "Bedingung",
    },
    "en": {
        "e_levelup": "Level up",
        "e_trade": "Trade",
        "e_item": "use {item}",
        "e_split": "also appears when it evolves into {species}, if the party has a free slot",
        "e_or": " or ",
        "c_friendship": "friendship {n} or higher",
        "c_time": "{time} ({hours})",
        "c_not_time": "not {time} ({hours})",
        "tod_morning": "in the morning", "tod_day": "during the day", "tod_evening": "in the evening",
        "tod_night": "at night",
        "hours": "{a}–{b}",
        "c_hold": "holding {item}",
        "c_knows": "knows {move}",
        "c_place": "at {places}",
        "c_used": "used {move} {n} times",
        "c_male": "male only",
        "c_female": "female only",
        "c_atk_gt_def": "{atk} higher than {df}",
        "c_atk_lt_def": "{atk} lower than {df}",
        "c_atk_eq_def": "{atk} equal to {df}",
        "c_random": "random ({pct})",
        "c_party": "{species} in the party",
        "c_bag": "{n}× {item} in the Bag (is used up)",
        "c_beauty": "Beauty {n} or higher",
        "evo_from": "From",
        "evo_to": "To",
        "evo_how": "How",
    },
}

_FIELD = re.compile(r"\{(\w+)\}")
_TIMES = ("morning", "day", "evening", "night")


class V:
    """A value with a plain-text and an HTML form."""
    def __init__(self, plain, html=None):
        self.plain = str(plain)
        self.html = H.esc(plain) if html is None else html


def _fmt(ctx, key, **vals):
    """Module string with values -> V (the sentence is escaped, HTML values are inserted)."""
    s = ctx.t(key)
    plain, parts, pos = [], [], 0
    for m in _FIELD.finditer(s):
        lit = s[pos:m.start()]
        v = vals[m.group(1)]
        if not isinstance(v, V):
            v = V(v)
        plain += [lit, v.plain]
        parts += [H.esc(lit), v.html]
        pos = m.end()
    plain.append(s[pos:])
    parts.append(H.esc(s[pos:]))
    return V("".join(plain), "".join(parts))


def _t():
    return tu.load("src/pokemon.c")


def hour_label(ctx, h):
    h %= 24
    if ctx.lang == "de":
        return str(h)
    return "%d %s" % ((h % 12) or 12, "AM" if h < 12 else "PM")


def hours_text(ctx, begin, end):
    return ctx.t("hours", a=hour_label(ctx, begin), b=hour_label(ctx, end))


def time_hours(ctx):
    """{"night": (19, 6), ...} of the build."""
    return {k[len("TIME_"):].lower(): v for k, v in wild_maps.time_hours().items()}


def _time_cond(ctx, value, negate):
    t = _t()
    name = None
    for tid in _TIMES:
        if t.const("TIME_" + tid.upper()) == value:
            name = tid
    hours = time_hours(ctx).get(name) if name else None
    if not hours:
        return None
    b, e = hours
    if negate:
        b, e = e, b
        if name == "night":          # "not at night" is simply the day
            return _fmt(ctx, "c_time", time=ctx.t("tod_day"), hours=hours_text(ctx, b, e))
    return _fmt(ctx, "c_not_time" if negate else "c_time", time=ctx.t("tod_" + name), hours=hours_text(ctx, b, e))


def _item(ctx, iid, icon=False):
    it = items.by_id(iid, ctx.lang)
    return V(it.name, H.item_link(ctx, it, icon=icon)) if it else None


def _move(ctx, mid):
    mv = moves.by_id(mid, ctx.lang)
    return V(mv.name, H.move_link(ctx, mv)) if mv else None


def _species(ctx, sid):
    sp = species.by_id(sid, ctx.lang)
    return V(sp.name, H.species_link(ctx, sp)) if sp else None


def _place(ctx, num):
    const = tu.load("src/level_scaling.c").names("MAPSEC_").get(num)
    name = maps.mapsec_name(const, ctx.lang) if const else None
    if not name or name == const:
        return None
    return V(name, H.location_link(ctx, const, name))


def _condition(ctx, name, args):
    """One IF_* condition -> V or None (unknown)."""
    t = _t()
    a = list(args) + [None, None]
    names = H.stat_names(ctx)
    if name == "IF_MIN_FRIENDSHIP":
        return _fmt(ctx, "c_friendship", n=a[0])
    if name in ("IF_TIME", "IF_NOT_TIME"):
        return _time_cond(ctx, a[0], name == "IF_NOT_TIME")
    if name == "IF_HOLD_ITEM":
        v = _item(ctx, a[0])
        return _fmt(ctx, "c_hold", item=v) if v else None
    if name == "IF_KNOWS_MOVE":
        v = _move(ctx, a[0])
        return _fmt(ctx, "c_knows", move=v) if v else None
    if name == "IF_USED_MOVE_X_TIMES":
        v = _move(ctx, a[0])
        return _fmt(ctx, "c_used", move=v, n=a[1]) if v else None
    if name == "IF_GENDER":
        if a[0] == t.need("MON_MALE"):
            return _fmt(ctx, "c_male")
        if a[0] == t.need("MON_FEMALE"):
            return _fmt(ctx, "c_female")
        return None
    if name in ("IF_ATK_GT_DEF", "IF_ATK_LT_DEF", "IF_ATK_EQ_DEF"):
        return _fmt(ctx, "c_" + name[3:].lower(), atk=names["atk"], df=names["def"])
    # personality checks: share of the values that pass
    pct = None
    if name == "IF_PID_MODULO_100_GT":
        pct = 99 - a[0]
    elif name == "IF_PID_MODULO_100_EQ":
        pct = 1
    elif name == "IF_PID_UPPER_MODULO_10_GT":
        pct = (9 - a[0]) * 10
    elif name == "IF_PID_UPPER_MODULO_10_LT":
        pct = a[0] * 10
    if pct is not None:
        return _fmt(ctx, "c_random", pct=ctx.pct(pct))
    if name == "IF_SPECIES_IN_PARTY":
        v = _species(ctx, a[0])
        return _fmt(ctx, "c_party", species=v) if v else None
    if name == "IF_BAG_ITEM_COUNT":
        v = _item(ctx, a[0])
        return _fmt(ctx, "c_bag", item=v, n=a[1]) if v else None
    if name == "IF_MIN_BEAUTY":
        return _fmt(ctx, "c_beauty", n=a[0])
    return None


def _method(ctx, evo, icon):
    m = evo.method
    if m == "EVO_LEVEL":
        return V(ctx.level(evo.param)) if evo.param else _fmt(ctx, "e_levelup")
    if m == "EVO_ITEM":
        v = _item(ctx, evo.param, icon)
        return _fmt(ctx, "e_item", item=v) if v else None
    if m == "EVO_TRADE":
        return _fmt(ctx, "e_trade")
    if m == "EVO_SPLIT_FROM_EVO":
        v = _species(ctx, evo.param)
        return _fmt(ctx, "e_split", species=v) if v else None
    return None


def alternatives(ctx, sp, target_id, icon=False):
    """Every way sp evolves into target_id: [V]. Entries that differ only in
    the place (IF_IN_MAPSEC) are joined into one."""
    groups, order = {}, []
    for evo in sp.evolutions:
        if evo.target != target_id:
            continue
        places = [a[0] for n, a in evo.conditions if n == "IF_IN_MAPSEC"]
        rest = tuple((n, tuple(a)) for n, a in evo.conditions if n != "IF_IN_MAPSEC")
        key = (evo.method, evo.param, rest)
        if key not in groups:
            groups[key] = (evo, [])
            order.append(key)
        groups[key][1].extend(places)
    out = []
    for key in order:
        evo, places = groups[key]
        first = _method(ctx, evo, icon)
        parts = [first]
        if places:
            pv = [_place(ctx, p) for p in places]
            if None in pv:
                parts.append(None)
            else:
                parts.append(_fmt(ctx, "c_place", places=V(" / ".join(p.plain for p in pv),
                                                           " / ".join(p.html for p in pv))))
        for n, a in key[2]:
            parts.append(_condition(ctx, n, a))
        if None in parts:
            ctx.todo("Evolution of %s into species %s: method or condition not worded (%s, %r)"
                     % (sp.const, target_id, evo.method, evo.conditions))
            continue
        out.append(V(", ".join(p.plain for p in parts), ", ".join(p.html for p in parts)))
    return out


def root_of(sp, lang):
    base, seen = sp, {sp.id}
    while True:
        prev = species.evolves_from(base.id, lang)
        if not prev or prev[0][0].id in seen:
            return base
        base = prev[0][0]
        seen.add(base.id)


def tree(ctx, sp):
    """(tree for H.evolution_chain, steps): the tree starts at the first stage of
    sp's line; steps = [(from Species, to Species, [V])] in tree order."""
    lang = ctx.lang
    steps = []

    def node(s, label, depth, path):
        kids = []
        if depth < 5:
            seen = []
            for evo in s.evolutions:
                if evo.target in seen or evo.target in path:
                    continue
                seen.append(evo.target)
                target = species.by_id(evo.target, lang)
                if target is None:
                    continue
                alts = alternatives(ctx, s, evo.target, icon=False)
                if not alts:
                    continue
                steps.append((s, target, alts))
                kids.append(node(target, ctx.t("e_or").join(a.plain for a in alts), depth + 1,
                                 path | {evo.target}))
        return {"species": s, "how": label, "children": kids}
    root = root_of(sp, lang)
    return node(root, None, 0, {root.id}), steps


def steps_table(ctx, steps):
    """Table of every step of a line with linked items, moves and places."""
    rows = []
    for src, dst, alts in steps:
        how = alts[0].html if len(alts) == 1 else H.ul([a.html for a in alts])
        rows.append([H.species_link(ctx, src, icon=True), H.species_link(ctx, dst, icon=True), how])
    return H.table([(ctx.t("evo_from"), ""), (ctx.t("evo_to"), "main"), (ctx.t("evo_how"), "")], rows)


def search_words(sp, lang):
    """Names of evolution items for the search keywords of a species."""
    out = []
    for e in sp.evolutions:
        if e.method == "EVO_ITEM" and items.by_id(e.param, lang):
            out.append(items.by_id(e.param, lang).name)
    return out
