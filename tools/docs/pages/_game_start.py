"""Getting started & FAQ (game/start): the first steps of a new game and the questions
players ask most.

The questions and sentence frames are hand-written; every name, number and rule in the
answers comes from the loaders, and each rule is pinned to the source with
hand_facts.require() or a loader check: region changes (gamedata.hand_progress),
Pokédex rewards and Trainer Card stars (gamedata.hand_completion), rematches
(gamedata.trainers, gamedata.levels), the clock (src/rtc.c, src/new_game.c), shiny odds
(gamedata.wild_shiny), Day Cares (gamedata.hand_breeding), the menus (gamedata.hand_menus).
"""
import glob
import re

from common import html as H
from gamedata import hand_breeding as B
from gamedata import hand_completion as HC
from gamedata import hand_facts as F
from gamedata import hand_progress as P
from gamedata import levels
from gamedata import repo_path
from gamedata import wild_shiny as WS
from pages import _game_util as U
from pages import _game_shared as X

PATH = "game/start"

S = {
    "de": {
        "st_keywords": "erste schritte faq fragen hilfe einstieg johto hoenn ticket gs-ball uhr spielstand",
        "st_lead": "Der schnelle Einstieg in Pokémon Origin Jade: was dich in der ersten Spielstunde erwartet – und "
                   "Antworten auf die Fragen, die unterwegs am häufigsten aufkommen.",
        "st_sec_first": "Die ersten Schritte",
        "st_step_rules": "{b} Zuerst wählst du auf dem Figurenrad deine Spielfigur: {chars}. Nach dem Namen "
                         "erscheint das Menü "
                         "„Herausforderungen“. Mit "
                         "„{recommended}“ spielst du mit den empfohlenen Regeln; wenn du nichts weiter änderst, sind "
                         "Nuzlocke, Zufallsmodus und alle Erschwernisse aus. Was die Einträge bedeuten, erklärt das "
                         "Menü selbst.",
        "st_step_home": "{b} Du startest in {pallet}. Mama gibt dir das PokéCom und die Turbotreter; im Beutel liegen "
                        "schon der {share} (eingeschaltet) und der {gb}.",
        "st_step_oak": "{b} Von Prof. Eich bekommst du dein erstes Pokémon und den Pokédex. Spielst du mit "
                       "Nuzlocke-Regeln, gelten sie ab diesem Moment.",
        "st_step_radio": "{b} In {viridian} schaltet dir der alte Mann, der das Fangen vorführt, das Radio im PokéCom "
                         "frei.",
        "st_step_go": "{b} Ab jetzt läuft Kanto wie gewohnt: acht Orden, dann die Pokémon-Liga. Danach geht es mit "
                      "demselben Team in Johto weiter.",
        "st_b_rules": "Regeln wählen.", "st_b_home": "Zu Hause.", "st_b_oak": "Im Labor.",
        "st_b_radio": "Radio abholen.", "st_b_go": "Losziehen.",
        "st_tips_title": "Gut zu wissen",
        "st_tip_hm": "VMs musst du niemandem beibringen: Die VM im Beutel und ein Pokémon im Team, das die Attacke "
                     "lernen könnte, reichen.",
        "st_tip_levels": "Gegner haben feste Level. Es lohnt sich, das ganze Team mitzuziehen – die Level steigen bis "
                         "zum Ende in Hoenn weiter.",
        "st_tip_pc": "Die Regeln aus dem Menü „Herausforderungen“ kannst du an jedem PC ansehen und viele davon "
                     "nachträglich lockern.",
        "st_sec_faq": "Häufige Fragen",
        "st_g_story": "Geschichte und Regionen",
        "st_g_play": "Spielablauf",
        "st_g_pokemon": "Pokémon",
        "st_g_settings": "Regeln und Uhr",
        "st_g_tech": "Spielstand",

        "st_q_order": "In welcher Reihenfolge spiele ich die Regionen?",
        "st_a_order": "Kanto, dann Johto, dann Hoenn – alles in einem Spielstand. Jede Region hat eigene Orden, eine "
                      "eigene Liga und einen eigenen Titel. Der Abspann läuft nach dem ersten Titel in Hoenn.",
        "st_q_johto": "Wie komme ich von Kanto nach Johto?",
        "st_a_johto": "Werde Champ von Kanto. Danach bittet dich Prof. Eich in sein Labor in {oak_lab} und gibt dir "
                      "den {gs_ball}. Erst dann lässt dich die Wache im Tor am Ende von {route22} durch; von dort "
                      "geht es über {route26} nach {elm_town}, wo Prof. Lind den {gs_ball} entgegennimmt.",
        "st_a_johto_2": "Vor dem Titel sagt die Wache: {closed} Nach dem Titel, aber ohne den Besuch bei Prof. Eich: "
                        "{oak}",
        "st_q_hoenn": "Wie komme ich nach Hoenn?",
        "st_a_hoenn": "Werde Champ von Johto und geh dann in Prof. Eichs Labor in {oak_lab}: Dort wartet {troy} und "
                      "gibt dir das {ticket}. Das Schiff nach Hoenn fährt in {vermilion} und {olivine} ab. Die erste "
                      "Fahrt endet auf {route104}, danach geht es zu Prof. Birk nach {birch}.",
        "st_a_hoenn_2": "Ohne Ticket sagt der Matrose: {no_ticket} Spätere Fahrten gehen direkt nach {slateport} "
                        "oder {lilycove}, sobald du dort warst.",
        "st_q_tickets": "Welche Tickets gibt es und wo bekomme ich sie?",
        "st_a_tickets": "{ss}: von Bill in seinem Haus ({route25}). {ticket}: von {troy} in Prof. Eichs Labor nach "
                        "dem Titel in Johto. {aurora}: von Prof. Eich für den vollständigen Hoenn-Pokédex; damit "
                        "steht die {birth} im Fahrplan der Schiffe.",
        "st_a_tickets_2": "{eon}, {mystic} und {oldmap} bekommst du im Spiel nicht. Die {frontier} erscheint im "
                          "Fahrplan erst nach dem Titel in Hoenn.",
        "st_q_map": "Wie wechsle ich auf der Karte zwischen den Regionen?",
        "st_a_map": "Die Karte im PokéCom zeigt Kanto und Johto zusammen. Sobald du in Hoenn warst, wechselst du mit Select zur Hoenn-Karte und zurück – oder indem du am unteren Rand weiter nach unten bzw. auf der Hoenn-Karte am oberen Rand weiter nach oben gehst.",
        "st_q_rival_hoenn": "Wer ist mein Rivale in Hoenn?",
        "st_a_rival_hoenn": "Maike – oder Brix, wenn du selbst Maike spielst.",
        "st_q_stars": "Was bedeuten die Sterne auf dem Trainerpass?",
        "st_a_stars": "Es gibt je einen Stern für den Titel in Kanto, Johto und Hoenn und einen für den Sieg über "
                      "{red}.",

        "st_q_rematch": "Wie funktionieren Rückkämpfe?",
        "st_a_rematch": "Über das PokéCom. Besiegte Trainer tragen sich ein und rufen an, sobald du in ihrer Region "
                        "{badges} Orden hast. Einen {seeker} gibt es nicht. Die Arenaleiter von Kanto forderst du "
                        "nach dem Titel in Kanto direkt in ihrer Arena erneut heraus.",
        "st_a_rematch_2": "Wenn dich die Anrufe stören, schalte sie in den Optionen unter „{opt}“ ab.",
        "st_q_share": "Was macht der EP-Teiler?",
        "st_a_share": "Der {share} liegt ab Spielstart eingeschaltet im Beutel. Ist er an, geht die Hälfte der "
                      "Erfahrung an die Pokémon, die gekämpft haben, die andere Hälfte wird auf das ganze Team "
                      "verteilt. Die Erfahrung wird also geteilt, nicht verdoppelt. Benutze ihn im Beutel, um ihn "
                      "aus- oder einzuschalten.",
        "st_q_hm": "Muss ich VM-Attacken beibringen?",
        "st_a_hm": "Nein. Die VM im Beutel und ein Pokémon im Team, das die Attacke lernen könnte, reichen. Die "
                   "Freigabe der Region brauchst du trotzdem: in Kanto den Orden, in Johto und Hoenn die Erlaubnis "
                   "für die jeweilige Attacke.",
        "st_a_hm_2": "Mit manchen Herausforderungen – etwa Nuzlocke, Teamlimit oder nur einem Typ – darf das erste "
                     "Pokémon im Team die Feldattacke auch dann einsetzen, wenn es sie nicht lernen kann.",
        "st_q_levels": "Warum sind die Pokémon in Johto und Hoenn so stark?",
        "st_a_levels": "Weil du Johto nach Kanto und Hoenn zuletzt spielst, schließen die Level dort an: Jede Region "
                       "beginnt etwa da, wo die vorige aufhört. Die Level sind fest und hängen nicht von deinem Team "
                       "ab. Zum Ausgleich gibt es je nach Region unterschiedlich viel Erfahrung. Alles dazu unter "
                       "{levels}.",
        "st_q_dex": "Wo bekomme ich die Belohnungen für den Pokédex?",
        "st_a_dex": "Bei Prof. Eich in seinem Labor in {oak_lab}. Sprich ihn an, wenn ein Regional-Pokédex "
                    "vollständig ist: {rewards}. Gezählt werden gefangene Pokémon.",
        "st_dex_row": "{region} ({n} Pokémon): {item}",
        "st_a_dex_2": "Welche Pokémon dazugehören, steht unter {completion}.",

        "st_q_daycare": "Wo sind die Pensionen?",
        "st_a_daycare": "Jede Region hat ihre eigene: {places}. Mit dem ersten Ei aus einer Pension bekommst du den "
                        "{oval}.",
        "st_a_daycare_2": "Mehr zur Zucht unter {breeding}.",
        "st_daycare_row": "{place} ({region})",
        "st_q_legend": "Ich habe ein legendäres Pokémon besiegt – ist es weg?",
        "st_a_legend": "Nein. Besiegte legendäre Pokémon kommen nach jedem Liga-Sieg zurück, geflohene nach {days} "
                       "Tageswechseln. Nur gefangen kommen sie nicht wieder.",
        "st_a_legend_2": "Wo sie zu finden sind, steht unter {legendaries}.",
        "st_q_shiny": "Wie hoch ist die Chance auf ein schillerndes Pokémon?",
        "st_a_shiny": "Normalerweise 1 zu {odds}. Im Menü „Herausforderungen“ lässt sie sich unter „{opt}“ erhöhen "
                      "({choices}). Der {charm} gibt {rolls} zusätzliche Versuche; du bekommst ihn von Prof. Eich "
                      "für den vollständigen Johto-Pokédex.",
        "st_a_shiny_2": "Mehr dazu unter {shiny}.",
        "st_q_mints": "Wo bekomme ich Minzen, um das Wesen zu ändern?",
        "st_a_mints": "Das hängt von der Einstellung „{opt}“ im Menü „Herausforderungen“ ab:",

        "st_q_time": "Wann ist Tag und wann Nacht?",
        "st_a_time": "Tag ist {d}, Nacht {n}. Vielerorts erscheinen nachts andere wilde Pokémon als am Tag.",
        "st_q_clock": "Die Uhr läuft nicht richtig – was kann ich tun?",
        "st_a_clock": "Stell im Menü „Herausforderungen“ unter „{rtc}“ auf „{fake}“ um; das geht auch später an jedem "
                      "PC. Die simulierte Uhr läuft nur, während du spielst. Ihr Tempo wählst du unter „{speed}“:",
        "st_a_clock_2": "Meldet die echte Uhr beim Start eines neuen Spiels einen Fehler, wählt das Spiel die "
                        "simulierte Uhr von selbst vor.",
        "st_q_nuzlocke": "Wann beginnen und enden die Nuzlocke-Regeln?",
        "st_a_nuzlocke": "Sie beginnen, sobald du bei Prof. Eich den Pokédex bekommst, und enden mit dem ersten "
                         "Titel in Hoenn. Die Stufen im Spiel:",
        "st_q_random": "Stimmen diese Seiten auch mit Zufallsmodus?",
        "st_a_random": "Nein. Alle Seiten zeigen das Spiel ohne Zufallsmodus. Was du auswürfeln lässt, weicht davon "
                       "ab.",
        "st_q_change": "Kann ich die Regeln nach dem Start noch ändern?",
        "st_a_change": "Ja, an jedem PC unter {pc}. Die Grundregeln und die Einstellungen zu Uhr und Shiny-Chance "
                       "lassen sich frei ändern. Nuzlocke, Zufallsmodus, Schwierigkeit und Sonderregeln lassen sich "
                       "fast alle nur noch lockern, nicht mehr verschärfen.",

        "st_q_saves": "Kann ich meinen Spielstand aus einer älteren Version weiterspielen?",
        "st_a_saves": "Nicht immer. Passt ein Spielstand nicht mehr zur Version, meldet das Spiel beim Laden: {msg}",
        "st_a_saves_2": "Dann bleibt nur ein neues Spiel; beim ersten Speichern wird der alte Spielstand "
                        "überschrieben.",
    },
    "en": {
        "st_keywords": "getting started faq questions help johto hoenn ticket gs ball clock save file",
        "st_lead": "The quick way into Pokémon Origin Jade: what to expect in your first hour – and answers to the "
                   "questions that come up most on the way.",
        "st_sec_first": "The first steps",
        "st_step_rules": "{b} First you choose your character on the character wheel: {chars}. After the name "
                         "the challenge menu comes up. "
                         "“{recommended}” gives you "
                         "the recommended rules; if you change nothing else, Nuzlocke, the randomizer and every "
                         "handicap are off. The menu itself explains what the entries mean.",
        "st_step_home": "{b} You start in {pallet}. Mom gives you the Pokégear and the Running Shoes; the {share} "
                        "(switched on) and the {gb} are already in your Bag.",
        "st_step_oak": "{b} Prof. Oak gives you your first Pokémon and the Pokédex. If you play with Nuzlocke rules, "
                       "they apply from this moment.",
        "st_step_radio": "{b} In {viridian} the old man who shows you how to catch Pokémon unlocks the radio on your "
                         "Pokégear.",
        "st_step_go": "{b} From here Kanto runs as you know it: eight Badges, then the Pokémon League. After that "
                      "you carry on in Johto with the same team.",
        "st_b_rules": "Choose your rules.", "st_b_home": "At home.", "st_b_oak": "At the lab.",
        "st_b_radio": "Pick up the radio.", "st_b_go": "Set off.",
        "st_tips_title": "Good to know",
        "st_tip_hm": "You never have to teach an HM: the HM in your Bag and a Pokémon in your party that could learn "
                     "the move are enough.",
        "st_tip_levels": "Opponents have fixed levels. It pays to raise the whole team – the levels keep climbing "
                         "until the end in Hoenn.",
        "st_tip_pc": "You can look at the rules of the challenge menu on any PC, and relax many of them later.",
        "st_sec_faq": "Frequently asked questions",
        "st_g_story": "Story and regions",
        "st_g_play": "Gameplay",
        "st_g_pokemon": "Pokémon",
        "st_g_settings": "Rules and clock",
        "st_g_tech": "Save file",

        "st_q_order": "In which order do I play the regions?",
        "st_a_order": "Kanto, then Johto, then Hoenn – all in one save file. Every region has its own Badges, its "
                      "own League and its own title. The credits roll after the first title in Hoenn.",
        "st_q_johto": "How do I get from Kanto to Johto?",
        "st_a_johto": "Become Champion of Kanto. Prof. Oak then asks you to his lab in {oak_lab} and gives you the "
                      "{gs_ball}. Only then does the guard in the gate at the end of {route22} let you through; from "
                      "there {route26} leads to {elm_town}, where Prof. Elm takes the {gs_ball}.",
        "st_a_johto_2": "Before the title the guard says: {closed} After the title, but without the visit to "
                        "Prof. Oak: {oak}",
        "st_q_hoenn": "How do I get to Hoenn?",
        "st_a_hoenn": "Become Champion of Johto, then go to Prof. Oak's lab in {oak_lab}: {troy} is waiting there "
                      "and gives you the {ticket}. The ship to Hoenn leaves from {vermilion} and {olivine}. The first "
                      "crossing ends on {route104}; from there you go to Prof. Birch in {birch}.",
        "st_a_hoenn_2": "Without a ticket the sailor says: {no_ticket} Later crossings go straight to {slateport} "
                        "or {lilycove} once you have been there.",
        "st_q_tickets": "Which tickets are there and where do I get them?",
        "st_a_tickets": "{ss}: from Bill at his house ({route25}). {ticket}: from {troy} at Prof. Oak's lab after "
                        "the title in Johto. {aurora}: from Prof. Oak for the complete Hoenn Pokédex; it puts "
                        "{birth} on the ships' timetable.",
        "st_a_tickets_2": "You cannot get the {eon}, the {mystic} or the {oldmap} in the game. The {frontier} only "
                          "appears on the timetable after the title in Hoenn.",
        "st_q_map": "How do I switch between the regions on the map?",
        "st_a_map": "The PokéGear map shows Kanto and Johto together. Once you have been to Hoenn, press Select to switch to the Hoenn map and back – or move further down at the bottom edge, and further up at the top edge of the Hoenn map.",
        "st_q_rival_hoenn": "Who is my rival in Hoenn?",
        "st_a_rival_hoenn": "May – or Brendan if you play as May yourself.",
        "st_q_stars": "What do the stars on the Trainer Card mean?",
        "st_a_stars": "There is one star each for the title in Kanto, Johto and Hoenn, and one for beating {red}.",

        "st_q_rematch": "How do rematches work?",
        "st_a_rematch": "Through the Pokégear. Trainers you beat register themselves and call once you have {badges} "
                        "Badges in their region. There is no {seeker}. The Kanto Gym Leaders can be challenged again "
                        "right in their Gyms after the title in Kanto.",
        "st_a_rematch_2": "If the calls bother you, turn them off in the options under “{opt}”.",
        "st_q_share": "What does the Exp. Share do?",
        "st_a_share": "The {share} is in your Bag, switched on, from the start. While it is on, half of the "
                      "experience goes to the Pokémon that fought and the other half is spread over the whole "
                      "party. So experience is shared, not doubled. Use it in the Bag to turn it off or on.",
        "st_q_hm": "Do I have to teach HM moves?",
        "st_a_hm": "No. The HM in your Bag and a Pokémon in your party that could learn the move are enough. You "
                   "still need the region's go-ahead: the Badge in Kanto, and in Johto and Hoenn the permission for "
                   "that move.",
        "st_a_hm_2": "With some challenges – Nuzlocke, a party limit or a single type, for example – the first "
                     "Pokémon in your party may use the field move even if it cannot learn it.",
        "st_q_levels": "Why are the Pokémon in Johto and Hoenn so strong?",
        "st_a_levels": "Because you play Johto after Kanto and Hoenn last, the levels there carry on: each region "
                       "starts roughly where the one before ends. The levels are fixed and do not depend on your "
                       "team. To balance that, each region gives a different amount of experience. Everything about "
                       "it is under {levels}.",
        "st_q_dex": "Where do I get the Pokédex rewards?",
        "st_a_dex": "From Prof. Oak at his lab in {oak_lab}. Talk to him when a regional Pokédex is complete: "
                    "{rewards}. Caught Pokémon are what counts.",
        "st_dex_row": "{region} ({n} Pokémon): {item}",
        "st_a_dex_2": "Which Pokémon belong to each is listed under {completion}.",

        "st_q_daycare": "Where are the Day Cares?",
        "st_a_daycare": "Every region has its own: {places}. With the first Egg from a Day Care you get the {oval}.",
        "st_a_daycare_2": "More about breeding under {breeding}.",
        "st_daycare_row": "{place} ({region})",
        "st_q_legend": "I knocked out a legendary Pokémon – is it gone?",
        "st_a_legend": "No. Legendary Pokémon you knocked out come back after every League victory, ones that fled "
                       "after {days} changes of day. Only caught ones never return.",
        "st_a_legend_2": "Where to find them is listed under {legendaries}.",
        "st_q_shiny": "What are the odds of a Shiny Pokémon?",
        "st_a_shiny": "Normally 1 in {odds}. In the challenge menu you can raise them under “{opt}” ({choices}). "
                      "The {charm} gives {rolls} extra tries; Prof. Oak gives it to you for the complete Johto "
                      "Pokédex.",
        "st_a_shiny_2": "More under {shiny}.",
        "st_q_mints": "Where do I get Mints to change a nature?",
        "st_a_mints": "That depends on the setting “{opt}” in the challenge menu:",

        "st_q_time": "When is it day and when is it night?",
        "st_a_time": "Day is {d}, night is {n}. In many places different wild Pokémon appear at night.",
        "st_q_clock": "The clock does not run properly – what can I do?",
        "st_a_clock": "Switch “{rtc}” in the challenge menu to “{fake}”; that also works later on any PC. The "
                      "simulated clock only runs while you play. You choose its speed under “{speed}”:",
        "st_a_clock_2": "If the real clock reports an error when a new game starts, the game selects the simulated "
                        "clock by itself.",
        "st_q_nuzlocke": "When do the Nuzlocke rules start and end?",
        "st_a_nuzlocke": "They start as soon as Prof. Oak gives you the Pokédex and end with the first title in "
                         "Hoenn. The levels in the game:",
        "st_q_random": "Are these pages right with the randomizer on?",
        "st_a_random": "No. All pages describe the game without the randomizer. Whatever you have shuffled differs "
                       "from them.",
        "st_q_change": "Can I still change the rules after starting?",
        "st_a_change": "Yes, on any PC under {pc}. The basic rules and the settings for the clock and the shiny odds "
                       "can be changed freely. Nuzlocke, the randomizer, difficulty and special rules can almost "
                       "all only be relaxed, not tightened.",

        "st_q_saves": "Can I carry on with a save file from an older version?",
        "st_a_saves": "Not always. If a save no longer fits the version, the game says when loading: {msg}",
        "st_a_saves_2": "Then you can only start a new game; the first time you save, the old save file is "
                        "overwritten.",
    },
}

