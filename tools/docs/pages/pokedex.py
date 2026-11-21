"""Pokédex (pokedex/index and one page per Pokémon).

Sources (all through gamedata, in the language of the build):
  * order and numbers: enum ObtainableDexOrder - the national Pokédex the game
    shows (CreateMonDexNum -> NationalToObtainableOrder); Johto number:
    sJohtoToNationalOrder (the regional Pokédex of the game); regional dex
    membership: sKantoToNationalOrder / sJohtoToNationalOrder / sHoennToNationalOrder;
  * every other species of gSpeciesInfo is a form of one entry and is shown on
    that entry's page (section "forms"; the form's constant is registered as an
    anchor there, so links to a form lead to it);
  * values, texts, abilities, learnsets, evolutions: gSpeciesInfo (gamedata.species);
    labels of egg groups, growth rates and catch rates: the in-game Pokédex
    (gamedata.dex_texts);
  * options that change the data: gamedata.dex_options (level-up and egg moves
    with the Gen-3 move pool, the legendary abilities, the types without Fairy);
  * where to find it: pages/_pokedex_data.py (wild tables with effective levels,
    gifts, eggs, static battles, trades, roamers, Odd Egg, Feebas spots,
    evolution and breeding);
  * wild held items: itemCommon / itemRare with the chances of SetWildMonHeldItem
    (src/pokemon.c): 45 % common and 10 % rare, 100 % when both are the same item.
"""
from common import html as H
from common import slugs
from gamedata import (abilities, dex_options, dex_texts, hand_breeding, items, maps, moves, species, tu,
                      typeinfo)

from pages import _pokedex_data as D
from pages import _pokedex_evo as EVO

INDEX = "pokedex/index"
HELD_COMMON, HELD_RARE = 45, 10          # SetWildMonHeldItem
BIG_TABLE = 36                           # more wild rows than this: grouped table
FILTER_ROWS = 12                         # more rows than this: the table gets a filter

# Abilities that change the damage taken from a type (CanAbilityAbsorbMove,
# CalcDefenderAbilityModifiers and the type-effectiveness code of src/battle_util.c).
ABILITY_TYPES = {
    "ABILITY_LEVITATE": ("immune", ("TYPE_GROUND",)),
    "ABILITY_FLASH_FIRE": ("immune", ("TYPE_FIRE",)),
    "ABILITY_WATER_ABSORB": ("immune", ("TYPE_WATER",)),
    "ABILITY_STORM_DRAIN": ("immune", ("TYPE_WATER",)),
    "ABILITY_DRY_SKIN": ("immune", ("TYPE_WATER",)),
    "ABILITY_VOLT_ABSORB": ("immune", ("TYPE_ELECTRIC",)),
    "ABILITY_MOTOR_DRIVE": ("immune", ("TYPE_ELECTRIC",)),
    "ABILITY_LIGHTNING_ROD": ("immune", ("TYPE_ELECTRIC",)),
    "ABILITY_SAP_SIPPER": ("immune", ("TYPE_GRASS",)),
    "ABILITY_THICK_FAT": ("half", ("TYPE_FIRE", "TYPE_ICE")),
    "ABILITY_WONDER_GUARD": ("wonder", ()),
    "ABILITY_FILTER": ("filter", ()),
    "ABILITY_SOLID_ROCK": ("filter", ()),
}

# Conditions of gifts and static battles that the scripts state: (map folder, species) -> string key.
SOURCE_NOTES = {
    ("PalletTown_ProfessorOaksLab_Frlg", "SPECIES_BULBASAUR"): "n_starter",
    ("PalletTown_ProfessorOaksLab_Frlg", "SPECIES_SQUIRTLE"): "n_starter",
    ("PalletTown_ProfessorOaksLab_Frlg", "SPECIES_CHARMANDER"): "n_starter",
    ("NewBarkTown_Lab_hns", "SPECIES_CHIKORITA"): "n_starter_johto",
    ("NewBarkTown_Lab_hns", "SPECIES_CYNDAQUIL"): "n_starter_johto",
    ("NewBarkTown_Lab_hns", "SPECIES_TOTODILE"): "n_starter_johto",
    ("RuinsOfAlph_Lab_hns", "SPECIES_KABUTO"): "n_kabuto",
    ("LakeOfRage_hns", "SPECIES_GYARADOS"): "n_red_gyarados",
}

