"""Pokéblocks (guides/pokeblocks): the blender's colour rules and what a Pokéblock does in
a Safari Zone feeder.

Sources (gamedata.hand_pokeblocks): gPokeblockNames and gPokeblockFlavorCompatibilityTable
(src/pokeblock.c), gNaturesInfo, the colour function of src/berry_blender.c, the feeder
(src/safari_zone.c; TryApplyPokeblockBonus and PickWildMonNature in src/wild_encounter.c).
Block icons are rendered from graphics/pokeblock/. The berries' flavors are on data/berries.
What one blend gives depends on the partners' berries and the speed; that arithmetic is
not mirrored, the page states the colour rules.
"""
import glob
import re

from common import html as H
from gamedata import hand_facts as F
from gamedata import hand_pokeblocks as PB
from gamedata import maps, repo_path
from pages import _game_util as U

PATH = "guides/pokeblocks"
STAT_ORDER = ("hp", "atk", "def", "spa", "spd", "spe")

S = {
    "de": {
        "pb_lead": "Im Beerenmixer werden Beeren zu Pokériegeln. Die Farbe eines Riegels hängt von seinen "
                   "Geschmäckern ab – und sie entscheidet, was der Riegel im Futterspender der Safari-Zone bewirkt.",
        "pb_sec_make": "Pokériegel herstellen",
        "pb_blenders": "Beerenmixer stehen hier: {places}. Welchen Geschmack jede Beere hat, steht in der Liste "
                       "der {berries}.",
        "pb_berries": "Beeren",
        "pb_sec_colors": "Welche Farbe ein Riegel bekommt",
        "pb_colors_intro": "Der Mixer prüft die Regeln in dieser Reihenfolge, die erste passende gilt.",
        "pb_col_flavors": "Geschmäcker des Riegels",
        "pb_col_block": "Riegel",
        "pb_rule_black": "kein Geschmack, mehr als drei negative Werte oder zweimal dieselbe Beere im Mixer",
        "pb_rule_four": "vier oder fünf Geschmäcker",
        "pb_rule_four_link": "vier oder fünf Geschmäcker (nur beim Mixen mit anderen Spielern)",
        "pb_rule_three": "drei Geschmäcker",
        "pb_rule_gold": "ein Geschmack stärker als {n}",
        "pb_rule_one": "nur {flavor}",
        "pb_rule_two": "{flavor} und ein zweiter Geschmack, {flavor} am stärksten",
        "pb_sec_feeder": "Der Futterspender der Safari-Zone",
        "pb_how_1": "Liegt ein Riegel im Futterspender, haben die wilden Pokémon dort ihre versteckte Fähigkeit, "
                    "wenn ihre Art eine hat.",
        "pb_how_2": "Die Farbe des Riegels legt {n} Werte fest, die perfekt sind (31). Ein goldener Riegel macht "
                    "{g} Werte perfekt.",
        "pb_how_3": "Mit {pct} % Chance hat das Pokémon ein Wesen, das den Geschmack des Riegels mag.",
        "pb_how_4": "Ein Riegel hält {steps} Schritte. Es gibt höchstens {n} gefüllte Futterspender gleichzeitig.",
        "pb_how_5": "Der Futterspender wirkt auf der ganzen Karte, auf der er steht.",
        "pb_how_6": "Nur die Farbe zählt – wie gut du beim Mixen warst, ändert nichts.",
        "pb_charts": "Die Tafeln am Eingang der Safari-Zone ({where}) zeigen dieselben Tabellen im Spiel.",
        "pb_sub_ivs": "Welche Werte jede Farbe perfekt macht",
        "pb_col_perfect": "Perfekte Werte",
        "pb_sub_gold": "Goldener Riegel: Welcher Wert nicht perfekt wird",
        "pb_col_strongest": "Stärkster Geschmack",
        "pb_col_not": "Nicht perfekt",
        "pb_sub_natures": "Welches Wesen welchen Geschmack mag",
        "pb_col_nature": "Wesen",
        "pb_col_likes": "Mag",
        "pb_col_dislikes": "Mag nicht",
    },
    "en": {
        "pb_lead": "The Berry Blender turns berries into Pokéblocks. A block's colour depends on its flavors – "
                   "and it decides what the block does in a Safari Zone feeder.",
        "pb_sec_make": "Making Pokéblocks",
        "pb_blenders": "Berry Blenders stand here: {places}. The flavor of every berry is in the list of "
                       "{berries}.",
        "pb_berries": "berries",
        "pb_sec_colors": "Which colour a block gets",
        "pb_colors_intro": "The blender checks the rules in this order; the first one that fits applies.",
        "pb_col_flavors": "Flavors of the block",
        "pb_col_block": "Block",
        "pb_rule_black": "no flavor, more than three negative values or the same berry twice in the blender",
        "pb_rule_four": "four or five flavors",
        "pb_rule_four_link": "four or five flavors (only when blending with other players)",
        "pb_rule_three": "three flavors",
        "pb_rule_gold": "one flavor stronger than {n}",
        "pb_rule_one": "only {flavor}",
        "pb_rule_two": "{flavor} and a second flavor, {flavor} strongest",
        "pb_sec_feeder": "The Safari Zone feeder",
        "pb_how_1": "While a block is in the feeder, the wild Pokémon there have their Hidden Ability if their "
                    "species has one.",
        "pb_how_2": "The block's colour fixes {n} IVs that are perfect (31). A gold block makes {g} IVs perfect.",
        "pb_how_3": "With a {pct}% chance the Pokémon has a nature that likes the block's flavor.",
        "pb_how_4": "A block lasts {steps} steps. At most {n} feeders can be filled at the same time.",
        "pb_how_5": "The feeder works on the whole map it stands on.",
        "pb_how_6": "Only the colour counts – how well you blended changes nothing.",
        "pb_charts": "The boards at the Safari Zone entrance ({where}) show the same tables in the game.",
        "pb_sub_ivs": "Which IVs each colour makes perfect",
        "pb_col_perfect": "Perfect IVs",
        "pb_sub_gold": "Gold block: which IV is not perfect",
        "pb_col_strongest": "Strongest flavor",
        "pb_col_not": "Not perfect",
        "pb_sub_natures": "Which nature likes which flavor",
        "pb_col_nature": "Nature",
        "pb_col_likes": "Likes",
        "pb_col_dislikes": "Dislikes",
    },
}


