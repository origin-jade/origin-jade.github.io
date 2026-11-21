"""Shared building blocks of the battle pages: names, places, teams as the game
fields them, battle cards and level tables.

Every function takes the page context first; names come from the data layer in
the page language, wording from the STRINGS of pages/battles.py.
"""
from common import html as H
from common import slugs
from gamedata import abilities as AB
from gamedata import items as IT
from gamedata import levels
from gamedata import maps
from gamedata import moves as MV
from gamedata import species as SP
from gamedata import trainers as T
from gamedata import trainers_rematch as RM

from pages import _battles_data as D
from pages import _battles_facts as F

REGION_KEY = {"Kanto": "kanto", "Johto": "johto", "Hoenn": "hoenn"}
REGIONS = ("Kanto", "Johto", "Hoenn")
STARTER_CONSTS = tuple("SPECIES_" + s for s in D.STARTERS)
_missing = set()          # (trainer const, species const) the build has no data for


def missing_species():
    return sorted(_missing)


# ------------------------------------------------------------------ names
def trainer(ctx, const):
    return T.by_const(const, ctx.lang)


def trainer_name(ctx, tr):
    """Name as the battle shows it; the Kanto rival carries the name the player chose."""
    if tr.class_const in D.RIVAL_NAME_CLASSES or "{" in (tr.name or ""):
        return ctx.t("rival_name")
    return tr.name


def person_name_mid(ctx, es):
    """person_name for the middle of a sentence ("dein Rivale")."""
    n = person_name(ctx, es)
    return ctx.t("rival_name_mid") if n == ctx.t("rival_name") else n


def person_name(ctx, es):
    names = [trainer_name(ctx, trainer(ctx, e.const)) for e in es]
    rn = ctx.t("rival_name")
    if rn in names:
        return rn
    return trainer_name(ctx, trainer(ctx, D.head_entry(es).const))


def region_name(ctx, region):
    return ctx.ui("region_" + REGION_KEY[region]) if region in REGION_KEY else ctx.t("region_other")


def region_chip(ctx, region):
    return H.region_chip(ctx, REGION_KEY[region]) if region in REGION_KEY else H.chip(ctx.t("region_other"), "muted")


def place_name(ctx, map_id):
    return maps.by_id(map_id, ctx.lang).display


def place_key(map_id):
    """Registry key of the location page a map belongs to (None: no map section of its own)."""
    m = maps.by_id(map_id)
    if m.mapsec in ("MAPSEC_DYNAMIC", "MAPSEC_NONE", None):
        return None
    return m.mapsec


def entry_places(ctx, e, link=True):
    """The place of a battle, or its alternative places joined with "/" (HTML or text)."""
    ids = [e.map_id] + list(getattr(e, "alt_maps", ()))
    if link:
        return " / ".join(place_link(ctx, m) for m in ids)
    return " / ".join(place_name(ctx, m) for m in ids)


def place_link(ctx, map_id):
    key = place_key(map_id)
    name = place_name(ctx, map_id)
    return H.location_link(ctx, key, name) if key else H.esc(name)


def step_text(ctx, step):
    return RM.step_label(step, ctx.lang)


def steps_text(ctx, steps):
    return RM.steps_label(steps, ctx.lang)


def title_cond_text(ctx, e):
    """"after the Kanto title, before the Johto title" from the title flags the script tests."""
    after, before = D.title_condition(e)
    parts = []
    if after is not None:
        parts.append(ctx.t("cond_after", region=region_name(ctx, REGIONS[after])))
    if before is not None:
        parts.append(ctx.t("cond_before", region=region_name(ctx, REGIONS[before])))
    return ", ".join(parts)


def fmt(ctx, key, **html):
    """Module string with HTML values: the sentence is escaped, the values are inserted as given."""
    marks = {k: "\x00%d\x00" % i for i, k in enumerate(html)}
    s = H.esc(ctx.t(key, **marks))
    for k, v in html.items():
        s = s.replace(marks[k], str(v))
    return s


