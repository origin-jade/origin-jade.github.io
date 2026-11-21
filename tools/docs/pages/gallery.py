"""Development gallery (built only with --dev): every component with real game
data, plus two complete page compositions to copy from.

    dev/gallery    all components, each with the call that produced it
    dev/pokemon    a complete Pokémon page (Bulbasaur)
    dev/location   a complete location page (Kanto Route 6: day and night encounters, trainers, items)
"""
from common import html as H
from gamedata import abilities, dex_texts, items, maps, moves, species, trainers, typeinfo
from pages import _gallery_data as D

DEV = True

MON = "SPECIES_BULBASAUR"
BRANCH = "SPECIES_ODDISH"
ROUTE = "MAP_ROUTE6"
LEADER = "TRAINER_LEADER_BROCK"

STRINGS = {
    "de": {
        "gallery_title": "Bausteine",
        "gallery_lead": "Alle Bausteine der Seite mit echten Spieldaten. Unter jedem Beispiel steht der Aufruf.",
        "pokemon_title": "Beispiel: Pokémon-Seite",
        "location_title": "Beispiel: Ort",
        "compositions": "Ganze Seiten",
        "s_tokens": "Farben und Schrift", "s_text": "Text und Hinweise", "s_chips": "Chips",
        "s_images": "Sprites und Icons", "s_tiles": "Kacheln und Karten", "s_tables": "Tabellen",
        "s_stats": "Basiswerte und Typen", "s_evo": "Entwicklung", "s_learn": "Attacken",
        "s_enc": "Wilde Pokémon", "s_trainers": "Trainer", "s_items": "Items und Shops",
        "s_ents": "Listen mit Filter", "s_tabs": "Reiter", "s_links": "Verweise",
        "sample_p": "Fließtext steht in einer angenehmen Zeilenlänge. Verweise wie {link} sind unterstrichen.",
        "sample_tip": "Tipps zeigen einen besseren Weg.",
        "sample_note": "Hinweise ergänzen den Text.",
        "sample_warn": "Warnungen stehen für Dinge, die man nicht rückgängig machen kann.",
        "sample_step1": "Sprich mit der Person im Haus.",
        "sample_step2": "Gehe nach Norden bis zur nächsten Stadt.",
        "sample_step3": "Besiege die Arena.",
        "sample_q": "Eine Frage zum Aufklappen",
        "sample_a": "Die Antwort steht darunter und ist auch ohne JavaScript erreichbar.",
        "dex_eyebrow": "#{n} · {category}-Pokémon",
        "sec_stats": "Basiswerte", "sec_abilities": "Fähigkeiten", "sec_defense": "Typen-Schwächen",
        "sec_evo": "Entwicklung", "sec_moves": "Attacken", "sec_where": "Fundorte", "sec_breeding": "Zucht und Daten",
        "defense_intro": "So viel Schaden nimmt {name} von Attacken dieser Typen.",
        "where_none": "{name} kommt nicht wild vor.",
        "k_egg_groups": "Ei-Gruppen", "k_egg_cycles": "Ei-Zyklen", "k_gender": "Geschlecht",
        "k_catch": "Fangrate", "k_growth": "Levelaufstieg", "k_exp": "Basis-EP", "k_ev": "Fleißpunkte",
        "k_height": "Größe", "k_weight": "Gewicht", "k_held": "Getragene Items",
        "height": "{v} m", "weight": "{v} kg", "catch": "{n} ({word})",
        "loc_eyebrow": "{region} · Route",
        "sec_wild": "Wilde Pokémon", "sec_trainers": "Trainer", "sec_items": "Items",
        "wild_intro": "Level und Chancen genau wie im Spiel. Im hohen Gras wechselt die Auswahl mit der Tageszeit.",
        "trainers_intro": "{n} Trainer warten hier auf einen Kampf.",
        "items_intro": "Sichtbare und versteckte Items auf dieser Route.",
        "n_trainers": "{n} Trainer", "n_items": "{n} Items",
    },
    "en": {
        "gallery_title": "Components",
        "gallery_lead": "Every component of the site with real game data. The call is shown below each example.",
        "pokemon_title": "Example: Pokémon page",
        "location_title": "Example: location",
        "compositions": "Whole pages",
        "s_tokens": "Colours and type", "s_text": "Text and notes", "s_chips": "Chips",
        "s_images": "Sprites and icons", "s_tiles": "Tiles and cards", "s_tables": "Tables",
        "s_stats": "Base stats and types", "s_evo": "Evolution", "s_learn": "Moves",
        "s_enc": "Wild Pokémon", "s_trainers": "Trainers", "s_items": "Items and shops",
        "s_ents": "Lists with a filter", "s_tabs": "Tabs", "s_links": "Links",
        "sample_p": "Running text keeps a comfortable line length. Links such as {link} are underlined.",
        "sample_tip": "Tips show a better way.",
        "sample_note": "Notes add to the text.",
        "sample_warn": "Warnings are for things that cannot be undone.",
        "sample_step1": "Talk to the person in the house.",
        "sample_step2": "Head north to the next town.",
        "sample_step3": "Beat the Gym.",
        "sample_q": "A question that unfolds",
        "sample_a": "The answer is below and can be reached without JavaScript, too.",
        "dex_eyebrow": "#{n} · {category} Pokémon",
        "sec_stats": "Base stats", "sec_abilities": "Abilities", "sec_defense": "Type defenses",
        "sec_evo": "Evolution", "sec_moves": "Moves", "sec_where": "Where to find it", "sec_breeding": "Breeding and data",
        "defense_intro": "How much damage {name} takes from moves of these types.",
        "where_none": "{name} does not appear in the wild.",
        "k_egg_groups": "Egg Groups", "k_egg_cycles": "Egg cycles", "k_gender": "Gender",
        "k_catch": "Catch rate", "k_growth": "Growth rate", "k_exp": "Base EXP", "k_ev": "Effort values",
        "k_height": "Height", "k_weight": "Weight", "k_held": "Held items",
        "height": "{v} m", "weight": "{v} kg", "catch": "{n} ({word})",
        "loc_eyebrow": "{region} · Route",
        "sec_wild": "Wild Pokémon", "sec_trainers": "Trainers", "sec_items": "Items",
        "wild_intro": "Levels and rates exactly as in the game. In tall grass the selection changes with the time of day.",
        "trainers_intro": "{n} trainers are waiting for a battle here.",
        "items_intro": "Visible and hidden items on this route.",
        "n_trainers": "{n} trainers", "n_items": "{n} items",
    },
}


