"""Legendary Pokémon (guides/legendaries): how to get each of them, step by step.

The rules for all of them are read from src/legendaries_oj.c (gamedata.wild_statics).
Levels come from the scripts through gamedata.wild_statics; every entry names the map of
its script, and the build stops when an entry no longer exists with that level. The steps
are written by hand from the map scripts:

  Kanto   SeafoamIslands_B4F_Frlg, PowerPlant_Frlg, VictoryRoad_4F_Frlg (object) /
          VictoryRoad_3F_Frlg (script), CeruleanCave_B1F_Frlg + hall_of_fame_frlg.inc,
          MtMoon_Cave_Frlg, Route4_Frlg + hoenn_arrival.inc
  Johto   Route39_hns (choice), EcruteakCity_Theater_hns (Kimono Girls, bells),
          EcruteakCity_SageOffice1_hns, TinTower_RoofDay_hns, WhirlIslands_LugiaChamber_hns,
          Route41_hns, TinTower_1F_hns + BurnedTower_B1F_hns, OlivineCity_hns, CianwoodCity_hns,
          Route42_hns, Route36_hns (Suicune), RuinsOfAlph_PuzzleAndRewardChambers_hns,
          RuinsOfAlph_B1F_hns, AzaleaTown_KurtsHouse_hns, AzaleaTown_hns, IlexForest_hns (Celebi),
          LakeOfRage_hns, UnionCave_B2F_hns
  Hoenn   SealedChamber_InnerRoom + src/braille_puzzles.c, DesertRuins, IslandCave,
          AncientTomb, Route119_WeatherInstitute_2F + src/field_specials.c, SkyPillar_Top,
          hall_of_fame.inc (roamers), BirthIsland_Exterior_hns + hoenn_arrival.inc +
          PalletTown_ProfessorOaksLab_Frlg (Aurora Ticket)
"""
from common import html as H
from gamedata import hand_facts as F
from gamedata import items as IT, maps, species as SP
from gamedata import wild_statics as WS
from pages import _game_util as U
from pages import _pokedex_data as PD

PATH = "guides/legendaries"

