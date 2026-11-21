"""The world (world/...): overview, one hub per region and one page per location.

A location is one region map section with all its maps (gamedata.locations). Each page
shows what the game has there: wild Pokémon per sub-area, method and time of day with the
levels the game really uses, visible map Pokémon, gifts, static encounters, trades and
roamers, the trainers with the teams they field, items, shops and how the place is
connected. Facts: pages/_world_data.py, rendering: pages/_world_view.py.

Registers the locations (kind "location": the MAPSEC_* constant; dive sections as anchors
on the page of the place above them; the ferry by its first map id) and the anchor of
every trainer (kind "trainer") on the page of the place where the battle happens.
"""
import re

from common import html as H
from gamedata import locations as LOC
from gamedata import maps
from gamedata import trainers as T

from pages import _world_areas as A
from pages import _world_data as D
from pages import _world_view as V

INDEX = "world/index"
KINDS = ("town", "route", "dungeon", "special")
# Event islands that exist in the data but that no ferry of this build goes to
# (data/maps/LilycoveCity_Harbor/scripts.inc offers no event-ticket destination).
NO_FERRY = ("MAPSEC_SOUTHERN_ISLAND", "MAPSEC_FARAWAY_ISLAND", "MAPSEC_NAVEL_ROCK")

STRINGS = {
    "de": {
        # overview
        "index_lead": "Die Reise führt durch drei Regionen: erst Kanto, dann Johto, dann Hoenn. Hier findest du "
                      "jeden Ort mit seinen wilden Pokémon, Trainern, Items und Läden – {n} Orte insgesamt.",
        "index_regions": "Die drei Regionen",
        "index_order": "Reihenfolge der Reise",
        "index_order_1": "Kanto: Du startest in {first} und sammelst die acht Orden von Kanto. Wilde Pokémon und "
                         "Trainer haben hier die niedrigsten Level.",
        "index_order_2": "Johto: Nach deinem Sieg über die Top Vier ruft dich Prof. Eich in sein Labor in "
                         "{oak_lab} und gibt dir den {gs_ball}. Damit lässt dich die Wache hinter {route22} durch "
                         "das Tor nach {route26}; von dort geht es weiter nach {elm_town}. Die Level schließen an "
                         "Kanto an – wilde Pokémon und Trainer sind in Johto von Anfang an deutlich stärker.",
        "index_order_3": "Hoenn: Nach dem Johto-Titel bekommst du im Labor in {oak_lab} das {ticket}. Das Schiff "
                         "legt in {vermilion} oder {olivine} ab und bringt dich zur {route104}. In Hoenn sind "
                         "wilde Pokémon und Trainer von Anfang an noch einmal stärker.",
        "index_order_4": "Später fährt das Schiff auch nach {slateport} und {lilycove}, sobald du die Städte "
                         "besucht hast, nach dem Hoenn-Titel zur {frontier} und mit dem {aurora} zur "
                         "{birth_island}.",
        "index_pages": "Was die Seiten zeigen",
        "index_pages_intro": "Jede Regionsseite listet ihre Orte in der Reihenfolge der Reise, getrennt nach "
                             "Städten, Routen, Höhlen und besonderen Orten, mit Suchfeld und Filter. Jede "
                             "Ortsseite zeigt:",
        "index_pages_1": "wilde Pokémon je Bereich, Methode und Tageszeit – mit Level und Chance",
        "index_pages_2": "Geschenke, feste Begegnungen, legendäre Pokémon und Tausche",
        "index_pages_3": "alle Trainer mit ihren Teams, dem Preisgeld und Hinweisen auf Rückkämpfe",
        "index_pages_4": "Items zum Aufheben, versteckte Items, Geschenke und Beerenbäume",
        "index_pages_5": "Läden mit Angebot und Preisen sowie Attacken-Lehrer",
        "region_levels": "Wilde Pokémon: {levels}",
        "index_special": "Besondere Orte",
        "index_special_intro": "Safari-Zonen, Schiffe, Verstecke und andere Orte abseits der Routen.",
        "index_closed": "Nicht erreichbar",
        "index_closed_intro": "Diese Inseln sind im Spiel angelegt, aber keine Fähre fährt dorthin. Was es dort "
                              "gäbe, kannst du in dieser Version nicht bekommen.",
        "region_tile": "{towns} Städte · {routes} Routen · {other} weitere Orte",
        # hubs
        "hub_lead": "Alle {n} Orte in {region} in der Reihenfolge, in der du sie auf der Reise erreichst. "
                    "Zu jedem Ort steht, wie viele verschiedene wilde Pokémon, Trainer und Items es dort gibt.",
        "hub_placeholder": "Ort suchen …",
        "facet_kind": "Art",
        "group_town": "Städte und Orte",
        "group_route": "Routen",
        "group_dungeon": "Höhlen, Wälder und Türme",
        "group_special": "Gebäude und besondere Orte",
        "kind_town": "Stadt",
        "kind_route": "Route",
        "kind_dungeon": "Höhle, Wald oder Turm",
        "kind_special": "Besonderer Ort",
        "facet_town": "Städte",
        "facet_route": "Routen",
        "facet_dungeon": "Höhlen & Wälder",
        "facet_special": "Besondere Orte",
        "n_wild": "{n} wilde Pokémon",
        "n_trainers": "{n} Trainer",
        "n_trainers_1": "1 Trainer",
        "n_items": "{n} Items",
        "n_items_1": "1 Item",
        # location page
        "eyebrow": "{region} · {kind}",
        "k_access": "Zugänge",
        "k_facilities": "Vor Ort",
        "dir_north": "Norden",
        "dir_south": "Süden",
        "dir_west": "Westen",
        "dir_east": "Osten",
        "fac_center": "Pokémon-Center",
        "fac_mart": "Markt",
        "fac_gym": "Arena",
        "fac_daycare": "Pension",
        "fac_gamecorner": "Spielhalle",
        "fac_relearner": "Attacken-Helfer",
        "fac_tutor": "Attacken-Lehrer",
        "fac_deleter": "Attacken-Verlerner",
        "nothing": "An diesem Ort gibt es weder wilde Pokémon noch Trainer, Items oder Läden.",
        "gate_note": "Dieses Tor zwischen {route22} und {route26} verbindet Kanto mit Johto. Es bleibt "
                     "verschlossen, bis du die Top Vier von Kanto besiegt hast. Danach ruft dich Prof. Eich in "
                     "sein Labor in {oak_lab} und gibt dir den {gs_ball}; erst dann lässt dich die Wache durch. "
                     "Den {gs_ball} bringst du nach {elm_town}.",
        "sec_wild": "Wilde Pokémon",
        "wild_intro": "Die Chancen sind die Werte, die das Spiel hier verwendet.",
        "wild_times": "Tagsüber heißt {d0} bis {d1} Uhr, nachts {n0} bis {n1} Uhr.",
        "enc_indoor": "Im Gebäude",
        "rock_both": "{rock} und {head}",
        "feebas_title": "Besondere Angelstellen",
        "feebas_note": "Nur an {spots} zufälligen Wasserfeldern der Route (je Spielstand andere), mit jeder Angel. "
                       "Die Chance gilt je Biss an einer solchen Stelle.",
        "altering_note": "Das Spiel hat für diesen Ort {n} weitere Tabellen, die nur ein besonderes Ereignis "
                         "einschaltet. Gezeigt ist die Tabelle, die von Anfang an gilt.",
        "ow_title": "Auf der Karte zu sehen",
        "ow_intro": "Diese Pokémon laufen sichtbar herum. Sie zeigen, was hier lebt – kämpfen kannst du nur "
                    "über die Tabellen oben.",
        "ow_day": "nur tagsüber",
        "ow_night": "nur nachts",
        "ow_flag": "zeitweise",
        "sec_special": "Besondere Pokémon",
        "special_intro": "Geschenke, feste Begegnungen und Tausche an diesem Ort. Das Level ist das Level im "
                         "Spiel.",
        "kind_gift": "Geschenk",
        "kind_egg": "Ei",
        "kind_trade": "Tausch",
        "kind_static": "Feste Begegnung",
        "kind_legendary": "Legendär",
        "kind_roamer": "Streift umher",
        "trade_for": "Im Tausch gegen {mon}",
        "trade_any": "Im Tausch gegen ein beliebiges Pokémon",
        "trade_names": "Spitzname {nick}, Original-Trainer {ot}",
        "trade_level": "Level deines Pokémon",
        "egg_level": "schlüpft auf Lv. 1",
        "roamer_level": "ab {lv}",
        "roamer_beasts": "Streift durch die Routen von Johto, sobald du es in der {place} aufgescheucht hast.",
        "roamer_hoenn": "Streift nach deinem Sieg in der Hoenn-Liga durch die Routen von Hoenn.",
        "roamer_other": "Streift durch mehrere Routen.",
        "holds": "Trägt {item}",
        "kind_prize": "Spielhallenpreis",
        "n_coins": "{n} Münzen",
        "always_shiny": "Immer schillernd",
        "buy_for": "Kostet {money}",
        "note_starter": "Du wählst eines von drei Pokémon.",
        "note_birch": "Du wählst eines von drei Pokémon – erst nach dem Hoenn-Titel und wenn du alle {n} "
                      "Pokémon des Hoenn-Dex gefangen hast.",
        "note_kabuto": "Vor dem vierten Johto-Orden das niedrigere Level, danach das höhere.",
        "note_lugia": "Im Lauf der Geschichte kämpfst du auf dem niedrigeren Level. Hast du dich für {hooh} "
                      "entschieden, wartet {lugia} später auf dem höheren Level.",
        "note_hooh": "Im Lauf der Geschichte kämpfst du auf dem niedrigeren Level. Hast du dich für {lugia} "
                     "entschieden, wartet {hooh} nach dem ersten Johto-Titel auf dem höheren Level, sobald "
                     "{lugia} gefangen ist.",
        "note_tentacruel": "Verschwinden, sobald das zweite der beiden legendären Vögel von Johto erscheint.",
        "note_celebi": "Nach dem Ereignis am Schrein wartet {name} dort erneut.",
        "note_gyarados": "Kampf im Lauf der Geschichte.",
        "sec_maps": "Karten",
        "map_open": "In voller Größe öffnen",
        "map_alt": "Karte: {place}",
        "sec_trainers": "Trainer",
        "trainers_intro": "{n} Trainer kämpfen hier gegen dich. Level und Pokémon sind die, die sie im Kampf "
                          "wirklich einsetzen.",
        "trainers_intro_1": "Ein Trainer kämpft hier gegen dich. Level und Pokémon sind die, die er im Kampf "
                            "wirklich einsetzt.",
        "trainers_phone": "Klick auf einen Trainer zeigt Details und seine Rückkampf-Teams.",
        "rival_name": "Dein Rivale",
        "rival_has": "Rivale mit {name}",
        "you_chose": "Du hast {name} gewählt",
        "starter_tabs": "Team je nach Starter",
        "cond_after": "nach dem {region}-Titel",
        "cond_before": "vor dem {region}-Titel",
        "cond_league": "nach dem Ligawechsel",
        "cond_daily": "einmal täglich",
        "tab_rival": "Rivale: {name}",
        "tab_you": "Du: {name}",
        "rematch": "Rückkampf",
        "rematch_n": "Rückkampf {n}",
        "leader_note": "Die Level richten sich nach deinem Fortschritt.",
        "phone_note": "Fordert dich später per PokéCom erneut heraus ({n} weitere Teams). Die Level richten sich nach deinem Fortschritt.",
        "phone_n": "Rückkampf {n}",
        "rematch_link": "Zu den Rückkämpfen",
        "evolves_later": "Bei höherem Level: {names}",
        "multi_2v2": "Mehrfachkampf: Du kämpfst mit {partner} gegen {foes}. Jeder Gegner setzt höchstens drei "
                     "Pokémon ein.",
        "multi_2v1": "Mehrfachkampf: Du kämpfst mit {partner} gegen {foes}.",
        "partner_team": "Team von {partner}: {team}",
        "and": " und ",
        "carries": "Setzt im Kampf ein: {items}",
        "sec_items": "Items",
        "items_found": "Zum Aufheben",
        "items_found_intro": "Itembälle und versteckte Items an diesem Ort.",
        "items_gifts": "Von Personen und durch Ereignisse",
        "items_gifts_intro": "Diese Items bekommst du hier geschenkt oder als Belohnung.",
        "items_bought": "Gegen Münzen oder Geld",
        "items_bought_intro": "Diese Items gibt es hier bei Personen oder am Preisschalter – nicht im Markt.",
        "items_berries": "Beerenbäume",
        "items_berries_intro": "Diese Beeren wachsen hier zu Beginn an den Bäumen.",
        "underfoot": "direkt unter dir",
        "not_a_ball": "kein Itemball",
        "n_times": "{n}-mal",
        "sec_tutors": "Attacken-Lehrer",
        "tutors_intro": "Diese Attacken bringt hier jemand deinen Pokémon bei.",
        "tutors_bp_intro": "Bezahlt wird mit Gewinnpunkten.",
        "tutors_once_intro": "„Einmalig“ heißt: Der Lehrer bringt die Attacke nur ein einziges Mal bei.",
        "col_tutor": "Bedingung",
        "col_where": "Wo",
        "tutor_bp": "{n} Gewinnpunkte",
        "tutor_once": "einmalig",
        "sec_shops": "Läden",
        "shops_intro": "Angebot und Preise der Läden an diesem Ort.",
        "shops_badges_intro": "Ein Teil des Angebots kommt erst mit mehr Johto-Orden dazu.",
        "shop_badges": "ab {n} Johto-Orden",
        "shop_badges_1": "ab 1 Johto-Orden",
    },
    "en": {
        "index_lead": "The journey leads through three regions: first Kanto, then Johto, then Hoenn. Here you "
                      "find every place with its wild Pokémon, trainers, items and shops – {n} places in all.",
        "index_regions": "The three regions",
        "index_order": "Order of the journey",
        "index_order_1": "Kanto: you start in {first} and collect the eight Kanto badges. Wild Pokémon and "
                         "trainers have the lowest levels here.",
        "index_order_2": "Johto: after you beat the Elite Four, Prof. Oak calls you to his lab in {oak_lab} and "
                         "hands you the {gs_ball}. With it the guard behind {route22} lets you through the gate "
                         "to {route26}; from there you go on to {elm_town}. The levels continue where Kanto "
                         "stopped – wild Pokémon and trainers in Johto are much stronger from the start.",
        "index_order_3": "Hoenn: after the Johto title you receive the {ticket} at the lab in {oak_lab}. The "
                         "ship leaves from {vermilion} or {olivine} and takes you to {route104}. In Hoenn wild "
                         "Pokémon and trainers are stronger again from the start.",
        "index_order_4": "Later the ship also goes to {slateport} and {lilycove} once you have visited them, to "
                         "the {frontier} after the Hoenn title and, with the {aurora}, to {birth_island}.",
        "index_pages": "What the pages show",
        "index_pages_intro": "Every region page lists its places in travel order, split into towns, routes, "
                             "caves and special places, with a search field and a filter. Every place page "
                             "shows:",
        "index_pages_1": "wild Pokémon by area, method and time of day – with levels and rates",
        "index_pages_2": "gifts, static encounters, legendary Pokémon and trades",
        "index_pages_3": "all trainers with their teams, prize money and notes on rematches",
        "index_pages_4": "items to pick up, hidden items, gifts and Berry trees",
        "index_pages_5": "shops with stock and prices, and move tutors",
        "region_levels": "Wild Pokémon: {levels}",
        "index_special": "Special places",
        "index_special_intro": "Safari Zones, ships, hideouts and other places off the routes.",
        "index_closed": "Out of reach",
        "index_closed_intro": "These islands exist in the game, but no ferry goes there. What they would hold "
                              "cannot be obtained in this version.",
        "region_tile": "{towns} towns · {routes} routes · {other} other places",
        "hub_lead": "All {n} places of {region} in the order you reach them on your journey. Every place lists "
                    "how many different wild Pokémon, trainers and items it has.",
        "hub_placeholder": "Search place …",
        "facet_kind": "Kind",
        "group_town": "Towns and cities",
        "group_route": "Routes",
        "group_dungeon": "Caves, forests and towers",
        "group_special": "Buildings and special places",
        "kind_town": "Town",
        "kind_route": "Route",
        "kind_dungeon": "Cave, forest or tower",
        "kind_special": "Special place",
        "facet_town": "Towns",
        "facet_route": "Routes",
        "facet_dungeon": "Caves & forests",
        "facet_special": "Special places",
        "n_wild": "{n} wild Pokémon",
        "n_trainers": "{n} trainers",
        "n_trainers_1": "1 trainer",
        "n_items": "{n} items",
        "n_items_1": "1 item",
        "eyebrow": "{region} · {kind}",
        "k_access": "Entrances",
        "k_facilities": "On site",
        "dir_north": "North",
        "dir_south": "South",
        "dir_west": "West",
        "dir_east": "East",
        "fac_center": "Pokémon Center",
        "fac_mart": "Poké Mart",
        "fac_gym": "Gym",
        "fac_daycare": "Day Care",
        "fac_gamecorner": "Game Corner",
        "fac_relearner": "Move Reminder",
        "fac_deleter": "Move Deleter",
        "fac_tutor": "Move Tutor",
        "nothing": "This place has no wild Pokémon, trainers, items or shops.",
        "gate_note": "This gate between {route22} and {route26} links Kanto with Johto. It stays closed until "
                     "you have beaten the Elite Four of Kanto. After that Prof. Oak calls you to his lab in "
                     "{oak_lab} and hands you the {gs_ball}; only then does the guard let you pass. You take "
                     "the {gs_ball} to {elm_town}.",
        "sec_wild": "Wild Pokémon",
        "wild_intro": "The rates are the values the game uses here.",
        "wild_times": "Day means {d0}:00 to {d1}:00, night {n0}:00 to {n1}:00.",
        "enc_indoor": "Inside the building",
        "rock_both": "{rock} and {head}",
        "feebas_title": "Special fishing spots",
        "feebas_note": "Only on {spots} random water tiles of the route (different in every save file), with "
                       "any rod. The rate applies to each bite on such a tile.",
        "altering_note": "The game has {n} more tables for this place that only a special event switches on. "
                         "Shown is the table that is active from the start.",
        "ow_title": "Seen on the map",
        "ow_intro": "These Pokémon walk around visibly. They show what lives here – you can only battle through "
                    "the tables above.",
        "ow_day": "day only",
        "ow_night": "night only",
        "ow_flag": "at times",
        "sec_special": "Special Pokémon",
        "special_intro": "Gifts, static encounters and trades at this place. The level is the level in the game.",
        "kind_gift": "Gift",
        "kind_egg": "Egg",
        "kind_trade": "Trade",
        "kind_static": "Static encounter",
        "kind_legendary": "Legendary",
        "kind_roamer": "Roaming",
        "trade_for": "In exchange for {mon}",
        "trade_any": "In exchange for any Pokémon",
        "trade_names": "Nickname {nick}, original Trainer {ot}",
        "trade_level": "level of your Pokémon",
        "egg_level": "hatches at Lv. 1",
        "roamer_level": "{lv} or higher",
        "roamer_beasts": "Roams the routes of Johto once you have startled it in the {place}.",
        "roamer_hoenn": "Roams the routes of Hoenn after your victory in the Hoenn League.",
        "roamer_other": "Roams several routes.",
        "holds": "Holds {item}",
        "kind_prize": "Game Corner prize",
        "n_coins": "{n} Coins",
        "always_shiny": "Always Shiny",
        "buy_for": "Costs {money}",
        "note_starter": "You choose one of three Pokémon.",
        "note_birch": "You choose one of three Pokémon – only after the Hoenn title and once you have caught "
                      "all {n} Pokémon of the Hoenn Dex.",
        "note_kabuto": "The lower level before the fourth Johto badge, the higher one after it.",
        "note_lugia": "During the story you battle at the lower level. If you decided for {hooh}, {lugia} "
                      "waits later at the higher level.",
        "note_hooh": "During the story you battle at the lower level. If you decided for {lugia}, {hooh} waits "
                     "at the higher level after the first Johto title, once {lugia} has been caught.",
        "note_tentacruel": "They disappear as soon as the second of Johto's two legendary birds appears.",
        "note_celebi": "After the event at the shrine, {name} waits there again.",
        "note_gyarados": "Battle during the story.",
        "sec_maps": "Maps",
        "map_open": "Open at full size",
        "map_alt": "Map: {place}",
        "sec_trainers": "Trainers",
        "trainers_intro": "{n} trainers battle you here. Levels and Pokémon are the ones they really use in "
                          "battle.",
        "trainers_intro_1": "One trainer battles you here. Levels and Pokémon are the ones really used in battle.",
        "trainers_phone": "Click a trainer to see details and the rematch teams.",
        "rival_name": "Your rival",
        "rival_has": "Rival with {name}",
        "you_chose": "You chose {name}",
        "starter_tabs": "Team by starter",
        "cond_after": "after the {region} title",
        "cond_before": "before the {region} title",
        "cond_league": "after the League change",
        "cond_daily": "once a day",
        "tab_rival": "Rival: {name}",
        "tab_you": "You: {name}",
        "rematch": "Rematch",
        "rematch_n": "Rematch {n}",
        "leader_note": "The levels depend on your progress.",
        "phone_note": "Calls you later on the Pokégear for rematches ({n} more teams). The levels depend on your progress.",
        "phone_n": "Rematch {n}",
        "rematch_link": "About rematches",
        "evolves_later": "At a higher level: {names}",
        "multi_2v2": "Multi battle: you fight together with {partner} against {foes}. Each opponent uses at "
                     "most three Pokémon.",
        "multi_2v1": "Multi battle: you fight together with {partner} against {foes}.",
        "partner_team": "Team of {partner}: {team}",
        "and": " and ",
        "carries": "Uses in battle: {items}",
        "sec_items": "Items",
        "items_found": "To pick up",
        "items_found_intro": "Item balls and hidden items at this place.",
        "items_gifts": "From people and events",
        "items_gifts_intro": "You receive these items here as a gift or reward.",
        "items_bought": "For Coins or money",
        "items_bought_intro": "People or the prize counter sell these items here – not the Poké Mart.",
        "items_berries": "Berry trees",
        "items_berries_intro": "These Berries grow on the trees here at the start.",
        "underfoot": "right under you",
        "not_a_ball": "not an item ball",
        "n_times": "{n} times",
        "sec_tutors": "Move Tutors",
        "tutors_intro": "Someone here teaches your Pokémon these moves.",
        "tutors_bp_intro": "You pay with Battle Points.",
        "tutors_once_intro": "“Once” means the tutor teaches the move a single time only.",
        "col_tutor": "Condition",
        "col_where": "Where",
        "tutor_bp": "{n} Battle Points",
        "tutor_once": "once",
        "sec_shops": "Shops",
        "shops_intro": "Stock and prices of the shops at this place.",
        "shops_badges_intro": "Part of the stock only arrives with more Johto badges.",
        "shop_badges": "from {n} Johto badges",
        "shop_badges_1": "from 1 Johto badge",
    },
}

