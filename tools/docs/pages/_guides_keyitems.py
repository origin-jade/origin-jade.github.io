"""Key items (guides/keyitems): what each key item is for and where it comes from.

The places come from the same data as the item pages (pages._items_data). What an item
is for is written by hand from the scripts that check or take it (checkitem / removeitem
in the map scripts, the field-use functions of src/data/items.h). Every key item that has
a page must have a text here, otherwise the build stops.
"""
from common import html as H
from gamedata import items as IT, locations as LOC, maps, species as SP
from pages import _game_util as U
from pages import _items_data as D
from pages import _pokedex_data as PD

PATH = "guides/keyitems"

S = {
    "de": {
        "ki_lead": "Was jedes Schlüssel-Item tut, wo du es bekommst und was es freischaltet.",
        "ki_col_item": "Item",
        "ki_col_use": "Wozu",
        "ki_col_where": "Woher",
        "ki_sec_travel": "Tickets und Reisen",
        "ki_sec_legend": "Für besondere Pokémon",
        "ki_sec_story": "Geschichte",
        "ki_sec_tools": "Werkzeuge und Dauerhaftes",
        "ki_sec_fossil": "Fossilien",
        "ki_k_gift": "Geschenk oder Ereignis",
        "ki_k_ball": "Itemball",
        "ki_k_hidden": "versteckt",
        "ki_k_shop": "Laden",
        "ki_start": "Von Spielbeginn an im Beutel.",
        "ki_legend_link": "Die ganzen Wege stehen unter {legendaries}.",
        "ki_legendaries": "Legendäre Pokémon",
        "ki_gifts": "Geschenke & Tausch",
        "ITEM_SS_TICKET": "Zutritt zum Schiff in {vermilion}. Nach dem Johto-Titel fährst du damit auch zwischen "
                          "{vermilion} und {olivine}.",
        "ITEM_HOENN_TICKET": "Die Überfahrt nach Hoenn von {olivine} oder {vermilion}. Du bekommst es nach "
                             "deinem ersten Johto-Titel.",
        "ITEM_AURORA_TICKET": "Die Schiffe fahren damit zur {birth}, wo {deoxys} wartet. Belohnung für den "
                              "vollständigen Hoenn-Pokédex.",
        "ITEM_PASS": "Fahrkarte für den Magnetzug zwischen {goldenrod} und {saffron}. Preis des Quiz im "
                     "Radioturm.",
        "ITEM_BIKE_VOUCHER": "Im Fahrradladen von {cerulean} bekommst du dafür das {bike}.",
        "ITEM_BICYCLE": "Schneller unterwegs; nötig für den Radweg.",
        "ITEM_MACH_BIKE": "Das schnelle Rad für Hoenn. Im Radladen von {mauville} tauschst du es jederzeit "
                          "gegen das {acro}.",
        "ITEM_ACRO_BIKE": "Das Rad für Kunststücke in Hoenn. Im Radladen von {mauville} tauschst du es "
                          "jederzeit gegen das {mach}.",
        "ITEM_GS_BALL": "Professor Eich gibt ihn dir nach dem Kanto-Titel: Bring ihn Professor Lind, dann steht dir Johto offen. Später bekommst du ihn von Kurt zurück und rufst damit {celebi}.",
        "ITEM_TIDAL_BELL": "Belohnung der Kimono-Girls, wenn du {lugia} gewählt hast. Öffnet den {tintower}.",
        "ITEM_CLEAR_BELL": "Belohnung der Kimono-Girls, wenn du {hooh} gewählt hast. Öffnet den {tintower}.",
        "ITEM_SILVER_WING": "Ein Andenken aus dem Radioturm, wenn du {lugia} gewählt hast. Für die Begegnung "
                            "brauchst du sie nicht.",
        "ITEM_RAINBOW_WING": "Ein Andenken aus dem Radioturm, wenn du {hooh} gewählt hast. Für die Begegnung "
                             "brauchst du sie nicht.",
        "ITEM_RED_SCALE": "Du bekommst sie nach dem Kampf gegen das rote {gyarados}. Mr. Pokémon tauscht sie "
                          "gegen: {expsmall}.",
        "ITEM_SQUIRT_BOTTLE": "Damit gießt du den seltsamen Baum auf {route36}: {sudowoodo} greift an. Es gibt "
                              "sie mit drei Johto-Orden.",
        "ITEM_POKE_FLUTE": "Weckt die beiden {snorlax} auf {route12} und {route16}.",
        "ITEM_SILPH_SCOPE": "Macht die Geister im {tower} sichtbar. Ohne es kommst du dort nicht weiter.",
        "ITEM_DEVON_SCOPE": "Macht unsichtbare {kecleon} sichtbar – auch das vor der Arena von {fortree}.",
        "ITEM_MAGMA_EMBLEM": "Öffnet das Versteck von Team Magma am {jagged}.",
        "ITEM_METEORITE": "Der Professor in {fallarbor} gibt dir dafür eine TM.",
        "ITEM_AZURE_FLUTE": "Gehört zu einem Gebiet, das in dieser Version noch nicht zugänglich ist.",
        "ITEM_PARCEL": "Bring es Professor Eich. Danach bekommst du den Pokédex.",
        "ITEM_TEA": "Die Wachen an den Toren von {saffron} lassen dich dafür durch.",
        "ITEM_LIFT_KEY": "Schaltet den Aufzug im {rockethideout} frei.",
        "ITEM_CARD_KEY": "Öffnet die Türen der {silph}. In Johto öffnet ein zweiter die Tür im Radioturm von "
                         "{goldenrod}.",
        "ITEM_SECRET_KEY": "Öffnet die Arena der {cinnabar}.",
        "ITEM_GOLD_TEETH": "Bring sie dem Wärter der Safari-Zone in {fuchsia}. Er gibt dir dafür eine VM.",
        "ITEM_MYSTERY_EGG": "Bring es von Mr. Pokémon zu Professor Lind.",
        "ITEM_BASEMENT_KEY": "Öffnet die Tür im Untergrund von {goldenrod}. Auch die Tür von {newmauville} "
                             "geht damit auf.",
        "ITEM_NEW_MAUVILLE_KEY": "Öffnet die Tür von {newmauville}.",
        "ITEM_SECRET_POTION": "Heilt das kranke Pokémon im Leuchtturm von {olivine}.",
        "ITEM_LETTER": "Bring ihn zu Troy in die {granite}.",
        "ITEM_DEVON_PARTS": "Bring sie dem Kapitän in {slateport}.",
        "ITEM_GO_GOGGLES": "Damit kannst du die Wüste auf {route111} betreten.",
        "ITEM_SCANNER": "Der Kapitän im Hafen von {slateport} tauscht ihn gegen ein Item.",
        "ITEM_STORAGE_KEY": "Öffnet den Lagerraum im {ship}.",
        "ITEM_KEY_TO_ROOM_1": "Öffnet eine Kabine im {ship}.",
        "ITEM_KEY_TO_ROOM_2": "Öffnet eine Kabine im {ship}.",
        "ITEM_KEY_TO_ROOM_4": "Öffnet eine Kabine im {ship}.",
        "ITEM_KEY_TO_ROOM_6": "Öffnet eine Kabine im {ship}.",
        "ITEM_CONTEST_PASS": "Damit darfst du an Wettbewerben teilnehmen.",
        "ITEM_COIN_CASE": "Ohne ihn kannst du in den Spielhallen nicht spielen.",
        "ITEM_POWDER_JAR": "Sammelt Beerenpuder.",
        "ITEM_POKEMON_BOX_LINK": "Öffnet deine PC-Boxen von überall. Du bekommst sie nach dem Kanto-Titel.",
        "ITEM_EXP_SHARE": "Schaltet den EP-Teiler für das ganze Team ein und aus.",
        "ITEM_OLD_ROD": "Zum Angeln. Lockt die schwächsten Pokémon an.",
        "ITEM_GOOD_ROD": "Zum Angeln. Lockt stärkere Pokémon an als die einfache Angel.",
        "ITEM_SUPER_ROD": "Zum Angeln. Lockt die stärksten Pokémon an.",
        "ITEM_DOWSING_MACHINE": "Zeigt versteckte Items in der Nähe an.",
        "ITEM_POKEBLOCK_CASE": "Bewahrt Pokériegel auf. Nötig für den Beerenmixer und die Futterspender der "
                               "Safari-Zone.",
        "ITEM_WAILMER_PAIL": "Zum Gießen von Beerenbäumen.",
        "ITEM_SOOT_SACK": "Sammelt Asche auf {route113}. Der Glasbläser dort tauscht sie gegen Items.",
        "ITEM_SHINY_CHARM": "Erhöht die Chance auf schillernde Pokémon. Belohnung für den vollständigen "
                            "Johto-Pokédex.",
        "ITEM_EXP_CHARM": "Dein Team bekommt mehr Erfahrung. Belohnung für den vollständigen Kanto-Pokédex.",
        "ITEM_OVAL_CHARM": "Erhöht die Chance auf Eier in der Pension. Du bekommst ihn mit deinem ersten Ei.",
        "ki_fossil": "Wird in einem Labor zu {mon}: {labs}.",
        "ki_fossil_intro": "Ein Forscher macht aus einem Fossil ein Pokémon, so oft du eines bringst. Im Labor der "
                           "{alph} verlässt du dafür kurz das Labor und kommst zurück; {kabuto} hat dort vor dem "
                           "vierten Johto-Orden Lv. 5, danach Lv. 20.",
    },
    "en": {
        "ki_lead": "What every key item does, where you get it and what it unlocks.",
        "ki_col_item": "Item",
        "ki_col_use": "What it is for",
        "ki_col_where": "Where from",
        "ki_sec_travel": "Tickets and travel",
        "ki_sec_legend": "For special Pokémon",
        "ki_sec_story": "Story",
        "ki_sec_tools": "Tools and permanent items",
        "ki_sec_fossil": "Fossils",
        "ki_k_gift": "gift or event",
        "ki_k_ball": "item ball",
        "ki_k_hidden": "hidden",
        "ki_k_shop": "shop",
        "ki_start": "In your Bag from the start.",
        "ki_legend_link": "The complete routes are under {legendaries}.",
        "ki_legendaries": "Legendary Pokémon",
        "ki_gifts": "Gifts & in-game trades",
        "ITEM_SS_TICKET": "Lets you board the ship in {vermilion}. After the Johto title it also takes you "
                          "between {vermilion} and {olivine}.",
        "ITEM_HOENN_TICKET": "The crossing to Hoenn from {olivine} or {vermilion}. You receive it after your "
                             "first Johto title.",
        "ITEM_AURORA_TICKET": "With it the ships sail to {birth}, where {deoxys} waits. Reward for the complete "
                              "Hoenn Pokédex.",
        "ITEM_PASS": "Ticket for the Magnet Train between {goldenrod} and {saffron}. Prize of the quiz in the "
                     "Radio Tower.",
        "ITEM_BIKE_VOUCHER": "The bike shop in {cerulean} gives you the {bike} for it.",
        "ITEM_BICYCLE": "Faster travel; needed for Cycling Road.",
        "ITEM_MACH_BIKE": "The fast bike for Hoenn. The bike shop in {mauville} swaps it for the {acro} at any "
                          "time.",
        "ITEM_ACRO_BIKE": "The trick bike for Hoenn. The bike shop in {mauville} swaps it for the {mach} at any "
                          "time.",
        "ITEM_GS_BALL": "Professor Oak gives it to you after the Kanto title: take it to Professor Elm and Johto is open to you. Later Kurt gives it back and you call {celebi} with it.",
        "ITEM_TIDAL_BELL": "Reward of the Kimono Girls if you chose {lugia}. Opens the {tintower}.",
        "ITEM_CLEAR_BELL": "Reward of the Kimono Girls if you chose {hooh}. Opens the {tintower}.",
        "ITEM_SILVER_WING": "A keepsake from the Radio Tower if you chose {lugia}. You do not need it for the "
                            "encounter.",
        "ITEM_RAINBOW_WING": "A keepsake from the Radio Tower if you chose {hooh}. You do not need it for the "
                             "encounter.",
        "ITEM_RED_SCALE": "You receive it after the battle against the red {gyarados}. Mr. Pokémon trades it "
                          "for: {expsmall}.",
        "ITEM_SQUIRT_BOTTLE": "Water the odd tree on {route36} with it and {sudowoodo} attacks. Available with "
                              "three Johto badges.",
        "ITEM_POKE_FLUTE": "Wakes the two {snorlax} on {route12} and {route16}.",
        "ITEM_SILPH_SCOPE": "Reveals the ghosts in the {tower}. You cannot get past them without it.",
        "ITEM_DEVON_SCOPE": "Reveals invisible {kecleon} – including the one in front of the Gym in {fortree}.",
        "ITEM_MAGMA_EMBLEM": "Opens Team Magma's hideout on {jagged}.",
        "ITEM_METEORITE": "The professor in {fallarbor} gives you a TM for it.",
        "ITEM_AZURE_FLUTE": "Belongs to an area that cannot be entered in this version yet.",
        "ITEM_PARCEL": "Take it to Professor Oak. Afterwards you receive the Pokédex.",
        "ITEM_TEA": "The guards at the gates of {saffron} let you through for it.",
        "ITEM_LIFT_KEY": "Unlocks the elevator in the {rockethideout}.",
        "ITEM_CARD_KEY": "Opens the doors of {silph}. In Johto a second one opens the door in the Radio Tower "
                         "of {goldenrod}.",
        "ITEM_SECRET_KEY": "Opens the Gym on {cinnabar}.",
        "ITEM_GOLD_TEETH": "Take them to the Safari Zone warden in {fuchsia}. He gives you an HM for them.",
        "ITEM_MYSTERY_EGG": "Take it from Mr. Pokémon to Professor Elm.",
        "ITEM_BASEMENT_KEY": "Opens the door in the underground of {goldenrod}. It also opens the door of "
                             "{newmauville}.",
        "ITEM_NEW_MAUVILLE_KEY": "Opens the door of {newmauville}.",
        "ITEM_SECRET_POTION": "Heals the sick Pokémon in the lighthouse of {olivine}.",
        "ITEM_LETTER": "Take it to Steven in {granite}.",
        "ITEM_DEVON_PARTS": "Take them to the captain in {slateport}.",
        "ITEM_GO_GOGGLES": "Let you enter the desert on {route111}.",
        "ITEM_SCANNER": "The captain at the harbor of {slateport} trades it for an item.",
        "ITEM_STORAGE_KEY": "Opens the storage room in the {ship}.",
        "ITEM_KEY_TO_ROOM_1": "Opens a cabin in the {ship}.",
        "ITEM_KEY_TO_ROOM_2": "Opens a cabin in the {ship}.",
        "ITEM_KEY_TO_ROOM_4": "Opens a cabin in the {ship}.",
        "ITEM_KEY_TO_ROOM_6": "Opens a cabin in the {ship}.",
        "ITEM_CONTEST_PASS": "Lets you enter contests.",
        "ITEM_COIN_CASE": "Without it you cannot play at the Game Corners.",
        "ITEM_POWDER_JAR": "Collects Berry Powder.",
        "ITEM_POKEMON_BOX_LINK": "Opens your PC Boxes from anywhere. You receive it after the Kanto title.",
        "ITEM_EXP_SHARE": "Switches the Exp. Share for the whole party on and off.",
        "ITEM_OLD_ROD": "For fishing. Attracts the weakest Pokémon.",
        "ITEM_GOOD_ROD": "For fishing. Attracts stronger Pokémon than the Old Rod.",
        "ITEM_SUPER_ROD": "For fishing. Attracts the strongest Pokémon.",
        "ITEM_DOWSING_MACHINE": "Shows hidden items nearby.",
        "ITEM_POKEBLOCK_CASE": "Holds Pokéblocks. Needed for the Berry Blender and the Safari Zone feeders.",
        "ITEM_WAILMER_PAIL": "For watering Berry trees.",
        "ITEM_SOOT_SACK": "Collects ash on {route113}. The glassblower there trades it for items.",
        "ITEM_SHINY_CHARM": "Raises the odds of shiny Pokémon. Reward for the complete Johto Pokédex.",
        "ITEM_EXP_CHARM": "Your party gains more experience. Reward for the complete Kanto Pokédex.",
        "ITEM_OVAL_CHARM": "Raises the chance of eggs at the Day Care. You receive it with your first egg.",
        "ki_fossil": "A lab turns it into {mon}: {labs}.",
        "ki_fossil_intro": "A scientist turns a fossil into a Pokémon, as often as you bring one. In the lab at the "
                           "{alph} you leave the lab for a moment and come back; {kabuto} is Lv. 5 there before the "
                           "fourth Johto badge and Lv. 20 after it.",
    },
}

