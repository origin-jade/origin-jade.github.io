# DATA_I18N – the data layer in German and English

Scope: `WT/tools/docs/gamedata/*` (WT = `<work>/<repo>`, commit `e160f672`).
German = the default build, English = `make GAME_LANG=ENGLISH` (`-DLANG_ENGLISH`).
Every statement below was checked against the source; where a built image was used as a
second witness it says so.

> Update: the repository now holds both languages. Species, moves, abilities, items, types,
> natures, trainer classes, trainer names and place names have English text in the source
> (`#if GERMAN ... #else`, `Name: DE_EN(de, en)` in the `.party` files, `name_en` in the map
> section list), and the loaders return it for `lang="en"`. Point 1 below, section 2 and the
> prize menu row of section 3 describe the state before that; `selftest.py` prints the
> current counts ("Zählung: woher die englischen Texte kommen").

## 0. The three things to know first

1. **The English build is English in its dialogue and most menus, but every name table is
   German.** Species names, categories, move names, ability names and descriptions, item
   names, type names, nature names, trainer classes, trainer names, place names, bag pocket
   names, berry names, Easy Chat words and almost the whole challenge and options menus have
   no English text in the source. The English build shows "Bisasam", "Tackle", "Notdünger",
   "Trank", "Alabastia", "Leiter Rocko". The data layer returns exactly that for `lang="en"`.
   An English site built from it therefore has English prose and labels around German names –
   that is what the English game looks like. Section 2 has the full list with counts.
2. **Nothing but text differs between the two builds**, with three small exceptions that the
   data layer does not read (clock format, one prize menu, the language id; section 3).
   Levels, tables, encounters, trainers, item locations, map data and all generated headers
   are identical. `selftest.py` checks this on every run.
3. **A defect of the old layer is fixed on the way:** texts that the tables reference by
   symbol (`.description = sFullHealDesc`) came out as the symbol name. That hit 127 items,
   48 moves and 37 species entries in German as well. They now resolve to the real text
   (and these shared strings are exactly the ones that have an English version).

## 1. API

### 1.1 Language argument

Every loader that returns text takes `lang="de" | "en"` as its last argument. `lang=None`
(the default everywhere) means the language of the process:

```python
import gamedata
gamedata.lang()            # "de"  (or $OJ_DOCS_LANG)
gamedata.set_lang("en")    # process default; returns the previous one
```

Existing calls without `lang` keep returning German. Results are cached per language; both
can be used side by side in one process (the current site build does that: `--lang` loop
with `abilities.all_abilities(ctx.lang)`).

Text objects carry two extra attributes:

* `obj.lang` – the build the object was read from.
* `obj.text_lang` – `{"name": "de"|"en", "description": ...}`: the language each text is
  really written in. `"de"` in an English-build object means the English build shows the
  German string (untranslated, or identical in both languages).

Numbers on those objects (stats, power, price, …) are equal in both languages.

### 1.2 Where each kind of name or text comes from

