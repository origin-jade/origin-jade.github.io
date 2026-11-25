"""Items (data/items), TMs & HMs (data/tms) and berries (data/berries).

One page per item that the game hands out somewhere, that a wild Pokémon can hold, that
Pickup finds or that a trainer uses, with every source. Sources: gItemsInfo, the item
balls, hidden items, script gifts, shops and berry trees of the maps (pages._items_data,
the same data as the location pages), itemCommon / itemRare of gSpeciesInfo with the
chances of SetWildMonHeldItem, sPickupTable, FOREACH_TM / FOREACH_HM, gBerries.
"""
from common import html as H
from common import search
from gamedata import abilities, hand_pokeblocks, items as IT, locations as LOC, maps, moves, species as SP
from gamedata import dex_pickup, typeinfo

from pages import _items_data as D
from pages import _world_view as V
from pages import world as WORLD

INDEX = "data/items/index"
TMS = "data/tms"
BERRIES = "data/berries"
KINDS = ("shop", "ball", "hidden", "gift", "bought", "berry")
FILTER_FROM = 15        # place tables with more rows get a filter bar

STRINGS = {
    "de": {
        "lead": "Alle {n} Items, die im Spiel vorkommen, mit Wirkung und Kaufpreis. Jedes Item hat eine eigene "
                "Seite mit allen Fundorten.",
        "placeholder": "Item oder Wirkung suchen …",
        "facet_pocket": "Beuteltasche",
        "facet_how": "Herkunft",
        "f_shop": "Laden",
        "f_found": "Fundstück",
        "f_gift": "Geschenk",
        "f_berry": "Beerenbaum",
        "f_held": "Wilde Pokémon",
        "teaches": "Enthaltene Attacke",
        "sec_where": "Fundorte",
        "where_intro": "Alle Stellen, an denen es das Item gibt, in Reihenfolge der Reise.",
        "col_place": "Ort",
        "col_how": "Wie",
        "col_qty": "Menge",
        "place_filter": "Ort suchen …",
        "k_ball": "Itemball",
        "k_object": "Fundstück",
        "k_hidden": "Verstecktes Item",
        "k_underfoot": "Verstecktes Item (direkt unter dir)",
        "k_gift": "Geschenk oder Ereignis",
        "k_bought": "Kauf bei einer Person – {price}",
        "n_bp": "{n} GP",
        "k_shop": "Laden – {price}",
        "k_shop_badges": "Laden – {price} (ab {n} Johto-Orden)",
        "k_shop_badges_1": "Laden – {price} (ab 1 Johto-Orden)",
        "k_berry": "Beerenbaum",
        "n_trees": "{n} Bäume",
        "one_tree": "1 Baum",
        "n_coins": "{n} Münzen",
        "sec_held": "Von wilden Pokémon getragen",
        "held_intro": "Wilde Pokémon dieser Arten können das Item tragen. Normalerweise trägt ein wildes Pokémon "
                      "sein häufiges Item mit {c} % und sein seltenes mit {r} % Chance. Führt ein Pokémon mit "
                      "{a1} oder {a2} dein Team an, sind es {cb} % und {rb} %.",
        "held_always": "immer",
        "sec_pickup": "Fund mit {ability}",
        "pickup_intro": "Ein Pokémon mit der Fähigkeit {ability}, das kein Item trägt, findet nach einem Kampf "
                        "mit {p} % Chance ein Item. Die Tabelle zeigt, wie oft es dann dieses Item ist – abhängig "
                        "vom Level des Pokémon.",
        "col_level": "Level",
        "col_chance": "Anteil",
        "sec_evo": "Entwicklung",
        "evo_intro": "Diese Pokémon entwickeln sich mit dem Item. Alle Bedingungen stehen auf der Seite des Pokémon.",
        "col_evo_to": "Wird zu",
        "evo_use": "Item einsetzen",
        "evo_hold": "Item tragen",
        "sec_smash": "Aus zertrümmerten Felsen",
        "smash_text": "Nach jedem mit {move} zertrümmerten Felsen findest du das Item mit {p} % Chance.",
        "tms_lead": "Alle {tm} TMs und {hm} VMs mit ihrer Attacke und den Stellen, an denen es sie gibt.",
        "tms_placeholder": "TM oder Attacke suchen …",
        "sec_tm": "TMs",
        "sec_hm": "VMs",
        "col_no": "Nr.",
        "col_where": "Fundort",
        "berries_lead": "Alle {n} Beeren mit ihrer Wirkung, ihrem Geschmack für Pokériegel und den Orten, an denen "
                        "ihre Bäume stehen.",
        "berries_placeholder": "Beere oder Wirkung suchen …",
        "col_berry": "Beere",
        "col_effect": "Wirkung",
        "col_flavor": "Geschmack",
        "col_trees": "Beerenbäume",
        "col_other": "Außerdem",
        "berries_note": "Der Geschmack einer Beere bestimmt, welche Pokériegel aus ihr entstehen. Die Zahl "
                        "hinter dem Geschmack ist seine Stärke.",
        "other_places": "{n} weitere Fundorte",
        "other_place": "1 weiterer Fundort",
    },
    "en": {
        "lead": "All {n} items that appear in the game, with their effect and price. Every item has its own "
                "page listing every place to get it.",
        "placeholder": "Search item or effect …",
        "facet_pocket": "Bag pocket",
        "facet_how": "Source",
        "f_shop": "Shop",
        "f_found": "Found item",
        "f_gift": "Gift",
        "f_berry": "Berry tree",
        "f_held": "Wild Pokémon",
        "teaches": "Move inside",
        "sec_where": "Where to find it",
        "where_intro": "Every place that has the item, in travel order.",
        "col_place": "Place",
        "col_how": "How",
        "col_qty": "Amount",
        "place_filter": "Search place …",
        "k_ball": "Item ball",
        "k_object": "Found item",
        "k_hidden": "Hidden item",
        "k_underfoot": "Hidden item (right under you)",
        "k_gift": "Gift or event",
        "k_bought": "Bought from a person – {price}",
        "n_bp": "{n} BP",
        "k_shop": "Shop – {price}",
        "k_shop_badges": "Shop – {price} (from {n} Johto badges)",
        "k_shop_badges_1": "Shop – {price} (from 1 Johto badge)",
        "k_berry": "Berry tree",
        "n_trees": "{n} trees",
        "one_tree": "1 tree",
        "n_coins": "{n} Coins",
        "sec_held": "Held by wild Pokémon",
        "held_intro": "Wild Pokémon of these species can hold the item. Normally a wild Pokémon holds its common "
                      "item with a {c}% chance and its rare item with a {r}% chance. With a Pokémon that has "
                      "{a1} or {a2} at the front of your party it is {cb}% and {rb}%.",
        "held_always": "always",
        "sec_pickup": "Found with {ability}",
        "pickup_intro": "A Pokémon with the ability {ability} that holds no item has a {p}% chance to find an "
                        "item after a battle. The table shows how often it is this item, depending on the "
                        "Pokémon's level.",
        "col_level": "Level",
        "col_chance": "Share",
        "sec_evo": "Evolution",
        "evo_intro": "These Pokémon evolve with the item. All conditions are on the Pokémon's page.",
        "col_evo_to": "Evolves into",
        "evo_use": "use the item",
        "evo_hold": "hold the item",
        "sec_smash": "From smashed rocks",
        "smash_text": "Every rock you smash with {move} has a {p}% chance to yield the item.",
        "tms_lead": "All {tm} TMs and {hm} HMs with their move and the places that have them.",
        "tms_placeholder": "Search TM or move …",
        "sec_tm": "TMs",
        "sec_hm": "HMs",
        "col_no": "No.",
        "col_where": "Where",
        "berries_lead": "All {n} berries with their effect, their flavor for Pokéblocks and the places where "
                        "their trees grow.",
        "berries_placeholder": "Search berry or effect …",
        "col_berry": "Berry",
        "col_effect": "Effect",
        "col_flavor": "Flavor",
        "col_trees": "Berry trees",
        "col_other": "Also",
        "berries_note": "A berry's flavor decides which Pokéblocks it makes. The number after the flavor is "
                        "its strength.",
        "other_places": "{n} more places",
        "other_place": "1 more place",
    },
}


