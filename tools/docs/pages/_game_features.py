"""What's new (game/features): what Origin Jade does differently from the games it
is made of.

Every number and name comes from the loaders; every statement about a script or a
rule is pinned to the source with hand_facts.require(), so a change there stops the
build instead of leaving the page stale. Sources: the scripts named next to each
pin, gamedata.levels, gamedata.hand_progress (region changes), gamedata.hand_completion
(Pokédex rewards), the option menus (gamedata.hand_menus) and the README (feature list).
"""
import glob
import re

import site_config
from common import html as H
from gamedata import hand_completion as HC
from gamedata import hand_facts as F
from gamedata import hand_progress as P
from gamedata import repo_path
from pages import _game_util as U
from pages import _game_shared as X

PATH = "game/features"

S = {
    "de": {
        "ft_keywords": "neuerungen funktionen features unterschiede beta regionen",
        "ft_lead": "Pokémon Origin Jade ist eine Reise durch drei Regionen in einem Spielstand: erst Kanto, dann "
                   "Johto, dann Hoenn. Diese Seite zeigt, was dabei anders läuft als in den Originalen.",
        "ft_sec_journey": "Drei Regionen, eine Reise",
        "ft_journey_intro": "Jede Region hat eigene Orden, eine eigene Liga und einen eigenen Titel. Der Abspann läuft "
                            "erst nach dem ersten Titel in Hoenn.",
        "ft_step_kanto": "{b}: Du startest in {pallet}. Kanto folgt den Karten aus Feuerrot und Blattgrün und führt "
                         "bis zur Pokémon-Liga.",
        "ft_step_johto": "{b}: Nach dem Titel in Kanto gibt dir Prof. Eich in seinem Labor in {oak_lab} den "
                         "{gs_ball}. Damit lässt dich die Wache am Ende von {route22} durch, und über {route26} "
                         "geht es nach {elm_town}.",
        "ft_step_hoenn": "{b}: Nach dem Titel in Johto wartet {troy} in Prof. Eichs Labor und gibt dir das {ticket}. "
                         "Das Schiff fährt in {vermilion} und {olivine} ab.",
        "ft_journey_more": "Die Wege im Einzelnen stehen unter {start}.",
        "ft_sec_play": "Was sich anders spielt",
        "ft_levels_t": "Feste Level",
        "ft_levels": "Wilde Pokémon und Trainer haben feste Level, die von Kanto über Johto bis Hoenn steigen. "
                     "Nichts richtet sich nach deinem Team. Mehr unter {levels}.",
        "ft_exp_t": "Erfahrung nach Region",
        "ft_exp": "Je nach Region gibt ein Kampf unterschiedlich viel Erfahrung: in Kanto {k_low} bis {k_until} und "
                  "darüber {k}, in Johto {j}, in Hoenn {h}. So wächst das Team mit der Reise mit.",
        "ft_share_t": "EP-Teiler von Anfang an",
        "ft_share": "Der {share} liegt beim Start eingeschaltet im Beutel und lässt sich jederzeit aus- und wieder "
                    "einschalten. Er teilt die Erfahrung auf, statt sie zu vermehren.",
        "ft_hm_t": "Feldattacken ohne Beibringen",
        "ft_hm": "Für eine Feldattacke reicht die VM im Beutel und ein Pokémon im Team, das sie lernen könnte – "
                 "beibringen musst du sie nicht. Die Freigabe der Region brauchst du weiterhin: in Kanto den Orden, "
                 "in Johto und Hoenn die Erlaubnis, die du unterwegs bekommst (in Johto für {johto_n} Attacken, in "
                 "Hoenn für {hoenn_n}).",
        "ft_phone_t": "PokéCom und Rückkämpfe",
        "ft_phone": "Das PokéCom bekommst du gleich zu Beginn von Mama, zusammen mit den Turbotretern. Es hat Telefon, "
                    "Karte und Radio. Besiegte Trainer tragen sich ein – {kanto} in Kanto, {johto} in Johto, {hoenn} in "
                    "Hoenn – und rufen zum Rückkampf an, sobald du in ihrer Region {badges} Orden hast. Die Anrufe "
                    "lassen sich in den Optionen unter „{opt}“ abstellen.",
        "ft_leaders_t": "Revanche gegen die Arenaleiter",
        "ft_leaders": "Nach dem Titel in Kanto kannst du die acht Arenaleiter von Kanto in ihrer Arena erneut "
                      "herausfordern, so oft du willst. Ihr stärkstes Pokémon liegt {low} bis {high} Level über dem "
                      "Richtlevel für deinen Fortschritt; nach dem Titel in Johto bringen sie ein stärkeres Team mit.",
        "ft_time_t": "Tag und Nacht",
        "ft_time": "Das Spiel läuft mit Uhr: morgens ({m}), tagsüber ({d}), abends ({e}) und nachts ({n}) ändert sich "
                   "das Licht, und vielerorts tauchen andere wilde Pokémon auf.",
        "ft_follow_t": "Pokémon, die dir folgen",
        "ft_follow": "Das erste Pokémon im Team kann hinter dir herlaufen. Das stellst du in den Optionen unter "
                     "„{opt}“ ein.",
        "ft_ships_t": "Schiffe zwischen den Regionen",
        "ft_ships": "Mit dem {ticket} fährst du von {vermilion} und {olivine} nach Hoenn. Die erste Fahrt endet auf "
                    "{route104}; später stehen {slateport} und {lilycove} im Fahrplan, sobald du dort warst. Die "
                    "{frontier} kommt nach dem Titel in Hoenn dazu, die {birth} mit dem {aurora}.",
        "ft_legend_t": "Legendäre Pokémon kommen zurück",
        "ft_legend": "Ein besiegtes legendäres Pokémon ist nicht verloren: Es kehrt nach jedem Liga-Sieg zurück. Ist "
                     "es geflohen, ist es nach {days} Tageswechseln wieder da. Nur gefangen kommt es nicht wieder.",
        "ft_mom_t": "Mamas Sparkonto",
        "ft_mom": "Wie in Gold und Silber kann Mama für dich sparen. Ist das Sparen an, legt sie nach jedem gewonnenen "
                  "Trainerkampf zusätzlich ein Viertel des Preisgelds zurück – dir wird dabei nichts abgezogen.",
        "ft_items_t": "Praktische Items",
        "ft_items": "Von Bill bekommst du nach dem Titel in Kanto das Item {boxlink}, mit dem ersten Ei aus einer "
                    "Pension das Item {oval}, und für jeden vollständigen Regional-Pokédex hat Prof. Eich eine "
                    "Belohnung: {rewards}.",
        "ft_gb_t": "Klänge von früher",
        "ft_gb": "Der {gb} liegt von Anfang an im Beutel. Im Spiel heißt es dazu: {desc}",
        "ft_sec_modes": "Eigene Regeln",
        "ft_modes": "Vor dem Start legst du im Menü „Herausforderungen“ fest, wie du spielen willst – und kannst vieles "
                    "später am PC wieder lockern.",
        "ft_mode_rules": "{b}: Attackenpool, physisch/speziell je Attacke, Fee-Typ, wiederverwendbare TMs und mehr "
                         "lassen sich einzeln auf den Stand der dritten Generation stellen.",
        "ft_mode_nuzlocke": "{b}: in drei Stufen fest eingebaut, mit einstellbaren Zusatzregeln. Die Regeln gelten "
                            "vom Erhalt des Pokédex bis zum ersten Titel in Hoenn.",
        "ft_mode_random": "{b}: Starter, wilde Pokémon, Trainer, Typen, Attacken, Fähigkeiten, Entwicklungen, Items "
                          "und mehr lassen sich einzeln auswürfeln.",
        "ft_mode_hard": "{b}: Level-Limit, Teamlimit, Items im Kampf, IVs und Fleiß-Punkte der Gegner, teurere "
                        "Läden, nur ein Typ, Spiegel-Modus.",
        "ft_mode_b_rules": "Grundregeln", "ft_mode_b_nuzlocke": "Nuzlocke", "ft_mode_b_random": "Zufallsmodus",
        "ft_mode_b_hard": "Schwierigkeit und Sonderregeln",
        "ft_modes_more": "Alle Einträge mit ihren Texten stehen unter {settings}.",
        "ft_sec_diff": "Weitere Unterschiede",
        "ft_d_species": "Dabei sind die Pokémon der ersten drei Generationen samt ihren späteren Entwicklungen und "
                        "Vorstufen. Mega-Entwicklungen, Gigadynamax- und Regionalformen gibt es nicht.",
        "ft_d_region": "Pokémon einer Region tauchen erst auf, wenn die Geschichte diese Region erreicht hat.",
        "ft_d_trade": "Tauschen ist nicht nötig: Jedes Pokémon und jedes Item ist in einem einzigen Spielstand "
                      "erhältlich.",
        "ft_d_split": "Ob eine Attacke physisch oder speziell ist, hängt von der Attacke ab, und es gibt den Typ Fee. "
                      "Beides lässt sich in den Herausforderungen umstellen.",
        "ft_d_run": "Die Turbotreter gibt es gleich zu Beginn, und du kannst auch in Gebäuden rennen.",
        "ft_d_contest": "Wettbewerbe laufen wie in Rubin und Saphir: ein Rang pro Wettbewerbshalle.",
        "ft_d_frontier": "{frontier} und {hill} sind dabei.",
        "ft_d_seeker": "Einen {seeker} gibt es nicht; Rückkämpfe laufen über das PokéCom.",
        "ft_sec_beta": "Stand der Beta",
        "ft_beta_version": "Diese Seiten beschreiben {version}. Fehler sind in einer Beta möglich.",
        "ft_beta_saves": "Spielstände lassen sich zwischen Beta-Versionen nicht immer übernehmen. Passt ein Spielstand "
                         "nicht mehr, meldet das Spiel: {msg}",
        "ft_beta_link": "Tausch und Linkkämpfe sind nicht getestet. Verbindungen mit den offiziellen Spielen oder "
                        "anderen Hacks werden nicht unterstützt.",
    },
    "en": {
        "ft_keywords": "what's new features differences beta regions",
        "ft_lead": "Pokémon Origin Jade is a journey through three regions in one save file: Kanto first, then "
                   "Johto, then Hoenn. This page shows what works differently from the original games on the way.",
        "ft_sec_journey": "Three regions, one journey",
        "ft_journey_intro": "Every region has its own Badges, its own League and its own title. The credits only roll "
                            "after the first title in Hoenn.",
        "ft_step_kanto": "{b}: You start in {pallet}. Kanto follows the maps of FireRed and LeafGreen and leads up to "
                         "the Pokémon League.",
        "ft_step_johto": "{b}: After the title in Kanto, Prof. Oak gives you the {gs_ball} at his lab in {oak_lab}. "
                         "With it the guard at the end of {route22} lets you through, and {route26} takes you to "
                         "{elm_town}.",
        "ft_step_hoenn": "{b}: After the title in Johto, {troy} is waiting at Prof. Oak's lab and gives you the "
                         "{ticket}. The ship leaves from {vermilion} and {olivine}.",
        "ft_journey_more": "The routes in detail are under {start}.",
        "ft_sec_play": "What plays differently",
        "ft_levels_t": "Fixed levels",
        "ft_levels": "Wild Pokémon and Trainers have fixed levels that rise from Kanto through Johto to Hoenn. "
                     "Nothing depends on your team. More under {levels}.",
        "ft_exp_t": "Experience by region",
        "ft_exp": "A battle gives a different amount of experience in each region: in Kanto {k_low} up to {k_until} "
                  "and {k} above that, in Johto {j}, in Hoenn {h}. That way your team grows with the journey.",
        "ft_share_t": "Exp. Share from the start",
        "ft_share": "The {share} is in your Bag, switched on, when you start, and can be turned off and on at any "
                    "time. It shares experience out instead of multiplying it.",
        "ft_hm_t": "Field moves without teaching them",
        "ft_hm": "For a field move it is enough to have the HM in your Bag and a Pokémon in your party that could "
                 "learn it – you do not have to teach it. You still need the region's go-ahead: the Badge in Kanto, "
                 "and in Johto and Hoenn the permission you are given on the way (for {johto_n} moves in Johto, "
                 "{hoenn_n} in Hoenn).",
        "ft_phone_t": "Pokégear and rematches",
        "ft_phone": "Mom gives you the Pokégear right at the start, together with the Running Shoes. It has a phone, "
                    "a map and a radio. Trainers you beat register themselves – {kanto} in Kanto, {johto} in Johto, "
                    "{hoenn} in Hoenn – and call for a rematch once you have {badges} Badges in their region. The "
                    "calls can be turned off in the options under “{opt}”.",
        "ft_leaders_t": "Gym Leader rematches",
        "ft_leaders": "After the title in Kanto you can challenge the eight Kanto Gym Leaders again in their Gyms, "
                      "as often as you like. Their strongest Pokémon is {low} to {high} levels above the reference "
                      "level for your progress; after the title in Johto they bring a stronger team.",
        "ft_time_t": "Day and night",
        "ft_time": "The game runs on a clock: in the morning ({m}), during the day ({d}), in the evening ({e}) and "
                   "at night ({n}) the light changes, and in many places different wild Pokémon appear.",
        "ft_follow_t": "Pokémon that follow you",
        "ft_follow": "The first Pokémon in your party can walk behind you. You set that in the options under "
                     "“{opt}”.",
        "ft_ships_t": "Ships between the regions",
        "ft_ships": "With the {ticket} you sail from {vermilion} and {olivine} to Hoenn. The first crossing ends on "
                    "{route104}; later {slateport} and {lilycove} are on the timetable once you have been there. The "
                    "{frontier} is added after the title in Hoenn, {birth} with the {aurora}.",
        "ft_legend_t": "Legendary Pokémon come back",
        "ft_legend": "A legendary Pokémon you knocked out is not lost: it returns after every League victory. If it "
                     "fled, it is back after {days} changes of day. Only a caught one never returns.",
        "ft_mom_t": "Mom's savings",
        "ft_mom": "As in Gold and Silver, Mom can save money for you. While saving is on, she puts aside an extra "
                  "quarter of the prize money after every Trainer battle you win – nothing is taken from you.",
        "ft_items_t": "Handy items",
        "ft_items": "Bill gives you the {boxlink} after the title in Kanto, the {oval} comes with the first Egg from "
                    "a Day Care, and Prof. Oak has a reward for every complete regional Pokédex: {rewards}.",
        "ft_gb_t": "Sounds of the past",
        "ft_gb": "The {gb} is in your Bag from the start. The game says about it: {desc}",
        "ft_sec_modes": "Rules of your own",
        "ft_modes": "Before you start, the challenge menu lets you decide how you want to play – and much of it can "
                    "be relaxed again later on a PC.",
        "ft_mode_rules": "{b}: movepool, physical/special by move, the Fairy type, reusable TMs and more can each be "
                         "set back to how the third generation did it.",
        "ft_mode_nuzlocke": "{b}: built in at three levels, with extra rules you can set. The rules apply from the "
                            "moment you get the Pokédex until the first title in Hoenn.",
        "ft_mode_random": "{b}: starters, wild Pokémon, Trainers, types, moves, abilities, evolutions, items and "
                          "more can each be shuffled.",
        "ft_mode_hard": "{b}: level cap, party limit, items in battle, the opponents' IVs and effort values, pricier "
                        "shops, a single type, Mirror Mode.",
        "ft_mode_b_rules": "Basic rules", "ft_mode_b_nuzlocke": "Nuzlocke", "ft_mode_b_random": "Randomizer",
        "ft_mode_b_hard": "Difficulty and special rules",
        "ft_modes_more": "Every entry with its text is listed under {settings}.",
        "ft_sec_diff": "More differences",
        "ft_d_species": "The game has the Pokémon of the first three generations together with their later "
                        "evolutions and pre-evolutions. There are no Mega Evolutions, Gigantamax forms or regional "
                        "forms.",
        "ft_d_region": "Pokémon of a region only show up once the story has reached that region.",
        "ft_d_trade": "No trading needed: every Pokémon and every item can be obtained in a single save file.",
        "ft_d_split": "Whether a move is physical or special depends on the move, and the Fairy type exists. Both "
                      "can be changed in the challenge menu.",
        "ft_d_run": "You get the Running Shoes right at the start, and you can run indoors too.",
        "ft_d_contest": "Contests work as in Ruby and Sapphire: one rank per Contest Hall.",
        "ft_d_frontier": "The {frontier} and the {hill} are in the game.",
        "ft_d_seeker": "There is no {seeker}; rematches go through the Pokégear.",
        "ft_sec_beta": "State of the beta",
        "ft_beta_version": "These pages describe {version}. A beta can have bugs.",
        "ft_beta_saves": "Save files do not always carry over between beta versions. If a save no longer fits, the "
                         "game says: {msg}",
        "ft_beta_link": "Trades and link battles are untested. Linking with the official games or other hacks is "
                        "not supported.",
    },
}