| What | Call | Source |
|---|---|---|
| Species name, category, Pokédex text | `species.by_const(c, lang)` → `.name .category .description`; also `all_species(lang)`, `by_id`, `by_slug`, `by_name`, `by_natdex`, `dex(kind, lang)`, `forms(id, lang)`, `evolves_from(id, lang)` | `gSpeciesInfo` (`src/pokemon.c`) |
| Form names | forms share the species name (`speciesName` of each form entry); there is no separate form-name text in `gSpeciesInfo` – not determinable beyond that | same |
| Gender line | `species.gender(ratio)` → `("mixed", 12.1)` (facts) / `species.gender_text(ratio, lang)` (site wording) | – |
| Move name, description | `moves.by_const(c, lang)`; `all_moves(lang)`, `by_id`, `by_name`, `learners(id, lang)` | `gMovesInfo` (`src/move.c`) |
| Ability name, description | `abilities.by_const(c, lang)`; `all_abilities(lang)`, `holders(id, lang)` | `gAbilitiesInfo` |
| Item name, description | `items.by_const(c, lang)`; `all_items(lang)`, `by_tm(kind, n, lang)` | `gItemsInfo` (`src/item.c`) |
| Bag pocket names | `items.pockets(lang)`, `items.pocket_name("POCKET_MEDICINE", lang)`, `item.pocket_name` | `gPocketNamesStringsTable` (`src/strings.c`) |
| Type names | `typeinfo.by_const(c, lang)`, `all_types(lang)`, `battle_types(lang)` | `gTypesInfo` |
| Nature names | `natures.all_natures(lang)`, `by_const`, `by_id`, `by_party_name("Adamant", lang)`; `trainers.nature_name(mon, lang)` | `gNaturesInfo` (new module `natures.py`) |
| Egg group, growth rate, catch class, dex titles, any stats-screen label | `dex_texts.egg_group(c, lang)`, `.growth(c, lang)`, `.catch_class(rate, lang)`, `.dex_title(kind, lang)`, `.string(sym, path, lang)`, `.label(sym, lang)`, `.no_evolution(name, lang)` | `src/pokedex_plus_hgss.c`, `src/strings.c` |
| Trainer class names | `trainers.class_name(c, lang)`, `trainers.classes(lang)`, `tr.class_name` | `gTrainerClasses` (`src/battle_main.c`) |
| Trainer names, teams | `trainers.by_const(c, lang)`, `all_trainers(lang)`, `partners(lang)` | `.party` files |
| Place names | `maps.by_id(id, lang).display`, `maps.mapsec_name(mapsec, lang)`, `all_maps(active_only, lang)`, `by_dir`, `by_group_num` | `region_map_sections.json`; `DYNAMIC_PLACES` |
| Floor labels | `wild_maps.floor_name("1F", lang)` | `gText_1F …` (`src/strings.c`) |
| Any named C string | `tu.cstring(path, symbol, lang)` (raw) / `hand_facts.c_string(path, symbol, lang)` (one clean line) | preprocessed TU |
| Any script text | `trainers_scriptdb.script_text(label, lang)` (raw) / `script_text_clean(label, lang)` / `hand_facts.inc_string(file, label, lang)` | event scripts, `#if GERMAN` resolved |
| Option / challenge menus | `hand_menus.challenge_tabs(lang)`, `option_tabs(lang)`, `dex_options.option(c, lang)`, `wild_shiny.option(c, lang)` | `src/challenge_menu.c`, `src/option_menu.c` |
| Pokéblock words | `hand_pokeblocks.flavors(lang)`, `colors(lang)`, `natures(lang)`, `berries(lang)` | `src/strings.c`, `src/pokeblock.c` |
| Breeding texts | `hand_breeding.odd_egg(lang)`, `compat_texts(lang)`, `daycares(lang)`, `incense_babies(lang)`, `special_moves(lang)`, `items_with_hold_effect(c, lang)` | `src/daycare.c`, `src/easy_chat.c` |
| Route facts with names | `hand_progress.badges(region, lang)`, `permit_sites(region, lang)`, `kanto_to_johto(lang)`, `johto_to_hoenn(lang)`, `hoenn_end(lang)` | map scripts |
| Dex checks | `hand_completion.dex_required(kind, lang)`, `dex_skipped(kind, lang)` | `src/pokedex.c` |
| In-game trades | `wild_statics.entries(lang)` (`trade["nickname"]`, `trade["ot_name"]`) | `sIngameTrades` |
| Move relearner / deleter places | `dex_relearner.places(kind, lang)`, `place_maps(kind)` | map scripts |
| Rematch progress wording | `trainers_rematch.step_fact(step)` (facts) / `step_label(step, lang)`, `steps_label(steps, lang)` (site wording) | – |

Low-level additions in `tu.py`: `tu.load(path, extra, lang)`, `tu.cpp(..., lang=)`,
`TU.strings()` (all named strings of a TU), `TU.text_field(entry, key)` / `TU.text_value(v)`
(literal or symbol → text), `TU.literals()`, `tu.written_in(path, s, lang)`,
`tu.clean(path, s, lang)`, `tu.nontext_diff(path)`, `tu.LOADED`.
`trainers_scriptdb`: `text_db(lang)`, `nontext_diff()`.

### 1.3 Real outputs