def join(ctx, parts, word="and"):
    parts = [p for p in parts if p]
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " " + ctx.t("word_" + word) + " " + parts[-1]


# ------------------------------------------------------------------ teams
def _species(ctx, sid):
    return SP.by_id(sid, ctx.lang) if sid else None


def _moves(ctx, ids):
    out = []
    for x in ids:
        mv = MV.by_id(x, ctx.lang) if x else None
        if mv is not None:
            out.append(mv)
    return out


def team(ctx, e, detail=True):
    """(members for H.team_member, facts) of a battle.

    facts: {"levels": (lo, hi), "last": level of the last Pokémon or None when it depends
    on progress, "default_moves": True when a Pokémon without written moves is in the team
    of a battle whose levels depend on progress, "count": Pokémon fielded}"""
    tr = T.by_const(e.const)
    tm = D.team_of(e)
    members = []
    lo_all, hi_all = 10 ** 6, 0
    dyn_default = False
    last = None
    for em in tm.mons:
        mon = em.mon
        if tm.dynamic:
            opts = [s for s in em.species_options if s]
            lo, hi = em.level_range
        else:
            opts = [em.species]
            lo = hi = em.level
        sps = [_species(ctx, s) for s in opts]
        if not sps or any(s is None for s in sps):
            _missing.add((e.const, mon.species_const))
            continue
        lo_all, hi_all = min(lo_all, lo), max(hi_all, hi)
        last = None if tm.dynamic and lo != hi else hi
        sp = sps[-1]
        m = {"species": sp, "shiny": bool(mon.shiny)}
        if lo == hi:
            m["level"] = lo
        else:
            m["level_text"] = ctx.level_range(lo, hi)
        notes = []
        if len(sps) > 1:
            notes.append(ctx.t("evolves_note", names=" → ".join(s.name for s in sps)))
        if detail:
            if mon.item:
                it = IT.by_id(mon.item, ctx.lang)
                if it is not None:
                    m["item"] = it
            ab = D.ability_of(mon, opts[-1])
            a = AB.by_id(ab, ctx.lang) if ab else None
            if a is not None:
                m["ability"] = a
            if mon.nature:
                nat = T.nature_name(mon, ctx.lang)
                if nat:
                    m["nature"] = nat
            if any(mon.moves):
                m["moves"] = _moves(ctx, mon.moves)
            elif not tm.dynamic:
                m["moves"] = _moves(ctx, D.default_moves(SP.by_id(opts[-1]), hi))
            else:
                dyn_default = True
        if notes:
            m["note"] = " ".join(notes)
        members.append(m)
    if not members:
        lo_all = hi_all = 0
    return members, {"levels": (lo_all, hi_all), "last": last, "default_moves": dyn_default,
                     "count": len(members), "dynamic": tm.dynamic, "team": tm}


def prize(ctx, e, facts):
    """Prize money of a fixed-level battle (None when the level depends on progress)."""
    if facts["last"] is None or not facts["count"]:
        return None
    tr = T.by_const(e.const)
    return F.prize_money(tr.money, facts["last"], tr.double, e.command in T.TWO_OPPONENT_COMMANDS)


def bag_chip(ctx, tr):
    """Chip with the items a trainer uses in battle ("4× Top-Genesung")."""
    if not tr.items:
        return None
    counts = []
    for iid in tr.items:
        for c in counts:
            if c[0] == iid:
                c[1] += 1
                break
        else:
            counts.append([iid, 1])
    parts = []
    for iid, n in counts:
        it = IT.by_id(iid, ctx.lang)
        if it is not None:
            parts.append("%d× %s" % (n, it.name))
    return H.chip(ctx.t("bag", items=", ".join(parts)), "muted") if parts else None