S = {
    "de": {
        "lg_lead": "Wie du jedes legendäre Pokémon bekommst: was vorher erledigt sein muss, welches Item du "
                   "brauchst und wo das Pokémon dann wartet.",
        "lg_sec_rules": "Regeln für alle legendären Pokémon",
        "lg_rule_caught": "Gefangen: Das Pokémon gibt es danach kein zweites Mal.",
        "lg_rule_ko": "Besiegt: Es kehrt nach deinem nächsten Sieg über eine Pokémon-Liga zurück – egal in "
                      "welcher Region.",
        "lg_rule_fled": "Geflohen (du oder das Pokémon): Es ist nach {days} Tageswechseln wieder da.",
        "lg_rule_lost": "Verlierst du den Kampf, bleibt alles, wie es war.",
        "lg_rule_roam": "Umherstreifende Pokémon wandern einfach weiter, bis du sie fängst. Nach jedem Liga-Sieg "
                        "laufen sie wieder los, falls sie nicht mehr unterwegs sind.",
        "lg_rule_enter": "Ob ein Pokémon da ist, entscheidet sich beim Betreten der Karte. Verlasse sie und komm "
                         "zurück, wenn sich etwas geändert haben sollte.",
        "lg_rule_also": "Dieselben Regeln gelten für {lapras} im {unioncave} und das rote {gyarados} am {lake}.",
        "lg_where": "Ort",
        "lg_level": "Level",
        "lg_sec_kanto": "Kanto",
        "lg_sec_johto": "Johto",
        "lg_sec_hoenn": "Hoenn",
        "lg_sec_none": "Was es nicht gibt",
        "lg_none_text": "Die Insel im Süden, das Ferneiland und der Nabelfels sind nicht erreichbar. {eon}, "
                        "{map} und {mystic} bekommst du nirgends. Jedes legendäre Pokémon gibt es genau einmal, "
                        "an den Orten auf dieser Seite.",
        "lg_free_1": "Keine Bedingung: Das Pokémon wartet dort, sobald du den Ort erreichst.",
        "lg_mewtwo_1": "Werde Champ von Kanto. Danach gibt der Wächter den Eingang der {ceruleancave} frei.",
        "lg_mewtwo_2": "{mon} wartet im Untergeschoss der Höhle.",
        "lg_mew_1": "Keine Bedingung. Im untersten Stockwerk des {mtmoon} führt ein Durchgang in eine eigene "
                    "kleine Höhle. Dort wartet {mon}.",
        "lg_jirachi_1": "Reise einmal nach Hoenn. Dafür brauchst du das {hoennticket}: Du bekommst es nach deinem "
                        "ersten Johto-Titel im Labor von Professor Eich in {pallet}.",
        "lg_jirachi_2": "Geh nachts (19 bis 6 Uhr) zum weißen Felsen auf {route4} und berühre ihn.",
        "lg_jirachi_3": "{mon} erscheint neben dem Felsen. Sprich es an.",
        "lg_jirachi_note": "Den Felsen musst du nur einmal berühren. Kehrt {mon} später zurück, steht es wieder "
                           "an derselben Stelle.",
        "lg_choice_title": "Lugia oder Ho-Oh: die Wahl auf Route 39",
        "lg_choice_1": "Auf {route39} fliegt ein Schatten über dich hinweg, und ein Mann fragt dich: "
                       "{gold} oder {silver}? {gold} macht {hooh} zum Pokémon deiner Geschichte, {silver} macht "
                       "es {lugia}. Die Wahl lässt sich nicht mehr ändern.",
        "lg_choice_2": "Das gewählte Pokémon triffst du in der Geschichte auf Lv. {lv_story}. Das andere "
                       "bekommst du später auf Lv. {lv_other} – beide sind in jedem Spielstand zu haben.",
        "lg_choice_3": "{silverwing} und {rainbowwing}: Eine der beiden bekommst du im Radioturm von {goldenrod}. "
                       "Für die Begegnungen brauchst du sie nicht – entscheidend sind die Glocken der "
                       "Kimono-Girls.",
        "lg_kimono_title": "Die Kimono-Girls im Tanztheater",
        "lg_kimono_1": "Schließe die Prüfung in der {dragonsden} ab. Wenn du danach {blackthorn} betrittst, ruft "
                       "Professor Lind an.",
        "lg_kimono_2": "Sprich mit Professor Lind in seinem Labor in {newbark}. Er gibt dir einen {masterball} "
                       "und schickt dich zu den Kimono-Girls.",
        "lg_kimono_3": "Geh nach {ecruteak}. Vor dem Tanztheater triffst du deinen Rivalen; betritt danach das "
                       "Theater und sprich mit {zuki}.",
        "lg_kimono_4": "Besiege die fünf Kimono-Girls direkt hintereinander.",
        "lg_kimono_5": "Als Belohnung bekommst du die {tidalbell} (wenn du {lugia} gewählt hast) oder die "
                       "{clearbell} (bei {hooh}).",
        "lg_kimono_note": "Die Pokémon-Liga von Johto lässt dich erst ein, wenn du acht Johto-Orden hast und dem "
                          "Pokémon deiner Geschichte begegnet bist.",
        "lg_lugia_a": "Wenn du Lugia gewählt hast",
        "lg_lugia_a1": "Besiege die Kimono-Girls und nimm die {tidalbell} entgegen. Die vier {tentacruel} auf "
                       "{route41}, die den Weg versperren, verschwinden damit.",
        "lg_lugia_a2": "Geh in die tiefste Kammer der {whirl}. Die Kimono-Girls tanzen, {mon} erscheint auf "
                       "Lv. {lv_story}.",
        "lg_lugia_b": "Wenn du Ho-Oh gewählt hast",
        "lg_lugia_b1": "Fange {hooh} – besiegen reicht nicht.",
        "lg_lugia_b2": "Werde Champ von Johto.",
        "lg_lugia_b3": "Betritt {route41}: Die {tentacruel} sind jetzt weg. {mon} wartet in der tiefsten Kammer "
                       "der {whirl} auf Lv. {lv_other}.",
        "lg_hooh_a": "Wenn du Ho-Oh gewählt hast",
        "lg_hooh_a1": "Besiege die Kimono-Girls und nimm die {clearbell} entgegen.",
        "lg_hooh_a2": "Zeige die Glocke dem Weisen im Haus vor dem {tintower} in {ecruteak}. Er gibt den Weg frei.",
        "lg_hooh_a3": "Steig auf das Dach des {tintower}. Die Kimono-Girls tanzen, {mon} erscheint auf "
                      "Lv. {lv_story}.",
        "lg_hooh_b": "Wenn du Lugia gewählt hast",
        "lg_hooh_b1": "Fange {lugia} – besiegen reicht nicht.",
        "lg_hooh_b2": "Werde Champ von Johto.",
        "lg_hooh_b3": "Der Weise lässt dich auch mit der {tidalbell} in den {tintower}. {mon} wartet auf dem Dach "
                      "auf Lv. {lv_other}.",
        "lg_suicune_1": "Geh in {ecruteak} in die {burned}. Nach dem Kampf gegen deinen Rivalen fällst du ins "
                        "Untergeschoss; dort laufen die drei legendären Raubkatzen davon.",
        "lg_suicune_2": "Reise weiter nach {olivine} und dann nach {cianwood}. Dort siehst du {mon} und kämpfst "
                        "gegen {eusine}.",
        "lg_suicune_3": "Begegne {mon} am Wasser auf {route42}.",
        "lg_suicune_4": "Geh danach auf {route36} zu der Stelle, an der {sudowoodo} stand. {mon} läuft nach Norden "
                        "davon, und {eusine} schickt dich zum {tintower}.",
        "lg_suicune_5": "Besiege die Kimono-Girls: Mit ihrer Glocke lässt dich der Weise in den {tintower}.",
        "lg_suicune_6": "{mon} wartet im Erdgeschoss des {tintower}.",
        "lg_beasts_1": "Geh in {ecruteak} in die {burned}. Nach dem Kampf gegen deinen Rivalen fällst du ins "
                       "Untergeschoss; dort laufen die drei davon.",
        "lg_beasts_2": "{raikou} und {entei} streifen ab jetzt über die Routen von Johto und wechseln ständig "
                       "die Route. Du triffst sie zufällig im hohen Gras.",
        "lg_beasts_note": "Der Arenaleiter von {ecruteak} lässt dich erst danach in seine Arena.",
        "lg_celebi_1": "Fange {raikou}, {entei} und {suicune}. Kurze Zeit später ruft dich Professor Lind an: Er hat den {gsball} von Professor Eich an Kurt geschickt.",
        "lg_celebi_2": "Besuche Kurt in {azalea} und sprich mit ihm. Er untersucht den Ball.",
        "lg_celebi_3": "Verlasse sein Haus. Kurt kommt dir nach und gibt dir den {gsball}.",
        "lg_celebi_4": "Geh zum Schrein im {ilex} und lege den Ball hinein. {mon} erscheint.",
        "lg_celebi_note1": "Es gibt nur einen {gsball}: den von Professor Eich, den du Professor Lind am Anfang von Johto bringst.",
        "lg_celebi_note2": "Fängst du {mon} nicht, wartet es später ohne Ball wieder am Schrein.",
        "lg_gyarados_1": "Das rote {mon} schwimmt mitten auf dem {lake}. Der erste Kampf gehört zur Geschichte: "
                         "Danach bekommst du die {redscale}, egal wie er ausgeht.",
        "lg_gyarados_note": "Es ist immer schillernd. Die {redscale} tauscht Mr. Pokémon auf {route30} gegen "
                            "einen {expshare}.",
        "lg_lapras_1": "Keine Bedingung und kein bestimmter Wochentag: {mon} schwimmt im untersten Stockwerk des "
                       "{unioncave}.",
        "lg_regi_title": "Regirock, Regice und Registeel",
        "lg_regi_1": "Geh in die {sealed} und setze im ersten Raum vor der Inschrift an der Rückwand {dig} ein. "
                     "Ein Durchgang öffnet sich.",
        "lg_regi_2": "Stell {wailord} an die erste und {relicanth} an die letzte Stelle deines Teams und lies die "
                     "Inschrift im hinteren Raum. Die Eingänge der drei Höhlen öffnen sich.",
        "lg_regi_3": "{regirock} – {desert} auf {route111}: Lies die Inschrift und setze an der beschriebenen "
                     "Stelle {rocksmash} ein.",
        "lg_regi_4": "{regice} – {island} auf {route105}: Lies die Inschrift und laufe dann einmal an der Wand "
                     "entlang um die ganze Höhle.",
        "lg_regi_5": "{registeel} – {tomb} auf {route120}: Lies die Inschrift und setze an der beschriebenen "
                     "Stelle {flash} ein.",
        "lg_weather_title": "Kyogre und Groudon",
        "lg_weather_1": "Werde Champ von Hoenn.",
        "lg_weather_2": "Sprich mit dem Forscher im Obergeschoss des Wetterinstituts auf {route119}. Er nennt dir "
                        "eine Route mit ungewöhnlichem Wetter.",
        "lg_weather_3": "Starker Regen: {kyogre} wartet in einer Höhle unter Wasser. Such auf der genannten Route "
                        "die Tauchstelle und tauche dort.",
        "lg_weather_4": "Große Dürre: {groudon} wartet in einer Höhle an Land. Such auf der genannten Route den "
                        "neuen Höhleneingang.",
        "lg_weather_note": "Das Wetter zieht nach 1.000 Schritten weiter. Frag dann den Forscher erneut. Sind "
                           "beide noch zu haben, entscheidet der Zufall, wessen Wetter er meldet.",
        "lg_rayquaza_1": "Spiel die Geschichte von Hoenn, bis Wassili dir den {skypillar} öffnet, und wecke "
                         "{mon} auf der Spitze.",
        "lg_rayquaza_2": "Sieh zu, wie {mon} den Kampf in {sootopolis} beendet.",
        "lg_rayquaza_3": "Steig danach erneut auf die Spitze des {skypillar}. {mon} wartet dort.",
        "lg_lati_title": "Latias und Latios",
        "lg_lati_1": "Werde Champ von Hoenn. Danach streifen beide über die Routen von Hoenn und wechseln ständig "
                     "die Route. Du triffst sie zufällig im hohen Gras oder auf dem Wasser.",
        "lg_deoxys_1": "Fange alle Pokémon des Hoenn-Pokédex. Welche dazu zählen, steht unter {completion}.",
        "lg_deoxys_2": "Sprich mit Professor Eich in seinem Labor in {pallet}. Er gibt dir das {aurora}.",
        "lg_deoxys_3": "Mit dem Ticket im Beutel bieten die Schiffe die {birth} als Ziel an – in den Häfen von "
                       "{olivine} und {vermilion} (ab dem Johto-Titel) sowie {slateport} und {lilycove} (ab dem "
                       "Hoenn-Titel).",
        "lg_deoxys_4": "Löse auf der Insel das Rätsel mit dem Dreieck. {mon} erscheint.",
        "lg_deoxys_note": "Am Schild auf der Insel bekommst du einen {meteorite}, wenn du keinen hast.",
        "lg_completion": "Pokédex vervollständigen",
        "lg_sec_fixed": "Weitere feste Begegnungen",
        "lg_fixed_intro": "Diese Pokémon stehen als Hindernis oder Falle in der Welt. Für sie gelten die Regeln "
                          "oben nicht.",
        "lg_col_mon": "Pokémon",
        "lg_col_how": "So kommt es zum Kampf",
        "lg_snorlax": "Du brauchst die {flute} von Herrn Fuji in {lavender}; er ist dort, nachdem du ihn im "
                      "{tower} befreit hast. Jedes {mon} gibt es nur einmal: Besiegt oder geflohen ist es weg.",
        "lg_sudowoodo": "Gieße den Baum mit der {squirt}. Du bekommst sie im Blumenladen von {goldenrod} mit "
                        "drei Johto-Orden. Fliehst du, bleibt es stehen; besiegt ist es weg.",
        "lg_kecleon": "Unsichtbar auf dem Weg. Das erste macht Troy auf der Brücke sichtbar; danach gibt er dir "
                      "das {devonscope} für die übrigen. Jedes gibt es nur einmal.",
        "lg_balls": "Sieht aus wie ein Itemball. Jedes gibt es nur einmal.",
        "lg_rocket": "Die drei gehören zur Geschichte im Versteck. Fliehst du, bleiben sie stehen.",
        "lg_marowak": "Der Geist im {tower}. Ohne {scope} kannst du nicht gegen ihn kämpfen; du findest es im "
                      "{rockethideout}.",
        "lg_tentacruel": "Sie versperren den Weg zu den {whirl} und greifen an, wenn du sie mehrmals ansprichst. "
                         "Sie lassen sich nicht fangen.",
    },
    "en": {
        "lg_lead": "How to get every legendary Pokémon: what has to be done first, which item you need and "
                   "where the Pokémon then waits.",
        "lg_sec_rules": "Rules for all legendary Pokémon",
        "lg_rule_caught": "Caught: there is no second one.",
        "lg_rule_ko": "Knocked out: it comes back after your next victory over a Pokémon League – in any region.",
        "lg_rule_fled": "Fled (you or the Pokémon): it is back after {days} day changes.",
        "lg_rule_lost": "If you lose the battle, nothing changes.",
        "lg_rule_roam": "Roaming Pokémon simply keep roaming until you catch them. After every League victory "
                        "they set off again if they are no longer on the move.",
        "lg_rule_enter": "Whether a Pokémon is there is decided when you enter the map. Leave and come back if "
                         "something should have changed.",
        "lg_rule_also": "The same rules apply to {lapras} in {unioncave} and the red {gyarados} at the {lake}.",
        "lg_where": "Place",
        "lg_level": "Level",
        "lg_sec_kanto": "Kanto",
        "lg_sec_johto": "Johto",
        "lg_sec_hoenn": "Hoenn",
        "lg_sec_none": "What does not exist",
        "lg_none_text": "Southern Island, Faraway Island and Navel Rock cannot be reached. The {eon}, the {map} "
                        "and the {mystic} are not handed out anywhere. Every legendary Pokémon exists exactly "
                        "once, at the places on this page.",
        "lg_free_1": "No condition: the Pokémon waits there as soon as you reach the place.",
        "lg_mewtwo_1": "Become Champion of Kanto. After that the guard clears the entrance of {ceruleancave}.",
        "lg_mewtwo_2": "{mon} waits in the basement of the cave.",
        "lg_mew_1": "No condition. On the lowest floor of {mtmoon} a passage leads into a small cave of its own. "
                    "{mon} waits there.",
        "lg_jirachi_1": "Travel to Hoenn once. You need the {hoennticket} for that: you receive it after your "
                        "first Johto title in Professor Oak's lab in {pallet}.",
        "lg_jirachi_2": "Go to the white rock on {route4} at night (7 p.m. to 6 a.m.) and touch it.",
        "lg_jirachi_3": "{mon} appears next to the rock. Talk to it.",
        "lg_jirachi_note": "You only have to touch the rock once. If {mon} comes back later, it stands at the "
                           "same spot again.",
        "lg_choice_title": "Lugia or Ho-Oh: the choice on Route 39",
        "lg_choice_1": "On {route39} a shadow flies over you and a man asks: {gold} or {silver}? {gold} makes "
                       "{hooh} the Pokémon of your story, {silver} makes it {lugia}. The choice cannot be changed.",
        "lg_choice_2": "You meet the chosen Pokémon in the story at Lv. {lv_story}. The other one comes later at "
                       "Lv. {lv_other} – both can be caught in every save file.",
        "lg_choice_3": "{silverwing} and {rainbowwing}: you receive one of them in the Radio Tower of "
                       "{goldenrod}. You do not need them for the encounters – what counts are the bells of the "
                       "Kimono Girls.",
        "lg_kimono_title": "The Kimono Girls at the Dance Theater",
        "lg_kimono_1": "Finish the trial in the {dragonsden}. When you enter {blackthorn} afterwards, Professor "
                       "Elm calls.",
        "lg_kimono_2": "Talk to Professor Elm in his lab in {newbark}. He gives you a {masterball} and sends you "
                       "to the Kimono Girls.",
        "lg_kimono_3": "Go to {ecruteak}. You meet your rival in front of the Dance Theater; then enter the "
                       "theater and talk to {zuki}.",
        "lg_kimono_4": "Defeat the five Kimono Girls one right after the other.",
        "lg_kimono_5": "As a reward you receive the {tidalbell} (if you chose {lugia}) or the {clearbell} "
                       "(for {hooh}).",
        "lg_kimono_note": "The Pokémon League of Johto only lets you in once you have eight Johto badges and "
                          "have met the Pokémon of your story.",
        "lg_lugia_a": "If you chose Lugia",
        "lg_lugia_a1": "Defeat the Kimono Girls and receive the {tidalbell}. The four {tentacruel} on {route41} "
                       "that block the way disappear.",
        "lg_lugia_a2": "Go to the deepest chamber of the {whirl}. The Kimono Girls dance and {mon} appears at "
                       "Lv. {lv_story}.",
        "lg_lugia_b": "If you chose Ho-Oh",
        "lg_lugia_b1": "Catch {hooh} – knocking it out is not enough.",
        "lg_lugia_b2": "Become Champion of Johto.",
        "lg_lugia_b3": "Enter {route41}: the {tentacruel} are gone now. {mon} waits in the deepest chamber of the "
                       "{whirl} at Lv. {lv_other}.",
        "lg_hooh_a": "If you chose Ho-Oh",
        "lg_hooh_a1": "Defeat the Kimono Girls and receive the {clearbell}.",
        "lg_hooh_a2": "Show the bell to the sage in the house in front of the {tintower} in {ecruteak}. He "
                      "clears the way.",
        "lg_hooh_a3": "Climb to the roof of the {tintower}. The Kimono Girls dance and {mon} appears at "
                      "Lv. {lv_story}.",
        "lg_hooh_b": "If you chose Lugia",
        "lg_hooh_b1": "Catch {lugia} – knocking it out is not enough.",
        "lg_hooh_b2": "Become Champion of Johto.",
        "lg_hooh_b3": "The sage also lets you into the {tintower} with the {tidalbell}. {mon} waits on the roof "
                      "at Lv. {lv_other}.",
        "lg_suicune_1": "Enter the {burned} in {ecruteak}. After the battle against your rival you fall into the "
                        "basement; the three legendary beasts run away there.",
        "lg_suicune_2": "Travel on to {olivine} and then to {cianwood}. There you see {mon} and battle {eusine}.",
        "lg_suicune_3": "Meet {mon} by the water on {route42}.",
        "lg_suicune_4": "Then go to the spot on {route36} where {sudowoodo} stood. {mon} runs off to the north "
                        "and {eusine} sends you to the {tintower}.",
        "lg_suicune_5": "Defeat the Kimono Girls: with their bell the sage lets you into the {tintower}.",
        "lg_suicune_6": "{mon} waits on the ground floor of the {tintower}.",
        "lg_beasts_1": "Enter the {burned} in {ecruteak}. After the battle against your rival you fall into the "
                       "basement; the three run away there.",
        "lg_beasts_2": "From now on {raikou} and {entei} roam the routes of Johto and keep changing routes. You "
                       "meet them by chance in tall grass.",
        "lg_beasts_note": "The Gym Leader of {ecruteak} only lets you into his Gym after that.",
        "lg_celebi_1": "Catch {raikou}, {entei} and {suicune}. A short time later Professor Elm calls you: he has sent Professor Oak's {gsball} to Kurt.",
        "lg_celebi_2": "Visit Kurt in {azalea} and talk to him. He examines the ball.",
        "lg_celebi_3": "Leave his house. Kurt follows you and gives you the {gsball}.",
        "lg_celebi_4": "Go to the shrine in {ilex} and place the ball inside. {mon} appears.",
        "lg_celebi_note1": "There is only one {gsball}: the one from Professor Oak that you take to Professor Elm at the start of Johto.",
        "lg_celebi_note2": "If you do not catch {mon}, it later waits at the shrine again without a ball.",
        "lg_gyarados_1": "The red {mon} swims in the middle of the {lake}. The first battle is part of the "
                         "story: afterwards you receive the {redscale}, however it ends.",
        "lg_gyarados_note": "It is always shiny. Mr. Pokémon on {route30} trades the {redscale} for an "
                            "{expshare}.",
        "lg_lapras_1": "No condition and no particular weekday: {mon} swims on the lowest floor of {unioncave}.",
        "lg_regi_title": "Regirock, Regice and Registeel",
        "lg_regi_1": "Go to the {sealed} and use {dig} in the first room in front of the inscription on the "
                     "back wall. A passage opens.",
        "lg_regi_2": "Put {wailord} first and {relicanth} last in your party and read the inscription in the "
                     "back room. The entrances of the three caves open.",
        "lg_regi_3": "{regirock} – {desert} on {route111}: read the inscription and use {rocksmash} at the spot "
                     "it describes.",
        "lg_regi_4": "{regice} – {island} on {route105}: read the inscription, then walk one full lap around "
                     "the cave along the wall.",
        "lg_regi_5": "{registeel} – {tomb} on {route120}: read the inscription and use {flash} at the spot it "
                     "describes.",
        "lg_weather_title": "Kyogre and Groudon",
        "lg_weather_1": "Become Champion of Hoenn.",
        "lg_weather_2": "Talk to the scientist upstairs in the Weather Institute on {route119}. He names a route "
                        "with unusual weather.",
        "lg_weather_3": "Heavy rain: {kyogre} waits in a cave under water. Look for the dive spot on the named "
                        "route and dive there.",
        "lg_weather_4": "Drought: {groudon} waits in a cave on land. Look for the new cave entrance on the "
                        "named route.",
        "lg_weather_note": "The weather moves on after 1,000 steps. Ask the scientist again then. If both are "
                           "still available, chance decides whose weather he reports.",
        "lg_rayquaza_1": "Play the Hoenn story until Wallace opens the {skypillar} for you, and wake {mon} at "
                         "the top.",
        "lg_rayquaza_2": "Watch {mon} end the battle in {sootopolis}.",
        "lg_rayquaza_3": "Then climb to the top of the {skypillar} again. {mon} waits there.",
        "lg_lati_title": "Latias and Latios",
        "lg_lati_1": "Become Champion of Hoenn. After that both roam the routes of Hoenn and keep changing "
                     "routes. You meet them by chance in tall grass or on the water.",
        "lg_deoxys_1": "Catch every Pokémon of the Hoenn Pokédex. Which ones count is listed under {completion}.",
        "lg_deoxys_2": "Talk to Professor Oak in his lab in {pallet}. He gives you the {aurora}.",
        "lg_deoxys_3": "With the ticket in your Bag the ships offer {birth} as a destination – at the harbors of "
                       "{olivine} and {vermilion} (from the Johto title) and of {slateport} and {lilycove} (from "
                       "the Hoenn title).",
        "lg_deoxys_4": "Solve the triangle puzzle on the island. {mon} appears.",
        "lg_deoxys_note": "The sign on the island gives you a {meteorite} if you have none.",
        "lg_completion": "Completing the Pokédex",
        "lg_sec_fixed": "Other fixed encounters",
        "lg_fixed_intro": "These Pokémon stand in the world as an obstacle or a trap. The rules above do not "
                          "apply to them.",
        "lg_col_mon": "Pokémon",
        "lg_col_how": "How the battle starts",
        "lg_snorlax": "You need the {flute} from Mr. Fuji in {lavender}; he is there after you free him in the "
                      "{tower}. Each {mon} exists only once: knocked out or fled, it is gone.",
        "lg_sudowoodo": "Water the tree with the {squirt}. You get it at the flower shop in {goldenrod} with "
                        "three Johto badges. If you flee, it stays; knocked out, it is gone.",
        "lg_kecleon": "Invisible on the path. Steven reveals the first one on the bridge; afterwards he gives "
                      "you the {devonscope} for the others. Each exists only once.",
        "lg_balls": "Looks like an item ball. Each exists only once.",
        "lg_rocket": "The three are part of the story in the hideout. If you flee, they stay.",
        "lg_marowak": "The ghost in the {tower}. Without the {scope} you cannot fight it; you find it in the "
                      "{rockethideout}.",
        "lg_tentacruel": "They block the way to the {whirl} and attack when you talk to them several times. They "
                         "cannot be caught.",
    },
}