for _lang in STRINGS:
    STRINGS[_lang].update(A.STRINGS[_lang])


def _path(loc):
    """Page path of a location (the ferry gets a readable one)."""
    if loc.mapsec == "MAPSEC_DYNAMIC":
        return "world/ss-tidal"
    from common import slugs
    return slugs.entity_path("location", loc.key)


def _kind_word(ctx, loc):
    return ctx.t("kind_" + loc.kind)


def register(ctx):
    ctx.add_page(INDEX)
    for region in LOC.REGIONS:
        ctx.add_page("world/" + region)
    lang = ctx.lang
    titles = V._titles(lang)
    paths = {}
    for loc in LOC.all_locations():
        region = ctx.ui("region_" + loc.region)
        fac = [ctx.t("fac_" + f) for f in D.facilities(loc.key)]
        path = _path(loc)
        paths[loc.key] = path
        ctx.add_entity("location", loc.key, titles[loc.key], sub="%s · %s" % (region, _kind_word(ctx, loc)),
                       keywords=list(dict.fromkeys([region, _kind_word(ctx, loc)] + fac + _area_words(ctx, loc))),
                       parent="world/" + loc.region, path=path)
        for sec, frag, _ids in loc.parts:
            ctx.add_anchor("location", sec, path, frag, "%s (%s)" % (titles[loc.key], ctx.t("a_underwater")),
                           search=False)
    # trainers: one anchor per trainer constant on the page of the battle
    homes = {}
    for loc in LOC.all_locations():
        cards, phone = V.visible_battles(loc.key)
        shown = set()
        for b in cards:
            if b.const in shown:
                continue
            shown.add(b.const)
            if b.const not in homes:
                homes[b.const] = (loc, b.const, True)
        for first, lst in phone.items():
            for b in lst:
                if b.const not in homes and first in shown:
                    homes[b.const] = (loc, first, False)
    for const, (loc, target, own) in homes.items():
        tr = T.by_const(const, lang)
        # the team must be renderable (the card is only written then)
        ctx.add_anchor("trainer", const, paths[loc.key], D.frag(target), _trainer_title(ctx, tr),
                       sub="%s · %s" % (titles[loc.key], ctx.ui("region_" + loc.region)),
                       search=own and not _rematch_stage(const, target))


