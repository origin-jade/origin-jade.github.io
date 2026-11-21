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
        "sh_lead": "Was bei schillernden Pokémon in Origin Jade besonders ist – und die {n} Pokémon mit einer zweiten Shiny-Färbung.",
        "sh_sec_odds": "Wie viele Begegnungen brauche ich?",
        "sh_odds_intro": "Das hängt von der Einstellung „{option}“ ab, die du zu Spielbeginn wählst.",
        "sh_col_setting": "Einstellung",
        "sh_col_chance": "Ein Shiny im Schnitt alle",
        "sh_col_charm": "Mit {charm}",
        "sh_col_desc": "Beschreibung im Spiel",
        "sh_one_in": "{n} Begegnungen",
        "sh_about": "≈ 1 zu {n}",
        "sh_average": "Das ist ein Durchschnitt, kein Zähler: Jede Begegnung wird neu gewürfelt. Nach so vielen Begegnungen haben etwa zwei von drei Spielern ein Shiny gesehen – manche viel früher, manche deutlich später.",
        "sh_sec_charm": "Schillerpin",
        "sh_charm_effect": "Mit dem {charm} schillern Pokémon etwa {x}-mal so oft.",
        "sh_charm_where": "Den {charm} bekommst du von Professor Eich im Labor in {place}, sobald dein Johto-Pokédex vollständig ist ({completion}).",
        "sh_completion": "Pokédex vervollständigen",
        "sh_sec_more": "Weitere Einflüsse",
        "sh_lure": "Auch {lures} erhöhen die Chance, solange sie wirken.",
        "sh_preview": "Starter: Die Vorschau im Labor würfelt einmal pro Pokéball. Der Starter schillert genau "
                      "dann, wenn er in der Vorschau geschillert hat. Der {charm} zählt mit.",
        "sh_obtainable": "Wo du nicht fangen kannst, gibt es keine schillernden Pokémon.",
        "sh_roamer": "Umherstreifende Pokémon: Ob sie schillern, entscheidet sich einmal, wenn sie loslaufen.",
        "sh_clause": "Nuzlocke-Einstellung „{option}“: {choices}",
        "sh_sec_locks": "Besonderheiten",
        "sh_lock_always": "Immer schillernd",
        "sh_lock_preview": "Schillernd genau wie in der Vorschau",
        "sh_lock_never": "Nie schillernd",
        "sh_lock_trade": "Tausch-Pokémon: nie schillernd",
        "sh_rule_always": "Immer schillernd: {names}.",
        "sh_rule_never": "Nie schillernd: {names}.",
        "sh_rule_preview": "Starter schillern genau dann, wenn sie in der Vorschau des Pokéballs geschillert haben.",
        "sh_rule_trade": "Pokémon aus einem Tausch im Spiel schillern nie.",
        "sh_sec_alt": "Zweite Shiny-Färbung",
        "sh_alt_intro": "Diese {n} Pokémon haben eine zweite Shiny-Färbung. Das Spiel zeigt sie, wenn die "
                        "Einstellung „{option}“ (Reiter „{tab}“) auf „{on}“ steht.",
        "sh_classic": "Klassisch",
        "sh_alternate": "Alternativ",
    },
    "en": {
        "sh_lead": "What is special about shiny Pokémon in Origin Jade – and the {n} Pokémon with a second shiny colouring.",
        "sh_sec_odds": "How many encounters do I need?",
        "sh_odds_intro": "That depends on the setting “{option}” you choose at the start of the game.",
        "sh_col_setting": "Setting",
        "sh_col_chance": "One shiny on average every",
        "sh_col_charm": "With {charm}",
        "sh_col_desc": "Description in the game",
        "sh_one_in": "{n} encounters",
        "sh_about": "≈ 1 in {n}",
        "sh_average": "This is an average, not a counter: every encounter is rolled anew. After that many encounters about two out of three players have seen a shiny – some much earlier, some a lot later.",
        "sh_sec_charm": "Shiny Charm",
        "sh_charm_effect": "With the {charm}, Pokémon are shiny about {x} times as often.",
        "sh_charm_where": "You get the {charm} from Professor Oak in the lab in {place} once your Johto Pokédex is complete ({completion}).",
        "sh_completion": "Completing the Pokédex",
        "sh_sec_more": "Other influences",
        "sh_lure": "{lures} also raise the chance while they are active.",
        "sh_preview": "Starters: the preview in the lab rolls once per Poké Ball. The starter is shiny exactly "
                      "when it was shiny in the preview. The {charm} counts.",
        "sh_obtainable": "Where you cannot catch Pokémon, there are no shiny Pokémon.",
        "sh_roamer": "Roaming Pokémon: whether they are shiny is decided once, when they start roaming.",
        "sh_clause": "Nuzlocke setting “{option}”: {choices}",
        "sh_sec_locks": "What is special",
        "sh_lock_always": "Always shiny",
        "sh_lock_preview": "Shiny exactly as in the preview",
        "sh_lock_never": "Never shiny",
        "sh_lock_trade": "In-game trades: never shiny",
        "sh_rule_always": "Always shiny: {names}.",
        "sh_rule_never": "Never shiny: {names}.",
        "sh_rule_preview": "Starters are shiny exactly when they were shiny in the preview of the Poké Ball.",
        "sh_rule_trade": "Pokémon from an in-game trade are never shiny.",
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

    # only what the game's menus and the main-series rules do not already tell the player
    rules = []
    givers = WSH.charm_givers()
    if givers:
        place = U.join(ctx, sorted({U.place(ctx, m) for m, _ in givers}))
        rules.append(U.fmt(ctx, "sh_charm_where", charm=U.item(ctx, charm), place=place,
                           completion=U.page(ctx, "guides/completion", t("sh_completion"))))
    else:
        ctx.todo("shiny guide: no script hands out the Shiny Charm")

    ents = _entries(lang)
    top = max(WSH.odds_table())
    groups = [("sh_lock_always", [e for e in ents if e.shiny == "always"]),
              ("sh_lock_preview", [e for e in ents if e.shiny == "preview"]),
              ("sh_lock_never", [e for e in ents if e.shiny == "never"]),
              ("sh_lock_trade", [e for e in ents if e.shiny == "fixed"
                                 and WS.trade_shiny_value(e.trade["ot_id"], e.trade["personality"]) >= top])]
    for key, lst in groups:
        lst = sorted(lst, key=lambda e: (SP.by_id(e.species, lang).natdex, e.map_id or ""))
        seen, names = set(), []
        for e in lst:
            x = _mon(ctx, e)
            if x not in seen:
                seen.add(x)
                names.append(x)
        if not names:
            continue
        if key == "sh_lock_always":
            continue            # the red Gyarados: known from the original games
        elif key == "sh_lock_never":
            rules.append(U.fmt(ctx, "sh_rule_never", names=U.join(ctx, names)))
        elif key == "sh_lock_preview":
            # the sentence names the starters as a group
            if any(e.kind != "gift" for e in lst):
                raise ValueError("shiny guide: a preview-locked Pokémon is not a gift")
            rules.append(U.fmt(ctx, "sh_rule_preview"))
        else:
            # the sentence covers every in-game trade
            if len(lst) != len([e for e in ents if e.kind == "trade"]):
                raise ValueError("shiny guide: not every in-game trade is shiny-locked any more")
            rules.append(U.fmt(ctx, "sh_rule_trade"))
    if rules:
        out.append(H.section(t("sh_sec_locks"), H.prose(H.ul(rules)), id="locks"))

    cards = []
    for sp in alt:
        classic = H.plate(H.sprite(ctx, sp, shiny=True, scale=1), H.esc(t("sh_classic")))
        other = H.plate(H.img(_alt_image(ctx, sp), 64, 64, "px", sp.name), H.esc(t("sh_alternate")))
        cards.append(H.card('<div class="plates">%s%s</div>' % (classic, other) + "<p>%s</p>" % U.species(ctx, sp)))
    out.append(H.section(t("sh_sec_alt"), H.grid(cards, "s"), id="alternate",
                         intro=H.esc(t("sh_alt_intro", n=len(alt), option=color.name, tab=color.tab,
                                       on=color.choices[1]))))
    ctx.end("".join(out), lead=H.esc(t("sh_lead", n=len(alt))), outline=False, cls="no-tabs")