OPTION_CALLS = "Anrufe"
DEX_KINDS = {"HasAllKantoMons": ("Kanto", "kanto"), "HasAllJohotoMons": ("Johto", "johto"),
             "HasAllHoennMons": ("Hoenn", "hoenn")}


def _characters(lang):
    """Names of the playable characters in the order of the selection (gPlayerCharacterInfo,
    src/player_character.c; the English names are written in capitals there)."""
    import re
    src = F.raw("src/player_character.c")
    pairs = re.findall(r'#if GERMAN\s*\.name = COMPOUND_STRING\("([^"]+)"\),\s*#else\s*'
                       r'\.name = COMPOUND_STRING\("([^"]+)"\),', src)
    if len(pairs) < 2:
        raise F.TU.DataError("src/player_character.c: character names not found")
    return [de if lang == "de" else en.title() for de, en in pairs]


def _pins():
    F.require("data/maps/Route25_SeaCottage_Frlg/scripts.inc",
              r"giveitem_msg Route25_SeaCottage_Text_ReceivedSSTicketFromBill, ITEM_SS_TICKET")
    F.require("src/data/items.h", r"// Origin Jade: not obtainable, kept so that the item ids do not shift.\n\s*\[ITEM_VS_SEEKER\]")
    F.require("src/save.c", r"status = SAVE_STATUS_OUTDATED;")
    F.require("src/new_game.c", r"if \(RtcGetErrorStatus\(\) & RTC_ERR_FLAG_MASK\)\n\s*"
                                r"gSaveblock3\.challengeSettings\.tx_Features_RTCType = 1;")
    F.require("data/scripts/cable_club.inc", r"setvar VAR_DISTRIBUTE_EON_TICKET, 0")
    F.require("src/field_specials.c", r"if \(!VarGet\(VAR_DISTRIBUTE_EON_TICKET\)\)")
    for p in glob.glob(repo_path("data", "maps", "*", "scripts.inc")):
        with open(p, encoding="utf-8") as f:
            if re.search(r"^\s*giveitem\w*\s+ITEM_(EON_TICKET|MYSTIC_TICKET|OLD_SEA_MAP|VS_SEEKER)\b", f.read(), re.M):
                raise F.TU.DataError("%s gives an event ticket or the Vs. Seeker: review the FAQ" % p)
    F.require("src/legendaries_oj.c", r"//  - knocked out: back after every league victory")
    F.require("src/legendaries_oj.c", r"//  - caught: never again;")
    lab = "data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc"
    F.require(lab, r"setflag FLAG_START_NUZLOCKE")
    home = "data/maps/PalletTown_PlayersHouse_1F_Frlg/scripts.inc"
    F.require(home, r"setflag FLAG_SYS_POKENAV_GET\n\tsetflag FLAG_HAS_MATCH_CALL")
    F.require(home, r"setflag FLAG_RECEIVED_RUNNING_SHOES")
    F.require("data/maps/ViridianCity_Frlg/scripts.inc", r"setflag FLAG_ENABLE_RADIO")
    F.require("data/scripts/new_game.inc", r"^\tadditem ITEM_EXP_SHARE$")
    F.require("data/scripts/new_game.inc", r"^\tadditem ITEM_GB_PLAYER$")
    F.require("data/scripts/new_game.inc", r"^\tsetflag FLAG_EXP_SHARE_ENABLED$")
    F.require("src/battle_script_commands.c", r"\*exp = SAFE_DIV\(calculatedExp / 2, viaSentIn\);")
    F.require("src/scrcmd.c", r"CheckBagHasItem\(itemId, 1\)")
    F.require("data/scripts/day_care.inc", r"call_if_unset FLAG_RECEIVED_OVAL_CHARM, DayCare_EventScript_GiveOvalCharm")
    F.require("src/oak_speech_hns.c", r"static void Task_NewGameHnsSpeech_ChallengeMenu\(u8 taskId\)[\s\S]*?"
                                      r"static void Task_NewGameHnsSpeech_WhatsYourName\(u8 taskId\)")
    HC.check_mirror()