_PLAIN_FLOOR = re.compile(r"^(U?\d+S|EG|B?\d+F)$")


def _area_words(ctx, loc):
    """Search words: the named sub-areas of a place (Radio Tower, Department Store ...)."""
    out = []
    for lab in A.labels(ctx, loc).values():
        for part in lab.split(", "):
            part = re.sub(r"\s*\(?\d+\)?$", "", part).strip()
            if part and not _PLAIN_FLOOR.match(part) and part not in out:
                out.append(part)
    return out


def _rematch_stage(const, target):
    return const != target


def _trainer_title(ctx, tr):
    if D.rival_named(tr):
        name = ctx.t("rival_name")
    else:
        name = tr.name or ""
    if tr.class_name and tr.class_name != name:
        return ("%s %s" % (tr.class_name, name)).strip()
    return name or tr.class_name or ""


# ---------------------------------------------------------------------- pages
def _tile(ctx, loc, with_region=False):
    name = V.title(ctx, loc) if with_region else V.short_title(ctx, loc)
    facts = V.facts_text(ctx, loc)
    meta = H.esc(facts) if facts else None
    data = H.filter_attrs([name, ctx.t("kind_" + loc.kind)] + [ctx.t("fac_" + f) for f in D.facilities(loc.key)]
                          + _area_words(ctx, loc), kind=loc.kind, region=loc.region)
    return H.ent(ctx.url_for("location", loc.key), name, meta=meta, data=data,
                 aside=H.region_chip(ctx, loc.region) if with_region else None)