PLACES = {
    "pallet": "PalletTown_ProfessorOaksLab_Frlg", "route4": "Route4_Frlg", "mtmoon": "MtMoon_Cave_Frlg",
    "ceruleancave": "CeruleanCave_B1F_Frlg", "route39": "Route39_hns", "ecruteak": "EcruteakCity_hns",
    "tintower": "TinTower_1F_hns", "whirl": "WhirlIslands_LugiaChamber_hns", "route41": "Route41_hns",
    "burned": "BurnedTower_B1F_hns", "olivine": "OlivineCity_hns", "cianwood": "CianwoodCity_hns",
    "route42": "Route42_hns", "route36": "Route36_hns", "newbark": "NewBarkTown_Lab_hns",
    "blackthorn": "BlackthornCity_hns", "dragonsden": "DragonsDen_Shrine_hns", "ruins": "RuinsOfAlph_B1F_hns",
    "azalea": "AzaleaTown_KurtsHouse_hns", "ilex": "IlexForest_hns", "lake": "LakeOfRage_hns",
    "unioncave": "UnionCave_B2F_hns", "sealed": "SealedChamber_InnerRoom", "desert": "DesertRuins",
    "island": "IslandCave", "tomb": "AncientTomb", "route119": "Route119", "route111": "Route111",
    "route105": "Route105", "route120": "Route120", "skypillar": "SkyPillar_Top", "sootopolis": "SootopolisCity",
    "birth": "BirthIsland_Exterior_hns", "lilycove": "LilycoveCity_Harbor", "slateport": "SlateportCity_Harbor",
    "vermilion": "VermilionCity_PortInside_Frlg", "goldenrod": "GoldenrodCity_FlowerShop_hns",
    "route30": "Route30_MrPokemonsHouse_hns", "lavender": "LavenderTown_VolunteerPokemonHouse_Frlg",
    "tower": "PokemonTower_6F_Frlg", "rockethideout": "RocketHideout_B4F_Frlg",
}
ITEMS = {
    "hoennticket": "ITEM_HOENN_TICKET", "aurora": "ITEM_AURORA_TICKET", "gsball": "ITEM_GS_BALL",
    "tidalbell": "ITEM_TIDAL_BELL", "clearbell": "ITEM_CLEAR_BELL", "silverwing": "ITEM_SILVER_WING",
    "rainbowwing": "ITEM_RAINBOW_WING", "masterball": "ITEM_MASTER_BALL", "redscale": "ITEM_RED_SCALE",
    "expshare": "ITEM_EXP_SHARE_SMALL", "meteorite": "ITEM_METEORITE", "eon": "ITEM_EON_TICKET",
    "map": "ITEM_OLD_SEA_MAP", "mystic": "ITEM_MYSTIC_TICKET", "flute": "ITEM_POKE_FLUTE",
    "squirt": "ITEM_SQUIRT_BOTTLE", "devonscope": "ITEM_DEVON_SCOPE", "scope": "ITEM_SILPH_SCOPE",
}
SPECIES = {
    "lugia": "SPECIES_LUGIA", "hooh": "SPECIES_HO_OH", "tentacruel": "SPECIES_TENTACRUEL",
    "sudowoodo": "SPECIES_SUDOWOODO", "raikou": "SPECIES_RAIKOU", "suicune": "SPECIES_SUICUNE", "entei": "SPECIES_ENTEI",
    "lapras": "SPECIES_LAPRAS", "gyarados": "SPECIES_GYARADOS", "wailord": "SPECIES_WAILORD",
    "relicanth": "SPECIES_RELICANTH", "regirock": "SPECIES_REGIROCK", "regice": "SPECIES_REGICE",
    "registeel": "SPECIES_REGISTEEL", "kyogre": "SPECIES_KYOGRE", "groudon": "SPECIES_GROUDON",
}
MOVES = {"dig": "MOVE_DIG", "rocksmash": "MOVE_ROCK_SMASH", "flash": "MOVE_FLASH"}

