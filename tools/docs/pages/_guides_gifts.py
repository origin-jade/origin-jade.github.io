"""Gifts & in-game trades (guides/gifts): every Pokémon the game hands to the player.

Species, levels, coin prices, trade partners, nicknames and held items come from the
scripts through gamedata.wild_statics (the entries the Pokédex pages use). Every such
entry must be listed in GIFTS below, otherwise the build stops - so a gift added to the
game cannot be missed. The conditions are written by hand from the map scripts named by
the map folders; four gifts with a fixed name or nature are created by ScrCmd_givenamedmon
(src/scrcmd.c) and listed in NAMED.
"""
import re

from common import html as H
from gamedata import hand_facts as F
from gamedata import items as IT, maps, natures, repo_path, species as SP
from pages import _game_util as U
from pages import _pokedex_data as PD

PATH = "guides/gifts"

S = {
    "de": {
        "gf_lead": "Alle Pokémon, die du geschenkt bekommst, kaufen kannst oder im Spiel ertauschst – mit dem, "
                   "was du dafür tun musst.",
        "gf_sec_starter": "Starter",
        "gf_sec_kanto": "Geschenke in Kanto",
        "gf_sec_johto": "Geschenke in Johto",
        "gf_sec_hoenn": "Geschenke in Hoenn",
        "gf_sec_prizes": "Preise der Spielhallen",
        "gf_prizes_intro": "Diese Pokémon bekommst du gegen Münzen. Du kannst sie beliebig oft holen.",
        "gf_sec_trades": "Tausch im Spiel",
        "gf_trades_intro": "Jeder Tausch geht nur einmal. Das Pokémon, das du bekommst, hat das Level des "
                           "Pokémon, das du abgibst.",
        "gf_col_mon": "Pokémon",
        "gf_col_place": "Ort",
        "gf_col_level": "Level",
        "gf_col_how": "So bekommst du es",
        "gf_col_price": "Preis",
        "gf_col_give": "Du gibst",
        "gf_col_get": "Du bekommst",
        "gf_col_names": "Spitzname / Original-Trainer",
        "gf_col_item": "Trägt",
        "gf_egg": "Ei",
        "gf_any": "ein beliebiges Pokémon",
        "gf_n_coins": "{n} Münzen",
        "gf_full": "Ist dein Team voll, kommt ein Geschenk in die PC-Box. Eier und die Pokémon mit festem Namen "
                   "brauchen einen freien Platz im Team.",
        "gf_starter_oak": "Zu Beginn des Spiels im Labor von Professor Eich: eines von drei. Es schillert genau "
                          "dann, wenn es in der Vorschau des Pokéballs geschillert hat.",
        "gf_starter_elm": "Im Labor von Professor Lind, nachdem du ihm den {gsball} von Professor Eich gebracht "
                          "hast: eines von drei.",
        "gf_starter_birch": "Im Labor von Professor Birk: eines von drei. Erst nach dem Hoenn-Titel und wenn du "
                            "alle Pokémon des Hoenn-Pokédex gefangen hast ({completion}).",
        "gf_completion": "Pokédex vervollständigen",
        "gf_magikarp": "Der Verkäufer im Pokémon-Center verkauft es dir für {price}.",
        "gf_eevee": "Der Pokéball im Dachzimmer des Wohnhauses.",
        "gf_dojo": "Besiege den Meister des Kampf-Dojos und nimm dir die beiden Pokébälle: Du bekommst beide.",
        "gf_lapras": "Sprich mit dem Angestellten im 7. Stock der Silph Co.",
        "gf_togepi": "Der Assistent von Professor Lind wartet im Pokémon-Center, nachdem dich der Professor in "
                     "{violet} angerufen hat. Danach bekommst du von ihm noch: {expshare}.",
        "gf_kenya": "Der Wächter im Durchgang zwischen {goldenrod} und {route35} vertraut es dir mit einem Brief "
                    "an: Spitzname {nick}, Original-Trainer {ot}, trägt {item}.",
        "gf_bill": "Sprich mit Bill in seinem Haus und sag Ja. Original-Trainer ist Bill.",
        "gf_tentacool": "Der Angler im Pokémon-Center gibt es dir, wenn kein Pokémon in deinem Team {surf} "
                        "einsetzen kann.",
        "gf_shuckie": "Ein Mann in {cianwood} vertraut es dir an: Spitzname {nick}, Original-Trainer {ot}, "
                      "trägt {item}.",
        "gf_tyrogue": "Besiege {kiyo} im {mortar} (Untergeschoss).",
        "gf_dratini": "Der Älteste im Schrein der {dragonsden} gibt es dir nach seiner Prüfung. Beantwortest du "
                      "alle Fragen ohne Fehler, ist es schillernd und hat das Wesen {adamant}.",
        "gf_oddegg": "Das Seltsame Ei aus der Pension auf {route34}: eines von elf Baby-Pokémon, je nach deiner "
                     "Antwort. Alles dazu steht unter {breeding}.",
        "gf_breeding": "Zucht",
        "gf_castform": "Besiege {shelly} im Wetterinstitut. Danach schenkt dir ein Forscher im Obergeschoss das "
                       "Pokémon; es trägt {item}.",
        "gf_wynaut": "Die alte Frau bei den heißen Quellen gibt dir das Ei.",
        "gf_beldum": "Der Pokéball in Troys Haus. Er liegt dort, sobald du Champ von Hoenn bist.",
        "gf_trade_jasmine": "Jasmin in ihrer Arena, nachdem du sie besiegt hast – spätestens nach dem "
                            "Johto-Titel bietet sie den Tausch an.",
        "gf_trade_frontier": "Die Kampfzone erreichst du mit dem Schiff, sobald du Champ von Hoenn bist.",
    },
    "en": {
        "gf_lead": "Every Pokémon you are given, can buy or get in an in-game trade – with what you have to do "
                   "for it.",
        "gf_sec_starter": "Starters",
        "gf_sec_kanto": "Gifts in Kanto",
        "gf_sec_johto": "Gifts in Johto",
        "gf_sec_hoenn": "Gifts in Hoenn",
        "gf_sec_prizes": "Game Corner prizes",
        "gf_prizes_intro": "You get these Pokémon for Coins, as often as you like.",
        "gf_sec_trades": "In-game trades",
        "gf_trades_intro": "Every trade works only once. The Pokémon you receive has the level of the Pokémon "
                           "you give away.",
        "gf_col_mon": "Pokémon",
        "gf_col_place": "Place",
        "gf_col_level": "Level",
        "gf_col_how": "How to get it",
        "gf_col_price": "Price",
        "gf_col_give": "You give",
        "gf_col_get": "You receive",
        "gf_col_names": "Nickname / original Trainer",
        "gf_col_item": "Holds",
        "gf_egg": "Egg",
        "gf_any": "any Pokémon",
        "gf_n_coins": "{n} Coins",
        "gf_full": "If your party is full, a gift goes to a PC Box. Eggs and the Pokémon with a fixed name need "
                   "a free slot in your party.",
        "gf_starter_oak": "At the start of the game in Professor Oak's lab: one of three. It is shiny exactly "
                          "when it was shiny in the Poké Ball's preview.",
        "gf_starter_elm": "In Professor Elm's lab, after you bring him the {gsball} from Professor Oak: one of "
                          "three.",
        "gf_starter_birch": "In Professor Birch's lab: one of three. Only after the Hoenn title and once you "
                            "have caught every Pokémon of the Hoenn Pokédex ({completion}).",
        "gf_completion": "Completing the Pokédex",
        "gf_magikarp": "The salesman in the Pokémon Center sells it to you for {price}.",
        "gf_eevee": "The Poké Ball in the roof room of the apartment building.",
        "gf_dojo": "Defeat the master of the Fighting Dojo and take the two Poké Balls: you get both.",
        "gf_lapras": "Talk to the employee on the 7th floor of Silph Co.",
        "gf_togepi": "Professor Elm's aide waits in the Pokémon Center after the professor has called you in "
                     "{violet}. Afterwards he also gives you an {expshare}.",
        "gf_kenya": "The guard in the gate between {goldenrod} and {route35} entrusts it to you with a letter: "
                    "nickname {nick}, original Trainer {ot}, holds {item}.",
        "gf_bill": "Talk to Bill in his house and say yes. The original Trainer is Bill.",
        "gf_tentacool": "The fisherman in the Pokémon Center gives it to you if no Pokémon in your party can "
                        "use {surf}.",
        "gf_shuckie": "A man in {cianwood} entrusts it to you: nickname {nick}, original Trainer {ot}, holds "
                      "{item}.",
        "gf_tyrogue": "Defeat {kiyo} in the basement of {mortar}.",
        "gf_dratini": "The elder in the shrine of the {dragonsden} gives it to you after his test. If you answer "
                      "every question without a mistake, it is shiny and has the nature {adamant}.",
        "gf_oddegg": "The Odd Egg from the Day Care on {route34}: one of eleven baby Pokémon, depending on your "
                     "answer. Everything about it is under {breeding}.",
        "gf_breeding": "Breeding",
        "gf_castform": "Defeat {shelly} in the Weather Institute. Afterwards a scientist upstairs gives you the "
                       "Pokémon; it holds a {item}.",
        "gf_wynaut": "The old woman by the hot springs gives you the egg.",
        "gf_beldum": "The Poké Ball in Steven's house. It lies there once you are Champion of Hoenn.",
        "gf_trade_jasmine": "Jasmine in her Gym, after you have defeated her – at the latest after the Johto "
                            "title she offers the trade.",
        "gf_trade_frontier": "You reach the Battle Frontier by ship once you are Champion of Hoenn.",
    },
}

