"""battles/rivals: the rivals of the three regions (every encounter, per starter),
the villain teams with their bosses and admins, other special opponents and the
multi battles with a partner.

Persons and battles: pages._battles_data (only battles a script of this build can
start); which rival team belongs to which starter of the player: the lab scripts
(starter_pairs); partner teams: gamedata.trainers.partner_team; default rival names:
src/strings.c.
"""
import functools

from common import html as H
from gamedata import hand_facts
from gamedata import items as IT
from gamedata import levels
from gamedata import species as SP
from gamedata import trainers as T
from gamedata import trainers_rematch as RM
from gamedata import trainers_scriptdb as SDB

from pages import _battles_data as D
from pages import _battles_gyms as G
from pages import _battles_view as V

PATH = "battles/rivals"
# Villain teams: classes of the boss, the admins and the grunts.
TEAMS = (
    ("rocket", ("TRAINER_CLASS_BOSS_FRLG", "TRAINER_CLASS_ROCKET_ADMIN_HNS"),
     ("TRAINER_CLASS_TEAM_ROCKET_FRLG", "TRAINER_CLASS_TEAM_ROCKET_HNS")),
    ("aqua", ("TRAINER_CLASS_AQUA_LEADER", "TRAINER_CLASS_AQUA_ADMIN"), ("TRAINER_CLASS_TEAM_AQUA",)),
    ("magma", ("TRAINER_CLASS_MAGMA_LEADER", "TRAINER_CLASS_MAGMA_ADMIN"), ("TRAINER_CLASS_TEAM_MAGMA",)),
)
# Named opponents outside gyms, leagues, rivals and villain teams.
SPECIAL_CLASSES = ("TRAINER_CLASS_PKMN_TRAINER_1_HNS", "TRAINER_CLASS_KIMONO_GIRL_HNS",
                   "TRAINER_CLASS_MYSTERY_MAN_HNS")
# Default names of the two rivals the player names (src/strings.c).
RIVAL_DEFAULT = {"Kanto": "gText_ExpandedPlaceholder_Green", "Johto": "gText_ExpandedPlaceholder_Silver"}
# Lab scripts that pair the player's starter with the rival's.
KANTO_LAB = "data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc"
JOHTO_LAB = "data/maps/NewBarkTown_Lab_hns/scripts.inc"


def _classes(es):
    return {T.by_const(e.const).class_const for e in es}


def _is_rival_variant(es):
    h = D.head_entry(es)
    tr = T.by_const(h.const)
    return bool(D.starter_of(h.const)) and (tr.class_const in D.RIVAL_FAMILY or D.role_of(tr) == "rival"
                                            or "RIVAL" in h.const or h.const.startswith(("TRAINER_MAY_",
                                                                                         "TRAINER_BRENDAN_")))


@functools.lru_cache(maxsize=None)
def rivals():
    """[(region, [[person per starter] per rival figure])] in region order: persons that
    exist once per starter, grouped by figure (class family and name)."""
    out = {}
    for es in D.groups():
        if not _is_rival_variant(es):
            continue
        h = D.head_entry(es)
        tr = T.by_const(h.const, "de")
        fam = D.RIVAL_FAMILY.get(tr.class_const, tr.class_const + "|" + tr.name)
        region = levels.reader_region(es[0].map_id)
        out.setdefault(region, {}).setdefault(fam, []).append(es)
    return [(r, list(out[r].values())) for r in V.REGIONS if r in out]


