# ORACLE – cross-check of the docs data layer against the compiled game

State: 2026-11-20 01:55 UTC, source commit `e160f672` (worktree `<repo>`, branch `documentation`),
data layer `tools/docs/gamedata` as it stood at that minute (the language work on it was still going on).

`S` = `<work>`,
`WT` = `S/<repo>`, `O` = `S/docs2/oracle`.

## 1. What exists

| File | Purpose |
|---|---|
| `WT/tools/docs/verify/romlib.py` | ELF32 reader (sections, symbols, program headers), ROM image reader (0x08000000 based, every table is also compared with the ELF segment), `charmap.txt` decoder |
| `WT/tools/docs/verify/cprobe.py` | struct layouts and constants from the project's own compiler: compiles a probe C file with the project headers and the build flags (`gamedata/tu.py` CPPFLAGS + `-mthumb -mthumb-interwork -O2 -mabi=apcs-gnu -mtune=arm7tdmi -march=armv4t` + language flag) and reads byte offset, bit offset, width, signedness, `sizeof` out of the object file. No offset is typed by hand. |
| `WT/tools/docs/verify/rom_dump.py` | ELF + ROM -> JSON of the game's tables |
| `WT/tools/docs/verify/rom_check.py` | data layer (per language) vs. a dump, totals per table, every difference, exit 1 on differences |
| `WT/tools/docs/verify/remap_harness.c` | host harness: includes the real `src/level_scaling.c`, state + stubs + driver |
| `WT/tools/docs/verify/remap_check.py` | builds the harness, runs the C rules and the Python mirror over the complete domain, exit 1 on differences |
| `O/de`, `O/en` | `Pokemon_Origin_Jade.elf/.map/.gba` of the German and the English build |
| `O/dump_de.json`, `O/dump_en.json` | dumps (4.4 MB each) |
| `O/check_de.txt`, `O/check_en.txt`, `O/remap.txt` | complete outputs of the last runs (every difference) |
| `O/probe/`, `O/remap/` | generated probe / harness files (`remap_tables.h`, `remap_extracted.inc`, binary) |

Builds:
* German: copied from `/home/user/pokemon_origin_jade` (HEAD `e160f672`, clean tree, no tracked source file newer
  than the ELF; `<repo>` differs from `e160f672` only by `tools/docs/` and `.github/workflows/docs.yml`).
* English: `S/wt_oracle` (detached `e160f672`), `make -j3 GAME_LANG=ENGLISH` (rc 0, log `O/build_en.log`,
  compiled with `-DLANG_ENGLISH`). Outputs have the same names as the German ones (Makefile `ROM_NAME`).
* Both dumps agree in every non-text table (trainers, wild, maps, rematch, type chart, ... byte for byte the same values).

## 2. How to run

```sh
export TMPDIR=S/tmp
cd WT
# 1. dump (2.5 s each)
python3 -I -B tools/docs/verify/rom_dump.py --lang de --elf O/de/Pokemon_Origin_Jade.elf --gba O/de/Pokemon_Origin_Jade.gba --out O/dump_de.json
python3 -I -B tools/docs/verify/rom_dump.py --lang en --elf O/en/Pokemon_Origin_Jade.elf --gba O/en/Pokemon_Origin_Jade.gba --out O/dump_en.json
# 2. data layer vs. ROM (10 s each); --max N = differences printed per table, --fields lists the compared fields
python3 -I -B tools/docs/verify/rom_check.py --lang de --dump O/dump_de.json --max 100000 --fields > O/check_de.txt
python3 -I -B tools/docs/verify/rom_check.py --lang en --dump O/dump_en.json --max 100000 --fields > O/check_en.txt
# 3. level rules: C code vs. Python mirror (13 s)
python3 -I -B tools/docs/verify/remap_check.py --dump O/dump_de.json --max 100000 > O/remap.txt
```
Needs `arm-none-eabi-gcc`, `arm-none-eabi-nm`, host `gcc` (`OJ_ARM_CC`, `OJ_HOST_CC` override), the generated
headers of a built tree (`src/data/wild_encounters.h` etc., as the data layer itself needs them).
`--repo` of `rom_dump.py` = tree whose headers and `charmap.txt` belong to the ROM (default: the tree the tool is in).
Language: `rom_check.py` hands `--lang` to the data layer once per process (`OJ_DOCS_LANG`, `gamedata.set_lang`,
`gamedata.tu.set_lang`); all loaders then run with `lang=None` = that language. With `--lang en` the German dump
(`dump_de.json` next to `--dump`, or `--dump-de`) is read too, only to tell translated texts from untranslated ones
(the data layer cleans German text with German rules, `text.clean_as`).

