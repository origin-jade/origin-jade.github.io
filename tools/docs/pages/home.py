"""Start page: what the site holds, the journey through the three regions and
quick ways into the most used pages. Tiles and links only appear for pages
that exist, so the page grows with the site.
"""
import site_config
from common import html as H
from gamedata import species

STRINGS = {
    "de": {
        "eyebrow": "Spieler-Doku · {version}",
        "lead": "Drei Regionen, eine Reise: erst Kanto, dann Johto, dann Hoenn. Hier steht alles, was du "
                "unterwegs nachschlagen willst – direkt aus den Daten des Spiels.",
        "keywords": "start übersicht origin jade doku",
        "fact_species": "Pokémon", "fact_move": "Attacken", "fact_ability": "Fähigkeiten",
        "fact_item": "Items", "fact_location": "Orte", "fact_trainer": "Trainer",
        "sec_about": "Über Origin Jade",
        "about": "Pokémon Origin Jade ist ein ROM-Hack für den Game Boy Advance: eine Reise durch drei Regionen mit einem Spielstand und einem Team. Kanto erzählt die Geschichte von Feuerrot und Blattgrün auf den moderneren Karten von Heart & Soul, Johto stammt aus Pokémon Heart & Soul, Hoenn aus Smaragd.",
        "about_1": "Drei Regionen hintereinander, jede mit eigenen Orden, eigener Liga und eigenem Titel",
        "about_2": "Sechs Spielfiguren zur Wahl auf dem Figurenrad",
        "about_3": "Herausforderungen für ein neues Spiel: Nuzlocke, Zufallsmodus, Level-Limit und mehr",
        "about_4": "VMs musst du keinem Pokémon beibringen",
        "about_credits": "Wer dahintersteht: {credits}",
        "sec_journey": "Die Reise",
        "journey_intro": "Jede Region hat ihre eigenen Orden, ihre eigene Liga und ihren eigenen Titel. "
                         "Der Abspann läuft erst am Ende der ganzen Reise.",
        "step": "Etappe {n}",
        "kanto_text": "Der Anfang. Acht Orden, die Pokémon-Liga und der erste Titel – danach geht es weiter "
                      "nach Westen.",
        "johto_text": "Die zweite Etappe mit eigenen Orden, eigener Liga und eigenem Titel.",
        "hoenn_text": "Die dritte Etappe: Nach dem Titel in Johto öffnet sich der Weg nach Hoenn.",
        "link_places": "Orte",
        "link_gyms": "Arenen & Liga",
        "sec_quick": "Oft gebraucht",
        "sec_all": "Alles im Überblick",
        "t_pokedex": "Alle Pokémon mit Werten, Attacken und Fundorten",
        "t_typechart": "Wer trifft wen sehr effektiv?",
        "t_moves": "Stärke, Genauigkeit, AP und wer sie lernt",
        "t_abilities": "Beschreibungen und Pokémon",
        "t_items": "Wirkung, Preis und Fundorte",
        "t_tms": "Alle Maschinen und wo es sie gibt",
        "t_keyitems": "Was jedes Schlüssel-Item tut und wo es es gibt",
        "t_start": "Der schnelle Einstieg",
        "t_trainers": "Jedes Team im Spiel",
        "t_breeding": "Pensionen, Ovalpin und Seltsames Ei",
    },
    "en": {
        "eyebrow": "Player's guide · {version}",
        "lead": "Three regions, one journey: Kanto first, then Johto, then Hoenn. Everything you want to "
                "look up on the way is here – read straight from the game's data.",
        "keywords": "home overview origin jade guide",
        "fact_species": "Pokémon", "fact_move": "moves", "fact_ability": "abilities",
        "fact_item": "items", "fact_location": "places", "fact_trainer": "trainers",
        "sec_about": "About Origin Jade",
        "about": "Pokémon Origin Jade is a ROM hack for the Game Boy Advance: one journey through three regions with one save file and one team. Kanto tells the story of FireRed and LeafGreen on the modern-looking maps of Heart & Soul, Johto is from Pokémon Heart & Soul, Hoenn from Emerald.",
        "about_1": "Three regions in a row, each with its own badges, League and title",
        "about_2": "Six player characters to choose from on the character wheel",
        "about_3": "Challenges for a new game: Nuzlocke, randomizer, level caps and more",
        "about_4": "You do not have to teach HMs to any Pokémon",
        "about_credits": "Who is behind it: {credits}",
        "sec_journey": "The journey",
        "journey_intro": "Every region has its own badges, its own League and its own title. "
                         "The credits only roll at the end of the whole journey.",
        "step": "Stage {n}",
        "kanto_text": "Where it starts. Eight badges, the Pokémon League and the first title – then the "
                      "road leads west.",
        "johto_text": "The second stage, with its own badges, its own League and its own title.",
        "hoenn_text": "The third stage: after the title in Johto the way to Hoenn opens.",
        "link_places": "Places",
        "link_gyms": "Gyms & League",
        "sec_quick": "Used most",
        "sec_all": "Everything at a glance",
        "t_pokedex": "Every Pokémon with stats, moves and locations",
        "t_typechart": "Who hits whom super effectively?",
        "t_moves": "Power, accuracy, PP and who learns them",
        "t_abilities": "Descriptions and Pokémon",
        "t_items": "Effect, price and where to find them",
        "t_tms": "Every machine and where to get it",
        "t_keyitems": "What every key item does and where to get it",
        "t_start": "The quick way in",
        "t_trainers": "Every team in the game",
        "t_breeding": "Day Cares, Oval Charm and the Odd Egg",
    },
}

