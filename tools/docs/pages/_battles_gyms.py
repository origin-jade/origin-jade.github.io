"""The three region pages (battles/kanto, battles/johto, battles/hoenn): the eight gyms
in badge order, the Elite Four and the champion, with every version of each battle.

Badges, gym maps and permits: gamedata.hand_progress; persons and battle versions:
pages._battles_data; rewards, obedience and field moves: pages._battles_facts.
"""
import functools

from common import html as H
from gamedata import hand_progress as HP
from gamedata import items as IT
from gamedata import levels
from gamedata import moves as MV
from gamedata import trainers as T

from pages import _battles_data as D
from pages import _battles_facts as F
from pages import _battles_view as V

PATHS = {"Kanto": "battles/kanto", "Johto": "battles/johto", "Hoenn": "battles/hoenn"}
# The league a class belongs to: the Kanto league of the first journey, the league that
# takes over the Indigo Plateau for Johto, and Hoenn's league.
LEAGUE_OF = {
    "TRAINER_CLASS_ELITE_FOUR_FRLG": "Kanto", "TRAINER_CLASS_CHAMPION_FRLG": "Kanto",
    "TRAINER_CLASS_ELITE_FOUR_HNS": "Johto", "TRAINER_CLASS_CHAMPION_HNS": "Johto",
    "TRAINER_CLASS_ELITE_FOUR": "Hoenn", "TRAINER_CLASS_CHAMPION": "Hoenn",
}


class Gym:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _roles(es):
    return {D.role_of(T.by_const(e.const)) for e in es}


@functools.lru_cache(maxsize=None)
def leaders_by_map():
    """{gym map id: [person]} of the gym leaders, the first leader of a gym first."""
    out = {}
    for es in D.groups():
        if "leader" in _roles(es):
            out.setdefault(D.head_entry(es).map_id, []).append(es)
    for lst in out.values():
        lst.sort(key=lambda es: (min(D.first_step(e) for e in es), es[0].order))
    return out


@functools.lru_cache(maxsize=None)
def gyms(region):
    """[Gym(n, badge_map, gym_map, persons, permit)] in badge order."""
    out = []
    lm = leaders_by_map()
    for b in HP.badges(region):
        gm = getattr(b, "fight_map", None) or b.map
        out.append(Gym(n=b.n, badge_map=b.map.id, gym_map=gm.id, persons=lm.get(gm.id, []),
                       permit=b.permit.const if b.permit else None))
    return out


@functools.lru_cache(maxsize=None)
def league(region):
    """(elite four persons, champion persons) of a region's league, in room order.
    The Kanto champion is the rival: one person per starter."""
    e4, champ = [], []
    for es in D.groups():
        for e in es:
            tr = T.by_const(e.const)
            if LEAGUE_OF.get(tr.class_const) != region:
                continue
            role = D.role_of(tr)
            sub = [x for x in es if LEAGUE_OF.get(T.by_const(x.const).class_const) == region]
            (champ if role == "champion" else e4).append(sub)
            break
    return e4, champ


def region_persons(region):
    """Every person shown on a region page (the trainer index marks them)."""
    out = []
    for g in gyms(region):
        out.extend(g.persons)
    e4, champ = league(region)
    return out + e4 + champ


# ------------------------------------------------------------------ rendering
def _tm_html(ctx, tms):
    parts = []
    for iid, title in tms:
        it = IT.by_id(iid, ctx.lang)
        if it is None:
            continue
        mv = MV.by_id(it.tm[2], ctx.lang) if it.tm else None
        s = H.item_link(ctx, it, icon=True)
        if mv is not None:
            s += " " + H.move_link(ctx, mv)
        if title is not None:
            s += " " + H.chip(ctx.t("cond_after", region=V.region_name(ctx, V.REGIONS[title])), "muted")
        parts.append(s)
    return "<br>".join(parts) if parts else None


def _person_tms(es):
    out = []
    for e in es:
        if e.row is not None:
            continue
        for x in F.reward_tms(e.map_id, e.const, e.label):
            if x not in out:
                out.append(x)
    return out


def gym_tms(g):
    """[(Item id, title index or None)] the first leader of a gym hands out. Normally the
    item follows the battle; where the leader gives it in a later talk (same gym) or at
    the place where the Badge is handed over, it is the TM a script there gives."""
    tms = _person_tms(g.persons[0]) if g.persons else []
    if tms:
        return tms
    found = F.map_gift_tms(g.gym_map)
    if not found and g.badge_map != g.gym_map:
        found = F.mapsec_gift_tms(g.badge_map)
    return [(x, None) for x in found[:1]]