def _blender_places(ctx):
    out = []
    for p in sorted(glob.glob(repo_path("data", "maps", "*", "map.json"))):
        if re.search(r'"script": "\w*BerryBlender\w*"', open(p, encoding="utf-8").read()):
            m = maps.by_dir(p.split("/")[-2], ctx.lang)
            if m and m.active and not maps.locked_mapsec(m.mapsec):
                x = U.place(ctx, m)
                if x not in out:
                    out.append(x)
    return out


def render(ctx):
    t = ctx.t
    lang = ctx.lang
    ctx.begin(PATH)
    stats = H.stat_names(ctx)
    fl = dict(PB.flavors(lang))
    colors = {c.const: c for c in PB.colors(lang)}

    def block(const):
        c = colors[const]
        ctx.write_image("pokeblock/%s.png" % c.slug, PB.icon(c, scale=3))
        return '<span class="item-link">%s<span>%s</span></span>' % (
            H.img(ctx.asset("pokeblock", c.slug), 24, 24, "px item-ic", ""), H.esc(c.name))

    def stat_list(keys):
        return H.esc(", ".join(stats[k] for k in STAT_ORDER if k in keys))

    out = []
    places = _blender_places(ctx)
    out.append(H.section(t("pb_sec_make"), H.prose(U.p(
        ctx, "pb_blenders", places=U.join(ctx, places),
        berries=U.page(ctx, "data/berries", t("pb_berries")))), id="make"))

    rules = PB.color_rules()
    fd = PB.feeder()
    rows = [[H.esc(t("pb_rule_black")), block("PBLOCK_CLR_BLACK")],
            [H.esc(t("pb_rule_four_link" if fd.white_link_only else "pb_rule_four")), block("PBLOCK_CLR_WHITE")],
            [H.esc(t("pb_rule_three")), block("PBLOCK_CLR_GRAY")],
            [H.esc(t("pb_rule_gold", n=rules["gold_above"])), block("PBLOCK_CLR_GOLD")]]
    for f, c in rules["single"].items():
        rows.append([H.esc(t("pb_rule_one", flavor=fl[f])), block(c)])
    for f, c in rules["double"].items():
        rows.append([H.esc(t("pb_rule_two", flavor=fl[f])), block(c)])
    out.append(H.section(t("pb_sec_colors"), H.table([(t("pb_col_flavors"), "main"), t("pb_col_block")], rows),
                         id="colors", intro=H.esc(t("pb_colors_intro"))))

    gate = "SafariZoneGate_SafariZoneEntrance_hns"
    F.require("data/maps/%s/scripts.inc" % gate, r"helpwindow HELP_POKEBLOCK_WINDOW")
    F.require("data/maps/%s/scripts.inc" % gate, r"helpwindow HELP_GOLD_POKEBLOCK_WINDOW")
    F.require("src/wild_encounter.c", r"// Only the color is read\.")
    how = [U.fmt(ctx, "pb_how_1"), U.fmt(ctx, "pb_how_2", n=fd.perfect, g=fd.gold_perfect),
           U.fmt(ctx, "pb_how_3", pct=fd.nature_percent),
           U.fmt(ctx, "pb_how_4", steps=ctx.num(fd.steps), n=fd.feeders)]
    if fd.whole_map:
        how.append(U.fmt(ctx, "pb_how_5"))
    how += [U.fmt(ctx, "pb_how_6"), U.fmt(ctx, "pb_charts", where=U.place(ctx, gate))]
    body = H.ul(how)
    body += H.sub(t("pb_sub_ivs"), H.table([(t("pb_col_block"), "main"), t("pb_col_perfect")],
                                           [[block(c), stat_list(ivs)] for c, ivs in fd.iv_sets]), id="ivs")
    body += H.sub(t("pb_sub_gold"), H.table(
        [(t("pb_col_strongest"), "main"), t("pb_col_perfect"), t("pb_col_not")],
        [[H.esc(fl[f]), stat_list(ivs), stat_list(set(STAT_ORDER) - set(ivs))] for f, ivs in fd.gold_sets]),
        id="gold")
    body += H.sub(t("pb_sub_natures"), H.table(
        [(t("pb_col_nature"), "main"), t("pb_col_likes"), t("pb_col_dislikes")],
        [[H.esc(n), H.esc(fl[l]) if l else None, H.esc(fl[d]) if d else None] for n, l, d in PB.natures(lang)]),
        id="natures")
    out.append(H.section(t("pb_sec_feeder"), body, id="feeder"))
    ctx.end("".join(out), lead=H.esc(t("pb_lead")))
