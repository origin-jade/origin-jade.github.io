"""Shiny Pokémon (guides/shiny): odds, Shiny Charm, other influences, shiny locks and the
alternate shiny colours.

Sources (gamedata.wild_shiny, gamedata.wild_statics): sShinyOddsTable / GetShinyOdds and the
"Shiny-Chance" setting; the re-rolls of CreateBoxMon (Shiny Charm, lures); the starter
preview roll; `giveitem ITEM_SHINY_CHARM` in the map scripts; setwildbattleshiny, givemon
shinyMode and the fixed ids of in-game trades; gSpeciesInfo[].shinyPaletteModern for the
alternate colours (front sprite with that palette).
"""
from common import html as H
from gamedata import graphics, items, repo_path, species as SP
from gamedata import wild_shiny as WSH
from gamedata import wild_statics as WS
from pages import _game_util as U
from pages import _pokedex_data as PD

PATH = "guides/shiny"

S = {
    "de": {
        "sh_lead": "Wie oft Pokémon schillern, was die Chance erhöht, welche Pokémon immer oder nie schillern – "
                   "und die {n} Pokémon mit einer zweiten Shiny-Färbung.",
        "sh_sec_odds": "Shiny-Chance",
        "sh_odds_intro": "Die Einstellung „{option}“ (Reiter „{tab}“) legt die Grundchance fest. Du wählst sie "
                         "zu Spielbeginn.",
        "sh_col_setting": "Einstellung",
        "sh_col_chance": "Chance",
        "sh_col_charm": "Mit {charm}",
        "sh_col_desc": "Beschreibung im Spiel",
        "sh_one_in": "1 zu {n}",
        "sh_about": "≈ 1 zu {n}",
        "sh_sec_charm": "Schillerpin",
        "sh_charm_effect": "Mit dem {charm} würfelt das Spiel bis zu {n}-mal neu, wenn ein Pokémon nicht "
                           "schillert. Das gilt für wilde Pokémon, Geschenke, Eier und die Starter-Vorschau.",
        "sh_charm_where": "Du bekommst ihn von Professor Eich im Labor in {place}, sobald dein Johto-Pokédex "
                          "vollständig ist. Welche Arten dafür zählen, steht unter {completion}.",
        "sh_completion": "Pokédex vervollständigen",
        "sh_sec_more": "Weitere Einflüsse",
        "sh_lure": "{lures}: Solange das Item wirkt, gibt es einen zusätzlichen Wurf. Zu kaufen in {where}.",
        "sh_preview": "Starter: Die Vorschau im Labor würfelt einmal pro Pokéball. Der Starter schillert genau "
                      "dann, wenn er in der Vorschau geschillert hat. Der {charm} zählt mit.",
        "sh_obtainable": "Wo du nicht fangen kannst, gibt es keine schillernden Pokémon.",
        "sh_roamer": "Umherstreifende Pokémon: Ob sie schillern, entscheidet sich einmal, wenn sie loslaufen.",
        "sh_clause": "Nuzlocke-Einstellung „{option}“: {choices}",
        "sh_sec_locks": "Feste Regeln für einzelne Pokémon",
        "sh_lock_always": "Immer schillernd",
        "sh_lock_preview": "Schillernd genau wie in der Vorschau",
        "sh_lock_never": "Nie schillernd",
        "sh_lock_trade": "Tausch-Pokémon: nie schillernd",
        "sh_sec_alt": "Zweite Shiny-Färbung",
        "sh_alt_intro": "Diese {n} Pokémon haben eine zweite Shiny-Färbung. Das Spiel zeigt sie, wenn die "
                        "Einstellung „{option}“ (Reiter „{tab}“) auf „{on}“ steht.",
        "sh_classic": "Klassisch",
        "sh_alternate": "Alternativ",
    },
    "en": {
        "sh_lead": "How often Pokémon are shiny, what raises the odds, which Pokémon are always or never shiny – "
                   "and the {n} Pokémon with a second shiny colouring.",
        "sh_sec_odds": "Shiny odds",
        "sh_odds_intro": "The setting “{option}” (tab “{tab}”) sets the base odds. You choose it when you start "
                         "the game.",
        "sh_col_setting": "Setting",
        "sh_col_chance": "Odds",
        "sh_col_charm": "With {charm}",
        "sh_col_desc": "Description in the game",
        "sh_one_in": "1 in {n}",
        "sh_about": "≈ 1 in {n}",
        "sh_sec_charm": "Shiny Charm",
        "sh_charm_effect": "With the {charm} the game rolls up to {n} more times when a Pokémon is not shiny. "
                           "This applies to wild Pokémon, gifts, eggs and the starter preview.",
        "sh_charm_where": "Professor Oak gives it to you in his lab in {place} once your Johto Pokédex is "
                          "complete. Which species count is listed under {completion}.",
        "sh_completion": "Completing the Pokédex",
        "sh_sec_more": "Other influences",
        "sh_lure": "{lures}: while the item is active you get one extra roll. On sale in {where}.",
        "sh_preview": "Starters: the preview in the lab rolls once per Poké Ball. The starter is shiny exactly "
                      "when it was shiny in the preview. The {charm} counts.",
        "sh_obtainable": "Where you cannot catch Pokémon, there are no shiny Pokémon.",
        "sh_roamer": "Roaming Pokémon: whether they are shiny is decided once, when they start roaming.",
        "sh_clause": "Nuzlocke setting “{option}”: {choices}",
        "sh_sec_locks": "Fixed rules for single Pokémon",
        "sh_lock_always": "Always shiny",
        "sh_lock_preview": "Shiny exactly as in the preview",
        "sh_lock_never": "Never shiny",
        "sh_lock_trade": "In-game trades: never shiny",
        "sh_sec_alt": "Second shiny colouring",
        "sh_alt_intro": "These {n} Pokémon have a second shiny colouring. The game shows it when the setting "
                        "“{option}” (tab “{tab}”) is set to “{on}”.",
        "sh_classic": "Classic",
        "sh_alternate": "Alternate",
    },
}