```text
species.by_const("SPECIES_BULBASAUR", lang)
  de  name 'Bisasam'  category 'Samen'  description 'Bisasam macht gern einmal ein Nickerchen im Sonnenschein. …'
      types ['Pflanze', 'Gift']  abilities ['Notdünger', 'Chlorophyll']
      egg groups ['Monster', 'Pflanze']  growth 'Mittel-Langsam'  catch class 'Sehr schwer'  gender '12,1 % weiblich'
  en  name 'Bisasam'  category 'Samen'  description (the same German text)   text_lang all "de"
      types ['Pflanze', 'Gift']  abilities ['Notdünger', 'Chlorophyll']
      egg groups ['MONSTER', 'GRASS']  growth 'MED. SLOW'  catch class 'VERY HARD'  gender '12.1% female'

moves.by_const("MOVE_TACKLE", lang)          Normal, physical, 40 / 100 / 35 in both
  de  'Tackle'  'Trifft den Gegner mit vollem Körpereinsatz.'
  en  'Tackle'  'Trifft den Gegner mit vollem Körpereinsatz.'
moves.by_const("MOVE_MEGA_DRAIN", lang)      (one of the 48 moves with an English description)
  de  'Megasauger'  'Saugt dem Ziel die Hälfte des Schadens als KP ab.'
  en  'Megasauger'  'Attack that absorbs half the damage inflicted.'      text_lang {'name': 'de', 'description': 'en'}

abilities.by_const("ABILITY_OVERGROW", lang)
  de  'Notdünger'  'Erhöht Pfl.-Att. i. d. Not.'
  en  'Notdünger'  'Erhöht Pfl.-Att. i. d. Not.'

items.by_const("ITEM_POTION", lang)          price 200, POCKET_MEDICINE in both
  de  'Trank'  'Füllt die KP eines Pokémon um 20 Punkte auf.'  pocket_name 'Medizin'
  en  'Trank'  'Füllt die KP eines Pokémon um 20 Punkte auf.'  pocket_name 'Medizin'
items.by_const("ITEM_FULL_HEAL", lang)
  de  'Hyperheiler'  'Beseitigt alle Statusprobleme eines Pokémon.'
  en  'Hyperheiler'  'Heals all the status problems of one Pokémon.'

maps.by_id("MAP_ROUTE1", lang).display            de 'Route 1'      en 'Route 1'
maps.mapsec_name("MAPSEC_PALLET_TOWN", lang)       de 'Alabastia'    en 'Alabastia'
maps.by_id("MAP_SS_TIDAL_CORRIDOR", lang).display  de 'MS Tide'      en 'S.S. TIDAL'
maps.by_id("MAP_CONTEST_HALL_HNS", lang).display   de 'Wettbewerbshalle'  en 'CONTEST HALL'

trainers.by_const("TRAINER_LEADER_BROCK", lang)    de 'Leiter' 'Rocko'   en 'Leiter' 'Rocko'   (TRAINER_CLASS_LEADER_FRLG)
trainers.by_const("TRAINER_FALKNER_1_HNS", lang)   de 'Leiter' 'Falk'    en 'Leiter' 'Falk'    (TRAINER_CLASS_LEADER_HNS)
trainers.class_name("TRAINER_CLASS_BUG_CATCHER", lang)   de 'Käfersammler'   en 'Käfersammler'
trainers.class_name("TRAINER_CLASS_YOUNGSTER", lang)     de 'Teenager'       en 'Teenager'

typeinfo.battle_types(lang)   both: Normal Kampf Flug Gift Boden Gestein Käfer Geist Stahl Feuer Wasser Pflanze Elektro Psycho Eis Drache Unlicht Fee
natures.all_natures(lang)     both: Robust, Solo, Mutig, Hart, Frech, …
items.pockets(lang)           both: Items, Medizin, Pokébälle, TMs & VMs, Beeren, Basis Items
dex_texts.dex_title           de 'Nationaler Dex' / 'Johto Dex'     en 'NATIONAL DEX' / 'HOENN DEX'
wild_maps.floor_name          de '1F'→'EG', 'B1F'→'U1S'             en '1F', 'B1F'
hand_pokeblocks.flavors       de scharf trocken süß bitter sauer    en spicy dry sweet bitter sour
hand_facts.c_string("src/strings.c", "gText_ShopBuy", lang)         de 'Kaufen'   en 'BUY'
trainers_scriptdb.script_text_clean("Common_Text_ObedienceLevel40", lang)
  de  'Mit sechs Orden gehorchen dir getauschte Pokémon bis Level 40!'
  en  'With six BADGES, traded POKéMON up to Lv. 40 will obey you!'
hand_progress.kanto_to_johto("en")
  {'oak_lab': 'Alabastia', 'gs_ball': 'GS-Ball', 'gate': 'Siegesstraße', 'elm_town': 'Neuborkia', …,
   'gate_oak': 'Hold it! PROF. OAK called here. He wants to see you at his lab in PALLET TOWN before you go on to JOHTO.'}
```

