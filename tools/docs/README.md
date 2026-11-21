# Spieler-Doku / player documentation (tools/docs)

Static website with the player documentation of Pokémon Origin Jade, in German
and English: Pokédex, world, battles, database and guides. All data is read
from the game's sources (C tables through the preprocessor with the build
flags of the respective language, `.party` files, map JSONs, graphics). Levels
are shown the way the game computes them. The built site is not checked in.

## Build

Needs `arm-none-eabi-gcc` (as for the game), Python 3 with Pillow and the
generated headers (`make generated src/data/pokemon/teachable_learnsets.h
src/data/tutor_moves.h`; present after a normal game build).

    python3 -I -B tools/docs/gamedata/selftest.py                  # check the data layer
    python3 -I -B tools/docs/build_site.py --out build/docs_site   # both languages
    python3 -I -B tools/docs/build_site.py --out build/docs_site --only abilities --lang de --skip-assets

Options: `--lang de|en`, `--only <module,...>`, `--fast`, `--skip-assets`,
`--dev` (component gallery at `de/dev/gallery.html`), `--strict`,
`--report <file>`, `--en-src <dir>|none`, `--en-name-style title|game`.
The same sources give byte-identical output.

## English names and texts

Values, tables and structure always come from this repository. English names
and texts come from the English version of the game:

- If this repository already contains it (names behind `#if GERMAN ... #else`,
  `Name: DE_EN(de, en)` in the `.party` files, `name_en` in the map section
  list), nothing has to be set up.
- Otherwise point the build at a checkout of the branch with the English
  version: `--en-src <dir>` or the environment variable `OJ_DOCS_EN_SRC`
  (default: `EN_TEXT_SOURCE` in `site_config.py`, used if the folder exists;
  `none` switches it off). Only sources are read from there (`include/`, `src/`,
  `data/`, `asm/macros/`); that tree does not have to be built. Texts are matched
  by constant, symbol or script label; an entry that only exists here keeps this
  repository's text.

The English game writes names in capitals. `EN_NAME_STYLE` in `site_config.py`
(or `--en-name-style`, `OJ_DOCS_EN_NAME_STYLE`) chooses `title` (Bulbasaur, Poké
Ball, Mt. Moon - the default) or `game` (BULBASAUR, POKé BALL, MT. MOON). Only
names are converted, never descriptions or dialogue; the rules and the list of
exceptions are in `gamedata/namestyle.py`.

## Checks

    python3 -I -B tools/docs/gamedata/selftest.py [--quick]

Optional cross-checks against a compiled game (`tools/docs/verify/`, need the
ELF and ROM of a build):

    python3 -I -B tools/docs/verify/rom_dump.py --lang de --elf X.elf --gba X.gba --out dump_de.json
    python3 -I -B tools/docs/verify/rom_check.py --lang de --dump dump_de.json      # data layer vs. ROM tables
    python3 -I -B tools/docs/verify/remap_check.py --dump dump_de.json              # level rules: C code vs. Python
    python3 -I -B tools/docs/verify/rom_dump.py --lang en --names-only --repo EN_TREE --elf EN.elf --gba EN.gba --out dump_en.json
    python3 -I -B tools/docs/verify/en_names_check.py --dump dump_en.json           # English names vs. the English ROM
    python3 -I -B tools/docs/verify/en_source_report.py                             # where each English text comes from

## Publishing

`.github/workflows/docs.yml` runs only when started by hand (Actions -> Docs ->
Run workflow). It checks out the English branch for the texts, runs the
self-test and builds both languages; the site is kept as an artifact and is
deployed to GitHub Pages only when "deploy" is ticked for that run.

## View

Open `build/docs_site/index.html` in a browser (works from the file system),
or serve the folder: `cd build/docs_site && python3 -m http.server 8000`.

## Layout

- `build_site.py` – entry point; builds `de/`, `en/` and the shared `assets/`
- `site_config.py` – version text, community links, default language, English
  text source, English name style
- `pages/` – one module per part of the site (`register(ctx)`, `render(ctx)`)
- `common/` – context and registry, component library (`html.py`), UI strings
  (`i18n.py`), URL slugs, search index, build checks
- `gamedata/` – data layer (species, moves, items, maps, trainers, levels,
  graphics; `entext.py` English texts, `namestyle.py` English name style)
- `verify/` – cross-checks of the data layer against a compiled game
- `export_assets.py` – images from the game graphics, exported when a page uses them
- `static/` – `site.css`, `site.js`
- `pages_v1/` – the previous single-language page modules, kept as reference