# Entry: (species consts, map folder of the encounter, script levels, step keys, note keys, sub-blocks)
# sub-blocks: [(title key, [step keys])] for an entry with two ways.
KANTO = (
    (("SPECIES_ARTICUNO",), "SeafoamIslands_B4F_Frlg", (40,), ("lg_free_1",), (), ()),
    (("SPECIES_ZAPDOS",), "PowerPlant_Frlg", (40,), ("lg_free_1",), (), ()),
    (("SPECIES_MOLTRES",), "VictoryRoad_4F_Frlg", (40,), ("lg_free_1",), (), ()),
    (("SPECIES_MEWTWO",), "CeruleanCave_B1F_Frlg", (50,), ("lg_mewtwo_1", "lg_mewtwo_2"), (), ()),
    (("SPECIES_MEW",), "MtMoon_Cave_Frlg", (40,), ("lg_mew_1",), (), ()),
    (("SPECIES_JIRACHI",), "Route4_Frlg", (80,), ("lg_jirachi_1", "lg_jirachi_2", "lg_jirachi_3"),
     ("lg_jirachi_note",), ()),
)
JOHTO = (
    (("SPECIES_LUGIA",), "WhirlIslands_LugiaChamber_hns", (78, 80), (), (),
     (("lg_lugia_a", ("lg_lugia_a1", "lg_lugia_a2")), ("lg_lugia_b", ("lg_lugia_b1", "lg_lugia_b2", "lg_lugia_b3")))),
    (("SPECIES_HO_OH",), "TinTower_RoofDay_hns", (78, 80), (), (),
     (("lg_hooh_a", ("lg_hooh_a1", "lg_hooh_a2", "lg_hooh_a3")), ("lg_hooh_b", ("lg_hooh_b1", "lg_hooh_b2", "lg_hooh_b3")))),
    (("SPECIES_SUICUNE",), "TinTower_1F_hns", (78,),
     ("lg_suicune_1", "lg_suicune_2", "lg_suicune_3", "lg_suicune_4", "lg_suicune_5", "lg_suicune_6"), (), ()),
    (("SPECIES_RAIKOU", "SPECIES_ENTEI"), None, (75,), ("lg_beasts_1", "lg_beasts_2"), ("lg_beasts_note",), ()),
    (("SPECIES_CELEBI",), "IlexForest_hns", (75,),
     ("lg_celebi_1", "lg_celebi_2", "lg_celebi_3", "lg_celebi_4"), ("lg_celebi_note1", "lg_celebi_note2"), ()),
    (("SPECIES_GYARADOS",), "LakeOfRage_hns", (55,), ("lg_gyarados_1",), ("lg_gyarados_note",), ()),
    (("SPECIES_LAPRAS",), "UnionCave_B2F_hns", (55,), ("lg_lapras_1",), (), ()),
)
HOENN = (
    (("SPECIES_REGIROCK", "SPECIES_REGICE", "SPECIES_REGISTEEL"), None, (100,),
     ("lg_regi_1", "lg_regi_2", "lg_regi_3", "lg_regi_4", "lg_regi_5"), (), ()),
    (("SPECIES_KYOGRE", "SPECIES_GROUDON"), None, (100,),
     ("lg_weather_1", "lg_weather_2", "lg_weather_3", "lg_weather_4"), ("lg_weather_note",), ()),
    (("SPECIES_RAYQUAZA",), "SkyPillar_Top", (100,), ("lg_rayquaza_1", "lg_rayquaza_2", "lg_rayquaza_3"), (), ()),
    (("SPECIES_LATIAS", "SPECIES_LATIOS"), None, (100,), ("lg_lati_1",), (), ()),
    (("SPECIES_DEOXYS",), "BirthIsland_Exterior_hns", (80,),
     ("lg_deoxys_1", "lg_deoxys_2", "lg_deoxys_3", "lg_deoxys_4"), ("lg_deoxys_note",), ()),
)
TITLES = {("SPECIES_REGIROCK", "SPECIES_REGICE", "SPECIES_REGISTEEL"): "lg_regi_title",
          ("SPECIES_KYOGRE", "SPECIES_GROUDON"): "lg_weather_title",
          ("SPECIES_LATIAS", "SPECIES_LATIOS"): "lg_lati_title"}