The last example shows the mix the English player really sees: the dialogue says
"PALLET TOWN", the map and the Town Map say "Alabastia".

### 1.4 Text helpers (`gamedata/text.py`)

* `text.clean(s, lang="de")` – `lang` is the language the *string* is written in.
  * German: line-end hyphen dropped before a lower-case letter (`bestimm-\nten` → `bestimmten`),
    kept before a capital or digit (`Feuer-\nAttacke` → `Feuer-Attacke`), kept with a space
    before `und/oder/bis/sowie/u.` (`Dies-\nund` → `Dies- und`). Unchanged.
  * English: the game never splits an English word; in all English strings of the C sources a
    line-end hyphen is a compound hyphen (`Psychic-\ntype`, `sea-\ndwelling`,
    `gray-\ncolored`, `seafloor-\ndwelling`, `umbrella-\nshaped`), so the hyphen is always
    kept and the lines are joined without a space.
* `text.clean_as(s, s_de, lang)` / `text.written_in(s, s_de, lang)` – because the English
  build carries German strings, the rule is chosen per string: a string of the English build
  that equals the German build's string is treated as German. All loaders do this
  (`hand_facts.clean_pair`, `tu.clean` are the same idea for strings without a table slot).
* Raw glyph codes are resolved through `charmap.txt`: `CATCH{0x5B}` → `CATCH%`.
* Placeholders are the same for both languages, because the font is: `{POKEBLOCK}` is drawn
  as "POKéRIEGEL" in the English build too (glyphs 0x55–0x59 of `graphics/fonts/latin_normal.png`),
  so the English build's block names read "RED Pokériegel".

## 2. What the English build shows in German anyway

Counts are entries of the build (`text_lang`), confirmed for a sample by byte search in the
two built images under `docs2/oracle/de|en` ("Bisasam", "Notdünger", "Trank", "Alabastia",
"Rocko", "Käfersammler" occur in the English image; "BULBASAUR", "Overgrow", "POTION",
"PALLET TOWN" as a name table entry do not).