class _WorldCtx:
    """The page context with the strings of the world module (for its area labels)."""

    def __init__(self, ctx):
        self.__dict__["_c"] = ctx

    def __getattr__(self, name):
        return getattr(self._c, name)

    def t(self, key, **fmt):
        return WORLD.STRINGS[self._c.lang][key].format(**fmt)


class Site:
    def __init__(self, ctx):
        self.lang = ctx.lang
        self.items = IT.all_items(ctx.lang)
        self.ids = D.listed_ids()
        self.listed = sorted((self.items[i] for i in self.ids), key=lambda it: (search.fold(_title(ctx, it)), it.id))
        self.places = D.places()
        self._labels = {}
        self.wctx = _WorldCtx(ctx)

    def labels(self, loc_key):
        if loc_key not in self._labels:
            self._labels[loc_key] = V.area_labels(self.wctx, LOC.by_key(loc_key))
        return self._labels[loc_key]


def _tm_move(ctx, it):
    return moves.by_id(it.tm[2], ctx.lang) if it.tm else None


def _title(ctx, it):
    mv = _tm_move(ctx, it)
    return "%s %s" % (it.name, mv.name) if mv else it.name


def _loc_title(ctx, key):
    return ctx.title_of("location", key) or maps.mapsec_name(key, ctx.lang)