# (section, map folder, [species], text key). Every reachable gift and egg entry must be here.
GIFTS = (
    ("starter", "PalletTown_ProfessorOaksLab_Frlg",
     ("SPECIES_BULBASAUR", "SPECIES_CHARMANDER", "SPECIES_SQUIRTLE"), "gf_starter_oak"),
    ("starter", "NewBarkTown_Lab_hns", ("SPECIES_CHIKORITA", "SPECIES_CYNDAQUIL", "SPECIES_TOTODILE"),
     "gf_starter_elm"),
    ("starter", "LittlerootTown_ProfessorBirchsLab",
     ("SPECIES_TREECKO", "SPECIES_TORCHIC", "SPECIES_MUDKIP"), "gf_starter_birch"),
    ("kanto", "Route4_PokemonCenter_1F_Frlg", ("SPECIES_MAGIKARP",), "gf_magikarp"),
    ("kanto", "CeladonCity_Condominiums_RoofRoom_Frlg", ("SPECIES_EEVEE",), "gf_eevee"),
    ("kanto", "SaffronCity_Dojo_Frlg", ("SPECIES_HITMONLEE", "SPECIES_HITMONCHAN"), "gf_dojo"),
    ("kanto", "SilphCo_7F_Frlg", ("SPECIES_LAPRAS",), "gf_lapras"),
    ("johto", "VioletCity_PokemonCenter_hns", ("SPECIES_TOGEPI",), "gf_togepi"),
    ("johto", "CianwoodPokecenter_hns", ("SPECIES_TENTACOOL",), "gf_tentacool"),
    ("johto", "MtMortar_B1F_hns", ("SPECIES_TYROGUE",), "gf_tyrogue"),
    ("johto", "DragonsDen_Shrine_hns", ("SPECIES_DRATINI",), "gf_dratini"),
    ("hoenn", "Route119_WeatherInstitute_2F", ("SPECIES_CASTFORM",), "gf_castform"),
    ("hoenn", "LavaridgeTown", ("SPECIES_WYNAUT",), "gf_wynaut"),
    ("hoenn", "MossdeepCity_StevensHouse", ("SPECIES_BELDUM",), "gf_beldum"),
)
# Gifts of ScrCmd_givenamedmon and the Odd Egg: (section, after map folder, map folder, species, level, key)
NAMED = (
    ("johto", "VioletCity_PokemonCenter_hns", "Gate_GoldenrodCity_Route35_hns", "SPECIES_SPEAROW", 20, "gf_kenya"),
    ("johto", "VioletCity_PokemonCenter_hns", "GoldenrodCity_BillsHouse_hns", "SPECIES_EEVEE", 20, "gf_bill"),
    ("johto", "CianwoodPokecenter_hns", "CianwoodHouse3_hns", "SPECIES_SHUCKLE", 20, "gf_shuckie"),
)
# Fossils revived in a lab are not gifts; the key items guide lists them.
FOSSIL_LABS = ("CinnabarIsland_PokemonLab_ExperimentRoom_Frlg", "RuinsOfAlph_Lab_hns", "RustboroCity_DevonCorp_2F")
# The Odd Egg (ScrCmd_giveoddegg) follows this gift in the order of the journey.
ODD_EGG_AFTER = "VioletCity_PokemonCenter_hns"
TRADE_NOTES = {"INGAME_TRADE_STEELIX": "gf_trade_jasmine", "INGAME_TRADE_MEOWTH": "gf_trade_frontier"}
REGION_ORDER = {"kanto": 0, "johto": 1, "hoenn": 2}