def register(ctx):
    t = ctx.t
    ctx.add_page("dev/gallery", t("gallery_title"), search=False)
    ctx.add_page("dev/pokemon", t("pokemon_title"), search=False, parent="dev/gallery")
    ctx.add_page("dev/location", t("location_title"), search=False, parent="dev/gallery")


def code(text):
    return '<code class="dev-code">%s</code>' % H.esc(text)


# ---------------------------------------------------------------------- Pokémon page
def pokemon_body(ctx, sp):
    """Sections of a complete Pokémon page. -> (body, header keyword arguments for ctx.end)"""
    t, lang = ctx.t, ctx.lang
    names = H.stat_names(ctx)
    out = []

    profile = H.kv([
        (t("k_height"), H.esc(t("height", v=ctx.num(sp.height / 10.0)))),
        (t("k_weight"), H.esc(t("weight", v=ctx.num(sp.weight / 10.0)))),
        (t("k_catch"), H.esc(t("catch", n=sp.catch_rate, word=dex_texts.catch_class(sp.catch_rate, lang)))),
        (t("k_exp"), str(sp.exp_yield)),
        (t("k_ev"), H.esc(", ".join("%d %s" % (v, names[k]) for k, v in sp.ev_yield.items() if v)) or None),
        (t("k_growth"), H.esc(dex_texts.growth(sp.growth_rate, lang))),
    ])
    out.append(H.section(t("sec_stats"), H.split(H.stat_bars(ctx, sp.stats), profile), id="stats"))

    abil = []
    for slot, aid in enumerate(sp.abilities[:3]):
        ab = abilities.by_id(aid, lang) if aid else None
        if ab is not None and ab.id not in [a.id for a, _h in abil]:
            abil.append((ab, slot == 2))
    out.append(H.section(t("sec_abilities"), H.ability_list(ctx, abil), id="abilities"))

    out.append(H.section(t("sec_defense"), H.type_matchups(ctx, sp.types), id="defense",
                         intro=H.esc(t("defense_intro", name=sp.name))))

    tree = D.evo_tree(ctx, sp)
    if tree["children"]:
        out.append(H.section(t("sec_evo"), H.evolution_chain(ctx, tree, current=sp), id="evolution"))

    level, tm, tutor, egg = D.learnsets(ctx, sp)
    out.append(H.section(t("sec_moves"), H.learnset(ctx, "moves", level, tm, tutor, egg), id="moves-sec"))

    rows = []
    for m, area, times, row in D.where_rows(ctx, sp):
        rows.append({"key": m.mapsec, "name": m.display, "region": D.REGION_ID.get(m.region), "method": area,
                     "times": times, "lo": row.eff_min, "hi": row.eff_max, "rate": row.pct})
    where = H.where_table(ctx, rows) if rows else H.p(t("where_none", name=sp.name), "muted")
    out.append(H.section(t("sec_where"), where, id="where"))

    held = []
    if sp.held_common:
        held.append(H.item_link(ctx, items.by_id(sp.held_common, lang), icon=True))
    if sp.held_rare and sp.held_rare != sp.held_common:
        held.append(H.item_link(ctx, items.by_id(sp.held_rare, lang), icon=True))
    breeding = H.kv([
        (t("k_egg_groups"), H.esc(", ".join(dex_texts.egg_group(g, lang) for g in sp.egg_groups))),
        (t("k_egg_cycles"), str(sp.egg_cycles)),
        (t("k_gender"), H.esc(species.gender_text(sp.gender_ratio, lang))),
        (t("k_held"), ", ".join(held) or None),
    ])
    out.append(H.section(t("sec_breeding"), breeding, id="breeding"))

    head = dict(title=sp.name, eyebrow=t("dex_eyebrow", n="%03d" % sp.natdex, category=sp.category),
                chips=H.types(ctx, sp.types), lead=H.esc(sp.description),
                aside=H.sprite_pair(ctx, sp, lazy=False))
    return "".join(out), head