def _render_index(ctx):
    t = ctx.t
    locs = LOC.all_locations()
    ctx.begin(INDEX)
    tiles = []
    for region in LOC.REGIONS:
        rl = [l for l in locs if l.region == region]
        towns = sum(1 for l in rl if l.kind == "town")
        routes = sum(1 for l in rl if l.kind == "route")
        text = t("region_tile", towns=towns, routes=routes, other=len(rl) - towns - routes)
        span = D.region_wild_levels(region)
        if span:
            text += " · " + t("region_levels", levels=ctx.level_range(*span))
        tiles.append(H.page_tile(ctx, "world/" + region, text=text, meta=H.region_chip(ctx, region)))
    body = [H.section(t("index_regions"), H.grid([x for x in tiles if x], "m"), id="regions")]
    first = next(l for l in locs if l.region == "kanto")
    from gamedata import hand_progress as HP
    from gamedata import items as IT
    j, h = HP.kanto_to_johto(ctx.lang), HP.johto_to_hoenn(ctx.lang)

    def place(sec, text):
        return V.loc_link(ctx, sec, text) if LOC.by_key(sec) else H.esc(text)

    def item(const):
        return H.item_link(ctx, IT.by_const(const, ctx.lang))

    steps = [V._fmt(ctx, "index_order_1", first=V.loc_link(ctx, first.key)),
             V._fmt(ctx, "index_order_2", oak_lab=place("MAPSEC_PALLET_TOWN", j["oak_lab"]),
                    gs_ball=item("ITEM_GS_BALL"), route22=place("MAPSEC_ROUTE_22", j["route22"]),
                    route26=place("MAPSEC_ROUTE_26", j["route26"]),
                    elm_town=place("MAPSEC_NEW_BARK_TOWN", j["elm_town"])),
             V._fmt(ctx, "index_order_3", oak_lab=place("MAPSEC_PALLET_TOWN", h["oak_lab"]),
                    ticket=item("ITEM_HOENN_TICKET"), vermilion=place("MAPSEC_VERMILION_CITY", h["vermilion"]),
                    olivine=place("MAPSEC_OLIVINE_CITY", h["olivine"]),
                    route104=place("MAPSEC_ROUTE_104", h["route104"])),
             V._fmt(ctx, "index_order_4", slateport=place("MAPSEC_SLATEPORT_CITY", h["slateport"]),
                    lilycove=place("MAPSEC_LILYCOVE_CITY", h["lilycove"]),
                    frontier=place("MAPSEC_BATTLE_FRONTIER", h["frontier"]), aurora=item("ITEM_AURORA_TICKET"),
                    birth_island=place("MAPSEC_BIRTH_ISLAND", h["birth_island"]))]
    body.append(H.section(t("index_order"), H.steps(steps), id="order"))
    body.append(H.section(t("index_pages"), H.ul([H.esc(t("index_pages_%d" % i)) for i in range(1, 6)]),
                          id="pages", intro=H.esc(t("index_pages_intro"))))
    special = [l for l in locs if l.kind == "special"]
    body.append(H.section(t("index_special"), H.ent_grid([_tile(ctx, l, with_region=True) for l in special]),
                          id="special", intro=H.esc(t("index_special_intro"))))
    closed = [maps.mapsec_name(s, ctx.lang) for s in NO_FERRY]
    body.append(H.section(t("index_closed"), H.ul([H.esc(x) for x in closed]), id="closed",
                          intro=H.esc(t("index_closed_intro"))))
    ctx.end("".join(body), lead=H.esc(t("index_lead", n=ctx.num(len(locs)))))