# German names of two entries of the options menu (the entries are found by them)
OPTION_FOLLOW = "Folgen"
OPTION_CALLS = "Anrufe"


def _pins():
    """Statements of the page, pinned to the code."""
    home = "data/maps/PalletTown_PlayersHouse_1F_Frlg/scripts.inc"
    F.require(home, r"setflag FLAG_SYS_POKENAV_GET\n\tsetflag FLAG_HAS_MATCH_CALL")
    F.require(home, r"setflag FLAG_SYS_B_DASH")
    F.require(home, r"erhielt das PokéCom\.\$")
    F.require(home, r"obtained the POKéGEAR\.\$")
    F.require(home, r"Turbotreter")
    F.require("data/maps/ViridianCity_Frlg/scripts.inc", r"setflag FLAG_ENABLE_RADIO")
    F.require("data/scripts/new_game.inc", r"^\tadditem ITEM_EXP_SHARE$")
    F.require("data/scripts/new_game.inc", r"^\tadditem ITEM_GB_PLAYER$")
    F.require("data/scripts/new_game.inc", r"^\tsetflag FLAG_EXP_SHARE_ENABLED$")
    F.require("src/battle_script_commands.c", r"if \(Mom_IsSavingEnabled\(\)\)\s*\{\s*u32 depositAmount = money / 4;")
    F.require("src/scrcmd.c", r"CheckBagHasItem\(itemId, 1\)\)\s*\{\s*for \(u32 i = 0; i < GetMaxPartySize\(\); i\+\+\)")
    F.require("src/legendaries_oj.c", r"//  - caught: never again;")
    F.require("src/legendaries_oj.c", r"//  - knocked out: back after every league victory")
    F.require("data/maps/Route25_SeaCottage_Frlg/scripts.inc",
              r"call_if_set FLAG_IS_KANTO_CHAMPION, Route25_SeaCottage_EventScript_BillTryGiveBoxLink")
    F.require("data/scripts/day_care.inc", r"call_if_unset FLAG_RECEIVED_OVAL_CHARM, DayCare_EventScript_GiveOvalCharm")
    F.require("src/region_rule_oj.c", r"bool32 IsRegionUnlocked\(enum Region region\)")
    F.require("src/data/items.h", r"// Origin Jade: not obtainable, kept so that the item ids do not shift.\n\s*\[ITEM_VS_SEEKER\]")
    F.require("data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc", r"setflag FLAG_START_NUZLOCKE")
    for flag in ("OW_ENABLE_DNS", "OW_TIME_OF_DAY_ENCOUNTERS", "OW_FOLLOWERS_ENABLED", "P_CROSS_GENERATION_EVOS"):
        if not F.C(flag):
            raise F.TU.DataError("%s is off: review the features page" % flag)
    for flag in ("P_MEGA_EVOLUTIONS", "P_GIGANTAMAX_FORMS", "P_REGIONAL_FORMS"):
        if F.C(flag):
            raise F.TU.DataError("%s is on: review the features page" % flag)
    if F.C("OW_RUNNING_INDOORS") < F.C("GEN_4"):
        raise F.TU.DataError("running indoors changed: review the features page")
    for p in glob.glob(repo_path("data", "maps", "*", "scripts.inc")) + glob.glob(repo_path("data", "scripts", "*.inc")):
        with open(p, encoding="utf-8") as f:
            if re.search(r"^\s*(?:giveitem|additem|finditem)\w*\s+ITEM_VS_SEEKER\b", f.read(), re.M):
                raise F.TU.DataError("%s hands out the Vs. Seeker: review the features page" % p)
    # statements taken from the README's feature list
    F.require("README.md", r"\*\*No trading needed\*\*: every species and every item can be obtained in\s+one game\.")
    F.require("README.md", r"\*\*Contests as in Ruby and Sapphire\*\*, one rank per contest hall\.")
    F.require("README.md", r"\*\*Battle Frontier and Trainer Hill\*\*")
    F.require("README.md", r"Trades and link battles come from Heart & Soul and were not\s+tested")
    # eight Kanto gyms offer the leader rematch
    n = sum(1 for b in P.badges("Kanto", "de")
            if "setflag FLAG_TEMP_KANTO_LEADER_REMATCH" in F.raw("data/maps/%s/scripts.inc" % b.map.dir))
    if n != 8:
        raise F.TU.DataError("Kanto leader rematches in %d gyms, the page says eight" % n)
    F.require("data/maps/PewterCity_Gym_Frlg/scripts.inc",
              r"goto_if_set FLAG_IS_JOHTO_CHAMPION, PewterCity_Gym_EventScript_BrockRematchPostJohto")