def _choice_list(item):
    return H.ul(["%s – %s" % (U.b(H.esc(c.name)), H.esc(c.desc)) for c in item.choices])


def _first(ctx):
    t = ctx.t
    mode = X.challenge(ctx, "TAB_MODE", "ITEM_MODE_GAMEMODE")

    def b(key):
        return U.b(H.esc(t(key)))
    steps = H.steps([
        U.fmt(ctx, "st_step_rules", b=b("st_b_rules"), recommended=H.esc(mode.choices[0].name),
              chars=U.join(ctx, [H.esc(n) for n in _characters(ctx.lang)], "or"),
              settings=U.page(ctx, "game/settings")),
        U.fmt(ctx, "st_step_home", b=b("st_b_home"), pallet=U.place(ctx, "PalletTown_PlayersHouse_1F_Frlg"),
              share=U.item(ctx, "ITEM_EXP_SHARE"), gb=U.item(ctx, "ITEM_GB_PLAYER")),
        U.fmt(ctx, "st_step_oak", b=b("st_b_oak")),
        U.fmt(ctx, "st_step_radio", b=b("st_b_radio"), viridian=U.place(ctx, "ViridianCity_Frlg")),
        U.fmt(ctx, "st_step_go", b=b("st_b_go")),
    ])
    tips = H.callout(ctx, "tip", U.ul(ctx, ["st_tip_hm", "st_tip_levels", "st_tip_pc"]), title=t("st_tips_title"))
    return steps + tips