STRINGS = {
    "de": dict(EVO.S["de"], **{
        "lead": "Alle {n} Pokémon des Spiels in der Reihenfolge des Nationalen Pokédex. Jede Seite zeigt Werte, "
                "Attacken, Entwicklungen und alle Fundorte in Kanto, Johto und Hoenn.",
        "placeholder": "Name oder Nummer suchen …",
        "facet_dex": "Regional-Dex",
        "facet_in": "Erhältlich in",
        "facet_how": "Herkunft",
        "facet_gen": "Generation",
        "how_wild": "Wild",
        "how_special": "Geschenk, Tausch, Begegnung",
        "how_evo": "Nur Entwicklung/Zucht",
        "how_none": "Nicht erhältlich",
        "gen_n": "Generation {n}",
        "tile_special": "Besondere Quelle",
        "tile_evo": "Entwicklung",
        "tile_breed": "Zucht",
        "tile_none": "Nicht erhältlich",
        "n_forms": "{n} Formen",
        "eyebrow": "#{n} · {category}-Pokémon",
        "sub": "#{n} · {types}",
        "chip_from": "Ab {region} erhältlich",
        "chip_none": "Nicht erhältlich",
        "sec_stats": "Basiswerte",
        "sec_abilities": "Fähigkeiten",
        "sec_defense": "Typen-Schwächen",
        "sec_evo": "Entwicklung",
        "sec_forms": "Formen",
        "sec_moves": "Attacken",
        "sec_where": "Fundorte",
        "sec_breeding": "Zucht",
        "sec_dex": "Pokédex-Nummern",
        "dex_intro": "Die Nummer oben auf der Seite ist die des Spiels („{title}“).",
        "k_height": "Größe", "k_weight": "Gewicht", "k_catch": "Fangrate", "k_exp": "Basis-EP",
        "k_ev": "Fleißpunkte (EV)", "k_growth": "Levelaufstieg", "k_friendship": "Basis-Freundschaft",
        "held_line": "Wilde Exemplare tragen manchmal ein Item: {items}.",
        "height": "{v} m", "weight": "{v} kg", "catch": "{n} ({word})", "ev": "{n} {stat}",
        "held": "{item} ({pct})",
        "abil_legend": "Mit der Einstellung „{opt}“ = {on} hat {name} statt {old} die Fähigkeit {new}.",
        "opt_recommended": "Das ist die empfohlene Einstellung.",
        "defense_intro": "So viel Schaden nimmt {name} von Attacken dieser Typen.",
        "abil_immune": "Mit {ability}: kein Schaden durch {types}-Attacken.",
        "abil_half": "Mit {ability}: halber Schaden durch {types}-Attacken.",
        "abil_wonder": "Mit {ability}: Nur sehr effektive Attacken richten Schaden an.",
        "abil_filter": "Mit {ability}: Sehr effektive Attacken richten nur drei Viertel des Schadens an.",
        "and": " und ",
        "prefairy_sum": "Typen mit der Einstellung „{opt}“ = {off}",
        "evo_none_line": "{name} gehört zu keiner Entwicklungsreihe.",
        "evo_steps": "Bedingungen im Einzelnen",
        "forms_intro": "{name} hat {n} weitere Formen. Das Spiel hat keine eigenen Namen für Formen, deshalb sind "
                       "sie hier nummeriert.",
        "forms_intro_one": "{name} hat eine weitere Form. Das Spiel hat keinen eigenen Namen dafür.",
        "forms_intro_unown": "{name} gibt es in {n} Formen – eine für jeden Buchstaben, dazu „!“ und „?“.",
        "form_n": "Form {n}",
        "forms_look": "Formen, die nur anders aussehen",
        "forms_look_intro": "Werte, Typen, Fähigkeiten und Attacken sind dieselben wie bei {name}.",
        "forms_no_evo": "Diese Formen entwickeln sich nicht weiter.",
        "form_no_evo": "Diese Form entwickelt sich nicht weiter.",
        "form_moves": "Attacken dieser Form (Level)",
        "form_same_moves": "Attacken wie {name}.",
        "moves_intro": "Level- und Ei-Attacken hängen von der Einstellung „{opt}“ ab. Die Reiter ohne Zusatz gelten "
                       "für {a}, die Reiter mit „{b}“ für {b}. TMs, VMs und Attacken-Lehrer sind in beiden Fällen "
                       "gleich.",
        "tab_level_alt": "Level ({choice})",
        "tab_egg_alt": "Ei-Attacken ({choice})",
        "where_wild": "Wilde Pokémon",
        "where_special": "Geschenke, Tausch und besondere Begegnungen",
        "where_other": "Auf anderem Weg",
        "where_wild_intro": "Die Chancen sind die Werte, die das Spiel verwendet. Tageszeiten: {times}.",
        "time_span": "{name} {hours}",
        "where_places": "Orte",
        "enc_indoor": "Im Gebäude",
        "enc_both": "{a} / {b}",
        "bug_contest": "Käferturnier",
        "form_note": "Form {n}",
        "only_evo": "{name} kommt nicht wild vor. Du erhältst es durch Entwicklung von {from}.",
        "also_evo": "Außerdem durch Entwicklung von {from}.",
        "only_breed": "{name} kommt nicht wild vor. Es schlüpft aus Eiern von {parents}.",
        "also_breed": "Außerdem schlüpft es aus Eiern von {parents}.",
        "not_obtainable": "{name} ist in den Spieldaten vorhanden, aber im Spiel nicht erhältlich: Es gibt keine "
                          "wilden Vorkommen, kein Geschenk, keinen Tausch und keine Entwicklung oder Zucht, die "
                          "zu ihm führt.",
        "first_region": "{name} gibt es frühestens in {region}. In {earlier} gibt es keine Quelle.",
        "kind_gift": "Geschenk",
        "kind_prize": "Spielhallen-Preis",
        "kind_egg": "Ei",
        "kind_static": "Feste Begegnung",
        "kind_trade": "Tausch",
        "kind_roamer": "Umherstreifend",
        "kind_fishing": "Besondere Angelstellen",
        "col_kind": "Art",
        "col_details": "Details",
        "roaming_in": "Wechselnde Routen in {region}",
        "roamer_level": "mindestens {lv}",
        "trade_for": "im Tausch gegen {species}",
        "trade_any": "im Tausch gegen ein beliebiges Pokémon",
        "trade_level": "Level wie das abgegebene Pokémon",
        "trade_holds": "trägt {item}",
        "trade_nick": "Spitzname {nick}",
        "prize_cost": "{n} Münzen",
        "holds": "trägt {item}",
        "always_shiny": "immer schillernd",
        "never_shiny": "nie schillernd",
        "odd_egg": "Kurios-Ei der Pension",
        "feebas": "{spots} zufällige Angelstellen auf der Route (je Spielstand fest), mit jeder Angel; dort "
                  "beißt es mit {pct} Chance",
        "n_starter": "Starter: einer von drei Pokébällen im Labor.",
        "n_starter_johto": "Johto-Starter: einer von drei Pokébällen im Labor.",
        "n_kabuto": "Lv. 5 vor dem vierten Johto-Orden, Lv. 20 danach.",
        "n_red_gyarados": "Das rote Garados.",
        "k_egg_groups": "Ei-Gruppen", "k_egg_cycles": "Ei-Zyklen", "k_gender": "Geschlecht",
        "k_dex_johto": "Johto-Pokédex",
        "k_dex_regional": "Regionale Pokédexe", "k_dex_official": "Offizielle National-Nr.",
        "egg_cycles": "{n} (je {steps} Schritte)",
        "egg_self": "Aus den Eiern schlüpft {baby}.",
        "egg_none": "Legt keine Eier.",
        "egg_ditto": "Eigene Eier nur zusammen mit {ditto}.",
        "egg_only_ditto": "Legt mit jedem Pokémon Eier, das Eier legen kann; es schlüpft immer das andere "
                          "Pokémon.",
        "incense_free": "Für {baby} ist in diesem Spiel kein {incense} nötig.",
        "incense_need": "{baby} schlüpft nur, wenn ein Elternteil {incense} trägt – sonst schlüpft {regular}.",
        "egg_move_item": "Trägt ein Elternteil {item}, kennt das geschlüpfte {baby} die Attacke {move}.",
        "dex_no": "Nr. {n}",
    }),
    "en": dict(EVO.S["en"], **{
        "lead": "All {n} Pokémon in the game, in the order of the National Pokédex. Every page shows stats, moves, "
                "evolutions and every location in Kanto, Johto and Hoenn.",
        "placeholder": "Search name or number …",
        "facet_dex": "Regional Dex",
        "facet_in": "Available in",
        "facet_how": "Source",
        "facet_gen": "Generation",
        "how_wild": "Wild",
        "how_special": "Gift, trade, encounter",
        "how_evo": "Evolution/breeding only",
        "how_none": "Not obtainable",
        "gen_n": "Generation {n}",
        "tile_special": "Special source",
        "tile_evo": "Evolution",
        "tile_breed": "Breeding",
        "tile_none": "Not obtainable",
        "n_forms": "{n} forms",
        "eyebrow": "#{n} · {category} Pokémon",
        "sub": "#{n} · {types}",
        "chip_from": "Available from {region}",
        "chip_none": "Not obtainable",
        "sec_stats": "Base stats",
        "sec_abilities": "Abilities",
        "sec_defense": "Type defenses",
        "sec_evo": "Evolution",
        "sec_forms": "Forms",
        "sec_moves": "Moves",
        "sec_where": "Where to find it",
        "sec_breeding": "Breeding",
        "sec_dex": "Pokédex numbers",
        "dex_intro": "The number at the top of the page is the game's own (“{title}”).",
        "k_height": "Height", "k_weight": "Weight", "k_catch": "Catch rate", "k_exp": "Base EXP",
        "k_ev": "Effort values (EV)", "k_growth": "Growth rate", "k_friendship": "Base friendship",
        "held_line": "Wild ones sometimes hold an item: {items}.",
        "height": "{v} m", "weight": "{v} kg", "catch": "{n} ({word})", "ev": "{n} {stat}",
        "held": "{item} ({pct})",
        "abil_legend": "With the setting “{opt}” = {on}, {name} has the ability {new} instead of {old}.",
        "opt_recommended": "That is the recommended setting.",
        "defense_intro": "How much damage {name} takes from moves of these types.",
        "abil_immune": "With {ability}: no damage from {types}-type moves.",
        "abil_half": "With {ability}: half damage from {types}-type moves.",
        "abil_wonder": "With {ability}: only super effective moves deal damage.",
        "abil_filter": "With {ability}: super effective moves deal only three quarters of their damage.",
        "and": " and ",
        "prefairy_sum": "Types with the setting “{opt}” = {off}",
        "evo_none_line": "{name} is not part of an evolution line.",
        "evo_steps": "Conditions in detail",
        "forms_intro": "{name} has {n} more forms. The game has no names of its own for forms, so they are "
                       "numbered here.",
        "forms_intro_one": "{name} has one more form. The game has no name of its own for it.",
        "forms_intro_unown": "{name} comes in {n} forms – one for each letter, plus “!” and “?”.",
        "form_n": "Form {n}",
        "forms_look": "Forms that only look different",
        "forms_look_intro": "Stats, types, abilities and moves are the same as {name}'s.",
        "forms_no_evo": "These forms do not evolve.",
        "form_no_evo": "This form does not evolve.",
        "form_moves": "Moves of this form (level-up)",
        "form_same_moves": "Moves as {name}.",
        "moves_intro": "Level-up and egg moves depend on the setting “{opt}”. Tabs without a suffix apply to {a}, "
                       "tabs marked “{b}” to {b}. TMs, HMs and move tutors are the same either way.",
        "tab_level_alt": "Level-up ({choice})",
        "tab_egg_alt": "Egg moves ({choice})",
        "where_wild": "Wild Pokémon",
        "where_special": "Gifts, trades and special encounters",
        "where_other": "Other ways",
        "where_wild_intro": "The rates are the values the game uses. Times of day: {times}.",
        "time_span": "{name} {hours}",
        "where_places": "Places",
        "enc_indoor": "Inside a building",
        "enc_both": "{a} / {b}",
        "bug_contest": "Bug-Catching Contest",
        "form_note": "Form {n}",
        "only_evo": "{name} does not appear in the wild. You get it by evolving {from}.",
        "also_evo": "It can also be evolved from {from}.",
        "only_breed": "{name} does not appear in the wild. It hatches from eggs of {parents}.",
        "also_breed": "It also hatches from eggs of {parents}.",
        "not_obtainable": "{name} exists in the game data but cannot be obtained in the game: there is no wild "
                          "encounter, no gift, no trade and no evolution or breeding that leads to it.",
        "first_region": "{name} is available in {region} at the earliest. There is no source in {earlier}.",
        "kind_gift": "Gift",
        "kind_prize": "Game Corner prize",
        "kind_egg": "Egg",
        "kind_static": "Fixed encounter",
        "kind_trade": "Trade",
        "kind_roamer": "Roaming",
        "kind_fishing": "Special fishing spots",
        "col_kind": "Kind",
        "col_details": "Details",
        "roaming_in": "Changing routes in {region}",
        "roamer_level": "at least {lv}",
        "trade_for": "in exchange for {species}",
        "trade_any": "in exchange for any Pokémon",
        "trade_level": "same level as the Pokémon you give",
        "trade_holds": "holds {item}",
        "trade_nick": "nicknamed {nick}",
        "prize_cost": "{n} Coins",
        "holds": "holds {item}",
        "always_shiny": "always shiny",
        "never_shiny": "never shiny",
        "odd_egg": "Odd Egg from the Day Care",
        "feebas": "{spots} random fishing spots on the route (fixed per save file), with any rod; it bites "
                  "there with a {pct} chance",
        "n_starter": "Starter: one of the three Poké Balls in the lab.",
        "n_starter_johto": "Johto starter: one of the three Poké Balls in the lab.",
        "n_kabuto": "Lv. 5 before the fourth Johto Badge, Lv. 20 after it.",
        "n_red_gyarados": "The red Gyarados.",
        "k_egg_groups": "Egg Groups", "k_egg_cycles": "Egg cycles", "k_gender": "Gender",
        "k_dex_johto": "Johto Pokédex",
        "k_dex_regional": "Regional Pokédexes", "k_dex_official": "Official National no.",
        "egg_cycles": "{n} ({steps} steps each)",
        "egg_self": "Its eggs hatch into {baby}.",
        "egg_none": "Does not lay eggs.",
        "egg_ditto": "Eggs of its own only together with {ditto}.",
        "egg_only_ditto": "Lays eggs with any Pokémon that can lay eggs; the egg always holds the other "
                          "Pokémon.",
        "incense_free": "No {incense} is needed for {baby} in this game.",
        "incense_need": "{baby} only hatches when a parent holds {incense} – otherwise {regular} hatches.",
        "egg_move_item": "If a parent holds {item}, the hatched {baby} knows {move}.",
        "dex_no": "No. {n}",
    }),
}