def _render_hub(ctx, region):
    t = ctx.t
    locs = LOC.in_region(region)
    ctx.begin("world/" + region)
    bar = H.filter_bar(ctx, "places", placeholder=t("hub_placeholder"), facets=[
        {"key": "kind", "label": t("facet_kind"), "options": [(k, t("facet_" + k)) for k in KINDS]}])
    groups = []
    for kind in KINDS:
        rl = [l for l in locs if l.kind == kind]
        if not rl:
            continue
        groups.append('<div data-group="%s">%s</div>' % (
            kind, H.section(t("group_" + kind), H.ent_grid([_tile(ctx, l) for l in rl]), id=kind)))
    regions = list(LOC.REGIONS)
    i = regions.index(region)
    ctx.end(bar + '<div id="places">%s</div>' % "".join(groups),
            lead=H.esc(t("hub_lead", n=ctx.num(len(locs)), region=ctx.ui("region_" + region))),
            prev="world/" + regions[i - 1] if i else INDEX,
            next="world/" + regions[i + 1] if i + 1 < len(regions) else None)


def _render_location(ctx, loc, prev, nxt):
    t = ctx.t
    ctx.begin("location", loc.key)
    body = ['<div class="place-top">%s%s</div>' % (V.overview(ctx, loc), V.map_side(ctx, loc))]
    secs = [V.wild_section(ctx, loc), V.special_section(ctx, loc), V.trainer_section(ctx, loc),
            V.items_section(ctx, loc), V.shops_section(ctx, loc), V.tutors_section(ctx, loc)]
    secs = [s for s in secs if s]
    maps_sec = V.map_section(ctx, loc)
    note = V.gate_note(ctx, loc)
    if note:
        body.append(note)
    elif not secs:
        body.append(H.callout(ctx, "note", H.p(t("nothing"))))
    body += secs
    if maps_sec:
        body.append(maps_sec)
    # anchors of the dive sections that are a part of this place
    marks = "".join('<span id="%s"></span>' % frag for _sec, frag, _ids in loc.parts)
    facts = V.facts_text(ctx, loc)
    chips = [H.region_chip(ctx, loc.region)] + [H.chip(x, "muted") for x in (facts.split(" · ") if facts else [])]
    ctx.end(marks + "".join(body), eyebrow=t("eyebrow", region=ctx.ui("region_" + loc.region),
                                           kind=t("kind_" + loc.kind)),
            chips="".join(chips), prev=("location", prev.key) if prev else "world/" + loc.region,
            next=("location", nxt.key) if nxt else None)


