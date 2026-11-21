"""battles/index (overview of the battle pages, how trainer levels work) and
battles/trainers (every trainer as a filterable index).

Level rules: gamedata.levels (RemapLevel constants of include/config/level_remap.h).
"""
import functools

from common import html as H
from common import search
from common import slugs
from gamedata import levels
from gamedata import maps
from gamedata import trainers as T

from pages import _battles_data as D
from pages import _battles_gyms as G
from pages import _battles_rematch as R
from pages import _battles_story as S
from pages import _battles_view as V

_RULE_REGION = {levels.KANTO: "Kanto", levels.JOHTO: "Johto", levels.HOENN: "Hoenn"}
INDEX = "battles/index"
TRAINERS = "battles/trainers"


@functools.lru_cache(maxsize=None)
def person_rows():
    """[(person, region, highest level, number of battles)] of every trainer, in the order
    of the journey (region, place in story order, map, trainer order)."""
    out = []
    for es in D.groups():
        region = levels.reader_region(es[0].map_id)
        out.append((es, region, max(D.max_level(e) for e in es), len(es)))
    return out


@functools.lru_cache(maxsize=None)
def region_spans():
    """{region: (lowest, highest)} level of the fixed-level battles of a region."""
    out = {}
    for es in D.groups():
        for e in es:
            if e.mode != "normal" or D.title_condition(e)[0] is not None:
                continue      # rematches and battles that need a title are not part of the journey
            # the region whose level rule applies (Johto's league rooms stand on Kanto's plateau)
            region = _RULE_REGION.get(levels.remap_region(e.map_id))
            if region is None:
                continue
            tm = D.team_of(e)
            for m in tm.mons:
                lo, hi = out.get(region, (10 ** 6, 0))
                out[region] = (min(lo, m.level), max(hi, m.level))
    return out


def counts():
    rows = person_rows()
    return len(rows), sum(r[3] for r in rows)


# ------------------------------------------------------------------ battles/index
def _ace(ctx, es):
    """Highest level of a person's first battle."""
    e = es[0]
    return D.max_level(e)


def render_index(ctx):
    t = ctx.t
    ctx.begin(INDEX)
    n_persons, n_battles = counts()
    spans = region_spans()
    tiles = []
    for region in V.REGIONS:
        gl = G.gyms(region)
        e4, champ = G.league(region)
        lo, hi = spans.get(region, (0, 0))
        first = gl[0].persons[0] if gl and gl[0].persons else None
        meta = H.chips([V.region_chip(ctx, region), H.chip(ctx.level_range(lo, hi), "muted")])
        last = gl[-1].persons[0] if gl and gl[-1].persons else None
        text = t("tile_region", leader=V.person_name(ctx, first) if first else "",
                 last=V.person_name(ctx, last) if last else "",
                 champ=V.person_name_mid(ctx, champ[0]) if champ else "")
        tiles.append(H.page_tile(ctx, G.PATHS[region], text=text, meta=meta))
    more = [
        H.page_tile(ctx, S.PATH, text=t("tile_rivals")),
        H.page_tile(ctx, R.PATH, text=t("tile_rematches", n=ctx.num(sum(len(v) for v in R.phone_persons().values())))),
        H.page_tile(ctx, TRAINERS, text=t("tile_trainers", n=ctx.num(n_persons), b=ctx.num(n_battles))),
    ]
    body = [H.section(t("sec_regions"), H.grid([x for x in tiles if x], "m"), id="regions",
                      intro=H.esc(t("regions_intro")))]
    body.append(H.section(t("sec_more"), H.grid([x for x in more if x], "m"), id="more"))
    # how levels work
    C = levels.C
    jl, jh = C("REMAP_JOHTO_TO_LO"), C("REMAP_JOHTO_TO_HI")
    hl, hh = C("REMAP_HOENN_TO_LO"), C("REMAP_HOENN_TO_HI")
    plo, phi = levels.phone_band()
    llo, lhi = levels.leader_band()
    _e4, kchamp = G.league("Kanto")
    kanto_champ = _ace(ctx, kchamp[0]) if kchamp else 0
    pts = H.ul([
        H.esc(t("lv_kanto", lo=spans.get("Kanto", (0, 0))[0], hi=kanto_champ)),
        H.esc(t("lv_johto", lo=jl, hi=jh)),
        H.esc(t("lv_hoenn", lo=hl, hi=hh)),
        H.esc(t("lv_evolve")),
        V.fmt(ctx, "lv_rematch", lo=-phi, hi=-plo, llo=llo, lhi=lhi,
              page=H.page_link(ctx, R.PATH, ctx.t("link_rematches"))),
    ])
    rows = []
    for region in V.REGIONS:
        gl = G.gyms(region)
        e4, champ = G.league(region)
        lo, hi = spans.get(region, (0, 0))
        first = gl[0].persons[0] if gl and gl[0].persons else None
        last = gl[-1].persons[0] if gl and gl[-1].persons else None
        rows.append([V.region_chip(ctx, region), H.esc(ctx.level_range(lo, hi)),
                     H.esc("%s · %s" % (V.person_name(ctx, first), ctx.level(_ace(ctx, first)))) if first else None,
                     H.esc("%s · %s" % (V.person_name(ctx, last), ctx.level(_ace(ctx, last)))) if last else None,
                     H.esc("%s · %s" % (V.person_name(ctx, champ[0]), ctx.level(_ace(ctx, champ[0])))) if champ
                     else None])
    table = H.table([(ctx.ui("region"), "main"), (t("col_span"), "num"), t("col_first_gym"), t("col_last_gym"),
                     t("col_champ")], rows)
    more_link = V.fmt(ctx, "lv_more", page=H.page_link(ctx, "game/levels"))
    lv = H.prose(pts) + table + (H.prose("<p>%s</p>" % more_link) if ctx.has("page", "game/levels") else "")
    body.append(H.section(t("sec_levels"), lv, id="levels", intro=H.esc(t("levels_intro"))))
    ctx.end("".join(body), lead=H.esc(t("lead_index", n=ctx.num(n_persons), b=ctx.num(n_battles))),
            next="battles/kanto")