# ---------------------------------------------------------------------- per-language data
class Site:
    """Everything the pages share, computed once per language."""

    def __init__(self, ctx):
        lang = self.lang = ctx.lang
        self.entries = D.entries(lang)
        self.num = {sp.id: n for n, sp in self.entries}
        self.regional = {k: {sp.natdex: n for n, sp in species.dex(k, lang)} for k in D.REGIONS}
        self.avail = D.availability()
        self.specials = D.specials(lang)
        self.odd_map, self.odd_ids = D.odd_egg(lang)
        self.feebas = D.feebas()
        self.eggs = D.egg_results()
        self.incense = {}
        for reg, it, baby in hand_breeding.incense_babies(lang):
            self.incense[reg.id] = self.incense[baby.id] = (reg, it, baby)
        t = tu.load("src/daycare.c")
        self.incense_needed = t.need("P_INCENSE_BREEDING") < t.need("GEN_9")
        self.egg_item_moves = {}
        for sp, it, mv in hand_breeding.special_moves(lang):
            self.egg_item_moves.setdefault(sp.id, []).append((it, mv))
        self.cycle_steps = hand_breeding.cycle_steps()
        self.machines = D.machines()
        self.tutors = set(moves.tutor_moves())
        self.opt_moves = dex_options.option("ITEM_MODE_MODERN_MOVES", lang)
        self.opt_legend = dex_options.option("ITEM_MODE_LEGENDARY_ABILITIES", lang)
        self.opt_fairy = dex_options.option("ITEM_MODE_FAIRY_TYPES", lang)
        self.legend_abilities = dex_options.legendary_abilities()
        self.pre_fairy = dex_options.pre_fairy_types()
        self.ditto = species.by_const("SPECIES_DITTO", lang)
        self.forms = {sp.id: self._forms(sp) for _n, sp in self.entries}

    def _forms(self, base):
        """(forms with other battle data, forms that only look different)."""
        battle, look = [], []
        for f in species.forms(base.id, self.lang):
            if f.id == base.id:
                continue
            same = (f.types == base.types and f.stats == base.stats and f.abilities == base.abilities
                    and f.levelup == base.levelup and f.teachable == base.teachable
                    and f.egg_moves == base.egg_moves)
            (look if same else battle).append(f)
        return battle, look

    def all_ids(self, base):
        b, l = self.forms[base.id]
        return [base.id] + [f.id for f in b + l]