def band_table(ctx, e, facts):
    """Level by progress for a battle whose levels follow the player's progress."""
    tm = facts["team"]
    if not tm.dynamic or not tm.by_step:
        return ""
    rows, cur = [], None
    for s, ms in tm.by_step:
        lv = [x.level for x in ms if SP.by_id(x.species) is not None]
        if not lv:
            continue
        sig = (min(lv), max(lv))
        if cur and cur[1] == sig and cur[0][-1] + 1 == s.step:
            cur[0].append(s.step)
        else:
            cur = [[s.step], sig]
            rows.append(cur)
    body = [[H.esc(steps_text(ctx, steps)), H.esc(ctx.level_range(a, b))] for steps, (a, b) in rows]
    return H.details(ctx.t("band_title"), H.table(
        [(ctx.t("col_progress"), "main"), (ctx.t("col_team_levels"), "num")], body))


def battle_card(ctx, e, *, id=None, chips=(), note_html=None, detail=True, show_place=False,
                show_prize=True, name=None):
    """H.trainer_card of one battle."""
    tr = trainer(ctx, e.const)
    members, facts = team(ctx, e, detail)
    meta = list(chips)
    if show_place:
        meta.insert(0, H.chip(entry_places(ctx, e, link=False), "muted"))
    bag = bag_chip(ctx, tr) if detail else None
    if bag:
        meta.append(bag)
    notes = []
    if note_html:
        notes.append(note_html)
    if facts["default_moves"] and detail:
        notes.append("<p>%s</p>" % H.esc(ctx.t("default_moves_note")))
    if facts["dynamic"] and detail:
        notes.append(band_table(ctx, e, facts))
    reward = prize(ctx, e, facts) if show_prize and detail else None
    return H.trainer_card(ctx, name or trainer_name(ctx, tr), members, cls_name=tr.class_name, pic=tr, id=id,
                          detail=detail, double=tr.double, reward=reward, meta=meta,
                          note="".join(notes) or None), facts


# ------------------------------------------------------------------ versions of a person's battle
def version_label(ctx, es, i):
    """Label of the i-th battle of a person (tab titles, list items)."""
    e = es[i]
    t = ctx.t
    if e.row is not None and e.mode in ("phone", "special"):
        return t("v_rematch_n", n=e.stage[0]) if len(e.stage) == 1 else t(
            "v_rematch_range", a=e.stage[0], b=e.stage[-1])
    after, before = D.title_condition(e)
    if e.mode == "leader" and after is None and e.steps and not e.league_change:
        # no title test on the way: the earliest step tells when
        first = min(e.steps)
        if first >= 20:
            after = 1
        elif first >= 10:
            after = 0
    if after is not None:
        return t("v_rematch_after", region=region_name(ctx, REGIONS[after]))
    if i > 0 and before is not None:
        return t("v_rematch_before", region=region_name(ctx, REGIONS[before]))
    return t("v_first") if i == 0 else t("v_rematch")


def unique_labels(labels):
    seen, count, out = {}, {}, []
    for lb in labels:
        seen[lb] = seen.get(lb, 0) + 1
    for lb in labels:
        if seen[lb] > 1:
            count[lb] = count.get(lb, 0) + 1
            out.append("%s (%d)" % (lb, count[lb]))
        else:
            out.append(lb)
    return out


def max_level(e):
    return D.max_level(e)


def anchor_of(const):
    return "t-" + slugs.slug(const)


def trainer_link(ctx, es, text):
    """Link to the trainer's anchor on a location page (plain text while nobody registered it)."""
    for e in [D.head_entry(es)] + list(es):
        if ctx.has("trainer", e.const):
            return H.link(ctx, "trainer", e.const, text)
    return H.esc(text)


def starter_species(ctx, es):
    """The starter line a rival variant fields: the base starter species whose family
    shows up in the person's teams (None when no starter is found)."""
    fam = {}
    for c in STARTER_CONSTS:
        base = SP.by_const(c)
        if base is None:
            continue
        ids, todo = set(), [base.id]
        while todo:
            x = todo.pop()
            if x in ids:
                continue
            ids.add(x)
            sp = SP.by_id(x)
            for ev in (sp.evolutions or []) if sp else []:
                todo.append(ev.target)
        fam[base.id] = ids
    for e in es:
        for m in T.by_const(e.const).mons:
            for base, ids in fam.items():
                if m.species in ids:
                    return SP.by_id(base, ctx.lang if ctx is not None else None)
    return None