# Fixed encounters: (species, [map folders], text key)
FIXED = (
    ("SPECIES_SNORLAX", ("Route12_Frlg", "Route16_Frlg"), "lg_snorlax"),
    ("SPECIES_MAROWAK", ("PokemonTower_6F_Frlg",), "lg_marowak"),
    ("SPECIES_ELECTRODE", ("PowerPlant_Frlg",), "lg_balls"),
    ("SPECIES_SUDOWOODO", ("Route36_hns",), "lg_sudowoodo"),
    ("SPECIES_TENTACRUEL", ("Route41_hns",), "lg_tentacruel"),
    ("SPECIES_ELECTRODE", ("RocketHideout_B2F_hns",), "lg_rocket"),
    ("SPECIES_KECLEON", ("Route120", "Route119"), "lg_kecleon"),
    ("SPECIES_ELECTRODE", ("AquaHideout_B1F",), "lg_balls"),
    ("SPECIES_VOLTORB", ("NewMauville_Inside",), "lg_balls"),
)


def _levels(lang):
    """{(species const, map id or None): [levels]} of the reachable scripted encounters."""
    out = {}
    for sid, lst in PD.specials(lang).items():
        const = SP.by_id(sid, lang).const
        for e in lst:
            if e.kind in ("static", "static_shiny", "roamer"):
                out.setdefault((const, e.map_id), set()).update(e.levels)
                out.setdefault((const, None), set()).update(e.levels)
    return out