def _type_names(sp, lang):
    out = []
    for t in sp.types:
        n = typeinfo.by_id(t, lang).name
        if n not in out:
            out.append(n)
    return out


def _type_slugs(sps, lang):
    out = []
    for sp in sps:
        for t in sp.types:
            s = typeinfo.by_id(t, lang).slug
            if s not in out:
                out.append(s)
    return out


def _dex_regions(site, sp):
    return [r for r in D.REGIONS if sp.natdex in site.regional[r]]


def _entry_avail(site, base):
    """(kinds, regions, first region) of an entry with all its forms."""
    kinds, regions = set(), set()
    for sid in site.all_ids(base):
        a = site.avail[sid]
        if a.wild:
            kinds.add("wild")
        if a.special:
            kinds.add("special")
        regions |= a.regions
    a = site.avail[base.id]
    regions |= a.regions
    if not kinds:
        kinds.add("evo" if (a.evolves_from or a.parents) else "none")
    first = next((r for r in D.REGIONS if r in regions), None)
    return kinds, regions, first


# ---------------------------------------------------------------------- register
def register(ctx):
    lang = ctx.lang
    ctx.add_page(INDEX)
    for num, sp in D.entries(lang):
        types = " ".join(_type_names(sp, lang))
        ctx.add_entity("species", sp.const, sp.name,
                       keywords="#%03d %d %s %s" % (num, num, types, sp.category),
                       icon=ctx.asset_rel("icon", sp.slug),
                       sub=ctx.t("sub", n="%03d" % num, types=" / ".join(_type_names(sp, lang))))
        path = slugs.entity_path("species", sp.const)
        for f in species.forms(sp.id, lang):
            if f.id != sp.id:
                ctx.add_anchor("species", f.const, path, "forms", f.name, search=False)


# ---------------------------------------------------------------------- index
def _tile(ctx, site, num, sp):
    t, lang = ctx.t, ctx.lang
    battle, look = site.forms[sp.id]
    kinds, regions, _first = _entry_avail(site, sp)
    a = site.avail[sp.id]
    note = None          # how a Pokémon is obtained is on its page and in the filter, not in the list
    gen = D.generation(sp.natdex)
    data = H.filter_attrs([sp.name, "%03d" % num, str(num), sp.category],
                          type=_type_slugs([sp] + battle, lang),
                          dex=_dex_regions(site, sp) or None,
                          **{"in": sorted(regions) or None, "how": sorted(kinds),
                             "gen": str(gen) if gen else None})
    meta = H.types(ctx, sp.types)
    n_forms = len(battle) + len(look)
    if n_forms:
        meta += " " + H.chip(t("n_forms", n=n_forms + 1), "muted")
    inner = ('<span class="ent-m">%s</span><span class="ent-b"><span class="ent-no">#%03d</span>'
             '<span class="ent-t">%s</span><span class="ent-x">%s</span>%s</span>'
             % (H.mon_icon(ctx, sp), num, H.esc(sp.name), meta,
                '<span class="ent-n">%s</span>' % H.esc(note) if note else ""))
    return '<li%s><a class="ent" href="%s">%s</a></li>' % (H.attrs(data), ctx.url_for("species", sp.const), inner)


def _render_index(ctx, site):
    t = ctx.t
    ctx.begin(INDEX)
    gens = sorted({D.generation(sp.natdex) for _n, sp in site.entries} - {None})
    regions = [(r, ctx.ui("region_" + r)) for r in D.REGIONS]
    facets = [
        H.type_facet(ctx),
        {"key": "dex", "label": t("facet_dex"), "options": regions, "style": "select"},
        {"key": "in", "label": t("facet_in"), "options": regions, "style": "select"},
        {"key": "how", "label": t("facet_how"), "style": "select",
         "options": [(k, t("how_" + k)) for k in ("wild", "special", "evo", "none")
                     if any(k in _entry_avail(site, sp)[0] for _n, sp in site.entries)]},
        {"key": "gen", "label": t("facet_gen"), "options": [(str(g), t("gen_n", n=g)) for g in gens],
         "style": "select"},
    ]
    bar = H.filter_bar(ctx, "dex", placeholder=t("placeholder"), facets=facets)
    tiles = [_tile(ctx, site, num, sp) for num, sp in site.entries]
    ctx.todo("Conditions of gifts, fixed encounters and roamers (story progress, items needed) are only "
             "listed where the map script states them in one line (%d notes); the rest shows place and level"
             % len(SOURCE_NOTES))
    ctx.todo("Trainers that use a Pokémon are not listed: trainer teams evolve with the level rules, so the "
             "species of the party files are not always the species fought")
    ctx.todo("How forms are obtained or changed (Deoxys, Castform, Pikachu, Pichu, Eevee) is not listed: "
             "not readable from the species data alone")
    ctx.end(bar + H.ent_grid(tiles, id="dex"), lead=H.esc(t("lead", n=ctx.num(len(site.entries)))))