SECTIONS = (
    ("ki_sec_travel", ("ITEM_SS_TICKET", "ITEM_HOENN_TICKET", "ITEM_AURORA_TICKET", "ITEM_PASS",
                       "ITEM_BIKE_VOUCHER", "ITEM_BICYCLE", "ITEM_MACH_BIKE", "ITEM_ACRO_BIKE")),
    ("ki_sec_legend", ("ITEM_GS_BALL", "ITEM_TIDAL_BELL", "ITEM_CLEAR_BELL", "ITEM_SILVER_WING",
                       "ITEM_RAINBOW_WING", "ITEM_RED_SCALE", "ITEM_SQUIRT_BOTTLE", "ITEM_POKE_FLUTE",
                       "ITEM_SILPH_SCOPE", "ITEM_DEVON_SCOPE", "ITEM_METEORITE", "ITEM_AZURE_FLUTE")),
    ("ki_sec_story", ("ITEM_PARCEL", "ITEM_TEA", "ITEM_LIFT_KEY", "ITEM_CARD_KEY", "ITEM_SECRET_KEY",
                      "ITEM_GOLD_TEETH", "ITEM_MYSTERY_EGG", "ITEM_BASEMENT_KEY", "ITEM_SECRET_POTION",
                      "ITEM_LETTER", "ITEM_DEVON_PARTS", "ITEM_GO_GOGGLES", "ITEM_MAGMA_EMBLEM",
                      "ITEM_NEW_MAUVILLE_KEY", "ITEM_SCANNER", "ITEM_STORAGE_KEY", "ITEM_KEY_TO_ROOM_1",
                      "ITEM_KEY_TO_ROOM_2", "ITEM_KEY_TO_ROOM_4", "ITEM_KEY_TO_ROOM_6", "ITEM_CONTEST_PASS")),
    ("ki_sec_tools", ("ITEM_EXP_SHARE", "ITEM_POKEMON_BOX_LINK", "ITEM_COIN_CASE", "ITEM_OLD_ROD",
                      "ITEM_GOOD_ROD", "ITEM_SUPER_ROD", "ITEM_DOWSING_MACHINE", "ITEM_POKEBLOCK_CASE",
                      "ITEM_POWDER_JAR", "ITEM_WAILMER_PAIL", "ITEM_SOOT_SACK", "ITEM_SHINY_CHARM",
                      "ITEM_EXP_CHARM", "ITEM_OVAL_CHARM")),
    ("ki_sec_fossil", ("ITEM_HELIX_FOSSIL", "ITEM_DOME_FOSSIL", "ITEM_OLD_AMBER", "ITEM_ROOT_FOSSIL",
                       "ITEM_CLAW_FOSSIL")),
)
FROM_START = ("ITEM_EXP_SHARE",)
# fossil -> (species, labs that revive it); checked against the gifts the scripts give there
FOSSILS = {
    "ITEM_HELIX_FOSSIL": ("SPECIES_OMANYTE", ("CinnabarIsland_PokemonLab_ExperimentRoom_Frlg", "RuinsOfAlph_Lab_hns")),
    "ITEM_DOME_FOSSIL": ("SPECIES_KABUTO", ("CinnabarIsland_PokemonLab_ExperimentRoom_Frlg", "RuinsOfAlph_Lab_hns")),
    "ITEM_OLD_AMBER": ("SPECIES_AERODACTYL", ("CinnabarIsland_PokemonLab_ExperimentRoom_Frlg", "RuinsOfAlph_Lab_hns")),
    "ITEM_ROOT_FOSSIL": ("SPECIES_LILEEP", ("RuinsOfAlph_Lab_hns", "RustboroCity_DevonCorp_2F")),
    "ITEM_CLAW_FOSSIL": ("SPECIES_ANORITH", ("RuinsOfAlph_Lab_hns", "RustboroCity_DevonCorp_2F")),
}
PLACES = {
    "vermilion": "VermilionCity_Frlg", "olivine": "OlivineCity_hns", "birth": "BirthIsland_Exterior_hns",
    "goldenrod": "GoldenrodCity_hns", "saffron": "SaffronCity_Frlg", "cerulean": "CeruleanCity_Frlg",
    "mauville": "MauvilleCity", "ruins": "RuinsOfAlph_B1F_hns", "tintower": "TinTower_1F_hns",
    "route36": "Route36_hns", "route12": "Route12_Frlg", "route16": "Route16_Frlg",
    "tower": "PokemonTower_6F_Frlg", "fortree": "FortreeCity", "jagged": "JaggedPass",
    "fallarbor": "FallarborTown", "rockethideout": "RocketHideout_B4F_Frlg", "silph": "SilphCo_7F_Frlg",
    "cinnabar": "CinnabarIsland_Frlg", "fuchsia": "FuchsiaCity_Frlg", "newmauville": "NewMauville_Inside",
    "granite": "GraniteCave_StevensRoom", "slateport": "SlateportCity", "route111": "Route111",
    "ship": "AbandonedShip_Corridors_B1F", "route113": "Route113",
}
SPECIES = {"deoxys": "SPECIES_DEOXYS", "celebi": "SPECIES_CELEBI", "lugia": "SPECIES_LUGIA",
           "hooh": "SPECIES_HO_OH", "gyarados": "SPECIES_GYARADOS", "sudowoodo": "SPECIES_SUDOWOODO",
           "snorlax": "SPECIES_SNORLAX", "kecleon": "SPECIES_KECLEON"}