## 3. Coverage

### 3.1 rom_dump.py (what is read out of the ROM)
Symbols by `arm-none-eabi-nm -S`; 22 tables are verified identical in ELF segment and ROM image.

| JSON key | ROM symbol | Fields |
|---|---|---|
| `species` (476 incl. NONE and EGG; empty entries of disabled species are skipped) | `gSpeciesInfo` + pointers | name, category, description, types, 6 base stats, 6 EV yields, 3 abilities, catch rate, EXP yield, gender ratio, egg groups, egg cycles, growth rate, friendship, wild held items (common/rare), national dex number, height, weight, body colour, icon palette index, safari flee rate, flags (legendary/mythical/form flags, `perfectIVCount`, `dexForceRequired`, `dexNotRequired`, `cannotBeTraded`, ...), level-up learnset, teachable learnset, egg moves, evolutions (method, param, target, conditions with 3 args), form table |
| `moves` (935) | `gMovesInfo` | name, description, effect, type, category, power, accuracy, target, PP, priority, strike count, critical-hit stage, number of additional effects, contest effect/category, 52 yes/no flags (makesContact, soundMove, punchingMove, ... all ban flags) |
| `abilities` (311) | `gAbilitiesInfo` | name, description, computer-opponent rating, 7 flags |
| `items` (904) | `gItemsInfo` | name, plural name, description, price, pocket, hold effect, hold effect param, secondary id, importance, notConsumed, sort type, type, battle usage, fling power |
| `tmhm` (102 incl. index 0) | `gTMHMItemMoveIds` | item, move |
| `tutor_moves` (60) | `gTutorMoves` | move |
| `types` (21), `type_chart` (21x21) | `gTypesInfo`, `gTypeEffectivenessTable` | name, generic move name, palette, damage category, special-case flag, hidden-power flag; UQ4.12 multipliers |
| `natures` (25) | `gNaturesInfo` | name, raised stat, lowered stat |
| `trainers` (2358 ids, 2133 with a party), `partners` (7) | `gTrainers[DIFFICULTY_NORMAL]`, `gBattlePartners[DIFFICULTY_NORMAL]` | name, class, picture, gender, music, battle type, 4 items, computer-opponent flags, mugshot colour, party size, pool size; per Pokémon: species, level, held item, 4 moves, ability, nature, IVs (packed and unpacked), EVs, nickname, gender, shiny, ball, friendship, tera type, dynamax level, tags. `trainers_other_difficulties`: number of non-empty entries of the EASY/HARD tables (0 and 0) |
| `trainer_classes` (172) | `gTrainerClasses` | name, prize money factor, ball |
| `wild` (369 headers, 966 tables) | `gWildMonHeaders` + pointers | map group/number; per time of day and area (land, water, rock smash, fishing; hidden: none in the ROM): encounter rate, all slots (min level, max level, species). Slot counts from the symbol sizes (22 tables have 12 slots where the game uses 5 or 10, listed in `meta.notes`) |
| `wild_rates` | none (see limits) | slot chances land / water / rock smash / old / good / super rod |
| `maps` (1089) | `gMapGroups` -> map headers | group, number, map section, map type, layout id, weather, battle type |
| `mapsecs` (237) | `gRegionMapEntries` | name, x, y, width, height |
| `trades` (25) | `sIngameTrades` | nickname, species, IVs, ability number, OT id, contest conditions, personality, held item, mail, OT name, OT gender, sheen, requested species |
| `rematch` (166 rows) | `gRematchTable` | 5 trainer ids, map group, map number |
| `scaling` | `sJohtoCorridors`, `sRematchBandPlayerLevels`, `sTrainerEvoLevels`, `sRematchLevelCeilingByBadges` | all members |
| `dex` | `sKantoToNationalOrder` (186), `sJohtoToNationalOrder` (283), `sHoennToNationalOrder` (212) | national numbers in regional order |
| `constants`, `names`, `enumerators` | compiler | 14002 constants evaluated by the project's compiler (3 non-numeric macros skipped) |