# ---------------------------------------------------------------------- species page: parts
def _abil_entries(sp, lang):
    out = []
    for slot, aid in enumerate(sp.abilities[:3]):
        ab = abilities.by_id(aid, lang) if aid else None
        if ab is not None and ab.id not in [a.id for a, _h in out]:
            out.append((ab, slot == 2))
    return out


def _profile(ctx, site, sp):
    t, lang = ctx.t, ctx.lang
    names = H.stat_names(ctx)
    ev = ", ".join(t("ev", n=v, stat=names[k]) for k, v in sp.ev_yield.items() if v)
    return H.kv([
        (t("k_height"), H.esc(t("height", v=ctx.num(sp.height / 10.0)))),
        (t("k_weight"), H.esc(t("weight", v=ctx.num(sp.weight / 10.0)))),
        (t("k_catch"), H.esc(t("catch", n=sp.catch_rate, word=dex_texts.catch_class(sp.catch_rate, lang)))),
        (t("k_exp"), str(sp.exp_yield)),
        (t("k_ev"), H.esc(ev) if ev else None),
        (t("k_growth"), H.esc(dex_texts.growth(sp.growth_rate, lang))),
        (t("k_friendship"), str(sp.friendship)),
    ])


def _abilities_section(ctx, site, sp):
    t, lang = ctx.t, ctx.lang
    body = H.ability_list(ctx, _abil_entries(sp, lang))
    leg = site.legend_abilities.get(sp.id)
    if leg and sp.abilities[0]:
        o = site.opt_legend
        new, old = abilities.by_id(leg, lang), abilities.by_id(sp.abilities[0], lang)
        text = EVO._fmt(ctx, "abil_legend", opt=o.name, on=o.choices[1], name=sp.name,
                        old=EVO.V(old.name, H.ability_link(ctx, old)),
                        new=EVO.V(new.name, H.ability_link(ctx, new))).html
        if o.recommended == 1:
            text += " " + H.esc(t("opt_recommended"))
        body += H.callout(ctx, "note", "<p>%s</p><p>%s</p>" % (text, H.esc(new.description)))
    return body


def _join(ctx, parts):
    parts = list(parts)
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + H.esc(ctx.t("and")) + parts[-1]


def _defense_section(ctx, site, sp):
    t, lang = ctx.t, ctx.lang
    body = H.type_matchups(ctx, sp.types)
    notes = []
    for ab, _hidden in _abil_entries(sp, lang):
        kind, tys = ABILITY_TYPES.get(ab.const, (None, ()))
        if not kind:
            continue
        types_html = _join(ctx, [H.type_chip(ctx, c) for c in tys])
        notes.append(EVO._fmt(ctx, "abil_" + kind, ability=EVO.V(ab.name, H.ability_link(ctx, ab)),
                              types=EVO.V("", types_html)).html)
    if notes:
        body += H.ul(notes)
    pre = site.pre_fairy.get(sp.id)
    if pre:
        o = site.opt_fairy
        body += H.details(t("prefairy_sum", opt=o.name, off=o.choices[0]),
                          "<p>%s</p>%s" % (H.types(ctx, pre), H.type_matchups(ctx, pre)))
    return body


def _evolution_section(ctx, site, sp):
    tree, steps = EVO.tree(ctx, sp)
    if not tree["children"]:
        return H.p(ctx.t("evo_none_line", name=sp.name), "muted")
    body = H.evolution_chain(ctx, tree, current=sp)
    if any(len(alts) > 1 or "<a " in alts[0].html for _s, _d, alts in steps):
        body += H.sub(ctx.t("evo_steps"), EVO.steps_table(ctx, steps))
    return body


def _level_rows(ctx, levelup, lang):
    out = []
    for lv, mid in levelup:
        mv = moves.by_id(mid, lang)
        if mv is not None:
            out.append((ctx.ui("learn_evo") if lv == 0 else lv, mv))
    return out


def _learnsets(ctx, site, sp):
    """(level, tm, tutor, egg, alternative level, alternative egg)."""
    lang = ctx.lang
    level = _level_rows(ctx, sp.levelup, lang)
    tm = []
    for mid in sp.teachable:
        if mid in site.machines:
            order, num, kind = site.machines[mid]
            it = items.by_tm(kind, num, lang)
            mv = moves.by_id(mid, lang)
            if mv is not None:
                tm.append((order, num, it.name if it else "%s%02d" % (kind, num), mv))
    tm.sort(key=lambda x: (x[0], x[1]))
    tm = [(label, mv) for _o, _n, label, mv in tm]
    tutor = [moves.by_id(mid, lang) for mid in sp.teachable if mid not in site.machines]
    tutor = sorted((m for m in tutor if m), key=lambda m: (m.name.lower(), m.id))
    egg = [m for m in (moves.by_id(mid, lang) for mid in sp.egg_moves) if m]
    g_lv, g_egg = dex_options.gen3_levelup(sp.id), dex_options.gen3_egg_moves(sp.id)
    alt_level = _level_rows(ctx, g_lv, lang) if g_lv is not None and g_lv != sp.levelup else None
    alt_egg = None
    if g_egg is not None and g_egg != sp.egg_moves:
        alt_egg = [m for m in (moves.by_id(mid, lang) for mid in g_egg) if m]
    return level, tm, tutor, egg, alt_level, alt_egg