ITEMS = {"bike": "ITEM_BICYCLE", "acro": "ITEM_ACRO_BIKE", "mach": "ITEM_MACH_BIKE",
         "expsmall": "ITEM_EXP_SHARE_SMALL"}
KINDS = {"gift": "ki_k_gift", "bought": "ki_k_gift", "ball": "ki_k_ball", "hidden": "ki_k_hidden",
         "shop": "ki_k_shop"}


def _where(ctx, it):
    seen, out = set(), []
    for p in D.places().get(it.id, ()):
        kind = ctx.t(KINDS.get(p.kind, "ki_k_gift"))
        if (p.loc, kind) in seen:
            continue
        seen.add((p.loc, kind))
        name = ctx.title_of("location", p.loc) or maps.mapsec_name(p.loc, ctx.lang)
        out.append('%s <span class="muted">(%s)</span>' % (H.location_link(ctx, p.loc, name), H.esc(kind)))
    return out


def _fossil_use(ctx, const, v):
    """Species and labs of one fossil, with the level each lab gives."""
    sp, labs = FOSSILS[const]
    gifts = {}
    for lst in PD.specials(ctx.lang).values():
        for e in lst:
            if e.kind == "gift":
                gifts[(maps.by_id(e.map_id, "de").dir, SP.by_id(e.species, "de").const)] = e
    parts = []
    for lab in labs:
        e = gifts.get((lab, SP.by_const(sp, "de").const))
        if e is None:
            raise ValueError("key items guide: %s is not revived at %s any more" % (sp, lab))
        parts.append("%s (%s)" % (U.place(ctx, lab), H.esc(" / ".join(ctx.level(x) for x in sorted(e.levels)))))
    return U.fmt(ctx, "ki_fossil", mon=U.species(ctx, sp), labs=U.join(ctx, parts), **v)


