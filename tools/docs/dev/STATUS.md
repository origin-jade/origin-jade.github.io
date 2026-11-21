# Player documentation: status and open work

The generator in `tools/docs/` builds the player documentation site in German and
English from the game source. This file says what exists and what is still to do.
Details: `FRAMEWORK.md` (how page modules work), `DATA.md` (data layer and languages),
`ROM_CHECK.md` (cross-check of the data layer against a compiled ROM).
In those three files, paths starting with `S/` or `<work>` point to a local work
folder that is not part of the repository.

## Build

    make -j4 generated src/data/pokemon/teachable_learnsets.h src/data/tutor_moves.h
    python3 -I -B tools/docs/gamedata/selftest.py --quick
    python3 -I -B tools/docs/build_site.py --out <dir> --strict

Output: `<dir>/de/...`, `<dir>/en/...`, shared `<dir>/assets/...`. About one minute,
deterministic. `--only <module> --fast --lang de` for quick iteration, `--dev` adds the
component gallery and stub pages for sitemap pages nobody has written yet.

## Publishing

The site is not published before the full release of the game. The generated site
never goes into this repository. It lives in a separate repository that holds only the
built website (copy the build output there and commit); `.github/workflows/docs.yml` here runs only when started by hand.

## Done

| Area | Module | Pages per language |
|---|---|---|
| Home | `pages/home.py` | 1 |
| Pokédex | `pages/pokedex.py` | 423 (422 Pokémon, 52 forms on their base pages) |
| World | `pages/world.py` | 194 (3 region hubs, 190 locations) |
| Battles | `pages/battles.py` | 7 (gyms and league per region, rivals, rematches, all trainers) |
| Abilities | `pages/abilities.py` | 311 |
| Type chart | `pages/typechart.py` | 1 |
| Moves | `pages/moves.py` | 596 (list + 595 moves) |
| Items, TMs & HMs, berries | `pages/items.py`, `pages/_items_data.py` | 497 (list, 494 items, TM page, berry page) |
| Game | `pages/game.py`, `pages/_game_*.py`, `gamedata/game_rules.py` | 5 (features, start & FAQ, settings, levels, credits) |
| Guides | `pages/guides.py`, `pages/_guides_*.py` | 7 (breeding, shiny, legendaries, gifts & trades, Pokéblocks, completion, key items) |

## Open

1. Clean-up:
   - `game/changelog` is in the sitemap but not built: the repository has no list of changes
     per version. Build it when such a list exists, or drop the sitemap entry.
   - Data layer returns a few things no player can reach; the filters are local:
     `pages/_pokedex_data.py` (`reachable_maps`, the event islands of the Lilycove ferry,
     unreferenced gift labels), `gamedata/trainers_items.py` (lines after an unconditional
     `end`/`return`/`goto`, the link-distribution script). The battles module does not use
     them yet (six post-title teams behind a story value that only a locked area sets).
   - Database: moves and items list only what a player can meet. Items whose script picks
     them at run time (exchange corner, lottery, vending machines) have no place rows. The
     berry page leaves out growth time and yield (two berry tree systems in the source).
     Item pages do not say which Pokémon evolve with the item.
   - Guides: the steps of `_guides_legendaries.py`, `_guides_gifts.py` and
     `_guides_keyitems.py` are written by hand from the map scripts; levels, species, prices
     and places are checked against the data layer on every build. When the game changes a
     condition (a flag, an item check), the sentence has to be changed by hand.
   - Components: `H.species_tile` needs extra data attributes and a meta chip (the Pokédex
     index copies its markup); level cells and long move names should not break inside
     narrow columns; a compact table variant for phones.
   - Page size: the report lists the pages above the 150 KB mark (battles pages, the three
     big lists, move pages with several hundred learners).
2. Review of the whole site: data against the source (samples per page type), rendering
   on phone and desktop in both themes, both languages complete and consistent, nothing
   on the pages that players do not care about.
3. All hand-written prose in both languages goes to the owner for review before release
   (`python3 -I -B tools/docs/export_texts.py OUT.txt`).