def _check(levels, consts, folder, want):
    """The level(s) the page states must be the script's."""
    for c in consts:
        c = SP.by_const(c, "de").const          # a species with forms answers with its base form
        mid = maps.by_dir(folder, "de").id if folder else None
        have = levels.get((c, mid))
        if folder == "VictoryRoad_4F_Frlg":       # the object is on 4F, its script in the 3F file
            have = levels.get((c, maps.by_dir("VictoryRoad_3F_Frlg", "de").id))
        if have is None or not set(want) <= have:
            raise ValueError("legendaries guide: %s at %s has levels %s, the page says %s"
                             % (c, folder, sorted(have or ()), list(want)))


def _vals(ctx):
    v = {k: U.place(ctx, d) for k, d in PLACES.items()}
    v.update({k: U.item(ctx, c) for k, c in ITEMS.items()})
    v.update({k: U.species(ctx, c) for k, c in SPECIES.items()})
    v.update({k: U.move(ctx, c) for k, c in MOVES.items()})
    v["zuki"] = U.trainer(ctx, "TRAINER_ZUKI_HNS")
    v["eusine"] = U.trainer(ctx, "TRAINER_EUSINE_HNS")
    v["gold"] = U.quote(ctx, F.c_string("src/strings.c", "gText_Gold", ctx.lang).title())
    v["silver"] = U.quote(ctx, F.c_string("src/strings.c", "gText_Silver", ctx.lang).title())
    v["completion"] = U.page(ctx, "guides/completion", ctx.t("lg_completion"))
    v["lv_story"], v["lv_other"] = 78, 80
    v["days"] = WS.legendary_rules()[0] if isinstance(WS.legendary_rules(), (tuple, list)) else WS.legendary_rules()
    return v


