"""Section "Battles": battles/index, battles/kanto, battles/johto, battles/hoenn,
battles/rivals, battles/rematches, battles/trainers.

Mirrors (through the data layer, see the helper modules):
  * the trainer parties, classes and battle sites: gamedata.trainers, trainers_scriptdb;
  * levels and species as fielded: gamedata.levels (ScaleTrainerMonLevel/-Species);
  * the rematch stages and progress steps: gamedata.trainers_rematch;
  * badges and field permits: gamedata.hand_progress; obedience, field moves, prize
    money and rematch call rules: pages._battles_facts, pages._battles_rematch.

Helpers: _battles_data (battles and persons), _battles_facts (rules read from the C
sources), _battles_view (cards), _battles_gyms (region pages), _battles_story (rivals,
villain teams, multi battles), _battles_rematch (phone rematches), _battles_index
(overview and trainer index), _battles_order (story order of the places).

This module registers no trainer entities: the anchors of the trainers live on the
location pages (world module); the pages here link to them.
"""
from gamedata import trainers_scriptdb as SDB

from pages import _battles_data as D
from pages import _battles_gyms as G
from pages import _battles_index as I
from pages import _battles_rematch as R
from pages import _battles_story as S
from pages import _battles_view as V

STRINGS = {
    "de": {
        # ---- shared
        "phone": "PokéCom",
        "rival_name": "Dein Rivale",
        "region_other": "Sonstige",
        "word_and": "und",
        "word_or": "oder",
        "cond_after": "nach dem {region}-Titel",
        "cond_before": "vor dem {region}-Titel",
        "evolves_note": "Je nach Level: {names}",
        "bag": "Im Beutel: {items}",
        "band_title": "Level nach deinem Fortschritt",
        "col_progress": "Fortschritt",
        "col_team_levels": "Level des Teams",
        "default_moves_note": "Pokémon ohne feste Attacken beherrschen die vier Attacken, die sie auf ihrem "
                              "Level zuletzt erlernt haben.",
        "v_first": "Erster Kampf",
        "v_rematch": "Rückkampf",
        "v_rematch_n": "Rückkampf {n}",
        "v_rematch_range": "Rückkampf {a}–{b}",
        "v_rematch_after": "Nach dem {region}-Titel",
        "v_rematch_before": "Vor dem {region}-Titel",
        "v_order": "Als {n}. der drei Arenen",
        # ---- region pages
        "lead_kanto": "Die acht Arenen von Kanto, die Top Vier und der Champ auf dem Indigo-Plateau – mit "
                      "allen Teams, auch denen der Rückkämpfe nach deinen Titeln.",
        "lead_johto": "Die acht Arenen von Johto und die Liga, die das Indigo-Plateau übernimmt – mit allen "
                      "Teams des ersten Kampfs und der Rückkämpfe.",
        "lead_hoenn": "Die acht Arenen von Hoenn, die Top Vier und der Champ in Prachtpolis City – mit allen "
                      "Teams des ersten Kampfs und der Rückkämpfe.",
        "sec_overview": "Überblick",
        "overview_intro_kanto": "Die Arenen in der Reihenfolge der Orden. Das höchste Level gilt für den ersten Kampf.",
        "overview_intro_johto": "Die Arenen in der Reihenfolge der Orden. Das höchste Level gilt für den ersten Kampf.",
        "overview_intro_hoenn": "Die Arenen in der Reihenfolge der Orden. Das höchste Level gilt für den ersten Kampf.",
        "levels_note_kanto": "Beim ersten Kampf haben die Arenaleiter von Kanto feste Level. Nach deinem Kanto-Titel "
                             "treten sie mit neuen Teams zum Rückkampf an, deren Level sich nach deinem "
                             "Fortschritt richten: Das stärkste Pokémon liegt {lo} bis {hi} Level über dem, was "
                             "das Spiel für deinen Stand erwartet.",
        "levels_note_johto": "In Johto sind alle Level fest. Die Arenen {gyms} kannst du in beliebiger Reihenfolge angehen – wer später drankommt, tritt mit einem stärkeren Team an. Nach deinem Johto-Titel warten alle Leiter und die Liga mit neuen Teams, und jedes Pokémon gehorcht dir.",
        "levels_note_hoenn": "In Hoenn sind alle Level fest. Nach deinem Hoenn-Titel fordern dich die Arenaleiter nach und nach zu bis zu {n} Rückkämpfen, und die Liga tritt mit stärkeren Teams an.",
        "col_leader": "Arenaleiter",
        "col_ace": "Höchstes Level",
        "kv_badge": "Orden",
        "kv_badge_place": "Orden erhältst du",
        "kv_obey": "Gehorsam",
        "kv_field_kanto": "Außerhalb von Kämpfen (Kanto)",
        "kv_field_johto": "Außerhalb von Kämpfen (Johto)",
        "kv_field_hoenn": "Außerhalb von Kämpfen (Hoenn)",
        "rival_name_mid": "dein Rivale",
        "kv_tm": "Belohnung",
        "badge_n": "{n}. Orden von {region}",
        "unlock_obey": "Mit {n} Orden: getauschte Pokémon bis Lv. {lv}",
        "unlock_obey_1": "Mit einem Orden: getauschte Pokémon bis Lv. {lv}",
        "gym_title": "{n}. Arena: {name} ({place})",
        "order_0": "Dieses Team stellt sich dir, wenn du weder {a} noch {b} besiegt hast.",
        "order_1": "Dieses Team stellt sich dir, wenn du {a} oder {b} schon besiegt hast.",
        "order_2": "Dieses Team stellt sich dir, wenn du {a} und {b} schon besiegt hast.",
        "leader_band_note": "Die Level richten sich nach deinem Fortschritt ({when}): Das stärkste Pokémon liegt "
                            "{lo} bis {hi} Level über dem erwarteten Level, die anderen halten ihren Abstand dazu.",
        "special_note": "Erst nach dem Hoenn-Titel. Die Rückkämpfe werden nacheinander angeboten; jeder "
                        "Sieg schaltet das nächste Team frei.",
        "later_leader_title": "Später in dieser Arena: {name}",
        "later_leader": "Sobald du {n} Orden von Johto besitzt, hat die Liga von Johto das Indigo-Plateau "
                        "übernommen – und {name} leitet diese Arena.",
        "league_intro_kanto": "Die Liga von Kanto erwartet dich hier: {place}. Du trittst gegen alle {n} hintereinander an. Nach deinem Titel kannst du die Liga mit stärkeren Teams erneut herausfordern, bis die Liga von Johto das Plateau übernimmt.",
        "league_intro_johto": "Sobald du {badges} Orden von Johto besitzt, übernimmt die Liga von Johto das Plateau: {place}. Nach deinem Johto-Titel tritt sie mit stärkeren Teams an.",
        "league_intro_hoenn": "Die Liga von Hoenn erwartet dich hier: {place}. Nach deinem Hoenn-Titel tritt sie mit stärkeren Teams an.",
        "sec_e4": "Top Vier",
        "champ_title": "Champ: {name}",
        "champ_rival_intro": "Der Champ von Kanto ist dein Rivale. Sein Team hängt davon ab, welches "
                             "Starter-Pokémon er gewählt hat.",
        "rival_with": "Rivale mit {species}",
        "variant_n": "Variante {n}",
        # ---- index
        "lead_index": "{n} Trainer und {b} Kämpfe warten in Kanto, Johto und Hoenn auf dich. Hier findest du "
                      "alle Teams – von den Arenen über Rivalen und Schurken bis zum letzten Rückkampf.",
        "sec_regions": "Arenen und Liga",
        "regions_intro": "Jede Region hat acht Arenen und eine Liga. Du spielst sie in der Reihenfolge Kanto, "
                         "Johto, Hoenn.",
        "tile_region": "Acht Arenen von {leader} bis {last}, dann die Top Vier und der Champ.",
        "sec_more": "Weitere Kämpfe",
        "tile_rivals": "Alle Begegnungen mit deinen Rivalen, die Bosse und Vorstände von Team Rocket, Team "
                       "Aqua und Team Magma, besondere Gegner und Multikämpfe.",
        "tile_rematches": "So fordern dich {n} Trainer per PokéCom erneut heraus – mit allen Teams und der "
                          "Level-Tabelle.",
        "tile_trainers": "{n} Trainer mit {b} Kämpfen zum Durchsuchen – nach Region, Ort und Klasse.",
        "sec_levels": "So funktionieren Trainer-Level",
        "levels_intro": "Trainer haben feste Level, die nicht von deinem Team abhängen. Nur Rückkämpfe "
                        "orientieren sich an deinem Fortschritt.",
        "lv_kanto": "Kanto beginnt bei Lv. {lo}; der Champ führt beim ersten Titelkampf Lv. {hi}.",
        "lv_johto": "Johto schließt daran an: Die Trainer der Geschichte liegen zwischen Lv. {lo} und Lv. {hi}, "
                    "was danach kommt, reicht bis Lv. 100.",
        "lv_hoenn": "Hoenn ist das Finale: von Lv. {lo} bis Lv. {hi}.",
        "lv_evolve": "In Johto und Hoenn treten Trainer-Pokémon in der Entwicklungsstufe an, die zu ihrem Level "
                     "passt. Die Seiten zeigen immer das Pokémon, das wirklich im Kampf steht.",
        "lv_rematch": "Bei {page} liegt das stärkste Pokémon {lo} bis {hi} Level unter dem Level, das das "
                      "Spiel für deinen Fortschritt erwartet; bei den Rückkämpfen der Arenaleiter von Kanto "
                      "{llo} bis {lhi} Level darüber.",
        "link_rematches": "Rückkämpfen per PokéCom",
        "lv_more": "Alles über Level, Erfahrung und Gehorsam: {page}.",
        "col_span": "Level auf der Reise",
        "col_first_gym": "Erste Arena",
        "col_last_gym": "Achte Arena",
        "col_champ": "Champ",
        # ---- trainers
        "lead_trainers": "Alle Trainer des Spiels, je einmal pro Ort, an dem du sie triffst. Ein Klick führt zum Team auf der Seite des Ortes.",
        "facet_role": "Bosse", "role_leader": "Arenaleiter", "role_elite": "Top Vier", "role_champion": "Champ", "role_rival": "Rivalen",
        "trainers_placeholder": "Name, Klasse oder Ort",
        "facet_class": "Klasse",
        "col_class": "Klasse",
        "col_battles": "Kämpfe",
        "col_first": "Erster Kampf",
        "col_rematches": "Rückkampf-Teams",
        "sec_orphans": "Teams ohne eigene Ortsseite",
        "orphans_intro": "Diese Trainer kämpfen an Orten, die keine eigene Seite haben.",
        # ---- rematches
        "lead_rematches": "{n} Trainer melden sich nach dem ersten Kampf per PokéCom und fordern dich erneut "
                          "heraus – mit stärkeren Teams, deren Level mit deinem Fortschritt wachsen.",
        "sec_how": "So funktioniert es",
        "how_intro": "Das PokéCom bekommst du gleich zu Beginn von deiner Mutter.",
        "how_1": "Besiege einen Trainer, der Rückkämpfe anbietet. Seine Nummer wird automatisch im PokéCom "
                 "gespeichert.",
        "how_2": "Sammle {need} Orden in der Region des Trainers. Vorher fordert er dich nicht heraus – die "
                 "Orden einer anderen Region zählen für ihn nicht.",
        "how_3": "Danach meldet er sich von selbst. Wer einen Rückkampf will, ist in der Liste des PokéCom "
                 "markiert und wartet an seinem alten Platz.",
        "how_4": "Sprich ihn an, um zu kämpfen. Nach dem Kampf beginnt das Warten von vorn.",
        "sec_calls": "Wann sich ein Trainer meldet",
        "calls_intro": "Es gibt drei Wege, auf denen ein gespeicherter Trainer einen Rückkampf anmeldet:",
        "call_map": "Beim Betreten eines Gebiets: Jederzeit kann es passieren, dass dich dort ein gespeicherter Trainer herausfordert – höchstens einer pro Besuch, und nur, wenn dort nicht schon jemand auf dich wartet.",
        "call_route": "Anruf vor Ort: Läufst du durch das Gebiet eines gespeicherten Trainers, kann jederzeit einer der Trainer von dort anrufen und kämpfen wollen.",
        "call_random": "Anruf aus der Ferne: Im Freien und in Höhlen kann jederzeit jemand anrufen, mit {ability} an der Spitze deines Teams häufiger. Meist meldet sich jemand aus der Region, in der du gerade bist. Nicht jeder Anruf ist eine Herausforderung zum Rückkampf.",
        "sec_teams": "Welches Team antritt",
        "teams_p1": "Jeder Trainer hat bis zu vier Rückkampf-Teams. Du bekommst immer das erste, das du noch "
                    "nicht besiegt hast; hast du alle freigeschalteten besiegt, bleibt es beim letzten.",
        "teams_p2": "Die späteren Teams werden mit den Orden der Region des Trainers freigeschaltet. Mit dem "
                    "Titel der Region sind alle Teams offen. Ab wann ein Team möglich ist, steht in der Liste "
                    "unten bei jedem Team.",
        "teams_p3": "Die Pokémon entwickeln sich passend zu ihrem Level – auch in Kanto. Deshalb nennt die "
                    "Liste bei manchen Pokémon mehrere Stufen.",
        "sec_band": "Level nach deinem Fortschritt",
        "band_intro": "Rückkämpfe sollen dich fordern, ohne dich zu überrollen. Das Spiel kennt für jeden "
                      "Fortschritt ein erwartetes Level für dein stärkstes Pokémon.",
        "band_p1": "Das stärkste Pokémon eines Rückkampf-Teams liegt mindestens {hi} und höchstens {lo} Level unter diesem erwarteten Level (Spalte „PokéCom“). Liegt sein eigenes Level schon in diesem Bereich, bleibt es unverändert. Die anderen Pokémon behalten ihren Abstand zum stärksten.",
        "band_p2": "Dein Fortschritt zählt nur vorwärts: erst die Orden von Kanto, mit dem Kanto-Titel die "
                   "Orden von Johto, mit dem Johto-Titel die Orden von Hoenn. Dein eigenes Team spielt "
                   "keine Rolle.",
        "col_p": "Erwartet",
        "col_phone_ace": "PokéCom",
        "col_leader_ace": "Leiter",
        "sec_other": "Rückkämpfe ohne PokéCom",
        "other_intro": "Arenaleiter und Ligen haben eigene Regeln:",
        "other_kanto": "{page}: Nach dem Kanto-Titel kannst du jeden Arenaleiter in seiner Arena erneut herausfordern. Sein stärkstes Pokémon liegt {lo} bis {hi} Level über dem erwarteten Level (Spalte „Leiter“ der Tabelle oben). Nach dem Johto-Titel wechseln die Teams.",
        "other_johto": "{page}: Nach dem Johto-Titel treten die Arenaleiter und die Liga mit neuen Teams auf "
                       "festen Leveln an.",
        "other_hoenn": "{page}: Nach dem Hoenn-Titel will von Zeit zu Zeit ein Arenaleiter einen Rückkampf – "
                       "nach jedem {tb}. Trainerkampf und jedem {wb}. Kampf gegen ein wildes Pokémon meldet "
                       "sich mit {chance} % Wahrscheinlichkeit einer von ihnen. Die Teams haben feste Level.",
        "sec_list": "Alle Trainer mit Rückkampf",
        "list_intro": "{n} Trainer in drei Regionen. Zu jedem Team steht, ab wann es möglich ist, und die Spanne vom niedrigsten bis zum höchsten Level, das es über deinen ganzen weiteren Fortschritt erreichen kann. Die Pokémon jedes Teams siehst du beim Trainer auf der Seite seines Ortes – ein Klick auf den Namen führt dorthin.",
        "rematch_placeholder": "Name, Klasse oder Ort",
        "from_step": "ab {step}",
        # ---- rivals
        "lead_rivals": "Deine Rivalen begleiten dich durch alle drei Regionen, und in jeder stellt sich dir "
                       "eine Verbrecherbande in den Weg. Hier stehen alle Begegnungen in der Reihenfolge der "
                       "Geschichte.",
        "rival_title": "Rivale in {region}: {name}",
        "rival_title_kanto": "Dein Rivale in Kanto",
        "rival_title_johto": "Dein Rivale in Johto",
        "rival_intro_kanto": "Den Namen deines Rivalen in Kanto legst du selbst fest (Vorschlag: {default}). "
                             "Er wählt das Starter-Pokémon, das deinem überlegen ist.",
        "rival_intro_johto": "Auch dem Rivalen in Johto gibst du seinen Namen (Vorschlag: {default}); beim ersten Kampf heißt er noch „{first}“. Er stiehlt das Starter-Pokémon, das deinem überlegen ist.",
        "rival_places": "{n} Kämpfe an diesen Orten: {places}.",
        "rival_champ_note": "Der Titelkampf der Liga – das ganze Team mit Attacken steht unter {page}.",
        "battle_n": "Kampf {n}",
        "sec_villains": "Schurken-Teams",
        "villain_intro": "{n} Rüpel von {team} findest du in der {list}; hier stehen die Anführer.",
        "trainer_list": "Trainerliste",
        "sec_special": "Besondere Gegner",
        "special_intro": "Starke Einzelgegner abseits von Arenen und Liga.",
        "special_note_wally": "Nach deinem Sieg auf der Siegesstraße fordert er dich per PokéCom erneut heraus. Die Level sind fest.",
        "special_note_wally_title": "Dieses Team stellt er erst nach deinem Hoenn-Titel auf. Die Level sind fest.",
        "sec_multi": "Multikämpfe",
        "multi_intro": "In diesen Kämpfen steht dir ein Partner zur Seite.",
        "multi_title": "Mit {partner}: {place}",
        "multi_2v2": "{partner} kämpft an deiner Seite gegen {foes}. Jeder Gegner setzt höchstens {n} Pokémon "
                     "ein, du und dein Partner ebenfalls je drei. Ort: {place}.",
        "multi_2v1": "{partner} kämpft an deiner Seite gegen {foes}. Ort: {place}.",
        "multi_see": "Multikampf mit Partner, siehe unten.",
        "partner_chip": "Dein Partner",
        "call_option": "Stört dich das Klingeln? In den Optionen kannst du „{option}“ auf „{off}“ stellen. Dann ruft niemand mehr an; Herausforderungen beim Betreten eines Gebiets gibt es weiterhin.",
        "sub_gifts": "Geschenke am Telefon",
        "gifts_intro": "Diese Trainer aus Johto haben bei einem Anruf vor Ort in einem von {n} Fällen statt eines Rückkampfs ein Item für dich. Sprich sie danach an, um es abzuholen.",
        "col_gifts": "Mögliche Items",
        "first_battle_lv": "erster Kampf {level}",
        "band_p3": "Das Spiel führt dafür {n} Stufen. Ein Titel und „0 Orden“ der nächsten Region haben dasselbe erwartete Level und stehen hier in einer Zeile. Ein Trainer fordert dich erst ab {need} Orden seiner Region heraus, die Rückkämpfe der Arenaleiter von Kanto (Spalte „Leiter“) gibt es ab dem Kanto-Titel – davor bleiben die Spalten leer.",
        "tab_starters": "Du: {you} – Rivale: {rival}",
        "rival_intro_single": "{name} fordert dich in dieser Region immer wieder heraus.",
        "link_league_kanto": "Arenen & Liga: Kanto",
        "rival_variant": "{name} ({species})",
        "word_to": "bis",
    },
    "en": {
        # ---- shared
        "phone": "Pokégear",
        "rival_name": "Your rival",
        "region_other": "Other",
        "word_and": "and",
        "word_or": "or",
        "cond_after": "after the {region} title",
        "cond_before": "before the {region} title",
        "evolves_note": "Depending on level: {names}",
        "bag": "In the Bag: {items}",
        "band_title": "Levels by your progress",
        "col_progress": "Progress",
        "col_team_levels": "Team levels",
        "default_moves_note": "Pokémon without fixed moves know the four moves they learned last at their level.",
        "v_first": "First battle",
        "v_rematch": "Rematch",
        "v_rematch_n": "Rematch {n}",
        "v_rematch_range": "Rematch {a}–{b}",
        "v_rematch_after": "After the {region} title",
        "v_rematch_before": "Before the {region} title",
        "v_order": "As gym {n} of the three",
        # ---- region pages
        "lead_kanto": "The eight Gyms of Kanto, the Elite Four and the Champion at Indigo Plateau – with every "
                      "team, including the rematch teams after your titles.",
        "lead_johto": "The eight Gyms of Johto and the League that takes over Indigo Plateau – with every team "
                      "of the first battle and the rematches.",
        "lead_hoenn": "The eight Gyms of Hoenn, the Elite Four and the Champion in Ever Grande City – with every "
                      "team of the first battle and the rematches.",
        "sec_overview": "Overview",
        "overview_intro_kanto": "The Gyms in Badge order. The highest level is the one of the first battle.",
        "overview_intro_johto": "The Gyms in Badge order. The highest level is the one of the first battle.",
        "overview_intro_hoenn": "The Gyms in Badge order. The highest level is the one of the first battle.",
        "levels_note_kanto": "In the first battle the Kanto Gym Leaders have fixed levels. After your Kanto title "
                             "they return with new teams for a rematch whose levels follow your progress: the "
                             "strongest Pokémon is {lo} to {hi} levels above what the game expects at your stage.",
        "levels_note_johto": "All levels in Johto are fixed. You can take on Gyms {gyms} in any order – whoever comes later uses a stronger team. After your Johto title all Leaders and the League wait with new teams, and every Pokémon obeys you.",
        "levels_note_hoenn": "All levels in Hoenn are fixed. After your Hoenn title the Gym Leaders challenge you to up to {n} rematches one after another, and the League uses stronger teams.",
        "col_leader": "Gym Leader",
        "col_ace": "Highest level",
        "kv_badge": "Badge",
        "kv_badge_place": "You receive the Badge at",
        "kv_obey": "Obedience",
        "kv_field_kanto": "Outside of battle (Kanto)",
        "kv_field_johto": "Outside of battle (Johto)",
        "kv_field_hoenn": "Outside of battle (Hoenn)",
        "rival_name_mid": "your rival",
        "kv_tm": "Reward",
        "badge_n": "Badge {n} of {region}",
        "unlock_obey": "With {n} Badges: traded Pokémon up to Lv. {lv}",
        "unlock_obey_1": "With one Badge: traded Pokémon up to Lv. {lv}",
        "gym_title": "Gym {n}: {name} ({place})",
        "order_0": "You face this team if you have beaten neither {a} nor {b}.",
        "order_1": "You face this team if you have already beaten {a} or {b}.",
        "order_2": "You face this team if you have already beaten {a} and {b}.",
        "leader_band_note": "The levels follow your progress ({when}): the strongest Pokémon is {lo} to {hi} "
                            "levels above the expected level, the others keep their distance to it.",
        "special_note": "Only after the Hoenn title. The rematches are offered one after another; each win "
                        "unlocks the next team.",
        "later_leader_title": "Later in this Gym: {name}",
        "later_leader": "Once you own {n} Johto Badges, the Johto League has taken over Indigo Plateau – and "
                        "{name} runs this Gym.",
        "league_intro_kanto": "The Kanto League awaits you here: {place}. You face all {n} in a row. After your title you can challenge the League again with stronger teams until the Johto League takes over the Plateau.",
        "league_intro_johto": "Once you own {badges} Johto Badges, the Johto League takes over the Plateau: {place}. After your Johto title it uses stronger teams.",
        "league_intro_hoenn": "The Hoenn League awaits you here: {place}. After your Hoenn title it uses stronger teams.",
        "sec_e4": "Elite Four",
        "champ_title": "Champion: {name}",
        "champ_rival_intro": "The Champion of Kanto is your rival. His team depends on the starter Pokémon "
                             "he chose.",
        "rival_with": "Rival with {species}",
        "variant_n": "Variant {n}",
        # ---- index
        "lead_index": "{n} Trainers and {b} battles await you in Kanto, Johto and Hoenn. Here you find every "
                      "team – from the Gyms to rivals and villains to the last rematch.",
        "sec_regions": "Gyms and League",
        "regions_intro": "Every region has eight Gyms and a League. You play them in the order Kanto, Johto, "
                         "Hoenn.",
        "tile_region": "Eight Gyms from {leader} to {last}, then the Elite Four and the Champion.",
        "sec_more": "More battles",
        "tile_rivals": "Every encounter with your rivals, the bosses and admins of Team Rocket, Team Aqua and "
                       "Team Magma, special opponents and multi battles.",
        "tile_rematches": "How {n} Trainers challenge you again by phone – with every team and the level table.",
        "tile_trainers": "{n} Trainers with {b} battles to search – by region, place and class.",
        "sec_levels": "How Trainer levels work",
        "levels_intro": "Trainers have fixed levels that do not depend on your team. Only rematches follow "
                        "your progress.",
        "lv_kanto": "Kanto starts at Lv. {lo}; the Champion's strongest Pokémon is at Lv. {hi} in the first title match.",
        "lv_johto": "Johto continues from there: the Trainers of the story are between Lv. {lo} and Lv. {hi}, "
                    "what comes after goes up to Lv. 100.",
        "lv_hoenn": "Hoenn is the finale: from Lv. {lo} to Lv. {hi}.",
        "lv_evolve": "In Johto and Hoenn, Trainer Pokémon appear in the evolution stage that fits their level. "
                     "The pages always show the Pokémon that really enters the battle.",
        "lv_rematch": "In {page} the strongest Pokémon is {lo} to {hi} levels below the level the game "
                      "expects for your progress; in the rematches of the Kanto Gym Leaders {llo} to {lhi} "
                      "levels above it.",
        "link_rematches": "phone rematches",
        "lv_more": "Everything about levels, experience and obedience: {page}.",
        "col_span": "Levels on the journey",
        "col_first_gym": "First Gym",
        "col_last_gym": "Eighth Gym",
        "col_champ": "Champion",
        # ---- trainers
        "lead_trainers": "Every Trainer in the game, once for each place where you meet them. A click takes you to the team on the page of that place.",
        "facet_role": "Bosses", "role_leader": "Gym Leaders", "role_elite": "Elite Four", "role_champion": "Champions", "role_rival": "Rivals",
        "trainers_placeholder": "Name, class or place",
        "facet_class": "Class",
        "col_class": "Class",
        "col_battles": "Battles",
        "col_first": "First battle",
        "col_rematches": "Rematch teams",
        "sec_orphans": "Teams without a place page",
        "orphans_intro": "These Trainers battle in places that have no page of their own.",
        # ---- rematches
        "lead_rematches": "{n} Trainers call you after the first battle and challenge you again – with stronger "
                          "teams whose levels grow with your progress.",
        "sec_how": "How it works",
        "how_intro": "You get the Pokégear from your mother right at the start.",
        "how_1": "Defeat a Trainer who offers rematches. The number is saved in the Pokégear automatically.",
        "how_2": "Collect {need} Badges in the Trainer's region. Before that there is no challenge – the Badges "
                 "of another region do not count for this Trainer.",
        "how_3": "After that the Trainer gets in touch. Whoever wants a rematch is marked in the Pokégear's "
                 "list and waits at the old spot.",
        "how_4": "Talk to the Trainer to battle. After the battle the wait starts again.",
        "sec_calls": "When a Trainer gets in touch",
        "calls_intro": "A saved Trainer can announce a rematch in three ways:",
        "call_map": "When you enter an area: at any time a saved Trainer there may challenge you – at most one per visit, and only if nobody there is already waiting for you.",
        "call_route": "Call on the spot: while you walk through the area of a saved Trainer, one of the Trainers from there may call at any time and want to battle.",
        "call_random": "Call from afar: outdoors and in caves somebody may call at any time, more often with {ability} at the head of your party. Usually the caller is from the region you are in. Not every call is a challenge to a rematch.",
        "sec_teams": "Which team you face",
        "teams_p1": "Every Trainer has up to four rematch teams. You always get the first one you have not "
                    "beaten yet; once you have beaten all unlocked ones, the last one stays.",
        "teams_p2": "The later teams are unlocked by the Badges of the Trainer's region. With the region's "
                    "title every team is open. The list below tells for each team from when it is possible.",
        "teams_p3": "The Pokémon evolve to fit their level – in Kanto as well. That is why the list names "
                    "several stages for some Pokémon.",
        "sec_band": "Levels by your progress",
        "band_intro": "Rematches should challenge you without steamrolling you. For every stage of progress "
                      "the game knows an expected level for your strongest Pokémon.",
        "band_p1": "The strongest Pokémon of a rematch team is at least {hi} and at most {lo} levels below that expected level (column “Pokégear”). If its own level is already inside this range, it stays as it is. The other Pokémon keep their distance to the strongest one.",
        "band_p2": "Your progress only counts forward: first the Kanto Badges, with the Kanto title the Johto "
                   "Badges, with the Johto title the Hoenn Badges. Your own team does not matter.",
        "col_p": "Expected",
        "col_phone_ace": "Pokégear",
        "col_leader_ace": "Leaders",
        "sec_other": "Rematches without the phone",
        "other_intro": "Gym Leaders and Leagues follow their own rules:",
        "other_kanto": "{page}: after the Kanto title you can challenge every Gym Leader again in the Gym. The strongest Pokémon is {lo} to {hi} levels above the expected level (column “Leaders” of the table above). After the Johto title the teams change.",
        "other_johto": "{page}: after the Johto title the Gym Leaders and the League use new teams at fixed "
                       "levels.",
        "other_hoenn": "{page}: after the Hoenn title a Gym Leader wants a rematch from time to time – after "
                       "every {tb}th Trainer battle and every {wb}th battle against a wild Pokémon one of them "
                       "gets in touch with a {chance}% chance. The teams have fixed levels.",
        "sec_list": "All Trainers with rematches",
        "list_intro": "{n} Trainers in three regions. Each team shows from when it is possible and the range from the lowest to the highest level it can reach over all your further progress. The Pokémon of each team are listed with the Trainer on the page of their place – click the name to go there.",
        "rematch_placeholder": "Name, class or place",
        "from_step": "from {step}",
        # ---- rivals
        "lead_rivals": "Your rivals accompany you through all three regions, and in each of them a gang of "
                       "villains gets in your way. Here is every encounter in story order.",
        "rival_title": "Rival in {region}: {name}",
        "rival_title_kanto": "Your rival in Kanto",
        "rival_title_johto": "Your rival in Johto",
        "rival_intro_kanto": "You choose the name of your rival in Kanto yourself (suggestion: {default}). "
                             "He picks the starter Pokémon that beats yours.",
        "rival_intro_johto": "You name the rival in Johto as well (suggestion: {default}); in the first battle he is still called “{first}”. He steals the starter Pokémon that beats yours.",
        "rival_places": "{n} battles at these places: {places}.",
        "rival_champ_note": "The League's title match – the full team with moves is on {page}.",
        "battle_n": "Battle {n}",
        "sec_villains": "Villain teams",
        "villain_intro": "You find {n} Grunts of {team} in the {list}; the leaders are shown here.",
        "trainer_list": "Trainer list",
        "sec_special": "Special opponents",
        "special_intro": "Strong single opponents apart from Gyms and League.",
        "special_note_wally": "After your win on Victory Road he challenges you again by phone. The levels are fixed.",
        "special_note_wally_title": "He only uses this team after your Hoenn title. The levels are fixed.",
        "sec_multi": "Multi battles",
        "multi_intro": "In these battles a partner fights at your side.",
        "multi_title": "With {partner}: {place}",
        "multi_2v2": "{partner} fights at your side against {foes}. Each opponent uses at most {n} Pokémon, "
                     "you and your partner three each as well. Place: {place}.",
        "multi_2v1": "{partner} fights at your side against {foes}. Place: {place}.",
        "multi_see": "Multi battle with a partner, see below.",
        "partner_chip": "Your partner",
        "call_option": "Tired of the ringing? In the options you can set “{option}” to “{off}”. Then nobody calls any more; challenges on entering an area still happen.",
        "sub_gifts": "Gifts by phone",
        "gifts_intro": "In one of {n} cases these Trainers from Johto have an item for you instead of a rematch when they call on the spot. Talk to them afterwards to pick it up.",
        "col_gifts": "Possible items",
        "first_battle_lv": "first battle {level}",
        "band_p3": "The game keeps {n} stages for this. A title and “0 Badges” of the next region have the same expected level and share a row here. A Trainer only challenges you from {need} Badges of the Trainer's region on, and the rematches of the Kanto Gym Leaders (column “Leaders”) start with the Kanto title – before that the columns stay empty.",
        "tab_starters": "You: {you} – rival: {rival}",
        "rival_intro_single": "{name} challenges you again and again in this region.",
        "link_league_kanto": "Gyms & League: Kanto",
        "rival_variant": "{name} ({species})",
        "word_to": "to",
    },
}

PAGES = (I.TRAINERS,)


def register(ctx):
    for path in PAGES:
        ctx.add_page(path)


def render(ctx):
    I.render_trainers(ctx)
    for const, species in V.missing_species():
        ctx.todo("battles: %s fields %s, which this build does not contain (left out of the team)"
                 % (const, species))
    for sec in D.missing_order_mapsecs():
        ctx.warn("battles: map section %s has no place in the story order (pages/_battles_order.py)" % sec)
    for label in ("PalletTown_PlayersHouse_1F_Text_ObtainedPokeGear",):
        txt = SDB.script_text_clean(label, ctx.lang) or ""
        if ctx.t("phone").lower() not in txt.lower():
            ctx.warn("battles: the game no longer calls the phone %r (%s)" % (ctx.t("phone"), label))