def _moves_section(ctx, site, sp):
    t = ctx.t
    level, tm, tutor, egg, alt_level, alt_egg = _learnsets(ctx, site, sp)
    o = site.opt_moves
    extra = []
    if alt_level:
        extra.append((t("tab_level_alt", choice=o.choices[0]),
                      H.move_table(ctx, [(H.esc(l), m) for l, m in alt_level], first=ctx.ui("level")), "level-alt"))
    if alt_egg:
        extra.append((t("tab_egg_alt", choice=o.choices[0]), H.move_table(ctx, alt_egg), "egg-alt"))
    intro = None
    if extra:
        intro = H.esc(t("moves_intro", opt=o.name, a=o.choices[1], b=o.choices[0]))
    return H.learnset(ctx, "moves", level, tm, tutor, egg, extra=extra), intro


def _method_text(ctx, method):
    """(method key for H.where_table or None, text override)."""
    lang = ctx.lang
    if method in H.METHODS:
        return method, None
    if method == "indoor":
        return None, ctx.t("enc_indoor")
    if method == "dive":
        return None, moves.by_const("MOVE_DIVE", lang).name
    head = moves.by_const("MOVE_HEADBUTT", lang).name
    if method == "headbutt":
        return None, head
    return None, ctx.t("enc_both", a=ctx.ui("enc_rock_smash"), b=head)


def _method_label(ctx, method):
    key, text = _method_text(ctx, method)
    return text or ctx.ui("enc_" + key)


def _wild_rows(ctx, site, base):
    """Wild rows of an entry and its forms, with a note where a row belongs to a form."""
    battle, look = site.forms[base.id]
    out = []
    forms = [base] + battle + look
    for i, f in enumerate(forms):
        note = None
        if i:
            note = D.form_caption(base, f, i) or ctx.t("form_note", n=i + 1)
        for r in D.wild_rows(f.id, ctx.lang):
            d = dict(r)
            bits = [x for x in (note, ctx.t("bug_contest") if r["special"] == "bug_contest" else None,
                                ", ".join(r["floors"]) if r["floors"] else None) if x]
            d["note"] = " · ".join(bits) if bits else None
            out.append(d)
    return out


def _times_html(ctx, times):
    return H.time_chips(ctx, times) if times else H.esc(ctx.ui("any_time"))


def _wild_table(ctx, rows):
    """Place-first table (H.where_table) or, for very long lists, one row per
    method, level span and rate with all its places."""
    if len(rows) <= BIG_TABLE:
        wrows = []
        for r in rows:
            key, text = _method_text(ctx, r["method"])
            d = {"key": r["mapsec"], "name": r["name"], "region": r["region"], "times": r["times"],
                 "lo": r["lo"], "hi": r["hi"], "rate": r["rate"], "note": r["note"]}
            if text:
                d["method_text"] = text
            else:
                d["method"] = key
            wrows.append(d)
        bar = ""
        if len(rows) > FILTER_ROWS:
            bar = H.filter_bar(ctx, "where-list", facets=[H.region_facet(ctx)])
        return bar + H.where_table(ctx, wrows, id="where-list")
    groups, order = {}, []
    for r in rows:
        key = (r["region"], r["method"], r["times"], r["rate"])
        if key not in groups:
            groups[key] = []
            order.append(key)
        place = H.location_link(ctx, r["mapsec"], r["name"])
        if r["note"]:
            place += ' <span class="muted">%s</span>' % H.esc(r["note"])
        if place not in groups[key]:
            groups[key].append(place)
    rank = {m: i for i, m in enumerate(D.METHOD_ORDER)}
    rrank = {r: i for i, r in enumerate(D.REGIONS)}
    order.sort(key=lambda k: (rrank.get(k[0], 9), rank.get(k[1], 99), -k[3]))
    body, ra = [], []
    for key in order:
        region, method, times, rate = key
        label = _method_label(ctx, method)
        body.append([H.esc(label) if " / " in label else _nb(label), H.region_chip(ctx, region) if region else None,
                     _times_html(ctx, times), _nb(ctx.pct(rate)),
                     ", ".join(groups[key])])
        ra.append(H.filter_attrs([_method_label(ctx, method)], region=region))
    cols = [(ctx.ui("method"), "main"), (ctx.ui("region"), ""), (ctx.ui("time"), ""),
            (ctx.ui("rate"), "num"), (ctx.t("where_places"), "")]
    return H.filter_bar(ctx, "where-list", text=False, facets=[H.region_facet(ctx)]) + \
        H.table(cols, body, id="where-list", row_attrs=ra)


def _nb(text):
    """Keep a short value such as "Lv. 4–11" or "20 %" on one line."""
    return H.esc(text.replace(" ", "\u00a0").replace("–", "–\u2060"))


def _place_cell(ctx, m):
    if m.mapsec in ("MAPSEC_DYNAMIC", "MAPSEC_NONE"):
        return H.esc(m.display)
    return H.location_link(ctx, m.mapsec, m.display)