def _price(ctx, price):
    if isinstance(price, tuple):
        cur, amount = price
        if cur == "bp":
            return ctx.t("n_bp", n=ctx.num(amount))
        return ctx.money(amount) if cur == "money" else ctx.t("n_coins", n=ctx.num(amount))
    return ctx.money(price)


def _how(ctx, p):
    t = ctx.t
    if p.kind == "ball":
        return t("k_object" if p.not_ball else "k_ball")
    if p.kind == "hidden":
        return t("k_underfoot" if p.underfoot else "k_hidden")
    if p.kind == "gift":
        return t("k_gift")
    if p.kind == "bought":
        return t("k_bought", price=_price(ctx, p.price))
    if p.kind == "shop":
        if p.badges:
            return t("k_shop_badges_1" if p.badges == 1 else "k_shop_badges", price=_price(ctx, p.price), n=p.badges)
        return t("k_shop", price=_price(ctx, p.price))
    return t("k_berry")


def _qty(ctx, p):
    if p.kind == "berry":
        return ctx.t("one_tree") if p.count == 1 else ctx.t("n_trees", n=ctx.num(p.count))
    if p.kind == "shop":
        return None
    return "×%s" % ctx.num(p.qty * p.count)


def _place_cell(ctx, site, p):
    lab = site.labels(p.loc).get(p.map_id, "") if p.map_id else ""
    cell = H.location_link(ctx, p.loc, _loc_title(ctx, p.loc))
    if lab:
        cell += ' <span class="muted">· %s</span>' % H.esc(lab)
    return cell


