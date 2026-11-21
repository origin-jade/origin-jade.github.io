"""Data for the development gallery: turns loader results into the inputs of
the components. Page authors can copy these functions as a starting point;
they cover the simple cases only (see the notes in each function).
"""
from gamedata import abilities, encounters, items, maps, moves, species, trainers, trainers_items

TIME_ID = {"TIME_MORNING": "morning", "TIME_DAY": "day", "TIME_EVENING": "evening", "TIME_NIGHT": "night"}
REGION_ID = {"Kanto": "kanto", "Johto": "johto", "Hoenn": "hoenn"}


def evo_tree(ctx, sp):
    """Evolution tree for H.evolution_chain, starting at the first stage.
    Only "reach level N" and "use item" are worded here; other methods get no label."""
    lang = ctx.lang
    base, seen = sp, {sp.id}
    while True:
        prev = species.evolves_from(base.id, lang)
        if not prev or prev[0][0].id in seen:
            break
        base = prev[0][0]
        seen.add(base.id)

    def how(evo):
        if evo.method == "EVO_LEVEL" and evo.param:
            return ctx.level(evo.param)
        if evo.method == "EVO_ITEM":
            it = items.by_id(evo.param, lang)
            return it.name if it else None
        return None

    def node(s, label, depth):
        kids = []
        if depth < 4:
            for evo in s.evolutions:
                target = species.by_id(evo.target, lang)
                if target is not None:
                    kids.append(node(target, how(evo), depth + 1))
        return {"species": s, "how": label, "children": kids}
    return node(base, None, 0)


def learnsets(ctx, sp):
    """(level, tm, tutor, egg) lists for H.learnset."""
    lang = ctx.lang
    level = [(lv, moves.by_id(mid, lang)) for lv, mid in sp.levelup]
    teach = set(sp.teachable)
    tm = []
    for kind, num, mid in moves.tm_hm_moves():
        if mid in teach:
            it = items.by_tm(kind, num, lang)
            tm.append((it.name if it else "%s%02d" % (kind, num), moves.by_id(mid, lang)))
    machine = {mid for _k, _n, mid in moves.tm_hm_moves()}
    tutor = [moves.by_id(mid, lang) for mid in moves.tutor_moves() if mid in teach and mid not in machine]
    egg = [moves.by_id(mid, lang) for mid in sp.egg_moves]
    return ([x for x in level if x[1]], [x for x in tm if x[1]], [m for m in tutor if m], [m for m in egg if m])


def enc_blocks(ctx, map_id):
    """Blocks for H.encounters: one per method; a method whose table changes
    with the time of day gets one block per time group."""
    lang = ctx.lang
    groups = encounters.time_groups(map_id)
    blocks = []
    for area in encounters.AREAS:
        per_group = [(times, d.get(area)) for times, d in groups if d.get(area)]
        if not per_group:
            continue
        keys = {tuple((r.species, r.pct, r.eff_min, r.eff_max) for r in rows) for _t, rows in per_group}
        same = len(keys) == 1 and len(per_group) == len(groups)
        for times, rows in (per_group[:1] if same else per_group):
            blocks.append({
                "method": area,
                "times": None if same else [TIME_ID[t] for t in times],
                "rows": [{"species": species.by_id(r.species, lang), "lo": r.eff_min, "hi": r.eff_max,
                          "rate": r.pct} for r in rows],
            })
    return blocks


def default_moves(sp, level, lang):
    """Moves of a trainer Pokémon without a move list: the last four level-up moves up to its level."""
    out = []
    for lv, mid in sp.levelup:
        if lv <= level and mid not in out:
            out.append(mid)
    return [moves.by_id(m, lang) for m in out[-4:]]


def team(ctx, tr, map_id, detail=True):
    """Team dicts for H.trainer_card (fixed-level battles)."""
    lang = ctx.lang
    out = []
    for e in trainers.effective_team(tr, map_id, "normal").mons:
        sp = species.by_id(e.species, lang)
        m = {"species": sp, "level": e.level, "shiny": bool(e.mon.shiny)}
        if detail:
            if e.mon.item:
                m["item"] = items.by_id(e.mon.item, lang)
            ab = e.mon.ability
            if isinstance(ab, int) and ab:
                m["ability"] = abilities.by_id(ab, lang)
            mv = [moves.by_id(x, lang) for x in e.mon.moves] if e.mon.moves else default_moves(sp, e.level, lang)
            m["moves"] = [x for x in mv if x]
        out.append(m)
    return out


def map_trainers(map_id, lang):
    """[(Trainer, Battle)] of the first battles on a map (no rematches), in trainer order."""
    out = []
    for const, tr in trainers.all_trainers(lang).items():
        for b in trainers.battles(const):
            if b.map_id == map_id and b.rematch_row is None and "rematch" not in b.command \
                    and trainers.battle_mode(tr, b) == "normal":
                out.append((tr, b))
                break
    return out


def map_items(ctx, map_id):
    """Entries for H.item_list (found and hidden items of a map) and for H.shop_table."""
    lang = ctx.lang
    found, shop = [], []
    for iid, lst in sorted(trainers_items.sources().items()):
        it = items.by_id(iid, lang)
        if it is None:
            continue
        for s in lst:
            if s.map_id != map_id:
                continue
            if s.kind in ("ball", "hidden"):
                mv = moves.by_id(it.tm[2], lang) if it.tm else None      # a TM/HM: say which move it teaches
                found.append({"item": it, "qty": s.amount or 1, "hidden": s.kind == "hidden",
                              "how": mv.name if mv else None})
            elif s.kind == "shop":
                shop.append({"item": it, "price": s.price})
    return found, shop


def where_rows(ctx, sp):
    """[(Map, method, [time ids] or None, row)] for a "where to find" table."""
    out = []
    for map_id, area, times, row in encounters.where(sp.id):
        m = maps.by_id(map_id, ctx.lang)
        if m is None or maps.locked_mapsec(m.mapsec):
            continue
        all_day = len(times) == len(encounters.times())
        out.append((m, area, None if all_day else [TIME_ID[t] for t in times], row))
    return out