def _order_note(ctx, e, leader_names):
    oc = F.order_conditions(e.map_id).get(e.const)
    if not oc:
        return None, None
    beaten, others = oc
    names = [leader_names.get(m) for m in others if leader_names.get(m)]
    if len(names) != len(others) or len(names) != 2:
        return None, None
    key = ("order_0", "order_1", "order_2")[beaten] if beaten <= 2 else None
    if key is None:
        return None, None
    return ctx.t("v_order", n=beaten + 1), ctx.t(key, a=names[0], b=names[1])


def _dyn_note(ctx, e):
    if e.mode != "leader":
        return None
    lo, hi = levels.leader_band()
    return ctx.t("leader_band_note", lo=lo, hi=hi, when=V.steps_text(ctx, e.steps))


def _version_labels(ctx, es, leader_names):
    labels, notes = [], []
    for i, e in enumerate(es):
        lb, note = _order_note(ctx, e, leader_names)
        if lb is None:
            lb = ctx.t("v_first") if i == 0 and e.row is None else V.version_label(ctx, es, i)
        notes.append(note)
        labels.append(lb)
    return V.unique_labels(labels), notes


def versions(ctx, es, tab_id, leader_names=None, anchor=None):
    """Every battle of a person: one card, or tabs with one card per version.
    Returns (html, [facts])."""
    labels, notes = _version_labels(ctx, es, leader_names or {})
    cards, facts_all = [], []
    for i, e in enumerate(es):
        note = []
        if notes[i]:
            note.append("<p>%s</p>" % H.esc(notes[i]))
        dn = _dyn_note(ctx, e)
        if dn:
            note.append("<p>%s</p>" % H.esc(dn))
        if e.mode == "special":
            note.append("<p>%s</p>" % H.esc(ctx.t("special_note")))
        card, facts = V.battle_card(ctx, e, note_html="".join(note) or None,
                                    id=anchor if i == 0 else None)
        cards.append(card)
        facts_all.append(facts)
    if len(cards) == 1:
        return cards[0], facts_all
    return H.tabs([(labels[i], cards[i], str(i + 1)) for i in range(len(cards))], tab_id), facts_all


def _obey_html(ctx, region, g):
    ob = F.obedience_levels().get(region)
    if not ob:
        return None
    return H.esc(ctx.t("unlock_obey" if g.n != 1 else "unlock_obey_1", lv=ob[g.n], n=g.n))


def _field_html(ctx, region, g):
    """Field moves the Badge allows outside of battle."""
    if region == "Kanto":
        mvs = [MV.by_const(c, ctx.lang) for c in F.kanto_field_moves().get(g.n, [])]
    else:
        mvs = [MV.by_const(g.permit, ctx.lang)] if g.permit else []
    mvs = [m for m in mvs if m is not None]
    if not mvs:
        return None
    return V.join(ctx, [H.move_link(ctx, m) for m in mvs])


def _gym_section(ctx, region, g, leader_names, overview):
    t = ctx.t
    if not g.persons:
        ctx.todo("%s: no leader found for gym %d" % (region, g.n))
        return ""
    first = g.persons[0]
    name = V.person_name(ctx, first)
    place = V.place_name(ctx, g.gym_map)
    sid = "gym-%d" % g.n
    tms = gym_tms(g)
    body = []
    pairs = [(ctx.ui("location"), V.place_link(ctx, g.gym_map)),
             (t("kv_badge"), H.esc(t("badge_n", n=g.n, region=V.region_name(ctx, region)))),
             (t("kv_obey"), _obey_html(ctx, region, g)),
             (t("kv_field_" + V.REGION_KEY[region]), _field_html(ctx, region, g)),
             (t("kv_tm"), _tm_html(ctx, tms))]
    if g.badge_map != g.gym_map:
        pairs.insert(2, (t("kv_badge_place"), V.place_link(ctx, g.badge_map)))
    body.append(H.kv(pairs))
    html, facts = versions(ctx, first, sid + "-v", leader_names, anchor=None)
    body.append(html)
    ace = facts[0]["levels"][1] if facts else None
    overview.append(['%d. <a href="#%s">%s</a>' % (g.n, sid, H.esc(name)), V.place_link(ctx, g.gym_map),
                     H.esc(ctx.level(ace)) if ace else None, _tm_html(ctx, [x for x in tms if x[1] is None])])
    for k, es in enumerate(g.persons[1:], 2):
        nm = V.person_name(ctx, es)
        extra = []
        if any(e.league_change for e in es):
            extra.append(H.prose("<p>%s</p>" % H.esc(t("later_leader", name=V.person_name_mid(ctx, es),
                                                         n=F.league_change_badges()))))
        tm2 = _tm_html(ctx, _person_tms(es))
        if tm2:
            extra.append(H.kv([(t("kv_tm"), tm2)]))
        h2, _f = versions(ctx, es, "%s-p%d" % (sid, k), leader_names)
        extra.append(h2)
        body.append(H.sub(t("later_leader_title", name=nm), "".join(extra), id="%s-p%d-h" % (sid, k)))
    return H.section(t("gym_title", n=g.n, place=place, name=name), "".join(body), id=sid)