def _alt_image(ctx, sp):
    from PIL import Image
    png = sp.gfx["front"]
    pal = graphics.palette(WSH.alt_palette(sp), png)
    w = Image.open(repo_path(png)).size[0]
    ctx.write_image("shiny-alt/%s.png" % sp.slug, graphics.render(png, pal, crop=(0, 0, w, w)))
    return ctx.asset("shiny-alt", sp.slug)


def _entries(lang):
    """Reachable scripted Pokémon (the Pokédex pages' filter)."""
    out = []
    for lst in PD.specials(lang).values():
        out.extend(lst)
    return out


def _mon(ctx, e):
    sp = SP.by_id(e.species, ctx.lang)
    mids = [e.map_id] if e.map_id else list(getattr(e, "callers", []))
    places = []
    for mid in mids:
        x = U.place(ctx, mid)
        if x not in places:
            places.append(x)
    return "%s (%s)" % (U.species(ctx, sp), ", ".join(places)) if places else U.species(ctx, sp)


def render(ctx):
    lang = ctx.lang
    t = ctx.t
    ctx.begin(PATH)
    charm = items.by_const("ITEM_SHINY_CHARM", lang)
    color = WSH.option("ITEM_FEATURES_SHINY_COLOR", lang)
    chance = WSH.option("ITEM_FEATURES_SHINY_CHANCE", lang)
    alt = sorted(WSH.alt_palette_species(lang), key=lambda s: s.natdex)
    rolls = WSH.charm_rolls()
    out = []

    rows = []
    for name, desc, odds in zip(chance.choices, chance.descriptions, WSH.odds_table()):
        base = round(65536 / odds)
        with_charm = round(1 / WSH.chance(odds, rolls))
        rows.append([H.esc(name), H.esc(t("sh_one_in", n=ctx.num(base))),
                     H.esc(t("sh_about", n=ctx.num(with_charm))), H.esc(desc)])
    out.append(H.section(t("sh_sec_odds"), H.table(
        [(t("sh_col_setting"), "main"), (t("sh_col_chance"), "num"),
         (t("sh_col_charm", charm=charm.name), "num"), t("sh_col_desc")], rows), id="odds",
        intro=H.esc(t("sh_odds_intro", option=chance.name, tab=chance.tab))))

    givers = WSH.charm_givers()
    body = U.p(ctx, "sh_charm_effect", charm=U.item(ctx, charm, icon=True), n=rolls)
    if givers:
        place = U.join(ctx, sorted({U.place(ctx, m) for m, _ in givers}))
        body += U.p(ctx, "sh_charm_where", place=place, completion=U.page(ctx, "guides/completion",
                                                                          t("sh_completion")))
    else:
        ctx.todo("shiny guide: no script hands out the Shiny Charm")
    out.append(H.section(t("sh_sec_charm"), H.prose(body), id="charm"))

    fl = WSH.flags()
    more = []
    lures = [items.by_const(c, lang) for c in ("ITEM_LURE", "ITEM_SUPER_LURE", "ITEM_MAX_LURE")]
    lures = [it for it in lures if it]
    shops = []
    for it in lures:
        for mid in WSH.marts_selling(it.const):
            x = U.place(ctx, mid)
            if x not in shops:
                shops.append(x)
    if lures and shops:
        more.append(U.fmt(ctx, "sh_lure", lures=U.join(ctx, [U.item(ctx, it) for it in lures]),
                          where=U.join(ctx, shops)))
    more.append(U.fmt(ctx, "sh_preview", charm=U.item(ctx, charm)))
    if fl.get("P_ONLY_OBTAINABLE_SHINIES"):
        more.append(U.fmt(ctx, "sh_obtainable"))
    more.append(U.fmt(ctx, "sh_roamer"))
    clause = WSH.option("ITEM_NUZLOCKE_SHINY_CLAUSE", lang)
    more.append(U.fmt(ctx, "sh_clause", option=U.e(clause.name), choices=U.e(" ".join(
        "„%s“ – %s" % (c, d) if lang == "de" else "“%s” – %s" % (c, d)
        for c, d in zip(clause.choices, clause.descriptions)))))
    out.append(H.section(t("sh_sec_more"), H.ul(more), id="more"))

    ents = _entries(lang)
    top = max(WSH.odds_table())
    groups = [("sh_lock_always", [e for e in ents if e.shiny == "always"]),
              ("sh_lock_preview", [e for e in ents if e.shiny == "preview"]),
              ("sh_lock_never", [e for e in ents if e.shiny == "never"]),
              ("sh_lock_trade", [e for e in ents if e.shiny == "fixed"
                                 and WS.trade_shiny_value(e.trade["ot_id"], e.trade["personality"]) >= top])]
    pairs = []
    for key, lst in groups:
        lst = sorted(lst, key=lambda e: (SP.by_id(e.species, lang).natdex, e.map_id or ""))
        seen, names = set(), []
        for e in lst:
            x = _mon(ctx, e)
            if x not in seen:
                seen.add(x)
                names.append(x)
        if names:
            pairs.append((t(key), ", ".join(names)))
    if pairs:
        out.append(H.section(t("sh_sec_locks"), "".join(H.sub(k, "<p>%s</p>" % v) for k, v in pairs), id="locks"))

    cards = []
    for sp in alt:
        classic = H.plate(H.sprite(ctx, sp, shiny=True, scale=1), H.esc(t("sh_classic")))
        other = H.plate(H.img(_alt_image(ctx, sp), 64, 64, "px", sp.name), H.esc(t("sh_alternate")))
        cards.append(H.card('<div class="plates">%s%s</div>' % (classic, other) + "<p>%s</p>" % U.species(ctx, sp)))
    out.append(H.section(t("sh_sec_alt"), H.grid(cards, "s"), id="alternate",
                         intro=H.esc(t("sh_alt_intro", n=len(alt), option=color.name, tab=color.tab,
                                       on=color.choices[1]))))
    ctx.end("".join(out), lead=H.esc(t("sh_lead", n=len(alt))))