# region -> title-screen legendaries shown on its card (species constants)
JOURNEY = (("kanto", ("SPECIES_MEWTWO",)), ("johto", ("SPECIES_HO_OH", "SPECIES_LUGIA")),
           ("hoenn", ("SPECIES_RAYQUAZA",)))
QUICK = (("pokedex/index", "t_pokedex"), ("data/typechart", "t_typechart"), ("data/moves/index", "t_moves"),
         ("data/abilities/index", "t_abilities"), ("data/items/index", "t_items"), ("data/tms", "t_tms"),
         ("guides/keyitems", "t_keyitems"), ("game/start", "t_start"),
         ("battles/trainers", "t_trainers"), ("guides/breeding", "t_breeding"))
FACTS = ("species", "move", "ability", "item", "location", "trainer")


def register(ctx):
    ctx.add_page("index", keywords=ctx.t("keywords"))


def _hero(ctx):
    t = ctx.t
    counts = {}
    for (kind, _key), e in ctx.entries.items():
        if kind in ("species", "location") and e.frag:
            continue          # forms and parts of a place are not counted as their own entry
        counts[kind] = counts.get(kind, 0) + 1
    facts = "".join("<li><b>%s</b>%s</li>" % (H.esc(ctx.num(counts[k])), H.esc(t("fact_" + k)))
                    for k in FACTS if counts.get(k, 0) > 1)
    art = ('<figure class="hero-art"><img src="%s" alt="%s" width="480" height="320" decoding="async"></figure>'
           % (ctx.root + "../assets/img/title-2x.png", H.esc(ctx.ui("site_name"))))
    name = ctx.ui("site_name")
    head, _, tail = name.partition(" ")
    return ('<section class="hero">%s<div class="hero-text"><p class="eyebrow">%s</p>'
            '<h1>%s <span>%s</span></h1><p class="hero-lead">%s</p>'
            '<button class="hero-search" type="button" data-search-open><span class="i i-search" aria-hidden="true">'
            '</span><span>%s</span><kbd aria-hidden="true">/</kbd></button>%s</div></section>'
            % (art, H.esc(t("eyebrow", version=site_config.VERSION[ctx.lang])), H.esc(head), H.esc(tail),
               H.esc(t("lead")), H.esc(ctx.ui("search_placeholder")),
               '<ul class="hero-facts">%s</ul>' % facts if facts else ""))


def _journey(ctx):
    t = ctx.t
    cards = []
    for n, (region, mons) in enumerate(JOURNEY, 1):
        name = ctx.ui("region_" + region)
        hub = ctx.url("world/" + region)
        title = '<a href="%s">%s</a>' % (hub, H.esc(name)) if hub else H.esc(name)
        art = "".join(H.sprite(ctx, species.by_const(c, ctx.lang), scale=1, lazy=False).replace(' alt="', ' title="', 1)
                      .replace("<img", '<img alt=""', 1) for c in mons)
        links = [l for l in (H.page_link(ctx, "world/" + region, t("link_places")) if hub else None,
                             H.page_link(ctx, "battles/" + region, t("link_gyms"))
                             if ctx.url("battles/" + region) else None) if l]
        cards.append(
            '<li><article class="jcard jcard-%s"><div class="jcard-top"><div><span class="jstep">%s</span>'
            '<h3>%s</h3></div><div class="jart">%s</div></div><p>%s</p>%s</article></li>'
            % (region, H.esc(t("step", n=n)), title, art, H.esc(t(region + "_text")),
               '<ul class="jlinks">%s</ul>' % "".join("<li>%s</li>" % l for l in links) if links else ""))
    return '<ol class="journey">%s</ol>' % "".join(cards)


def _all_pages(ctx):
    """Every sidebar section as a card with its pages."""
    cards = []
    for sec, pages in ctx.nav_tree():
        if sec == "home" or not pages:
            continue
        links = "".join('<li><a href="%s">%s</a></li>' % (ctx.url(p.path), H.esc(p.nav_title if p.path.endswith("/index") and p.nav_title != p.title and sec in ("world", "battles") else p.title)) for p in pages)
        cards.append(H.card('<ul class="plain">%s</ul>' % links, title=ctx.ui("sec_" + sec)))
    return H.grid(cards, "m")


def render(ctx):
    t = ctx.t
    ctx.begin("index")
    body = [_hero(ctx)]
    about = H.p(t("about")) + H.ul([H.esc(t("about_%d" % i)) for i in (1, 2, 3, 4)])
    if ctx.url("game/credits"):
        about += "<p>%s</p>" % H.esc(t("about_credits")).replace("{credits}", H.page_link(ctx, "game/credits"))
    body.append(H.section(t("sec_about"), H.prose(about), id="about"))
    body.append(H.section(t("sec_journey"), _journey(ctx), id="journey", intro=H.esc(t("journey_intro"))))
    quick = [H.page_tile(ctx, path, t(key)) for path, key in QUICK]
    quick = [q for q in quick if q]
    if quick:
        body.append(H.section(t("sec_quick"), H.grid(quick, "m"), id="quick"))
    body.append(H.section(t("sec_all"), _all_pages(ctx), id="all"))
    ctx.end("".join(body), outline=False, description=t("lead"))