def _entry(ctx, vals, levels, entry):
    consts, folder, want, steps, notes, subs = entry
    _check(levels, consts, folder, want)
    sps = [SP.by_const(c, ctx.lang) for c in consts]
    v = dict(vals)
    v["mon"] = U.species(ctx, sps[0])
    title = ctx.t(TITLES[consts]) if consts in TITLES else sps[0].name
    meta = [(ctx.t("lg_level"), H.esc(" / ".join(ctx.level(x) for x in want)))]
    if folder:
        meta.insert(0, (ctx.t("lg_where"), U.place(ctx, folder)))
    body = H.kv(meta)
    if steps:
        body += H.steps([U.fmt(ctx, k, **v) for k in steps])
    for tkey, skeys in subs:
        body += "<p><strong>%s</strong></p>" % H.esc(ctx.t(tkey)) + H.steps([U.fmt(ctx, k, **v) for k in skeys])
    if notes:
        body += H.callout(ctx, "note", "".join("<p>%s</p>" % U.fmt(ctx, k, **v) for k in notes))
    icons = "".join(H.sprite(ctx, sp, scale=1) for sp in sps)
    return H.sub(title, H.split(body, '<div class="plates">%s</div>' % "".join(
        H.plate(H.sprite(ctx, sp, scale=1), U.species(ctx, sp)) for sp in sps)) if icons else body,
        id=sps[0].slug.replace("_", "-"))