| Text | Entries | English in the English build | Why |
|---|---|---|---|
| Species names | 474 | 0 | `species_info/*.h` has no language branch |
| Species categories | 474 | 0 | same |
| Pokédex texts | 474 | 40 (all forms of Pichu, Pikachu, Evoli, Icognito) | only `shared_dex_text.h` has `#if GERMAN` |
| Move names | 934 | 0 | `moves_info.h`: names not branched |
| Move descriptions | 934 | 48 (the shared description strings, e.g. Megasauger, Schutzschild, Kehrtwende) | 24 `#if GERMAN` blocks for shared strings only |
| Ability names / descriptions | 310 / 310 | 0 / 0 | `abilities.h` has no branch |
| Item names | 903 | 0 | |
| Item descriptions | 903 | 117 (the shared strings: Hyperheiler, Top-Beleber, feathers, fossils, …) | 35 `#if GERMAN` blocks |
| Type names | 21 | 0 | `types_info.h` |
| Nature names | 25 | 0 | `gNaturesInfo` |
| Trainer class names | 172 | 0 | `gTrainerClasses` |
| Trainer names, teams | 2134 trainers | – (one name per trainer) | `.party` files contain no preprocessor line at all; their cpp output is byte-identical for both flag sets |
| Place names (map sections) | 236 | 0 | `region_map_sections.json` has one `name` per section; the generated `region_map_entries.h` is identical |
| Bag pocket names | 6 | 0 | `gPocketNamesStringsTable` |
| Berry names, Easy Chat words (Odd Egg answers) | all | 0 | `src/berry.c`, `src/easy_chat.c`: no English literal at all |
| Challenge menu (new game / PC) | 6 tabs, 58 options | descriptions of 3 options (Teamlimit, Spieler-EVs, Ein Typ); every option name, choice name and all other descriptions are German | 8 branches |
| Options menu | 3 tabs, 23 options | descriptions of 2 options (Text-Ges., Einheiten); names and choices German | 2 branches |
| In-game trades | 18 used by scripts (25 table rows) | 1 nickname ("Beißer" → "Rusty"); OT names all German | `src/data/trade.h` |
| Pokédex screen labels (egg groups, growth, catch class, …) | 65 `sText_Stats_*` | translated (upper case: "MONSTER", "MED. SLOW", "VERY HARD") | 68 branches |
| `src/strings.c` | 1092 literals | 971 translated | 1101 branches |
| Battle messages (`src/battle_message.c`) | 875 literals | 146 translated, 733 shared (many are placeholders only) | 156 branches |
| Script texts (dialogue, signs) | 16689 labels | 15996 translated; 693 identical, of which 148 are clearly German (103 Fame Checker texts, a few Johto NPCs), the rest are debug/retired-map texts or the same in both | `#if GERMAN … #else … #endif` per text |

Consequences for pages:

* An English page that says "Bulbasaur" would not match the English game. The source has no
  English names; the only English-looking handle is the constant (`sp.slug` = "bulbasaur",
  `SPECIES_BULBASAUR`), which is an internal name and not game text. Whether the English site
  adds such a helper name for search is an owner decision; the data layer does not invent one.
* English dialogue still uses the English names of the original games in capitals
  ("PALLET TOWN", "CLEFAIRY", "S.S. TIDAL", "GYM LEADER"). Quoting dialogue next to table
  names will show both.
* The regional dex title is "HOENN DEX" in the English build where the German build says
  "Johto Dex" (`gText_DexHoennTitle`).

## 3. Differences between the builds that are not text

Method: (a) all 395 `src/*.c` preprocessed with the Makefile flags, once without and once
with `-DLANG_ENGLISH`; string literals removed, the rest compared token by token.
(b) `data/event_scripts.s` with every include, read once with the German and once with the
English branches (`trainers_scriptdb.text_db`), compared without `.string`/`.braille` lines.
(c) grep for `LANG_ENGLISH`, `GAME_LANG`, `GERMAN`, `ENGLISH` over the whole tree.
(d) the generated headers of the German worktree against those of the worktree that was
built in English (`<work>/wt_oracle`). (e) symbol sizes of the two built images.

Result of (a): 322 units identical, 53 differ in string literals only, 18 differ only
through `GAME_LANGUAGE`, and two units have real differences (rows 2 and 3).