def _where_section(ctx, site, it):
    t = ctx.t
    ps = site.places.get(it.id)
    if not ps:
        return ""
    rows, attrs = [], []
    for p in ps:
        loc = LOC.by_key(p.loc)
        q = _qty(ctx, p)
        rows.append([_place_cell(ctx, site, p), H.region_chip(ctx, loc.region), H.esc(_how(ctx, p)),
                     H.esc(q) if q else None])
        attrs.append(H.filter_attrs([_loc_title(ctx, p.loc)], region=loc.region))
    cols = [(t("col_place"), "main"), ctx.ui("region"), t("col_how"), (t("col_qty"), "num")]
    if not any(r[3] for r in rows):
        cols, rows = cols[:3], [r[:3] for r in rows]
    bar = ""
    if len(rows) > FILTER_FROM:
        bar = H.filter_bar(ctx, "where", placeholder=t("place_filter"), facets=[H.region_facet(ctx)])
    return H.section(t("sec_where"), bar + H.table(cols, rows, id="where", row_attrs=attrs), id="places",
                     intro=H.esc(t("where_intro")))


def _held_section(ctx, it):
    t = ctx.t
    h = D.held().get(it.id)
    if not h:
        return ""
    (c, r), (cb, rb) = D.held_chances()
    tiles = []
    for slot, note in ((0, t("held_always")), (1, ctx.pct(c)), (2, ctx.pct(r))):
        for const in h[slot]:
            sp = SP.by_const(const, ctx.lang)
            tiles.append(H.species_tile(ctx, sp, number=sp.natdex or None, note=note))
    a1 = abilities.by_const("ABILITY_COMPOUND_EYES", ctx.lang).name
    a2 = abilities.by_const("ABILITY_SUPER_LUCK", ctx.lang).name
    return H.section(t("sec_held"), H.ent_grid(tiles), id="held",
                     intro=H.esc(t("held_intro", c=c, r=r, cb=cb, rb=rb, a1=a1, a2=a2)))


def _pickup_section(ctx, it):
    t = ctx.t
    pct = D.pickup().get(it.id)
    if not pct:
        return ""
    ab = abilities.by_const("ABILITY_PICKUP", ctx.lang).name
    rows = [[H.esc(ctx.level_range(lo, hi)), H.esc(ctx.pct(p))]
            for (lo, hi), p in zip(dex_pickup.columns(), pct) if p]
    return H.section(t("sec_pickup", ability=ab),
                     H.table([(t("col_level"), "main"), (t("col_chance"), "num")], rows), id="pickup",
                     intro=H.esc(t("pickup_intro", ability=ab, p=dex_pickup.PICKUP_CHANCE)))


def _evo_index(lang):
    """{item id: [(Species, target Species, "use" | "hold")]} from the evolution tables."""
    out = {}
    for sp in sorted(SP.all_species(lang).values(), key=lambda s: (s.natdex or 9999, s.id)):
        for evo in sp.evolutions:
            target = SP.by_id(evo.target, lang)
            if target is None:
                continue
            hits = []
            if evo.method == "EVO_ITEM" and evo.param:
                hits.append((evo.param, "use"))
            for name, args in evo.conditions:
                if name == "IF_HOLD_ITEM":
                    hits.extend((a, "hold") for a in args)
            for iid, how in hits:
                row = (sp, target, how)
                lst = out.setdefault(iid, [])
                if not any(r[0].id == sp.id and r[1].id == target.id and r[2] == how for r in lst):
                    lst.append(row)
    return out


_EVO = {}


def _evo_section(ctx, it):
    if ctx.lang not in _EVO:
        _EVO[ctx.lang] = _evo_index(ctx.lang)
    rows = _EVO[ctx.lang].get(it.id)
    if not rows:
        return ""
    t = ctx.t
    body = [[H.species_link(ctx, a, icon=True), H.species_link(ctx, b, icon=True),
             H.esc(t("evo_use" if how == "use" else "evo_hold"))] for a, b, how in rows]
    return H.section(t("sec_evo"), H.table([(ctx.ui("pokemon"), "main"), t("col_evo_to"), t("col_how")], body),
                     id="evolution", intro=H.esc(t("evo_intro")))