def _faq(ctx):
    t = ctx.t
    lang = ctx.lang
    k2j, j2h = P.kanto_to_johto(lang), P.johto_to_hoenn(lang)
    lab = U.place(ctx, "PalletTown_ProfessorOaksLab_Frlg")
    ticket = U.item(ctx, "ITEM_HOENN_TICKET")
    vermilion, olivine = U.place(ctx, "VermilionCity_PortInside_Frlg"), U.place(ctx, "OlivineCity_PortInside_hns")
    slateport, lilycove = U.place(ctx, "MAP_SLATEPORT_CITY_HARBOR"), U.place(ctx, "MAP_LILYCOVE_CITY_HARBOR")
    troy = H.esc(j2h["troy"])
    settings_link = U.page(ctx, "game/settings")

    def more(key, path, name):
        """A closing sentence that links another page; left out while that page does not exist."""
        return U.p(ctx, key, **{name: U.page(ctx, path)}) if ctx.url(path) else ""

    # ---- story and regions
    story = [
        (t("st_q_order"), U.p(ctx, "st_a_order")),
        (t("st_q_johto"),
         U.p(ctx, "st_a_johto", oak_lab=lab, gs_ball=U.item(ctx, "ITEM_GS_BALL"), route22=U.place(ctx, "MAP_ROUTE22"),
             route26=U.place(ctx, "MAP_ROUTE26NORTH_HNS"), elm_town=U.place(ctx, "NewBarkTown_Lab_hns"))
         + U.p(ctx, "st_a_johto_2", closed=U.quote(ctx, k2j["gate_closed"]), oak=U.quote(ctx, k2j["gate_oak"]))),
        (t("st_q_hoenn"),
         U.p(ctx, "st_a_hoenn", oak_lab=lab, troy=troy, ticket=ticket, vermilion=vermilion, olivine=olivine,
             route104=U.place(ctx, "MAP_ROUTE104"), birch=U.place(ctx, "MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB"))
         + U.p(ctx, "st_a_hoenn_2", no_ticket=U.quote(ctx, j2h["no_ticket"]), slateport=slateport, lilycove=lilycove)),
        (t("st_q_tickets"),
         U.p(ctx, "st_a_tickets", ss=U.item(ctx, "ITEM_SS_TICKET"), route25=U.place(ctx, "Route25_SeaCottage_Frlg"),
             ticket=ticket, troy=troy, aurora=U.item(ctx, "ITEM_AURORA_TICKET"),
             birth=U.mapsec(ctx, "MAPSEC_BIRTH_ISLAND"))
         + U.p(ctx, "st_a_tickets_2", eon=H.esc(U.item_obj(ctx, "ITEM_EON_TICKET").name),
               mystic=H.esc(U.item_obj(ctx, "ITEM_MYSTIC_TICKET").name),
               oldmap=H.esc(U.item_obj(ctx, "ITEM_OLD_SEA_MAP").name),
               frontier=U.mapsec(ctx, "MAPSEC_BATTLE_FRONTIER"))),
    ]
    stars = HC.stars()
    if len(stars) != 4 or [s.kind for s in stars].count("trainer") != 1 or stars[-1].kind != "trainer":
        raise F.TU.DataError("Trainer Card stars changed: review the FAQ")
    story.append((t("st_q_stars"), U.p(ctx, "st_a_stars", red=U.trainer(ctx, stars[-1].const))))
    # map switch and Hoenn rival as the code handles them
    F.require("src/region_map.c", r"if \(hoennKnown && JOY_NEW\(SELECT_BUTTON\)\)")
    F.require("src/region_map.c", r"JOY_HELD\(DPAD_DOWN\) && sRegionMap->cursorPosY >= MAPCURSOR_Y_MAX")
    F.require("src/region_map.c", r"JOY_HELD\(DPAD_UP\) && sRegionMap->cursorPosY <= MAPCURSOR_Y_MIN")
    story.append((t("st_q_map"), U.p(ctx, "st_a_map")))
    F.require("src/player_character.c",
              r"bool8 IsHoennRivalBrendan\(void\)\s*\{\s*return GetPlayerCharacter\(\) == PLAYER_CHARACTER_MAY;")
    story.append((t("st_q_rival_hoenn"), U.p(ctx, "st_a_rival_hoenn")))

    # ---- gameplay
    rewards = []
    for check, const, _flag in HC.oak_rewards():
        region, kind = DEX_KINDS[check]
        rewards.append(U.fmt(ctx, "st_dex_row", region=H.esc(U.region_name(ctx, region)),
                             n=len(HC.dex_required(kind, lang)), item=U.item(ctx, const)))
    if len(rewards) != 3:
        raise F.TU.DataError("Pokédex rewards changed: review the FAQ")
    play = [
        (t("st_q_rematch"),
         U.p(ctx, "st_a_rematch", badges=F.C("OW_REMATCH_BADGE_COUNT"), seeker=H.esc(U.item_obj(ctx, "ITEM_VS_SEEKER").name))
         + U.p(ctx, "st_a_rematch_2",
               opt=H.esc(X.option(ctx, OPTION_CALLS).name))),
        (t("st_q_share"), U.p(ctx, "st_a_share", share=U.item(ctx, "ITEM_EXP_SHARE"))),
        (t("st_q_hm"), U.p(ctx, "st_a_hm") + U.p(ctx, "st_a_hm_2")),
        (t("st_q_dex"), U.p(ctx, "st_a_dex", oak_lab=lab, rewards="; ".join(rewards))
         + more("st_a_dex_2", "guides/completion", "completion")),
    ]

    # ---- Pokémon
    daycares = B.daycares(lang)
    if sorted(m.region for m in daycares) != ["Hoenn", "Johto", "Kanto"]:
        raise F.TU.DataError("Day Cares changed: review the FAQ")
    places = U.join(ctx, [U.fmt(ctx, "st_daycare_row", place=U.place(ctx, m), region=H.esc(U.region_name(ctx, m.region)))
                          for m in daycares])
    shiny_opt = X.challenge(ctx, "TAB_FEATURES", "ITEM_FEATURES_SHINY_CHANCE")
    odds = WS.odds_table()
    if [65536 // o for o in odds] != [int(c.name) for c in shiny_opt.choices]:
        raise F.TU.DataError("shiny odds and the menu choices differ: review the FAQ")
    if not any(check == "HasAllJohotoMons" and const == "ITEM_SHINY_CHARM" for check, const, _ in HC.oak_rewards()):
        raise F.TU.DataError("the Shiny Charm is no longer the Johto Pokédex reward: review the FAQ")
    mints = X.challenge(ctx, "TAB_MODE", "ITEM_MODE_MINTS")
    pokemon = [
        (t("st_q_daycare"), U.p(ctx, "st_a_daycare", places=places, oval=U.item(ctx, "ITEM_OVAL_CHARM"))
         + more("st_a_daycare_2", "guides/breeding", "breeding")),
        (t("st_q_legend"), U.p(ctx, "st_a_legend", days=F.C("FLEE_COOLDOWN_DAYS", "src/legendaries_oj.c"))
         + more("st_a_legend_2", "guides/legendaries", "legendaries")),
        (t("st_q_shiny"),
         U.p(ctx, "st_a_shiny", odds=H.esc(ctx.num(65536 // odds[0])), opt=H.esc(shiny_opt.name),
             choices=X.choices_line(ctx, shiny_opt), charm=U.item(ctx, "ITEM_SHINY_CHARM"), rolls=WS.charm_rolls())
         + more("st_a_shiny_2", "guides/shiny", "shiny")),
        (t("st_q_mints"), U.p(ctx, "st_a_mints", opt=H.esc(mints.name)) + _choice_list(mints)),
    ]

    # ---- rules and clock
    hours = [H.esc(X.hours_text(ctx, h)) for h in X.day_hours()]
    rtc = X.challenge(ctx, "TAB_FEATURES", "ITEM_FEATURES_RTC_TYPE")
    speed = X.challenge(ctx, "TAB_FEATURES", "ITEM_FEATURES_RTC_SPEED")
    nuz = X.challenge(ctx, "TAB_NUZLOCKE", "ITEM_NUZLOCKE_NUZLOCKE")
    pc_entry = X.pc_entry(ctx)
    settings = [
        (t("st_q_change"), U.p(ctx, "st_a_change", pc=U.quote(ctx, pc_entry), settings=settings_link)),
        (t("st_q_time"), U.p(ctx, "st_a_time", d=H.esc(X.hours_text(ctx, (X.day_hours()[0][0], X.day_hours()[2][1]))),
                             n=hours[3])),
        (t("st_q_clock"), U.p(ctx, "st_a_clock", rtc=H.esc(rtc.name), fake=H.esc(rtc.choices[1].name),
                              speed=H.esc(speed.name)) + _choice_list(speed) + U.p(ctx, "st_a_clock_2")),
        (t("st_q_nuzlocke"), U.p(ctx, "st_a_nuzlocke") + _choice_list(nuz)),
        (t("st_q_random"), U.p(ctx, "st_a_random")),
    ]

    # ---- save file
    msg = F.c_string("src/main_menu.c", "gText_SaveFileOutdated", lang)
    tech = [(t("st_q_saves"), U.p(ctx, "st_a_saves", msg=U.quote(ctx, msg)) + U.p(ctx, "st_a_saves_2"))]

    groups = (("story", story), ("play", play), ("pokemon", pokemon), ("settings", settings), ("tech", tech))
    return "".join(H.sub(t("st_g_" + key), U.faq(items), id="faq-" + key) for key, items in groups)


def render(ctx):
    t = ctx.t
    ctx.begin(PATH)
    _pins()
    ctx.todo("game/start: which emulators run the game's real-time clock correctly is not something the "
             "source says; the FAQ only explains the simulated clock.")
    body = [
        H.section(t("st_sec_first"), _first(ctx), id="first"),
        H.section(t("st_sec_faq"), _faq(ctx), id="faq"),
    ]
    ctx.end("".join(body), lead=H.esc(t("st_lead")), description=t("st_lead"))