### 3.2 rom_check.py (what is compared; exact field lists as printed by `--fields`)
* **species** (474 = all enabled species without NONE/EGG): constant, name, category, description, types, base hp/atk/def/spa/spd/spe,
  abilities (3 slots), catch rate, exp yield, ev yield, gender ratio, egg groups, egg cycles, growth rate, friendship,
  held item common, held item rare, national dex number, height, weight, flags, level-up moves (level + move, order),
  teachable moves, egg moves, evolutions (method, param, target, conditions), forms. **dex orders**: Kanto/Johto/Hoenn number -> species.
* **moves** (934): constant name, name, description, type, category, power, accuracy, pp, priority, target, effect,
  critical hit stage, flags (all 52). **tm/hm list** (101): machine -> move, machine item (`items.tm`). **tutor moves** (60).
* **abilities** (310): constant name, name, description.
* **items** (903): constant name, name, description, price, pocket, hold effect, hold effect param, secondary id.
* **types** (21): constant, constant name, name, generic move name, palette, special case, damage category. **type chart**: all 441 multipliers.
* **natures** (25): constant, constant name, name, raised stat, lowered stat.
* **trainer classes** (172): name, prize money factor.
* **trainers** (2134) and **battle partners** (7): name, class, class name, prize money factor, picture, double battle,
  items, gender, party size; per Pokémon: species, level (raw data level), held item, moves, ability, nature, ivs, evs,
  nickname, gender, shiny. ROM trainers that the data layer does not have must be empty (all 224 are).
* **rematch table** (166 rows): rows, trainers (ids), trainer constants (names must be trainers of the data layer), map, map constant, special row.
* **wild tables** (966 = every table of every header and time): header count and order, map, time-of-day order, encounter rate, all slots.
  **wild slot rates** (6 lists). **wild as shown** (3475 = `encounters.table()` for every map x time x area): slots
  (index, species, min, max, rate) and encounter rate against the ROM header of the map with the fallback time.
* **maps** (1089): map constant, map section (number and constant), map type. **map sections** (236): name.
* **level rule tables**: Johto corridor map sections, band player levels, trainer evolution levels, rematch level ceilings.
* **in-game trades** (25): species, requested species, nickname, ot name, ivs, ability number, held item, ot id, personality.
* Also printed, not counted as differences: species of trainer parties and wild tables that are not in the build (section 6).

Constant names of the data layer (EGG_GROUP_*, GROWTH_*, EVO_*, IF_*, TARGET_*, EFFECT_*, POCKET_*, HOLD_EFFECT_*, STAT_*, MAPSEC_*,
MAP_*, TRAINER_CLASS_*, TRAINER_PIC_*, NATURE_*) are converted to numbers with the compiler's constants before comparing.
For the real enums (moves, items, abilities, types, natures) the name itself must be an enumerator with that value.