| # | Where | German build | English build | Player-visible effect |
|---|---|---|---|---|
| 1 | `include/constants/global.h` `GAME_LANGUAGE` (used in 18 units: `pokemon.c`, `daycare.c`, `egg_hatch.c`, `mail.c`, `trade.c`, `tv.c`, `contest.c`, `secret_base.c`, `record_mixing.c`, `rom_header_gf.c`, …) | `LANGUAGE_GERMAN` (5) | `LANGUAGE_ENGLISH` (2) | Language id stored on every Pokémon, egg, mail and secret base. A Pokémon from the other build counts as foreign: the Name Rater treats it as not the player's (`MonOTNameNotPlayer`), and an evolution does not update its default name (`EvolutionRenameMon`). Battle Frontier apprentice names are picked by this id (`GetApprenticeNameInLanguage`). No level, rate or availability depends on it. |
| 2 | `src/start_menu.c` `ShowTimeWindow`, `sWindowTemplate_StartClock` | 24-hour clock, window width 12 | 12-hour clock with AM/PM, window width 13 | Clock in the start menu only. |
| 3 | `src/data/script_menu.h` `sMultichoiceList_GameCornerPokemonPrizes` (menu `MULTI_GAME_CORNER_POKEMON_PRIZES`, Celadon Game Corner prize room) | 8 Pokémon + "Nein danke": Abra 180, Piepi 500, Dratini 2.800, Sichlor 5.500, Porygon 9.999, Porenta 1.500, Schlurp 1.800, Pantimos 2.000 | 5 Pokémon + "NO THANKS": ABRA 120, CLEFAIRY 750, PINSIR 2,500, DRATINI 4,600, PORYGON 6,500 | The script (`CeladonCity_GameCorner_PrizeRoom_Frlg/scripts.inc`, identical in both builds) maps menu positions 0–7 to Abra 180, Piepi 500, Dratini 2800, Sichlor 5500, Porygon 9999, Porenta 1500, Schlurp 1800, Pantimos 2000 and position 8 to "leave". The German menu matches it. In the English build the menu text is stale: position 2 is labelled PINSIR 2,500 but gives Dratini for 2800, position 3 is labelled DRATINI 4,600 but gives Sichlor for 5500, position 4 says 6,500 but costs 9999, the "NO THANKS" entry (position 5) opens the Porenta purchase, and Schlurp and Pantimos cannot be selected at all (B still leaves). The data layer reads the script, so `wild_statics` shows the German-build truth for both languages; for English this needs a note or a fix in the game. |

Everything else:

* (b) Scripts: 37840 labels in both; every instruction outside `.string`/`.braille` is
  identical (`trainers_scriptdb.nontext_diff() == []`). Language switches exist in 863 map
  script files, 44 `data/scripts/*.inc`, 39 `data/text/*.inc` and `data/event_scripts.s` –
  all of them around `.string` lines.
* (c) Classification of every use:
  * `Makefile:133-137` `GAME_LANG ?= GERMAN`, `LANGFLAG := -DLANG_ENGLISH` → goes into
    `CPPFLAGS`, which is used for C files, for `.s`/`.inc` (through cpp), for map data and
    for the `.party` files (`trainer_rules.mk`). `Makefile:470-476` "ENGLISH" is an argument
    of the RAM-script tool, unrelated.
  * `include/constants/global.h:82-90` defines `GERMAN`, `ENGLISH`, `GAME_LANGUAGE`.
  * C sources and headers: `#if GERMAN` in 51 `src/*.c` and in `src/data/` (`moves_info.h` 24,
    `items.h` 35, `species_info/shared_dex_text.h` 46, `script_menu.h` 27, `trade.h` 15,
    `union_room.h`, `party_menu.h`, `help_window.h`, `lilycove_lady.h`,
    `decoration/description.h`, `text/*.h`) – all text, except the three rows above.
  * `tools/check_game_text.py`, `tools/check_text_width.py`, `tools/check_save_safety.py`
    mention the switch in their own preprocessing; no build effect.
  * No `.party`, `.json`, layout, tileset or graphics file mentions a language; no `INCBIN`
    path differs (no language-specific graphics).
* (d) Identical in both worktrees: `wild_encounters.h`, `trainers.h`, `trainers_frlg.h`,
  `trainers_hns.h`, `battle_partners.h`, `region_map_entries.h`, `region_map_sections.h`,
  `map_groups.h`, `layouts.h`, `map_event_ids.h`, both `heal_locations.h`,
  `map_group_count.h`, `teachable_learnsets.h`, `tutor_moves.h`, `script_commands.h`.
* (e) Same 90846 symbols in both images. 32 functions differ in size: `ShowTimeWindow`
  (row 2), functions that use `GAME_LANGUAGE` (row 1) and functions whose code embeds string
  lengths or text layout; none of them has a non-string source difference.

Guard: `selftest.py` runs `tu.nontext_diff` on every TU the data layer loads (32) and
`trainers_scriptdb.nontext_diff()`. If a later commit adds a real difference to one of them,
the test fails instead of the English site silently showing German-build numbers.
Loaders that return numbers only read one TU and are not keyed by language.

## 4. Site wording that lives in the data layer (for the page authors)