# ---------------------------------------------------------------------- location page
def location_body(ctx, map_id):
    t, lang = ctx.t, ctx.lang
    m = maps.by_id(map_id, lang)
    out = []
    blocks = D.enc_blocks(ctx, map_id)
    if blocks:
        out.append(H.section(t("sec_wild"), H.encounters(ctx, blocks), id="wild", intro=H.esc(t("wild_intro"))))
    trs = D.map_trainers(map_id, lang)
    if trs:
        cards = [H.trainer_card(ctx, tr.name, D.team(ctx, tr, map_id, detail=False), cls_name=tr.class_name,
                                pic=tr, detail=False, double=bool(tr.double),
                                id="trainer-" + tr.const[len("TRAINER_"):].lower().replace("_", "-"))
                 for tr, _b in trs]
        out.append(H.section(t("sec_trainers"), H.trainer_list(cards), id="trainers",
                             intro=H.esc(t("trainers_intro", n=len(trs)))))
    found, _shop = D.map_items(ctx, map_id)
    if found:
        out.append(H.section(t("sec_items"), H.item_list(ctx, found), id="items", intro=H.esc(t("items_intro"))))
    region = D.REGION_ID.get(m.region)
    chips = [H.region_chip(ctx, region)] if region else []
    if trs:
        chips.append(H.chip(t("n_trainers", n=len(trs)), "muted"))
    if found:
        chips.append(H.chip(t("n_items", n=len(found)), "muted"))
    head = dict(title=m.display, eyebrow=t("loc_eyebrow", region=ctx.ui("region_" + region) if region else ""),
                chips="".join(chips))
    return "".join(out), head, (trs, found, blocks)