def render(ctx):
    t = ctx.t
    lang = ctx.lang
    ctx.begin(PATH)
    v = {k: U.place(ctx, d) for k, d in PLACES.items()}
    v.update({k: U.species(ctx, c) for k, c in SPECIES.items()})
    v.update({k: U.item(ctx, c) for k, c in ITEMS.items()})
    v["gifts"] = U.page(ctx, "guides/gifts", t("ki_gifts"))
    v["legendaries"] = U.page(ctx, "guides/legendaries", t("ki_legendaries"))
    alls = IT.all_items(lang)
    listed = {alls[i].const for i in D.listed_ids() if alls[i].pocket == "POCKET_KEY_ITEMS"}
    covered = {c for _s, consts in SECTIONS for c in consts}
    if listed - covered:
        raise ValueError("key items guide: key items without a text: %s" % sorted(listed - covered))
    out = []
    cols = [(t("ki_col_item"), "main"), t("ki_col_use"), t("ki_col_where")]
    for sec, consts in SECTIONS:
        rows = []
        for c in consts:
            it = IT.by_const(c, lang)
            if it is None or it.const not in listed:
                raise ValueError("key items guide: %s is not handed out any more" % c)
            where = _where(ctx, it)
            if c in FROM_START:
                where = [H.esc(t("ki_start"))]
            if not where:
                ctx.todo("key items guide: no source known for %s" % it.name)
            use = _fossil_use(ctx, c, v) if sec == "ki_sec_fossil" else U.fmt(ctx, c, **v)
            rows.append([U.item(ctx, it, icon=True), use, "<br>".join(where) if where else None])
        intro = U.fmt(ctx, "ki_legend_link", **v) if sec == "ki_sec_legend" else None
        if sec == "ki_sec_fossil":
            intro = U.fmt(ctx, "ki_fossil_intro", alph=U.place(ctx, "RuinsOfAlph_Lab_hns"),
                          kabuto=U.species(ctx, "SPECIES_KABUTO"))
        out.append(H.section(t(sec), H.table(cols, rows), id=sec[7:], intro=intro))
    ctx.end("".join(out), lead=H.esc(t("ki_lead")))