The data layer holds almost no prose; the German sentences of the first site are in the
retired page modules (`tools/docs/pages_v1/`, 418 German string literals: `faq.py` 47,
`breeding.py` 37, `_common_v1/strings_de.py` 36, `features.py` 34, `pokeblocks.py` 26,
`index.py` 22, `trainers.py` 22, `pokedex.py` 19, `walkthrough.py` 19, `statics.py` 17,
`download.py` 17, `shinies.py` 16, `items.py` 15, `completion.py` 14, `moves.py` 14,
`_statics_notes.py` 13, `encounters.py` 11, `abilities.py` 10, `credits.py` 10,
`_pokedex_evo.py` 10, 9 more in three files). Those need both languages when the pages are rewritten.

Literals in `gamedata/` that can reach the reader:

| File:line | Literal | Status |
|---|---|---|
| `species.py:358-363` `GENDER_TEXT` | "Geschlechtslos", "100 % weiblich", "100 % männlich", "%s %% weiblich" | **Changed:** `species.gender(ratio)` now returns the fact `(kind, female percent)`; `gender_text(ratio, lang)` has German (unchanged) and English wording ("Genderless", "100% female", "12.5% female"). English wording is a proposal. |
| `trainers_rematch.py:121-136` `STRINGS_DE`, `STRINGS_EN`, `STRINGS` | "{region}: {n} Orden", "{region}: 1 Orden", "{region}-Titel", "{a} bis {b}", "ab {a}" | **Changed:** `step_fact(step)` returns `(region, badges, title)`; `step_label(step, lang)` / `steps_label(steps, lang)` have both languages (English: "{region}: {n} badges", "{region} title", "{a} to {b}", "from {a}" – proposal). The old call form `step_label(step, STRINGS_DE)` still works. |
| `hand_facts.py:39` `DPAD_NAME` | "Steuerkreuz" (word for the D-pad picture glyph) | **Changed:** per language, English "D-Pad" (proposal; the game shows a picture). |
| `hand_facts.py:41-45` `GLYPHS` | "A", "B", "L", "R", "START", "SELECT", arrows | language-neutral |
| `hand_facts.py:76` `gen()` | "Gen %d" | same in both languages |
| `maps.py:61,119,122,128`, `levels.py:204` | region key "Sonder" (also "Kanto", "Johto", "Hoenn", "Alola", "Hisui") | **Not changed** (other code compares these strings). Documented as keys (`maps.REGION_KEYS`); pages must map "Sonder" to their own label ("Sonstige" / "Other") and must not print it. |
| `maps.py:55-58` `DYNAMIC_PLACES` | "MS Tide", "Wettbewerbshalle" | **Changed:** now `(prefix, script text label, {"de": …, "en": …})` with the English counterparts "S.S. TIDAL" and "CONTEST HALL" quoted from the English branch of the same dialogue (`SSTidalCorridor_Text_BrineyWelcomeAboard`, `SlateportCity_Text_ScottLeavesContestHall`); selftest checks each name against the script text of its build. The old "Wettbewerbshalle" needle sat in a branch the jade build does not compile; the new label is in the build. `maps.dynamic_place(dir, lang)` returns `(name, label, prefix)`. |
| `text.py:34-40` `PLACEHOLDERS` | "Pokémon", "Pokériegel", "Lv.", "PK" | same for both languages (font glyphs, see 1.4) |
| `moves.py:26` `CATEGORY` | "physical", "special", "status" | keys, not display text |
| `encounters.py:85` `times()` | "Morning", "Day", "Evening", "Night" | identifiers from the table labels, not display text |
| `wild_statics.py:292-300` | "fixed", "preview", "never", "always", "roll"; kinds "gift", "egg", "static", … | keys |
| `hand_completion.py:164-173` | "later", "hoenn", "mythical", "not_required" | keys |
| `species.dex_blocks()` | "Kanto", "Johto", "Hoenn", "Alolan Regional Forms", "Galarian Regional Forms", "Hisuian Regional Forms", "Paldean Regional Forms", "Other" | read from the comments of `include/constants/pokedex.h` (English, developer wording) – pages should treat them as keys |
| `hand_credits.roll()`, `.chain()`, `.contributors()`, `.resources()` | role and section titles | English in the game and in the repository files; identical for both languages |