def _special_rows(ctx, site, base):
    """Rows of the table of scripted sources: [kind, place, region, level, details]."""
    t, lang = ctx.t, ctx.lang
    battle, look = site.forms[base.id]
    rows = []
    for i, f in enumerate([base] + battle + look):
        fnote = None
        if i:
            fnote = D.form_caption(base, f, i) or t("form_note", n=i + 1)
        for e in site.specials.get(f.id, ()):
            details = [H.esc(fnote)] if fnote else []
            region = None
            if e.kind == "roamer":
                kind = t("kind_roamer")
                region = e.roamer.get("table") if e.roamer.get("table") in D.REGIONS else None
                place = H.esc(t("roaming_in", region=ctx.ui("region_" + region))) if region else None
                level = _nb(t("roamer_level", lv=ctx.level(e.roamer["level"])))
            else:
                m = maps.by_id(e.map_id, lang) if e.map_id else None
                if m is None:
                    callers = [maps.by_id(c, lang) for c in getattr(e, "callers", ())]
                    callers = [c for c in callers if D.map_ok(c)]
                    if not callers:
                        continue
                    seen, cells = set(), []
                    for c in callers:
                        if c.mapsec not in seen:
                            seen.add(c.mapsec)
                            cells.append(_place_cell(ctx, c))
                    place = ", ".join(cells)
                    region = D.region_of(callers[0])
                else:
                    place = _place_cell(ctx, m)
                    region = D.region_of(m)
                kind = t("kind_" + {"gift": "gift", "egg": "egg", "static": "static", "static_shiny": "static",
                                    "trade": "trade"}[e.kind])
                level = None
                if e.kind == "trade":
                    level = H.esc(t("trade_level"))
                    req = species.by_id(e.trade["requested"], lang) if e.trade.get("requested") else None
                    if req:
                        details.append(EVO._fmt(ctx, "trade_for", species=EVO.V(
                            req.name, H.species_link(ctx, req))).html)
                    else:
                        details.append(H.esc(t("trade_any")))
                    if e.trade.get("nickname"):
                        details.append(H.esc(t("trade_nick", nick=e.trade["nickname"])))
                    held = items.by_id(e.trade["held_item"], lang) if e.trade.get("held_item") else None
                    if held:
                        details.append(EVO._fmt(ctx, "trade_holds", item=EVO.V(
                            held.name, H.item_link(ctx, held))).html)
                elif e.levels:
                    level = " / ".join(_nb(ctx.level(x)) for x in e.levels)
                if e.price:
                    kind = t("kind_prize")
                    details.append(H.esc(t("prize_cost", n=ctx.num(e.price))))
                for iid in e.items:
                    it = items.by_id(iid, lang)
                    if it:
                        details.append(EVO._fmt(ctx, "holds", item=EVO.V(it.name, H.item_link(ctx, it))).html)
                if e.shiny == "always":
                    details.append(H.esc(t("always_shiny")))
                elif e.shiny == "never":
                    details.append(H.esc(t("never_shiny")))
                if m is not None:
                    nk = SOURCE_NOTES.get((m.dir, f.const))
                    if nk:
                        details.append(H.esc(t(nk)))
            rows.append([H.esc(kind), place, H.region_chip(ctx, region) if region else None, level,
                         " · ".join(details) or None])
        if f.id in site.odd_ids and site.odd_map is not None:
            m = site.odd_map
            rows.append([H.esc(t("kind_egg")), _place_cell(ctx, m), H.region_chip(ctx, D.region_of(m)),
                         None, H.esc(" · ".join(x for x in (fnote, t("odd_egg")) if x))])
        fb = site.feebas
        if fb and fb["species"] == f.id:
            m = maps.by_id(fb["map_id"], lang)
            rows.append([H.esc(t("kind_fishing")), _place_cell(ctx, m), H.region_chip(ctx, D.region_of(m)),
                         _nb(ctx.level_range(fb["lo"], fb["hi"])),
                         H.esc(t("feebas", spots=fb["spots"], pct=ctx.pct(fb["pct"])))])
    return rows


def _links(ctx, ids):
    lang = ctx.lang
    sps = [species.by_id(i, lang) for i in ids]
    return _join(ctx, [H.species_link(ctx, s) for s in sps if s])


def _where_section(ctx, site, sp, first, kinds):
    t, lang = ctx.t, ctx.lang
    a = site.avail[sp.id]
    out = []
    wild = _wild_rows(ctx, site, sp)
    special = _special_rows(ctx, site, sp)
    direct = bool(wild or special)
    if first and first != D.REGIONS[0]:
        earlier = D.REGIONS[:D.REGIONS.index(first)]
        out.append(H.callout(ctx, "note", H.p(t("first_region", name=sp.name, region=ctx.ui("region_" + first),
                                                earlier=t("and").join(ctx.ui("region_" + r) for r in earlier)))))
    if wild:
        hours = EVO.time_hours(ctx)
        spans = {}
        if all(k in hours for k in ("morning", "evening", "night")):
            spans = {"day": (hours["morning"][0], hours["evening"][1]), "night": hours["night"]}
        times = ", ".join(t("time_span", name=ctx.ui("time_" + k), hours=EVO.hours_text(ctx, *spans[k]))
                          for k in ("day", "night") if k in spans)
        show_times = any(r["times"] for r in wild)
        body = (H.p(t("where_wild_intro", times=times), "muted") if show_times else "") + _wild_table(ctx, wild)
        held = _held_items(ctx, sp)
        if held:
            body += "<p>%s</p>" % EVO._fmt(ctx, "held_line", items=EVO.V("", held)).html
        out.append(H.sub(t("where_wild"), body, id="wild"))
    if special:
        cols = [(t("col_kind"), ""), (ctx.ui("location"), "main"), (ctx.ui("region"), ""),
                (ctx.ui("levels"), ""), (t("col_details"), "")]
        out.append(H.sub(t("where_special"), H.table(cols, special), id="special"))
    other = []
    if a.evolves_from:
        other.append(EVO._fmt(ctx, "also_evo" if direct else "only_evo", name=sp.name,
                              **{"from": EVO.V("", _links(ctx, a.evolves_from))}).html)
    if a.parents and (not direct or a.regions - a.direct_regions):
        key = "also_breed" if (direct or a.evolves_from) else "only_breed"
        other.append(EVO._fmt(ctx, key, name=sp.name, parents=EVO.V("", _links(ctx, a.parents))).html)
    if other:
        html = "".join("<p>%s</p>" % x for x in other)
        out.append(H.sub(t("where_other"), H.prose(html), id="other") if direct else H.prose(html))
    if not direct and not other:
        out.append(H.callout(ctx, "warning", H.p(t("not_obtainable", name=sp.name))))
    return "".join(out)


def _held_items(ctx, sp):
    lang = ctx.lang
    out = []
    common = items.by_id(sp.held_common, lang) if sp.held_common else None
    rare = items.by_id(sp.held_rare, lang) if sp.held_rare else None

    def one(it, pct):
        return EVO._fmt(ctx, "held", item=EVO.V(it.name, H.item_link(ctx, it, icon=True)), pct=ctx.pct(pct)).html
    if common and rare and common.id == rare.id:
        out.append(one(common, 100))
    else:
        if common:
            out.append(one(common, HELD_COMMON))
        if rare:
            out.append(one(rare, HELD_RARE))
    return ", ".join(out) or None