def _entries(lang):
    out = []
    for lst in PD.specials(lang).values():
        out.extend(lst)
    return out


def _named_facts():
    """Species, level, held item, nickname and OT of the named gifts as src/scrcmd.c creates them."""
    src = open(repo_path("src", "scrcmd.c"), encoding="utf-8").read()
    names = dict(re.findall(r'static const u8 (s\w+)\[\]\s*=\s*_\("([^"]*)"\);', src))
    out = {}
    for m in re.finditer(r"case \d+: // \w+.*?\n\s*species\s*=\s*(SPECIES_\w+);\s*level\s*=\s*(\d+);\s*"
                         r"item\s*=\s*(ITEM_\w+);\s*nickname\s*=\s*(\w+);\s*otName\s*=\s*([\w>\-]+);", src):
        sp, lv, item, nick, ot = m.groups()
        out[sp] = (int(lv), item, names.get(nick), names.get(ot))
    return out


def _vals(ctx):
    lang = ctx.lang
    v = {}
    for k, c in (("gsball", "ITEM_GS_BALL"), ("expshare", "ITEM_EXP_SHARE_SMALL")):
        v[k] = U.item(ctx, c)
    for k, d in (("violet", "VioletCity_hns"), ("goldenrod", "GoldenrodCity_hns"), ("route35", "Route35_hns"),
                 ("cianwood", "CianwoodCity_hns"), ("mortar", "MtMortar_B1F_hns"),
                 ("dragonsden", "DragonsDen_Shrine_hns"), ("ruins", "RuinsOfAlph_Lab_hns"),
                 ("route34", "Route34_DayCare_hns")):
        v[k] = U.place(ctx, d)
    v["surf"] = U.move(ctx, "MOVE_SURF")
    v["kiyo"] = U.trainer(ctx, "TRAINER_KIYO_HNS")
    v["shelly"] = U.trainer(ctx, "TRAINER_SHELLY_WEATHER_INSTITUTE")
    v["adamant"] = U.e(natures.by_party_name("Adamant", lang).name)
    v["completion"] = U.page(ctx, "guides/completion", ctx.t("gf_completion"))
    v["breeding"] = U.anchor_link(ctx, "guides/breeding", "odd-egg", ctx.t("gf_breeding"))
    price = int(F.require("data/maps/Route4_PokemonCenter_1F_Frlg/scripts.inc",
                          r"\.equ\s+MAGIKARP_PRICE,\s*(\d+)").group(1))
    v["price"] = U.e(ctx.money(price))
    return v