No function in `gamedata/` returns a German sentence any more except through game text of
the requested build.

## 5. Other changes made in this round

* `tu.py`: language everywhere, named-string index, literal index, build comparison.
* `species.py`, `moves.py`, `abilities.py`, `items.py`, `typeinfo.py`, `maps.py`, `trainers.py`:
  `lang` on every public function, caches keyed by language, `lang`/`text_lang` attributes,
  symbol-referenced texts resolved. German results are unchanged except for the fixed
  descriptions (compared entry by entry against the previous version: species 474, moves 934,
  abilities 310, items 903, types 21, maps 1311, trainers 2134, partners 7, item sources,
  dex orders, level spans).
* `natures.py`: new.
* `trainers_scriptdb.py`: `text_db(lang)`; `db()` stays the German database for everything
  about what scripts do; script texts per language are read from the source line itself
  (the script tool splits arguments at commas, which would damage sentences).
* `hand_facts.inc_string` now takes the text from the script database (all conditionals
  resolved as in the build) and falls back to the file only for labels outside it. Compared
  over all 16550 labels the old version could read: 15 German results changed, all of them
  cases the old cut got wrong (text after an inner `#if IS_HNS`, a duplicated passage, the
  berry-tree texts of the wrong branch).
* `dex_texts.py`, `dex_options.py`, `dex_relearner.py`, `wild_maps.py`, `wild_shiny.py`,
  `wild_statics.py`, `hand_*.py`, `trainers_rematch.py`: `lang` arguments as listed in 1.2.
* `text.py`: English rules, `clean_as`, raw glyph codes.
* `selftest.py`: 87 checks (22 before). The English expectations are read in the test from the
  raw source files by small readers of its own (`raw_field`, `raw_string`,
  `raw_script_text`: the file as written with the `#if GERMAN` branch picked by hand), not
  through the loaders. `--quick` limits the build comparison to four TUs.

Runs: `python3 -I -B tools/docs/gamedata/selftest.py` → "Alle Prüfungen bestanden", 87 ok,
about 43 s. `python3 -I -B tools/docs/build_site.py --out <work>/tmp/site_check
--skip-assets` (the generator as it stands now, with the new framework and three pages) →
de and en, 313 pages each, no error. The first-generation page modules (`pages_v1/`) are no
longer wired into `build_site.py`, so they could not be run; calls they make into the data
layer keep their old signatures except `maps.dynamic_place` / `maps.DYNAMIC_PLACES`
(shape changed, see section 4) – `pages_v1` does not use either.

## 6. Surprising or open

1. English dialogue is not always up to date with the jade rules where the German text
   was rewritten. Example (active map, `CeruleanCity_House1_Frlg`): German "Mit zwei Orden
   … bis Level 20", "vier Orden … Level 30", "sechs Orden … Level 40", "acht Orden … Level 50";
   English "up to Lv. 30", "Lv. 50", "Lv. 70", "All POKéMON will obey you!". Of 16689 text
   labels, 248 contain different numbers in the two languages (192 on active maps or shared
   scripts); most are harmless ("thirty" vs "30", floor numbering "EG/1S" vs "1F/2F"), ten
   concern levels, badges or coins. The list is in `<work>/tmp/i18n/numdiff.txt`
   (temporary folder). Pages that quote dialogue for a rule should take the number from the
   code and not from the English text.
2. `GoldenrodCity_Text_MoveTutorCost`: German "A-aber…", English "It'll cost you 1000 coins.
   Okay?" – the two branches are different texts.
3. The Celadon prize menu (section 3, row 3) is a functional defect of the English build.
4. English sign text "ROUTE 1O4" (letter O) on Route 104.
5. The English Pokédex shows the German Pokédex text for 434 of 474 entries, under English
   labels.
6. `trainers.by_const("TRAINER_FALKNER_1_HNS").class_name` is "Leiter" (the docstring of
   the old layer said "Arenaleiter"; the table says "Leiter").
7. Form names: the game has no separate text for a form; every form entry repeats the
   species name. A page that needs to tell forms apart has only the constant.
8. Not determinable from the source: English names for anything in section 2 marked 0.