def _smash_section(ctx, it):
    p = D.smash().get(it.id)
    if p is None:
        return ""
    mv = moves.by_const("MOVE_ROCK_SMASH", ctx.lang).name
    return H.section(ctx.t("sec_smash"), H.p(ctx.t("smash_text", move=mv, p=ctx.num(p))), id="smash")


def _data_section(ctx, it):
    mv = _tm_move(ctx, it)
    if not mv:
        return ""
    return H.section(ctx.t("teaches"), H.move_table(ctx, [mv]), id="move")


def _how_tags(site, it):
    ps = site.places.get(it.id, ())
    kinds = {p.kind for p in ps}
    tags = []
    if "shop" in kinds or "bought" in kinds:
        tags.append("shop")
    if "ball" in kinds or "hidden" in kinds:
        tags.append("found")
    if "gift" in kinds:
        tags.append("gift")
    if "berry" in kinds:
        tags.append("berry")
    if it.id in D.held():
        tags.append("held")
    return tags


def _short_where(ctx, site, it, kinds=None, limit=None):
    """Places of an item as one line of links: "Marmoria City (Geschenk oder Ereignis); …"."""
    seen, out = set(), []
    for p in site.places.get(it.id, ()):
        if kinds and p.kind not in kinds:
            continue
        how = _how(ctx, p)
        if (p.loc, how) in seen:
            continue
        seen.add((p.loc, how))
        out.append("%s <span class=\"muted\">(%s)</span>" % (
            H.location_link(ctx, p.loc, _loc_title(ctx, p.loc)), H.esc(how)))
    if limit and len(out) > limit:
        return out[:limit], len(out) - limit
    return out, 0


# ------------------------------------------------------------------ pages
def register(ctx):
    site = Site(ctx)
    ctx.add_page(INDEX)
    ctx.add_page(TMS)
    ctx.add_page(BERRIES)
    for it in site.listed:
        mv = _tm_move(ctx, it)
        ctx.add_entity("item", it.const, _title(ctx, it), sub=it.pocket_name,
                       icon=ctx.asset_rel("item", it.slug), keywords=mv.name if mv else "")


def _render_index(ctx, site):
    t = ctx.t
    ctx.begin(INDEX)
    ents = []
    for it in site.listed:
        data = H.filter_attrs([_title(ctx, it), it.description], pocket=it.pocket.lower(),
                              how=_how_tags(site, it) or None)
        ents.append(H.ent(ctx.url_for("item", it.const), _title(ctx, it), media=H.item_icon(ctx, it),
                          note=it.description, data=data,
                          aside=H.chip(ctx.money(it.price), "muted") if it.price else None))
    pockets = [(c.lower(), n) for c, n in IT.pockets(ctx.lang)]
    bar = H.filter_bar(ctx, "items", placeholder=t("placeholder"), facets=[
        {"key": "pocket", "label": t("facet_pocket"), "options": pockets, "style": "select"},
        {"key": "how", "label": t("facet_how"), "options": [
            ("shop", t("f_shop")), ("found", t("f_found")), ("gift", t("f_gift")), ("berry", t("f_berry")),
            ("held", t("f_held"))]}])
    groups = H.letter_groups([(_title(ctx, it), x) for it, x in zip(site.listed, ents)],
                             lambda xs: H.ent_grid(xs, cls="ents-wide"), "items")
    ctx.end(bar + groups, lead=H.esc(t("lead", n=ctx.num(len(site.listed)))))


def _render_items(ctx, site):
    for i, it in enumerate(site.listed):
        ctx.begin("item", it.const)
        body = [_data_section(ctx, it), _evo_section(ctx, it), _where_section(ctx, site, it), _smash_section(ctx, it),
                _held_section(ctx, it), _pickup_section(ctx, it)]
        chips = [H.chip(it.pocket_name, "jade")]
        if it.price:
            chips.append(H.chip(ctx.money(it.price), "muted"))
        ctx.end("".join(body), title=_title(ctx, it), eyebrow=ctx.ui("item"),
                lead=H.esc(it.description) if it.description else None, chips=H.chips(chips),
                aside=H.plate(H.item_icon(ctx, it, scale=3)),
                prev=("item", site.listed[i - 1].const) if i else None,
                next=("item", site.listed[i + 1].const) if i + 1 < len(site.listed) else None)