def _notes(ctx):
    """What the location pages leave out because it cannot be read reliably (report only)."""
    from gamedata import trainers_items as TI
    n = len(TI.unresolved())
    if n:
        ctx.todo("%d script lines hand out an item that is chosen at run time (vending machines, berry "
                 "gifts of the day, apricorn balls, phone gifts, the Battle Frontier exchange corner); these "
                 "items are not listed on the location pages" % n)
    ctx.todo("hidden coins of the Celadon Game Corner (hidden items that only carry an amount) are not shown")
    ctx.todo("fossil revival, Name Rater, Day Care and other services are only named as facilities; "
             "what they offer in detail is not read from the scripts")
    ctx.todo("conditions of gifts and static encounters are shown only where a rule of the scripts is "
             "known (starter choices, Lugia/Ho-Oh, daily rival battle); other story conditions are not stated")
    ctx.todo("named houses (Bill, Kurt, Mr. Pokémon ...) are labelled 'Haus'/'House' - the game has no "
             "text for the names of sub-areas")


def render(ctx):
    _notes(ctx)
    _render_index(ctx)
    for region in LOC.REGIONS:
        _render_hub(ctx, region)
        locs = LOC.in_region(region)
        for i, loc in enumerate(locs):
            _render_location(ctx, loc, locs[i - 1] if i else None, locs[i + 1] if i + 1 < len(locs) else None)