# ------------------------------------------------------------------ battles/trainers
def _featured():
    """{id(person): page path} of the persons shown with full teams on a battle page."""
    out = {}
    for region in V.REGIONS:
        for es in G.region_persons(region):
            out[id(es)] = G.PATHS[region]
    for es in S.story_persons():
        out.setdefault(id(es), S.PATH)
    return out


def render_trainers(ctx):
    t = ctx.t
    ctx.begin(TRAINERS)
    rows = person_rows()
    n_persons, n_battles = counts()
    any_anchor = any(ctx.has("trainer", e.const) for es, _r, _l, _n in rows[:50] for e in es) or any(
        ctx.has("trainer", e.const) for es, _r, _l, _n in rows for e in es)
    featured = _featured()
    items, classes, places, orphans = [], {}, {}, []
    for es, region, top, n in rows:
        h = D.head_entry(es)
        tr = V.trainer(ctx, h.const)
        name = V.person_name(ctx, es)
        if name == t("rival_name") and S._is_rival_variant(es):
            ssp = V.starter_species(ctx, es)
            if ssp is not None:
                name = t("rival_variant", name=name, species=ssp.name)
        cname = tr.class_name or ""
        place = V.place_name(ctx, h.map_id)
        ckey = slugs.anchor(cname) or "x"
        pkey = slugs.anchor(place) or "x"
        classes.setdefault(ckey, cname)
        places.setdefault(pkey, (place, V.REGION_KEY.get(region, "other")))
        href = None
        for e in [h] + list(es):
            href = ctx.url_for("trainer", e.const)
            if href:
                break
        if href is None and id(es) in featured:
            href = ctx.url(featured[id(es)])
        if href is None and V.place_key(h.map_id):
            href = ctx.url_for("location", V.place_key(h.map_id))
        elif href is None and any_anchor:
            orphans.append(es)
        data = H.filter_attrs([name, cname, place], region=V.REGION_KEY.get(region, "other"), cls=ckey, loc=pkey)
        first_top = D.max_level(es[0])
        link = '<a href="%s">%s</a>' % (H.esc(href), H.esc(name)) if href else H.esc(name)
        items.append(([link, H.esc(cname), H.esc(place),
                       H.esc(ctx.level_range(min(first_top, top), top)), ctx.num(n) if n > 1 else None], data))
    # the places follow the region chosen first (option attribute data-region)
    popts = [(k, v[0], v[1]) for k, v in places.items()]
    bar = H.filter_bar(ctx, "trainers", placeholder=t("trainers_placeholder"), facets=[
        H.region_facet(ctx),
        {"key": "loc", "label": ctx.ui("location"), "options": popts, "style": "select"},
    ])
    body = bar + H.table([(ctx.ui("trainer"), "main"), t("col_class"), ctx.ui("location"),
                          (ctx.ui("levels"), "num"), (t("col_battles"), "num")],
                         [r for r, _d in items], id="trainers", row_attrs=[d for _r, d in items])
    if orphans:
        cards = []
        for es in orphans:
            for i, e in enumerate(es):
                c, _f = V.battle_card(ctx, e, detail=False, show_place=True,
                                      chips=[H.chip(V.version_label(ctx, es, i), "jade")] if len(es) > 1 else [])
                cards.append(c)
        body += H.section(t("sec_orphans"), H.trainer_list(cards), id="more-teams", intro=H.esc(t("orphans_intro")))
    ctx.end(body, lead=H.esc(t("lead_trainers", n=ctx.num(n_persons), b=ctx.num(n_battles))), wide=True)