@functools.lru_cache(maxsize=None)
def starter_pairs():
    """{rival's starter (species const): the player's starter (species const)}.

    Kanto: the lab script sets both species side by side. Johto: the lab script sets a
    number per chosen starter; the first rival battle picks its team by that number."""
    import re
    from gamedata import repo_path
    d = SDB.db()

    def alias(file, name):
        """The variable a script file's own name stands for (.equ NAME, VAR)."""
        m = re.search(r"^\.equ\s+%s\s*,\s*(\w+)" % name, open(repo_path(file), encoding="utf-8").read(), re.M)
        return m.group(1) if m else name

    k_player, k_rival = alias(KANTO_LAB, "PLAYER_STARTER_SPECIES"), alias(KANTO_LAB, "RIVAL_STARTER_SPECIES")
    out = {}
    player = None
    by_num, num = {}, None
    for ins in d.instrs:
        if ins.cmd != "setvar" or len(ins.args) < 2:
            continue
        if ins.file == KANTO_LAB and ins.args[1].startswith("SPECIES_"):
            if ins.args[0] == k_player:
                player = ins.args[1]
            elif ins.args[0] == k_rival and player:
                out[ins.args[1]] = player
                player = None
        elif ins.file == JOHTO_LAB:
            if ins.args[0] == "VAR_JOHTO_STARTER_MON" and ins.args[1].strip().isdigit():
                num = int(ins.args[1])
            elif num is not None and ins.args[1].startswith("SPECIES_"):      # the species shown for that choice
                by_num.setdefault(num, ins.args[1])
                num = None
    if by_num:
        fam = {}
        for _r, figs in rivals():
            for fig in figs:
                for es in fig:
                    sp = V.starter_species(None, es)
                    for e in es:
                        fam[e.const] = sp.const if sp else None
        for i, ins in enumerate(d.instrs):
            if ins.cmd == "goto_if_eq" and len(ins.args) >= 3 and ins.args[0] == "VAR_JOHTO_STARTER_MON" \
                    and ins.args[1].strip().isdigit() and ins.args[2] in d.labels:
                j = d.labels[ins.args[2]]
                nxt = d.instrs[j]
                if nxt.cmd.startswith("trainerbattle"):
                    for a in nxt.args:
                        if fam.get(a) and int(ins.args[1]) in by_num:
                            out.setdefault(fam[a], by_num[int(ins.args[1])])
    return out


@functools.lru_cache(maxsize=None)
def villains():
    """[(team key, grunt class const, [figure], number of grunts)]; a figure is the list of
    all battles of one boss or admin (same name) in story order."""
    out = []
    groups = D.groups()
    for key, heads, grunts in TEAMS:
        figures = {}
        for es in groups:
            if not (_classes(es) & set(heads)):
                continue
            name = T.by_const(D.head_entry(es).const, "de").name
            figures.setdefault(name, []).extend(es)
        figs = []
        for ents in figures.values():
            ents = sorted(ents, key=lambda e: D.person_sort_key([e]))
            figs.append(ents)
        figs.sort(key=lambda ents: D.person_sort_key(ents))
        n = sum(1 for es in groups if _classes(es) & set(grunts))
        out.append((key, grunts[0], figs, n))
    return out


@functools.lru_cache(maxsize=None)
def specials():
    """Other named opponents: special classes and the rival-class figures without a starter variant."""
    out = []
    shown = set()
    for region in V.REGIONS:
        for es in G.region_persons(region):
            shown.add(id(es))
    for es in D.groups():
        if _is_rival_variant(es) or id(es) in shown:
            continue
        cl = _classes(es)
        if cl & set(SPECIAL_CLASSES) or any(D.role_of(T.by_const(e.const)) == "rival" for e in es):
            out.append(es)
    return out


@functools.lru_cache(maxsize=None)
def multis():
    """[(map id, label, command, partner const, [entries])] of the multi battles."""
    out = {}
    for es in D.groups():
        for e in es:
            if e.command in T.MULTI_COMMANDS:
                out.setdefault((e.map_id, e.label, e.command, e.partner), []).append(e)
    res = []
    for (mid, label, cmd, partner), ents in out.items():
        order = {c: i for i, c in enumerate(ents[0].opponents)}
        ents = sorted(ents, key=lambda e: order.get(e.const, 99))
        res.append((mid, label, cmd, partner, ents))
    res.sort(key=lambda r: D.map_rank(r[0]))
    return res


def story_persons():
    """Persons shown with full teams on this page (the trainer index marks them)."""
    out = []
    for _r, figs in rivals():
        for fig in figs:
            out.extend(fig)
    by_entry = {}
    for es in D.groups():
        for e in es:
            by_entry[id(e)] = es
    for _k, _c, figs, _n in villains():
        for ents in figs:
            for e in ents:
                es = by_entry.get(id(e))
                if es is not None and all(es is not x for x in out):
                    out.append(es)
    return out + specials()