### 3.3 remap_check.py (C rules vs. `gamedata/levels.py`, `trainers.py`, `encounters.py`)
C side: `src/level_scaling.c` compiled as a whole; cut verbatim from the sources: `TrainerIdToRematchTableId`,
`IsNormalPhoneRematchBattle`, `IsKantoLeaderRematchBattle` (battle_setup.c), `GetTrainerDifficultyLevel` (difficulty.c),
`IsSpeciesEnabled`, `SanitizeSpeciesId`, `GetSpeciesEvolutions` (pokemon.c), `GenConfigTimeOfDay` (rtc.c),
`GetCurrentMapWildMonHeaderId`, `GetTimeOfDayForEncounters` (wild_encounter.c); `GetTrainerStructFromId` etc. from `include/data.h`.
Tables (trainers, partners, rematch table, evolutions, wild headers, map sections of the maps) from the ROM dump.
Stubbed: flags (three title flags, `FLAG_TEMP_KANTO_LEADER_REMATCH`, `FLAG_BADGE03_GET`), badge counts, time of day,
`VarGet(VAR_ALTERING_CAVE_WILD_SET)` = 0, difficulty = normal, not in Battle Pike/Pyramid. Any other flag/var read aborts.
The driver repeats the call sites of `CreateNPCTrainerPartyWithId`, `FillPartnerParty`, `TryGenerateWildMon`;
the tool stops if those source lines change.

| Section | Domain | Values |
|---|---|---|
| progress steps | 30 states (Kanto/Johto/Hoenn badges 0-8, titles): player level `P` | 30 |
| levels on every map | 1089 maps x levels 1-100 x {trainer, trainer of class LEADER_KANTO_HNS, wild, partner, scripted} + remap region of every map | 545 589 |
| every trainer class | 172 classes x levels 1-100 on one map of each of the 5 kinds of maps | 86 000 |
| experience percent | 100 x 100 level pairs x third badge yes/no x 5 kinds of maps | 100 000 |
| trainer battles | 1984 battles (trainer x map x script command x fielded party; 1711 trainers) x 30 steps: rule (fixed / phone band / leader band), level and species of all 6962 slots | 268 380 |
| battle partners | 4 partner teams x 30 steps | 360 |
| evolution hash | every trainer id x 6 slots x 2 steps | 28 392 |
| wild | 1089 maps (293 with tables) x 4 times x 6 areas, twice (step 0 and 29): table present, time used, encounter rate, per slot species, min, max, effective min, effective max (C: min/max of `ScaleWildMonLevel` over the whole level range of the slot) | 272 342 |

### 3.4 Not covered
* Everything that lives in scripts or maps: where a trainer is fought (map, command, leader flag: `trainers.battles()` is the
  *domain* of remap_check, read by the data layer from the scripts and not verified here; 148 battle sites without a map and
  423 trainers without a battle on a map are outside the check), item balls, hidden items, shops, gifts, static encounters,
  roamers, berry trees, map names beyond the map section, map events.
* Slot chances are not a table in the ROM (immediate numbers in `ChooseWildMonIndex_*`); the ROM side of "wild slot rates"
  are the `ENCOUNTER_CHANCE_*` constants of the generated `src/data/wild_encounters.h` as the project's compiler evaluates them.