def _card(ctx, key, **kw):
    return H.card("<p>%s</p>" % U.fmt(ctx, key, **kw), title=ctx.t(key + "_t"))


def render(ctx):
    t = ctx.t
    lang = ctx.lang
    ctx.begin(PATH)
    _pins()
    C = F.C
    k2j, j2h = P.kanto_to_johto(lang), P.johto_to_hoenn(lang)
    P.hoenn_end(lang)
    lab = "PalletTown_ProfessorOaksLab_Frlg"

    def region_b(region):
        return U.b(H.esc(U.region_name(ctx, region)))

    # ---- journey
    steps = H.steps([
        U.fmt(ctx, "ft_step_kanto", b=region_b("Kanto"), pallet=U.place(ctx, "PalletTown_PlayersHouse_1F_Frlg")),
        U.fmt(ctx, "ft_step_johto", b=region_b("Johto"), oak_lab=U.place(ctx, lab), gs_ball=U.item(ctx, "ITEM_GS_BALL"),
              route22=U.place(ctx, "MAP_ROUTE22"), route26=U.place(ctx, "MAP_ROUTE26NORTH_HNS"),
              elm_town=U.place(ctx, "NewBarkTown_Lab_hns")),
        U.fmt(ctx, "ft_step_hoenn", b=region_b("Hoenn"), troy=H.esc(j2h["troy"]), ticket=U.item(ctx, "ITEM_HOENN_TICKET"),
              vermilion=U.place(ctx, "VermilionCity_PortInside_Frlg"), olivine=U.place(ctx, "OlivineCity_PortInside_hns")),
    ])
    journey = steps + H.prose(U.p(ctx, "ft_journey_more", start=U.anchor_link(
        ctx, "game/start", "faq-story", ctx.title_of("page", "game/start") or "")))

    # ---- what plays differently
    L = X.levels.C
    hours = [H.esc(X.hours_text(ctx, h)) for h in X.day_hours()]
    counts = X.rematch_counts()
    (_plow, _phigh), (llow, lhigh) = X.bands()
    rewards = U.join(ctx, [U.item(ctx, const) for _check, const, _flag in HC.oak_rewards()])
    gb = U.item_obj(ctx, "ITEM_GB_PLAYER")
    cards = [
        _card(ctx, "ft_levels", levels=U.page(ctx, "game/levels")),
        _card(ctx, "ft_exp", k_low=H.esc(ctx.pct(L("REMAP_EXP_KANTO_LOW_PERCENT"))),
              k_until=H.esc(ctx.level(L("REMAP_EXP_KANTO_LOW_UNTIL"))), k=H.esc(ctx.pct(L("REMAP_EXP_KANTO_PERCENT"))),
              j=H.esc(ctx.pct(L("REMAP_EXP_JOHTO_PERCENT"))), h=H.esc(ctx.pct(L("REMAP_EXP_HOENN_PERCENT")))),
        _card(ctx, "ft_share", share=U.item(ctx, "ITEM_EXP_SHARE")),
        _card(ctx, "ft_hm", johto_n=len({m.const for _, m in P.permit_sites("Johto", lang)}),
              hoenn_n=len({m.const for _, m in P.permit_sites("Hoenn", lang)})),
        _card(ctx, "ft_phone", kanto=counts["Kanto"], johto=counts["Johto"], hoenn=counts["Hoenn"],
              badges=C("OW_REMATCH_BADGE_COUNT"), opt=H.esc(X.option(ctx, OPTION_CALLS).name)),
        _card(ctx, "ft_leaders", low=llow, high=lhigh),
        _card(ctx, "ft_time", m=hours[0], d=hours[1], e=hours[2], n=hours[3]),
        _card(ctx, "ft_follow", opt=H.esc(X.option(ctx, OPTION_FOLLOW).name)),
        _card(ctx, "ft_ships", ticket=U.item(ctx, "ITEM_HOENN_TICKET"),
              vermilion=U.place(ctx, "VermilionCity_PortInside_Frlg"), olivine=U.place(ctx, "OlivineCity_PortInside_hns"),
              route104=U.place(ctx, "MAP_ROUTE104"), slateport=U.place(ctx, "MAP_SLATEPORT_CITY_HARBOR"),
              lilycove=U.place(ctx, "MAP_LILYCOVE_CITY_HARBOR"), frontier=U.mapsec(ctx, "MAPSEC_BATTLE_FRONTIER"),
              birth=U.mapsec(ctx, "MAPSEC_BIRTH_ISLAND"), aurora=U.item(ctx, "ITEM_AURORA_TICKET")),
        _card(ctx, "ft_legend", days=C("FLEE_COOLDOWN_DAYS", "src/legendaries_oj.c")),
        _card(ctx, "ft_mom"),
        _card(ctx, "ft_items", boxlink=U.item(ctx, "ITEM_POKEMON_BOX_LINK"), oval=U.item(ctx, "ITEM_OVAL_CHARM"),
              rewards=rewards),
        _card(ctx, "ft_gb", gb=U.item(ctx, gb), desc=U.quote(ctx, gb.description)),
    ]

    # ---- rules of your own
    modes = H.ul([U.fmt(ctx, "ft_mode_" + k, b=U.b(H.esc(t("ft_mode_b_" + k))))
                  for k in ("rules", "nuzlocke", "random", "hard")])
    modes += H.prose(U.p(ctx, "ft_modes_more", settings=U.page(ctx, "game/settings")))

    # ---- more differences
    diffs = H.ul([
        U.fmt(ctx, "ft_d_species"), U.fmt(ctx, "ft_d_region"), U.fmt(ctx, "ft_d_trade"), U.fmt(ctx, "ft_d_split"),
        U.fmt(ctx, "ft_d_run"), U.fmt(ctx, "ft_d_contest"),
        U.fmt(ctx, "ft_d_frontier", frontier=U.mapsec(ctx, "MAPSEC_BATTLE_FRONTIER"),
              hill=U.mapsec(ctx, "MAPSEC_TRAINER_HILL")),
        U.fmt(ctx, "ft_d_seeker", seeker=H.esc(U.item_obj(ctx, "ITEM_VS_SEEKER").name)),
    ])

    # ---- beta
    F.require("src/save.c", r"status = SAVE_STATUS_OUTDATED;")
    msg = F.c_string("src/main_menu.c", "gText_SaveFileOutdated", lang)
    beta = H.ul([
        U.fmt(ctx, "ft_beta_version", version=H.esc(site_config.VERSION[lang])),
        U.fmt(ctx, "ft_beta_saves", msg=U.quote(ctx, msg)),
        U.fmt(ctx, "ft_beta_link"),
    ])

    body = [
        H.section(t("ft_sec_journey"), journey, id="journey", intro=H.esc(t("ft_journey_intro"))),
        H.section(t("ft_sec_play"), H.grid(cards, "l"), id="gameplay"),
        H.section(t("ft_sec_modes"), modes, id="modes", intro=H.esc(t("ft_modes"))),
        H.section(t("ft_sec_diff"), diffs, id="differences"),
        H.section(t("ft_sec_beta"), beta, id="beta"),
    ]
    ctx.end("".join(body), lead=H.esc(t("ft_lead")), description=t("ft_lead"))