def _render_tms(ctx, site):
    t = ctx.t
    ctx.begin(TMS)
    blocks, counts = [], {}
    for kind, sec, sid in (("TM", "sec_tm", "tm"), ("HM", "sec_hm", "hm")):
        rows, attrs = [], []
        for k, num, mid in moves.tm_hm_moves():
            if k != kind:
                continue
            it = IT.by_tm(k, num, ctx.lang)
            mv = moves.by_id(mid, ctx.lang)
            if it is None or mv is None:
                continue
            ty = typeinfo.by_id(mv.type, ctx.lang)
            where, _more = _short_where(ctx, site, it)
            rows.append([H.item_link(ctx, it, icon=True), H.move_link(ctx, mv), H.type_chip(ctx, ty),
                         H.cat_chip(ctx, mv.category), ctx.num(mv.power) if mv.power > 1 else None,
                         H.esc(ctx.pct(mv.accuracy)) if mv.accuracy else None, ctx.num(mv.pp),
                         "<br>".join(where) if where else None])
            attrs.append(H.filter_attrs([it.name, mv.name], type=[ty.slug]))
        counts[kind] = len(rows)
        cols = [(t("col_no"), "main"), ctx.ui("move"), ctx.ui("type"), ctx.ui("category"),
                (ctx.ui("power"), "num"), (ctx.ui("accuracy"), "num"), (ctx.ui("pp"), "num"), t("col_where")]
        blocks.append('<div data-group="%s">%s</div>' % (
            sid, H.section(t(sec), H.table(cols, rows, row_attrs=attrs), id=sid)))
    bar = H.filter_bar(ctx, "tms", placeholder=t("tms_placeholder"), facets=[H.type_facet(ctx)])
    ctx.end(bar + '<div id="tms">%s</div>' % "".join(blocks),
            lead=H.esc(t("tms_lead", tm=counts["TM"], hm=counts["HM"])), wide=True)


def _render_berries(ctx, site):
    t = ctx.t
    ctx.begin(BERRIES)
    flavor = dict(hand_pokeblocks.flavors(ctx.lang))
    rows, attrs = [], []
    for b in hand_pokeblocks.berries(ctx.lang):
        it = b.item
        if it.id not in site.ids:
            continue
        fl = ", ".join("%s %d" % (flavor[f], n) for f, n in b.flavors.items() if n)
        trees, _ = _short_where(ctx, site, it, kinds=("berry",))
        n_other = len({(p.loc, p.kind) for p in site.places.get(it.id, ()) if p.kind != "berry"})
        other = None
        if n_other:
            other = H.link(ctx, "item", it.const, t("other_place") if n_other == 1 else t("other_places", n=n_other))
        rows.append([H.item_link(ctx, it, icon=True), H.esc(it.description), H.esc(fl) if fl else None,
                     ", ".join(x.split(" <span")[0] for x in trees) if trees else None, other])
        attrs.append(H.filter_attrs([it.name, it.description, fl]))
    cols = [(t("col_berry"), "main"), t("col_effect"), t("col_flavor"),
            t("col_trees"), t("col_other")]
    bar = H.filter_bar(ctx, "berries", placeholder=t("berries_placeholder"))
    ctx.end(bar + H.table(cols, rows, id="berries", row_attrs=attrs) + H.callout(ctx, "note", H.p(t("berries_note"))),
            lead=H.esc(t("berries_lead", n=len(rows))), wide=True)


def render(ctx):
    site = Site(ctx)
    _render_index(ctx, site)
    _render_items(ctx, site)
    _render_tms(ctx, site)
    _render_berries(ctx, site)