def render(ctx):
    t = ctx.t
    ctx.begin(PATH)
    vals = _vals(ctx)
    levels = _levels(ctx.lang)
    F.require("src/legendaries_oj.c", r"#define FLEE_COOLDOWN_DAYS\s+%d\b" % vals["days"])
    out = []
    rules = [U.fmt(ctx, k, **vals) for k in ("lg_rule_caught", "lg_rule_ko", "lg_rule_fled", "lg_rule_lost",
                                              "lg_rule_roam", "lg_rule_enter", "lg_rule_also")]
    out.append(H.section(t("lg_sec_rules"), H.ul(rules), id="rules"))

    out.append(H.section(t("lg_sec_kanto"), "".join(_entry(ctx, vals, levels, e) for e in KANTO), id="kanto"))

    choice = H.sub(t("lg_choice_title"), H.prose("".join(
        "<p>%s</p>" % U.fmt(ctx, k, **vals) for k in ("lg_choice_1", "lg_choice_2", "lg_choice_3"))), id="choice")
    kimono = H.sub(t("lg_kimono_title"), H.steps([U.fmt(ctx, k, **vals) for k in (
        "lg_kimono_1", "lg_kimono_2", "lg_kimono_3", "lg_kimono_4", "lg_kimono_5")]) + H.callout(
            ctx, "note", "<p>%s</p>" % U.fmt(ctx, "lg_kimono_note", **vals)), id="kimono-girls")
    out.append(H.section(t("lg_sec_johto"), choice + kimono + "".join(
        _entry(ctx, vals, levels, e) for e in JOHTO), id="johto"))

    out.append(H.section(t("lg_sec_hoenn"), "".join(_entry(ctx, vals, levels, e) for e in HOENN), id="hoenn"))

    rows = []
    for const, folders, key in FIXED:
        sp = SP.by_const(const, ctx.lang)
        lv = set()
        for f in folders:
            mid = maps.by_dir(f, "de").id
            have = levels.get((const, mid))
            if const == "SPECIES_KECLEON" and have is None:      # the shared script of the invisible ones
                have = levels.get((const, None))
            if not have:
                raise ValueError("legendaries guide: no %s at %s" % (const, f))
            lv |= have
        v = dict(vals)
        v["mon"] = U.species(ctx, sp)
        places = []
        for f in folders:
            x = U.place(ctx, f)
            if x not in places:
                places.append(x)
        rows.append([U.species(ctx, sp, icon=True), ", ".join(places),
                     H.esc(" / ".join(ctx.level(x) for x in sorted(lv))), U.fmt(ctx, key, **v)])
    out.append(H.section(t("lg_sec_fixed"), H.table(
        [(t("lg_col_mon"), "main"), t("lg_where"), (t("lg_level"), "min"), t("lg_col_how")], rows),
        id="fixed", intro=H.esc(t("lg_fixed_intro"))))

    out.append(H.section(t("lg_sec_none"), H.prose("<p>%s</p>" % U.fmt(ctx, "lg_none_text", **vals)), id="none"))
    ctx.end("".join(out), lead=H.esc(t("lg_lead")))