def _breeding_section(ctx, site, sp, num):
    t, lang = ctx.t, ctx.lang
    groups = []
    for g in sp.egg_groups:
        n = dex_texts.egg_group(g, lang)
        if n not in groups:
            groups.append(n)
    can_breed = sp.id in site.eggs
    egg_lines = []
    if D.DITTO_GROUP in sp.egg_groups:
        egg_lines.append(H.esc(t("egg_only_ditto")))
    elif not can_breed:
        egg_lines.append(H.esc(t("egg_none")))
    else:
        babies = [species.by_id(b, lang) for b in site.eggs[sp.id]]
        egg_lines.append(EVO._fmt(ctx, "egg_self", baby=EVO.V("", _join(
            ctx, [H.species_link(ctx, b) if b.id != sp.id else H.esc(b.name) for b in babies if b]))).html)
        if D.needs_ditto(sp) and site.ditto is not None:
            egg_lines.append(EVO._fmt(ctx, "egg_ditto", ditto=EVO.V(
                site.ditto.name, H.species_link(ctx, site.ditto))).html)
    inc = site.incense.get(sp.id)
    if inc:
        reg, it, baby = inc
        vals = dict(baby=EVO.V(baby.name, H.species_link(ctx, baby) if baby.id != sp.id else H.esc(baby.name)),
                    incense=EVO.V(it.name, H.item_link(ctx, it)),
                    regular=EVO.V(reg.name, H.species_link(ctx, reg) if reg.id != sp.id else H.esc(reg.name)))
        if site.incense_needed:
            egg_lines.append(EVO._fmt(ctx, "incense_need", **vals).html)
        else:
            egg_lines.append(EVO._fmt(ctx, "incense_free", baby=vals["baby"], incense=vals["incense"]).html)
    for it, mv in site.egg_item_moves.get(sp.id, ()):
        egg_lines.append(EVO._fmt(ctx, "egg_move_item", item=EVO.V(it.name, H.item_link(ctx, it)), baby=sp.name,
                                  move=EVO.V(mv.name, H.move_link(ctx, mv))).html)
    pairs = [
        (t("k_egg_groups"), H.esc(", ".join(groups))),
        (t("k_egg_cycles"), H.esc(t("egg_cycles", n=sp.egg_cycles, steps=ctx.num(site.cycle_steps)))
         if can_breed or site.avail[sp.id].parents else None),
        (t("k_gender"), H.esc(species.gender_text(sp.gender_ratio, lang))),
    ]
    return H.kv(pairs) + H.prose("".join("<p>%s</p>" % x for x in egg_lines))


def _dex_section(ctx, site, sp, num):
    t, lang = ctx.t, ctx.lang
    regions = _dex_regions(site, sp)
    johto = site.regional["johto"].get(sp.natdex)
    return H.kv([
        (dex_texts.dex_title("national", lang), H.esc(t("dex_no", n="%03d" % num))),
        (t("k_dex_johto"), H.esc(t("dex_no", n="%03d" % johto)) if johto else None),
        (t("k_dex_regional"), H.chips([H.region_chip(ctx, r) for r in regions]) if regions else None),
        (t("k_dex_official"), H.esc(t("dex_no", n="%03d" % sp.natdex)) if sp.natdex else None),
    ])


def _forms_section(ctx, site, base):
    t, lang = ctx.t, ctx.lang
    battle, look = site.forms[base.id]
    unown = base.const == "SPECIES_UNOWN"
    n = len(battle) + len(look)
    if unown:
        intro = t("forms_intro_unown", name=base.name, n=n + 1)
    else:
        intro = t("forms_intro_one", name=base.name) if n == 1 else t("forms_intro", name=base.name, n=n)
    out = []
    idx = 1
    panels = []
    for f in battle:
        idx += 1
        cap = t("form_n", n=idx)
        left = H.sprite_pair(ctx, f) + "<p>%s</p>" % H.types(ctx, f.types)
        body = H.split(H.stat_bars(ctx, f.stats), left)
        if f.abilities != base.abilities:
            body += H.ability_list(ctx, _abil_entries(f, lang))
        if f.types != base.types:
            body += H.type_matchups(ctx, f.types)
        if f.levelup != base.levelup:
            rows = [(H.esc(l), m) for l, m in _level_rows(ctx, f.levelup, lang)]
            body += H.details(t("form_moves"), H.move_table(ctx, rows, first=ctx.ui("level")))
        else:
            body += H.p(t("form_same_moves", name=base.name), "muted")
        if base.evolutions and not f.evolutions:
            body += H.p(t("form_no_evo"), "muted")
        panels.append((cap, body, str(idx)))
    if len(panels) == 1:
        out.append(H.sub(panels[0][0], panels[0][1]))
    elif panels:
        out.append(H.tabs(panels, "form"))
    if look:
        plates = []
        if unown:
            plates.append(H.sprite_plate(ctx, base, scale=1, caption=D.form_caption(base, base, 0)))
        for f in look:
            idx += 1
            cap = D.form_caption(base, f, idx) or t("form_n", n=idx)
            plates.append(H.sprite_plate(ctx, f, scale=1, caption=cap))
        body = '<div class="plates">%s</div>' % "".join(plates)
        if not unown:
            text = t("forms_look_intro", name=base.name)
            if base.evolutions and not any(f.evolutions for f in look):
                text += " " + t("forms_no_evo")
            body = H.p(text, "muted") + body
            out.append(H.sub(t("forms_look"), body))
        else:
            out.append(body)
    if not unown:
        ctx.todo("Form names of %s: the game has no text for forms; the page numbers them" % base.const)
    return "".join(out), H.esc(intro)


# ---------------------------------------------------------------------- species page
def _render_species(ctx, site, i):
    t, lang = ctx.t, ctx.lang
    num, sp = site.entries[i]
    ctx.begin("species", sp.const)
    kinds, regions, first = _entry_avail(site, sp)
    out = []
    out.append(H.section(t("sec_stats"), H.split(H.stat_bars(ctx, sp.stats), _profile(ctx, site, sp)), id="stats"))
    out.append(H.section(t("sec_abilities"), _abilities_section(ctx, site, sp), id="abilities"))
    out.append(H.section(t("sec_evo"), _evolution_section(ctx, site, sp), id="evolution"))
    battle, look = site.forms[sp.id]
    if battle or look:
        body, intro = _forms_section(ctx, site, sp)
        out.append(H.section(t("sec_forms"), body, id="forms", intro=intro))
    mbody, mintro = _moves_section(ctx, site, sp)
    out.append(H.section(t("sec_moves"), mbody, id="learnset", intro=mintro, cls="start-closed"))
    out.append(H.section(t("sec_where"), _where_section(ctx, site, sp, first, kinds), id="where"))

    chips = H.types(ctx, sp.types)
    if "none" in kinds:
        chips += " " + H.chip(t("chip_none"), "warn")
    elif first:
        chips += " " + H.chip(t("chip_from", region=ctx.ui("region_" + first)), first)
    ctx.end("".join(out), title=sp.name, eyebrow=t("eyebrow", n="%03d" % num, category=sp.category),
            chips=chips, lead=H.esc(sp.description), aside=H.sprite_pair(ctx, sp, lazy=False),
            prev=("species", site.entries[i - 1][1].const) if i else None,
            next=("species", site.entries[i + 1][1].const) if i + 1 < len(site.entries) else None,
            description=sp.description)


def render(ctx):
    site = Site(ctx)
    _render_index(ctx, site)
    for i in range(len(site.entries)):
        _render_species(ctx, site, i)