def _level(ctx, levels):
    if not levels:
        return H.esc(ctx.t("gf_egg"))
    return H.esc(" / ".join(ctx.level(x) for x in sorted(levels)))


def render(ctx):
    t = ctx.t
    lang = ctx.lang
    ctx.begin(PATH)
    vals = _vals(ctx)
    ents = _entries(lang)
    by = {}
    for e in ents:
        if e.kind in ("gift", "egg") and not e.price:
            folder = maps.by_id(e.map_id, "de").dir
            if folder in FOSSIL_LABS:
                continue
            by[(folder, SP.by_id(e.species, "de").const)] = e

    # ---- gifts
    rows = {"starter": [], "kanto": [], "johto": [], "hoenn": []}
    used = set()
    named = _named_facts()
    for sec, folder, consts, key in GIFTS:
        levels = set()
        item = None
        for c in consts:
            c = SP.by_const(c, "de").const
            e = by.get((folder, c))
            if e is None:
                raise ValueError("gifts guide: no gift %s at %s any more" % (c, folder))
            used.add((folder, c))
            levels.update(e.levels)
            if e.items:
                item = IT.by_id(e.items[0], lang)
        v = dict(vals)
        if item:
            v["item"] = U.item(ctx, item)
        mons = ", ".join(U.species(ctx, c, icon=True) for c in consts)
        rows[sec].append([mons, U.place(ctx, folder), _level(ctx, levels), U.fmt(ctx, key, **v)])
        if folder == ODD_EGG_AFTER:
            rows[sec].append([H.esc(ctx.t("gf_egg")), U.place(ctx, "Route34_DayCare_hns"), _level(ctx, []),
                              U.fmt(ctx, "gf_oddegg", **vals)])
        for nsec, after, nfolder, nconst, nlevel, nkey in NAMED:
            if after != folder:
                continue
            lv, it, nick, ot = named[nconst]
            if lv != nlevel:
                raise ValueError("gifts guide: named gift %s has level %d" % (nconst, lv))
            nv = dict(vals)
            nv.update(nick=U.e(nick.title() if nick else ""), ot=U.e(ot.title() if ot else ""))
            if it != "ITEM_NONE":
                nv["item"] = U.item(ctx, it)
            rows[nsec].append([U.species(ctx, nconst, icon=True), U.place(ctx, nfolder),
                               _level(ctx, [lv]), U.fmt(ctx, nkey, **nv)])
    missing = sorted(set(by) - used)
    if missing:
        raise ValueError("gifts guide: gifts without a row: %s" % missing)
    cols = [(t("gf_col_mon"), "main"), t("gf_col_place"), (t("gf_col_level"), "min"), t("gf_col_how")]
    out = []
    for sec in ("starter", "kanto", "johto", "hoenn"):
        body = H.table(cols, rows[sec])
        if sec == "starter":
            body += H.callout(ctx, "note", U.p(ctx, "gf_full"))
        out.append(H.section(t("gf_sec_" + sec), body, id=sec))

    # ---- game corner prizes
    prizes = sorted((e for e in ents if e.kind == "gift" and e.price),
                    key=lambda e: (REGION_ORDER.get(PD.region_of(maps.by_id(e.map_id, "de")), 9), e.map_id, e.price))
    prows = [[U.species(ctx, SP.by_id(e.species, lang), icon=True), U.place(ctx, e.map_id), _level(ctx, e.levels),
              H.esc(t("gf_n_coins", n=ctx.num(e.price)))] for e in prizes]
    out.append(H.section(t("gf_sec_prizes"), H.table(
        [(t("gf_col_mon"), "main"), t("gf_col_place"), (t("gf_col_level"), "min"), (t("gf_col_price"), "num")],
        prows), id="prizes", intro=H.esc(t("gf_prizes_intro"))))

    # ---- trades
    trades = sorted((e for e in ents if e.kind == "trade"),
                    key=lambda e: (REGION_ORDER.get(PD.region_of(maps.by_id(e.map_id, "de")), 9), e.map_id))
    trows = {}
    for e in trades:
        tr = e.trade
        want = SP.by_id(tr["requested"], lang) if tr["requested"] else None
        held = IT.by_id(tr["held_item"], lang) if tr["held_item"] else None
        place = U.place(ctx, e.map_id)
        note = TRADE_NOTES.get(tr["const"])
        if note:
            place += '<br><span class="muted">%s</span>' % U.fmt(ctx, note, **vals)
        region = PD.region_of(maps.by_id(e.map_id, "de")) or "hoenn"     # Battle Frontier: reached from Hoenn
        trows.setdefault(region, []).append([U.species(ctx, want, icon=True) if want else H.esc(t("gf_any")),
                      U.species(ctx, SP.by_id(e.species, lang), icon=True), place,
                      H.esc("%s / %s" % (tr["nickname"], tr["ot_name"])),
                      U.item(ctx, held, icon=True) if held else None])
    tcols = [(t("gf_col_give"), "main"), t("gf_col_get"), t("gf_col_place"), t("gf_col_names"), t("gf_col_item")]
    tbody = "".join(H.sub(ctx.ui("region_" + r), H.table(tcols, trows[r]), id="trades-" + r.lower())
                    for r in sorted(trows, key=lambda r: REGION_ORDER.get(r, 9)))
    out.append(H.section(t("gf_sec_trades"), tbody, id="trades", intro=H.esc(t("gf_trades_intro"))))
    ctx.end("".join(out), lead=H.esc(t("gf_lead")))