* Display clean-up of texts (`gamedata/text.py`: joining lines, hyphens, placeholders) is applied to both sides; what is
  verified is the text itself. Characters that share a byte in `charmap.txt` (' and ’, - and _) count as equal.
* Dumped but not compared (no counterpart read by the pages or no loader): species body colour / icon palette / safari flee rate,
  move strike count / contest data / additional-effect count, ability computer-opponent rating and flags, item plural / importance / type /
  battle usage / fling power, trainer music / computer-opponent flags / ball / friendship / tera type, trade contest conditions / mail / sheen,
  map layout / weather, map section coordinates, type hidden-power flag.
* Not dumped: graphics, cries, move additional effects (chances), form change tables, Battle Frontier / Battle Pike / Pyramid
  tables, berries, pickup table, level caps, Feebas spots, `sTrainerEvoExcluded` (inlined by the compiler, no symbol; it is part
  of the C code in remap_check), `sJohtoRooms` (unused with fixed levels), EASY/HARD trainer tables (empty).
* remap_check: randomizer off, Altering Cave set 0, hours -> time of day (`GetTimeOfDay`) not checked, the pre-remap scaling
  code paths (`LEVEL_REMAP == FALSE`) not exercised.

## 4. Totals

`rom_check.py`, German and English give the same numbers (`O/check_de.txt`, `O/check_en.txt`):

| Table | Entries | Fields | Differences DE | Differences EN |
|---|---|---|---|---|
| species | 474 | 31 | 0 | 0 |
| dex orders | 679 | 1 | 0 | 0 |
| moves | 934 | 13 | 2 | 2 |
| tm/hm list | 101 | 2 | 0 | 0 |
| tutor moves | 60 | 1 | 0 | 0 |
| abilities | 310 | 3 | 1 | 1 |
| items | 903 | 8 | 3 | 3 |
| types | 21 | 7 | 0 | 0 |
| type chart | 441 | 1 | 0 | 0 |
| natures | 25 | 4 | 0 | 0 |
| trainer classes | 172 | 2 | 30 | 30 |
| trainers | 2134 | 19 | 532 | 532 |
| battle partners | 7 | 19 | 1 | 1 |
| rematch table | 166 | 6 | 2 | 2 |
| wild tables | 966 | 5 | 0 | 0 |
| wild slot rates | 6 | 1 | 0 | 0 |
| wild as shown | 3475 | 2 | 0 | 0 |
| maps | 1089 | 4 | 0 | 0 |
| map sections | 236 | 1 | 0 | 0 |
| level rule tables | 178 | 3 | 0 | 0 |
| in-game trades | 25 | 9 | 3 | 3 |
| **total** | | | **574** | **574** |

`remap_check.py` (`O/remap.txt`): 1 301 093 values compared, **114 differences**, all in "trainer battles" (2 battles x 30 steps,
one root cause, 5.1); 6 game assertions fired (section 6). All other sections 0.

Sensitivity (done once, not part of the tools): 26 single values changed in a copy of the dump (base stat, description letter,
learnset level, evolution param, ability, move power/flag/name, item price, TM move, chart cell, nature, trainer level/move/species,
class money, wild level/rate, map section, map section name, rematch id, band level, dex order, trade species, slot rate) - every
one was reported. Five changes patched into the Python mirror at run time (rounding, band upper edge, evolution skip percent,
Johto entry sections, time fallback) gave 170 412 / 11 170 / 1 675 / 1 144 / 10 954 differences.

## 5. Remaining differences = real data-layer bugs

### 5.1 `tu.canonical(prefix)` returns constants of other families (moves 2, abilities 1, items 3, rematch table 2, remap 114)
`tools/docs/gamedata/tu.py`, `TU.canonical` (line 155): it prefers any `#define` with that prefix whose body is a plain number.
Unrelated macros share the prefix and the number, and win over the enumerator.

| Call | Input | Expected (ROM / enum) | Actual |
|---|---|---|---|
| `moves.py:50` | `moves.by_id(3).const` | `MOVE_DOUBLE_SLAP` | `MOVE_EFFECT_BYTE` |
| | `moves.by_id(16).const` | `MOVE_GUST` | `MOVE_NAME_LENGTH` |
| `abilities.py:39` | `abilities.by_id(16).const` | `ABILITY_COLOR_CHANGE` | `ABILITY_NAME_LENGTH` |
| `items.py:99` | `items.by_id(1).const` / `.slug` | `ITEM_POKE_BALL` / `poke_ball` | `ITEM_FRIENDSHIP_MAPSEC_BONUS` / `friendship_mapsec_bonus` |
| | `items.by_id(6)` | `ITEM_HEAL_BALL` / `heal_ball` | `ITEM_EFFECT_ARG_START` / `effect_arg_start` |
| | `items.by_id(20)` | `ITEM_FAST_BALL` / `fast_ball` | `ITEM_NAME_LENGTH` / `name_length` |
| `trainers.py:472` `rematch_rows()` | row 71 `trainer_consts[0]` (id 26) | `TRAINER_CHAD_HNS` | `TRAINER_ENCOUNTER_MUSIC_RG_GYM_LEADER` |
| | row 81 `trainer_consts[0]` (id 17) | `TRAINER_JACK_HNS` | `TRAINER_TOWER_FUNC_GET_NUM_FLOORS` |

Consequences of the two rematch rows (this is what remap_check reports):
* `trainers.is_phone_rematch("TRAINER_JACK_HNS", "trainerbattle_rematch")` and the same for `TRAINER_CHAD_HNS` are False, the game
  says phone rematch. `battle_mode` gives "normal", `effective_team` shows fixed levels instead of the band:
  Jack (National Park) Python 51/51/52 at every step, game e.g. 3/3/4 (step 0), 41/41/42 (step 10), species differ too;
  Chad (Route 38) Python 54/54/54, game e.g. 4/4/4 (step 0), 90/90/90 with Magnezone instead of Magneton (step 29).
* The later teams of both rows (`TRAINER_JACK_2..5_HNS`, `TRAINER_CHAD_2..5_HNS`) get no battle site at all (`trainers.battles()` empty),
  because `_battle_index` looks the calls up under `row.trainer_consts[0]`.
* The wrong item slugs end up in asset file names and links (Poké Ball, Heal Ball, Fast Ball).
`species.py:110` uses the same function; all 474 species constants evaluate to their id (SPECIES_* are macros, alias choice is not checkable).

### 5.2 Octal number literals are not understood (in-game trades 3)
`tools/docs/gamedata/cparse.py`, `CEval.primary` (line 328, `int(s, 0)`): `src/data/trade.h` has `.otId = 00475` for trades 13, 14, 15.
In C that is octal = **317** (ROM: 317). The data layer raises `ValueError: invalid literal for int() with base 0: '00475'`
(`wild_statics._trade_table()` -> `t.field(row, "otId")`, used by `wild_statics._entries` and the shiny check of trades).

### 5.3 Prize money factor of 30 trainer classes is `None` instead of 0 (trainer classes 30)
`tools/docs/gamedata/trainers.py`, `_classes` (line 278): classes whose initializer has only a name (`{ _("...") }`) get money `None`;
the ROM has 0. Affected: `TRAINER_CLASS_ARENA_TYCOON(_HNS)`, `DOME_ACE(_HNS)`, `FACTORY_HEAD(_HNS)`, `BIKER_HNS`, `BURGLAR_HNS`,
`FIREBREATHER_HNS`, `JUGGLER_HNS`, `KIMONO_GIRL_HNS`, `MYSTERY_MAN_HNS`, `OFFICER_HNS`, ... (all 30 in `O/check_de.txt`). `Trainer.money` of
their 221 trainers is `None` as well (reported once per class, not per trainer).

### 5.4 Trainer Pokémon without an "IVs:" line: `ivs` is `None`, the game stores 31 in every stat (trainers 532)
`tools/docs/gamedata/trainers.py`, `_build` (`ivs=_stats(m.get("IVs"))`): 532 Pokémon of 163 trainers (e.g. `TRAINER_JOEY_2_HNS`
all slots, `TRAINER_LANCE_3_HNS`) have no IVs line. `tools/trainerproc` then writes its default, 31 for all six stats
(ROM `iv` = 0x3FFFFFFF). The data layer hands out `None`, which a page cannot tell from "0". Where an IVs line exists, all values agree.
(EVs: no line = no EVs in the ROM = `None`, agrees.)

### 5.5 `PARTNER_DUMMY` has one Pokémon in the data layer, none in the ROM (battle partners 1)
`src/data/battle_partners.party`: `Party Size: 0` followed by "Wynaut". ROM party size 0; `trainers.partners()["PARTNER_DUMMY"].mons` has 1 entry.
Not visible to players (test dummy), but `parse_party` ignores `Party Size: 0`.

### 5.6 No difference today, but a wrong model: progress steps 9 and 19
`levels.band_steps()` describes step 9 as "Kanto title" and 19 as "Johto title". `GetRematchProgressStep` never returns 9 or 19:
with the title set it goes on to the next region's badge count (10 / 20). The levels agree only because
`REMATCH_BAND_PLAYER_LEVELS` has the same value at 9/10 (43) and 19/20 (70). With more than 8 badges before a title the game stays at step 8 / 18.

### 5.7 Fixed while this check was written
First run (data layer of 01:35 UTC): 127 items had the name of a C symbol as description (`items.by_const("ITEM_FULL_HEAL").description == "sFullHealDesc"`,
all items whose description is a shared `static const u8 s...Desc[]`). Gone after the `items.py` update of the language work; now 0.

## 6. Findings about the game itself (ROM and data layer agree)

* **English build, names are German.** In the English ROM these texts are byte-identical to the German ROM: all 476 species names and
  categories, all 935 move names, all 904 item names, all 311 ability names and descriptions, all nature, type, trainer class,
  trainer and map section names. English are only 41 species descriptions, 48 move descriptions and 117 item descriptions
  (the entries with a language branch in the source). "The wording of the English build" for names is therefore the German wording.
* **Species that are not in the build** (their `gSpeciesInfo` entry is empty) are in 24 trainer parties and 11 wild slots
  (full list at the end of `O/check_de.txt`). On unlocked maps: `TRAINER_BROCK/LTSURGE/ERIKA/JANINE/SABRINA/BLAINE/BLUE_POSTOBC_HNS`
  (Kanto gyms), `TRAINER_WILL/KOGA/BRUNO/KAREN/LANCE_POSTOBC_HNS` (Johto league rooms), `TRAINER_RED_POSTOBC_HNS` (Mt. Silver).
  For the six on Johto maps the game's own check in `SanitizeSpeciesId` ("disabled species") fires while the team is built
  (Slowking-Galar, Overqwil, Tauros-Paldea, Obstagoon, Noivern): a build without `RELEASE` shows its assert screen there.
  Wild: Route 49, the three Alola caves and Snowswept Cavern (locked areas). Whether those post-game battles can be reached at all
  cannot be told from the tables.
* **OT id of three trades**: `00475` in the source is an octal number, the game shows OT id 00317 (5.2).
* 22 wild tables carry 12 entries where the game only ever uses 5 (water) or 10 (fishing): Route 30 fishing, Lake of Rage,
  Route 45, Route 28 and the Johto city water tables (`meta.notes` of the dump). The extra entries never appear.
* `gTrainers` has tables for three difficulties; EASY and HARD are empty, the game always uses NORMAL.

## 7. Decoder bugs found and fixed in the tools while writing them
* Charmap: sound/music ids (`SE_M_MILK_DRINK = E1 00`) were matched inside running text ("m " is E1 00). Sequences of several
  bytes are now only decoded behind the PKMN/POKEBLOCK ligature bytes and the control prefixes F8/F9/FC/FD.
* Name buffers that were never initialised (all zero, no terminator) decoded as spaces; now empty.
* Map groups contain `NULL` entries (unused map numbers); they are skipped.
* `DIFFICULTY_NORMAL` is index 1 of `gTrainers`, not 0 (taken from the compiler's constants).
* Struct alignment under `-mabi=apcs-gnu` (unions padded to 4 bytes) is why layouts come from the compiler only.