def _starter_tabs(ctx, persons, tab_id):
    """Rival persons (one per starter) as tabs; inside each, the battles stacked."""
    panels = []
    for k, es in enumerate(persons):
        sp = V.starter_species(ctx, es)
        label = ctx.t("rival_with", species=sp.name) if sp else ctx.t("variant_n", n=k + 1)
        labels, _n = _version_labels(ctx, es, {})
        cards = []
        for i, e in enumerate(es):
            card, _f = V.battle_card(ctx, e, chips=[H.chip(labels[i], "jade")] if len(es) > 1 else [])
            cards.append(card)
        panels.append((label, "".join(cards), str(k + 1)))
    if len(panels) == 1:
        return panels[0][1]
    return H.tabs(panels, tab_id)


def _levels_note(ctx, region, gl):
    """The note under the overview; its numbers come from the data."""
    t = ctx.t
    rk = V.REGION_KEY[region]
    if region == "Kanto":
        lo, hi = levels.leader_band()
        return t("levels_note_kanto", lo=lo, hi=hi)
    if region == "Johto":
        free = [g.n for g in gl if g.persons and any(F.order_conditions(e.map_id).get(e.const)
                                                      for e in g.persons[0] if e.row is None)]
        if not free or free != list(range(free[0], free[-1] + 1)):
            ctx.todo("battles/johto: the gyms with a free order are not a run of numbers any more (%s)" % free)
            free = free or [0]
        return t("levels_note_johto", gyms="%d %s %d" % (free[0], t("word_to"), free[-1]))
    stages = max((e.stage[-1] for g in gl for es in g.persons for e in es if e.row is not None), default=0)
    return t("levels_note_hoenn", n=stages)


def render_region(ctx, region):
    t = ctx.t
    rk = V.REGION_KEY[region]
    ctx.begin(PATHS[region])
    gl = gyms(region)
    leader_names = {g.gym_map: V.person_name(ctx, g.persons[0]) for g in gl if g.persons}
    overview, secs = [], []
    for g in gl:
        secs.append(_gym_section(ctx, region, g, leader_names, overview))
    e4, champ = league(region)
    lg = []
    if e4:
        place = V.place_link(ctx, e4[0][0].map_id)
        lg.append(H.prose("<p>%s</p>" % V.fmt(ctx, "league_intro_" + rk, place=place, n=len(e4) + (1 if champ else 0),
                                              badges=F.league_change_badges())))
        for k, es in enumerate(e4, 1):
            html, _f = versions(ctx, es, "e4-%d-v" % k)
            lg.append(H.sub(V.person_name(ctx, es), html, id="e4-%d" % k))
    champ_html = ""
    if champ:
        if len(champ) > 1:
            inner = H.prose("<p>%s</p>" % H.esc(t("champ_rival_intro"))) + _starter_tabs(ctx, champ, "champ-v")
        else:
            inner, _f = versions(ctx, champ[0], "champ-v")
        champ_html = H.section(t("champ_title", name=V.person_name(ctx, champ[0])), inner, id="champion")
    head = H.section(t("sec_overview"), H.table(
        [(t("col_leader"), "main"), ctx.ui("location"), (t("col_ace"), "num"),
         t("kv_tm")], overview) + H.callout(ctx, "note", "<p>%s</p>" % H.esc(_levels_note(ctx, region, gl))),
        id="overview", intro=H.esc(t("overview_intro_" + rk)))
    body = head + "".join(secs)
    if lg:
        body += H.section(t("sec_e4"), "".join(lg), id="elite-four")
    body += champ_html
    order = ["battles/kanto", "battles/johto", "battles/hoenn"]
    i = order.index(PATHS[region])
    ctx.end(body, lead=H.esc(t("lead_" + rk)), chips=V.region_chip(ctx, region),
            prev=order[i - 1] if i else "battles/index", next=order[i + 1] if i + 1 < len(order) else "battles/rivals")