# ---------------------------------------------------------------------- gallery
def gallery_body(ctx):
    t, lang = ctx.t, ctx.lang
    sp = species.by_const(MON, lang)
    out = []

    out.append(H.section(t("compositions"), H.grid([
        H.page_tile(ctx, "dev/pokemon", media=H.mon_icon(ctx, sp)),
        H.page_tile(ctx, "dev/location"),
    ], "m"), id="pages"))

    # tokens
    sw = "".join('<div class="dev-sw" style="background:var(--%s);color:var(--%s)">%s</div>' % (bg, fg, bg)
                 for bg, fg in (("bg", "text"), ("surface", "text"), ("surface-2", "text"), ("surface-3", "text"),
                                ("jade", "surface"), ("jade-soft", "jade-strong"), ("jade-tint", "text"),
                                ("gold-soft", "gold"), ("warn-soft", "warn"), ("ink", "on-ink")))
    out.append(H.section(t("s_tokens"), '<div class="dev-swatches">%s</div>' % sw, id="tokens"))

    # text
    text = H.prose("<p>%s</p>" % t("sample_p", link=H.page_link(ctx, "data/typechart")))
    text += H.callout(ctx, "tip", H.p(t("sample_tip"))) + H.callout(ctx, "note", H.p(t("sample_note")))
    text += H.callout(ctx, "warning", H.p(t("sample_warn")))
    text += code('H.prose(html)   H.callout(ctx, "tip" | "note" | "warning", html, title=None)')
    text += H.steps([H.esc(t("sample_step1")), H.esc(t("sample_step2")), H.esc(t("sample_step3"))])
    text += code("H.steps([html, ...])")
    text += H.details(t("sample_q"), H.p(t("sample_a")))
    text += code("H.details(summary, body, open=False)")
    text += H.kv([(t("k_height"), H.esc(t("height", v=ctx.num(sp.height / 10.0)))),
                  (t("k_weight"), H.esc(t("weight", v=ctx.num(sp.weight / 10.0)))),
                  (t("k_exp"), str(sp.exp_yield))])
    text += code("H.kv([(label, value_html), ...])")
    out.append(H.section(t("s_text"), text, id="text"))

    # chips
    tys = typeinfo.battle_types(lang)
    ch = "<p>%s</p>" % H.chips([H.chip("Standard"), H.chip("jade", "jade"), H.chip("gold", "gold"),
                                H.chip("muted", "muted"), H.chip("warn", "warn")] +
                               [H.region_chip(ctx, r) for r in H.REGIONS])
    ch += code('H.chip(text, tone)   H.chips([...])   H.region_chip(ctx, "kanto")')
    ch += "<p>%s</p>" % H.chips([H.type_chip(ctx, x) for x in tys])
    ch += code('H.type_chip(ctx, type)   H.types(ctx, sp.types)')
    ch += "<p>%s %s</p>" % (H.chips([H.cat_chip(ctx, c) for c in H.CATEGORIES]),
                            H.chips([H.time_chip(ctx, x) for x in H.TIMES]))
    ch += code('H.cat_chip(ctx, "physical", icon_only=False)   H.time_chip(ctx, "night")')
    out.append(H.section(t("s_chips"), ch, id="chips"))

    # images
    potion = items.by_const("ITEM_POTION", lang)
    leader = trainers.by_const(LEADER, lang)
    im = H.sprite_pair(ctx, sp)
    im += code("H.sprite_pair(ctx, sp)   H.sprite_plate(ctx, sp, shiny=False, scale=2, caption=None)")
    im += "<p>%s %s %s %s</p>" % (H.mon_icon(ctx, sp), H.mon_icon(ctx, sp, 2), H.item_icon(ctx, potion),
                                  H.item_icon(ctx, potion, 2))
    im += code("H.mon_icon(ctx, sp, scale=1)   H.item_icon(ctx, item, scale=1)")
    im += "<p>%s</p>" % H.plate(H.trainer_pic(ctx, leader), H.esc(leader.name))
    im += code("H.trainer_pic(ctx, trainer)   H.plate(inner_html, caption_html)")
    out.append(H.section(t("s_images"), im, id="images"))

    # tiles and cards
    ti = H.grid([x for x in (H.page_tile(ctx, "data/typechart", media=H.cat_chip(ctx, "special", True)),
                             H.page_tile(ctx, "data/abilities/index"),
                             H.tile(None, sp.name, sp.category, media=H.mon_icon(ctx, sp))) if x], "m")
    ti += code("H.grid([H.page_tile(ctx, path, text, media), H.tile(href, title, text, media, meta)], size)")
    ti += H.grid([H.card(H.p(t("sample_note")), title=ctx.ui("note")), H.card(H.p(t("sample_tip")), title=ctx.ui("tip"))], "l")
    ti += code("H.card(body, title=None)   H.split(main, side)")
    out.append(H.section(t("s_tiles"), ti, id="tiles"))

    # tables
    shop_items = [items.by_const(c, lang) for c in ("ITEM_POTION", "ITEM_ANTIDOTE", "ITEM_POKE_BALL", "ITEM_REPEL")]
    shop_items = [x for x in shop_items if x]
    tb = H.table([(ctx.ui("item"), "main"), (ctx.ui("price"), "num"), (ctx.ui("note"), "")],
                 [[H.item_link(ctx, i, icon=True), H.esc(ctx.money(i.price)), H.esc(i.description)]
                  for i in shop_items])
    tb += code('H.table([(label, "main"), (label, "num"), label], rows, stack=True)')
    out.append(H.section(t("s_tables"), tb, id="tables"))

    # stats and types
    st = H.stat_bars(ctx, sp.stats) + code("H.stat_bars(ctx, sp.stats)")
    st += H.type_matchups(ctx, sp.types) + code("H.type_matchups(ctx, sp.types)")
    abil = [(abilities.by_id(a, lang), i == 2) for i, a in enumerate(sp.abilities[:3]) if a]
    st += H.ability_list(ctx, abil) + code("H.ability_list(ctx, [(ability, hidden), ...])")
    out.append(H.section(t("s_stats"), st, id="stats"))

    # evolution
    ev = H.evolution_chain(ctx, D.evo_tree(ctx, sp), current=sp)
    ev += H.evolution_chain(ctx, D.evo_tree(ctx, species.by_const(BRANCH, lang)))
    ev += code('H.evolution_chain(ctx, {"species": sp, "how": None, "children": [...]}, current=sp)')
    out.append(H.section(t("s_evo"), ev, id="evolution"))

    # learnsets
    level, tm, tutor, egg = D.learnsets(ctx, sp)
    le = H.learnset(ctx, "g-moves", level, tm, tutor, egg)
    le += code("H.learnset(ctx, id, level=[(lv, move)], tm=[(label, move)], tutor=[move], egg=[move])   "
               "H.move_table(ctx, rows, first=None)")
    out.append(H.section(t("s_learn"), le, id="learnsets"))

    # encounters
    blocks = D.enc_blocks(ctx, ROUTE)
    en = H.encounters(ctx, blocks[:3])
    en += code('H.encounters(ctx, [{"method": "land", "times": ["night"], "rows": [{"species", "lo", "hi", "rate"}]}])')
    rows = []
    for m, area, times, row in D.where_rows(ctx, species.by_const(BRANCH, lang))[:6]:
        rows.append({"key": m.mapsec, "name": m.display, "region": D.REGION_ID.get(m.region), "method": area,
                     "times": times, "lo": row.eff_min, "hi": row.eff_max, "rate": row.pct})
    if rows:
        en += H.where_table(ctx, rows) + code("H.where_table(ctx, [{key, name, region, method, times, lo, hi, rate}])")
    out.append(H.section(t("s_enc"), en, id="encounters"))

    # trainers
    b = trainers.battles(LEADER)[0]
    tr = H.trainer_card(ctx, leader.name, D.team(ctx, leader, b.map_id), cls_name=leader.class_name, pic=leader,
                        reward=None, id="trainer-demo")
    tr += code("H.trainer_card(ctx, name, team, cls_name=..., pic=trainer, detail=True, double=False, reward=None)")
    trs = D.map_trainers(ROUTE, lang)[:3]
    tr += H.trainer_list([H.trainer_card(ctx, x.name, D.team(ctx, x, ROUTE, detail=False), cls_name=x.class_name,
                                         pic=x, detail=False) for x, _b in trs])
    tr += code("H.trainer_list([H.trainer_card(..., detail=False), ...])")
    out.append(H.section(t("s_trainers"), tr, id="trainers"))

    # items and shops
    found, _ = D.map_items(ctx, ROUTE)
    it = H.item_list(ctx, found) + code('H.item_list(ctx, [{"item": item, "qty": 1, "hidden": False, "how": text}])')
    it += H.shop_table(ctx, [{"item": i} for i in shop_items])
    it += code('H.shop_table(ctx, [{"item": item, "price": None, "note": text}])')
    out.append(H.section(t("s_items"), it, id="items"))

    # entity grid with a filter
    dex = [s for _n, s in species.dex("national", lang)][:36]
    en2 = H.filter_bar(ctx, "g-ents", facets=[H.type_facet(ctx)])
    en2 += H.ent_grid([H.species_tile(ctx, s, number=s.natdex) for s in dex], id="g-ents")
    en2 += code('H.filter_bar(ctx, "list-id", facets=[H.type_facet(ctx), H.region_facet(ctx)])   '
                'H.ent_grid([H.species_tile(ctx, sp, number=...)], id="list-id")')
    out.append(H.section(t("s_ents"), en2, id="lists"))

    # tabs
    tabs = H.tabs([(ctx.ui("region_kanto"), H.p(t("sample_note"))), (ctx.ui("region_johto"), H.p(t("sample_tip"))),
                   (ctx.ui("region_hoenn"), H.p(t("sample_warn")))], "g-tabs")
    tabs += code('H.tabs([(label, html), ...], id)')
    out.append(H.section(t("s_tabs"), tabs, id="tabs"))

    # links
    mv = moves.by_const("MOVE_TACKLE", lang)
    ab = abilities.by_id(sp.abilities[0], lang)
    li = "<p>%s · %s · %s · %s · %s</p>" % (
        H.species_link(ctx, sp, icon=True), H.move_link(ctx, mv), H.ability_link(ctx, ab),
        H.item_link(ctx, potion, icon=True), H.location_link(ctx, "MAPSEC_ROUTE_6", maps.by_id(ROUTE, lang).display))
    li += code("H.species_link(ctx, sp, icon=True)   H.move_link(ctx, move)   H.ability_link(ctx, ability)   "
               "H.item_link(ctx, item, icon=True)   H.location_link(ctx, key, text)")
    out.append(H.section(t("s_links"), li, id="links"))
    return "".join(out)


def render(ctx):
    t = ctx.t
    ctx.begin("dev/gallery")
    ctx.end(gallery_body(ctx), lead=H.esc(t("gallery_lead")))

    ctx.begin("dev/pokemon")
    body, head = pokemon_body(ctx, species.by_const(MON, ctx.lang))
    ctx.end(body, **head)

    ctx.begin("dev/location")
    body, head, _ = location_body(ctx, ROUTE)
    ctx.end(body, **head)