# ------------------------------------------------------------------ rendering
def _encounters(ctx, es, compact_classes=(), number=True):
    """The battles of a person as stacked cards with a numbered chip and the place."""
    cards = []
    n = len(es)
    labels = []
    k = 0
    for i, e in enumerate(es):
        if e.row is not None and e.mode in ("phone", "special"):
            labels.append(V.version_label(ctx, es, i))
        else:
            k += 1
            lb = ctx.t("battle_n", n=k) if n > 1 and number else None
            cond = V.title_cond_text(ctx, e)
            labels.append(" · ".join(x for x in (lb, cond) if x) or None)
    for i, e in enumerate(es):
        chips = [H.chip(labels[i], "jade")] if labels[i] else []
        tr = T.by_const(e.const)
        detail = tr.class_const not in compact_classes
        note = None
        if e.mode == "special":
            if e.const.startswith("TRAINER_WALLY_VR"):
                # IsRematchForbidden: Wally only needs his Victory Road battle; the later teams
                # wait for the Hoenn title like every stage above the Badge ceiling
                early = e.stage[0] <= RM.max_stage(e.row, 8)
                note = "<p>%s</p>" % H.esc(ctx.t("special_note_wally" if early else "special_note_wally_title"))
            else:
                note = "<p>%s</p>" % H.esc(ctx.t("special_note"))
        if e.command in T.MULTI_COMMANDS:
            note = "<p>%s</p>" % H.esc(ctx.t("multi_see"))
        if not detail:
            note = "<p>%s</p>" % V.fmt(ctx, "rival_champ_note", page=H.page_link(
                ctx, "battles/kanto", ctx.t("link_league_kanto")))
        card, _f = V.battle_card(ctx, e, chips=chips, show_place=True, detail=detail, note_html=note)
        cards.append(card)
    return "".join(cards)


def _places(ctx, es):
    places = []
    for e in es:
        p = V.entry_places(ctx, e)
        if p not in places:
            places.append(p)
    return places


def _rival_block(ctx, region, fig, idx):
    """One rival figure: tabs per starter, the encounters in order inside."""
    t = ctx.t
    rk = V.REGION_KEY[region]
    pairs = starter_pairs()
    panels = []
    for k, es in enumerate(fig):
        rsp = V.starter_species(ctx, es)
        psp = SP.by_const(pairs[rsp.const], ctx.lang) if rsp is not None and rsp.const in pairs else None
        if rsp is not None and psp is not None:
            label, order = t("tab_starters", you=psp.name, rival=rsp.name), psp.id
        elif rsp is not None:
            label, order = t("rival_with", species=rsp.name), rsp.id
        else:
            label, order = t("variant_n", n=k + 1), 10 ** 6 + k
        panels.append((order, label, _encounters(ctx, es, compact_classes=("TRAINER_CLASS_CHAMPION_FRLG",))))
    panels.sort(key=lambda p: p[0])
    sid = "rival-%s" % rk if idx == 1 else "rival-%s-%d" % (rk, idx)
    intro = []
    named = any(V.trainer_name(ctx, V.trainer(ctx, e.const)) == t("rival_name") for e in fig[0])
    if named and region in RIVAL_DEFAULT:
        default = hand_facts.c_string("src/strings.c", RIVAL_DEFAULT[region], ctx.lang)
        from gamedata import namestyle
        if ctx.lang == "en" and default:
            default = namestyle.show(default, "en", "trainer", ctx.lang)
        first = V.trainer_name(ctx, V.trainer(ctx, fig[0][0].const))
        intro.append("<p>%s</p>" % H.esc(t("rival_intro_" + rk, default=default, first=first)))
        title = t("rival_title_" + rk)
    else:
        name = V.person_name(ctx, fig[0])
        title = t("rival_title", region=V.region_name(ctx, region), name=name)
        if len(fig) == 1:
            intro.append("<p>%s</p>" % H.esc(t("rival_intro_single", name=name)))
    intro.append("<p>%s</p>" % V.fmt(ctx, "rival_places", n=len(fig[0]), places=", ".join(_places(ctx, fig[0]))))
    body = H.prose("".join(intro))
    if len(panels) > 1:
        body += H.tabs([(lb, html, str(i + 1)) for i, (_o, lb, html) in enumerate(panels)], sid + "-v")
    else:
        body += panels[0][2]
    return H.section(title, body, id=sid)


def _partner_card(ctx, partner_const, map_id):
    p, mons = T.partner_team(partner_const, map_id)
    if p is None:
        return "", None
    p = T.partners(ctx.lang).get(partner_const)
    members = []
    for em in mons:
        sp = SP.by_id(em.species, ctx.lang)
        if sp is None:
            continue
        m = {"species": sp, "level": em.level, "shiny": bool(em.mon.shiny)}
        m["moves"] = V._moves(ctx, em.mon.moves) if any(em.mon.moves) else V._moves(
            ctx, D.default_moves(SP.by_id(em.species), em.level))
        if em.mon.item:
            it = IT.by_id(em.mon.item, ctx.lang)
            if it is not None:
                m["item"] = it
        members.append(m)
    return H.trainer_card(ctx, p.name, members, cls_name=p.class_name, pic=p,
                          meta=[H.chip(ctx.t("partner_chip"), "gold")]), p


def _figure_block(ctx, ents, sid):
    """All battles of one named figure (a boss or an admin) under the name."""
    tr = V.trainer(ctx, ents[0].const)
    name = V.trainer_name(ctx, tr)
    return H.sub("%s (%s)" % (name, tr.class_name) if tr.class_name else name,
                 _encounters(ctx, ents), id=sid)


def render(ctx):
    t = ctx.t
    ctx.begin(PATH)
    body = []
    for region, figs in rivals():
        for i, fig in enumerate(figs, 1):
            body.append(_rival_block(ctx, region, fig, i))
    # villain teams
    for key, grunt_cls, figs, n_grunts in villains():
        if not figs:
            continue
        name = T.class_name(grunt_cls, ctx.lang)
        inner = [H.prose("<p>%s</p>" % V.fmt(ctx, "villain_intro", team=H.esc(name), n=n_grunts, list=H.page_link(
            ctx, "battles/trainers", ctx.t("trainer_list"))))]
        for k, ents in enumerate(figs, 1):
            inner.append(_figure_block(ctx, ents, "team-%s-%d" % (key, k)))
        body.append(H.section(name, "".join(inner), id="team-" + key))
    sp = specials()
    if sp:
        inner = []
        for k, es in enumerate(sp, 1):
            tr = V.trainer(ctx, D.head_entry(es).const)
            name = V.trainer_name(ctx, tr)
            inner.append(H.sub("%s (%s)" % (name, tr.class_name) if tr.class_name else name,
                               _encounters(ctx, es), id="special-%d" % k))
        body.append(H.section(t("sec_special"), "".join(inner), id="special", intro=H.esc(t("special_intro"))))
    ml = multis()
    if ml:
        inner = []
        for k, (mid, label, cmd, partner, ents) in enumerate(ml, 1):
            pcard, p = _partner_card(ctx, partner, mid)
            if p is None:
                continue
            foes = V.join(ctx, [H.esc(V.trainer_name(ctx, V.trainer(ctx, e.const))) for e in ents])
            key = "multi_2v2" if cmd in T.TWO_OPPONENT_COMMANDS else "multi_2v1"
            n = T.party_count(T.by_const(ents[0].const), cmd)
            txt = V.fmt(ctx, key, partner=H.esc(p.name), foes=foes, n=n, place=V.place_link(ctx, mid))
            cards = [pcard]
            for e in ents:
                c, _f = V.battle_card(ctx, e)
                cards.append(c)
            inner.append(H.sub(t("multi_title", partner=p.name, place=V.place_name(ctx, mid)),
                               H.prose("<p>%s</p>" % txt) + "".join(cards), id="multi-%d" % k))
        body.append(H.section(t("sec_multi"), "".join(inner), id="multi", intro=H.esc(t("multi_intro"))))
    ctx.end("".join(body), lead=H.esc(t("lead_rivals")), prev="battles/hoenn", next="battles/rematches")
