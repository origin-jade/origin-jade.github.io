# FRAMEWORK2 – contract for page authors (site v2)

Code: `WT/tools/docs/` (WT = `<work>/<repo>`). Data layer and languages: `S/docs2/DATA_I18N.md`.
Working examples: `pages/abilities.py` (list + one page per entity – copy this), `pages/typechart.py`
(one generated page), `pages/home.py`, `pages/gallery.py` + `pages/_gallery_data.py` (every component with
real data; complete Pokémon page and complete location page). The old single-language modules are in
`pages_v1/` for reference only (they no longer run).

## 0. Rules for parallel work

* **Create only new files:** `pages/<module>.py`, helpers `pages/_<module>_<topic>.py`, new loaders
  `gamedata/<topic>.py`. One module per author topic; pick a file name nobody else uses.
* **Shared files are not edited by authors:** `build_site.py`, `site_config.py`, `export_assets.py`,
  `common/*`, `static/*`, existing `gamedata/*`, `pages/home.py|typechart.py|abilities.py|gallery.py|_gallery_data.py`.
  If you need a new component, CSS, UI string, sitemap entry or a loader fix: work around it in your module
  and **report the need** in your final report. There is no page-specific CSS; use the components.
* Use your own `--out` directory. Never build into someone else's.
* Content rules (the build enforces most of them): names and numbers only from the loaders in the
  language of the build; no constants, symbols, file names, config names in visible text; nothing about
  how the pages are made; no ROM sources, file names, patch tools, checksums; no external addresses.
  **Unknown or unverifiable content is left out of the page** and reported with `ctx.todo("...")`
  (goes to the `--report` file, never into the site).
* Budgets: a typical page under 150 KB HTML (the report lists pages above it), whole site under 250 MB,
  full build under 5 minutes. Measured: shell and checks cost about 2 ms per page; a full Pokémon page
  (gallery composition for all 474 species) is 46 KB on average and renders in about 20 ms per page.

## 1. Build, look, check

```sh
cd WT;  export TMPDIR=S/tmp
python3 -I -B tools/docs/build_site.py --out OUT --dev --report OUT.report.txt      # everything, de + en (parallel)
python3 -I -B tools/docs/build_site.py --out OUT --dev --skip-assets --lang de --only mymodule          # all modules register, mine renders
python3 -I -B tools/docs/build_site.py --out OUT --dev --skip-assets --lang de --only mymodule --fast   # only mine registers; others from the last full build into OUT
```

| Option | Meaning |
|---|---|
| `--out DIR` | output: `DIR/index.html`, `DIR/de/…`, `DIR/en/…`, `DIR/assets/…` |
| `--lang de\|en` | one language only (no cross-language check, nothing is pruned) |
| `--only a,b` | render only these modules (file names without `.py`); every module still registers, so links resolve |
| `--fast` | with `--only`: skip the other modules' register pass, take their registry from the last full build into the same `--out` (cache in `tools/docs/.cache/`); no search index is written |
| `--skip-assets` | do not re-export images that already exist |
| `--dev` | also build `dev/gallery`, `dev/pokemon`, `dev/location` and a stub for every fixed page nobody has claimed yet (so navigation and start page are complete while modules are missing) |
| `--strict` | warnings fail the build |
| `--report FILE` | notes of `ctx.todo`, warnings, problems, phrases to check by hand, timings per module, page sizes |

The build fails (exit 1) on: contract errors, a missing string key, text hygiene hits, broken links or
anchors, a page registered but not rendered, different page sets in de and en. A full build (no `--only`,
no `--lang`) removes stale files in `OUT/de`, `OUT/en` and `OUT/assets`. Output is deterministic.

Open `OUT/de/index.html` directly (file://) or serve the folder. Component gallery: `OUT/de/dev/gallery.html`.

Screenshots and checks (Node + Playwright, pages opened from file://):

```sh
node S/docs2/tools/shots.js OUT SHOTDIR [--full] [--langs de,en] [--themes light,dark] [--sizes desktop,phone] pokedex/bulbasaur=bulba data/typechart
#  -> SHOTDIR/<name>_<desktop|phone>_<light|dark>_<lang>.png (1440x900 / 390x844); prints console errors, external requests, horizontal overflow; exit 1 on any
python3 S/docs2/tools/slice.py SHOT.png 1500 [x0 x1]      # cut a --full shot into readable pieces
node S/docs2/tools/states.js OUT SHOTDIR                   # menu, search, tabs, filter, theme, language, no-JS checks (needs a --dev build)
python3 S/docs2/tools/contrast.py WT/tools/docs/static/site.css
```

## 2. A page module

```python
# tools/docs/pages/moves.py
"""What the module shows and which loaders it mirrors."""
from common import html as H
from gamedata import moves

STRINGS = {                                # every text of the module, both languages, same keys
    "de": {"lead": "Alle {n} Attacken …", "eyebrow": "Attacke"},
    "en": {"lead": "All {n} moves …",     "eyebrow": "Move"},
}

def register(ctx):                         # pass 1 (per language): announce pages and entities
    ctx.add_page("data/moves/index")                       # fixed page: title, section, sidebar place from the sitemap
    for m in moves.all_moves(ctx.lang).values():
        ctx.add_entity("move", m.const, m.name, sub=..., keywords=...)

def render(ctx):                           # pass 2: write every registered page
    ctx.begin("data/moves/index")          # FIRST: from here on links and image URLs are relative to this page
    body = H.filter_bar(ctx, "moves", facets=[H.type_facet(ctx)]) + H.move_table(ctx, rows, id="moves")
    ctx.end(body, lead=H.esc(ctx.t("lead", n=ctx.num(len(rows)))))
    for m in ...:
        ctx.begin("move", m.const)
        ctx.end(body, eyebrow=ctx.t("eyebrow"), lead=H.esc(m.description), chips=H.type_chip(ctx, m.type))
```

* A module is every `pages/*.py` not starting with `_`; it needs `register(ctx)` and `render(ctx)`.
  `STRINGS` is optional; if present it must be `{"de": {...}, "en": {...}}` with identical key sets and no
  empty text (else the build stops). `DEV = True` marks a module that is only built with `--dev`.
* The module runs once per language in its own process; `ctx.lang` is `"de"` or `"en"` and is also the
  process language of the loaders (`lang=None`). Pass `ctx.lang` explicitly anyway.
* Both passes must be deterministic and must produce the same pages in both languages. Every registered
  page must be rendered. Modules run in file-name order; do not depend on that – only on the registry.
* Call `ctx.begin(...)` before any `H.*` helper or `ctx.url_for/url/asset` (they raise otherwise).
* Speed: load data once per module (the loaders cache), build shared fragments once, no per-page scans over
  all species/trainers/maps (build an index dict first).

## 3. `ctx`

| Call | Meaning |
|---|---|
| `ctx.lang`, `ctx.dev` | language of this run; True in a `--dev` build |
| **Registration (only in `register`)** | |
| `ctx.add_page(path, title=None, *, nav=None, nav_title=None, parent=None, section=None, search=True, keywords="", icon="", sub="")` | a page; `path` = URL below the language folder without `.html`. Paths of the sitemap (section 5) get title, section and sidebar position from there. Other pages need `title`; `nav=<number>` puts them into the sidebar of their section (first path segment), `parent=<path>` sets breadcrumb and active sidebar entry (default: `<folder>/index`). Registered as kind `"page"`, key = path. |
| `ctx.add_entity(kind, const, title, *, keywords="", icon="", sub="", search=True, parent=None, path=None)` | the page of one entity; path from the slug rules (section 4). `const`: constant name or loader object with `.const`. |
| `ctx.add_anchor(kind, key, page_path, frag, title, *, keywords="", icon="", sub="", search=True)` | an entity without its own page: `url_for` gives `page_path.html#frag` (e.g. trainers on a location page). The build checks that the page has `id="frag"`. |
| `ctx.asset_rel(kind, name)` | image path for `icon=` (`"icon/bulbasaur.png"`); marks the image as used |
| **Lookup (render pass, after `begin`)** | |
| `ctx.url_for(kind, key)` | relative URL or `None` if nobody registered it. Kinds: `species move ability item location trainer page` |
| `ctx.url(path)` | the same for a page path |
| `ctx.has(kind, key)`, `ctx.title_of(kind, key)`, `ctx.entry(kind, key)` | registry queries (also allowed in `register`, but other modules may not have registered yet – use them in `render`) |
| `ctx.pages`, `ctx.entries`, `ctx.nav_tree()` | the registry itself (read only) |
| `ctx.asset(kind, name, ext="png")` | relative URL of `assets/<kind>/<name>.png`; the image is exported because it is used. Kinds and names: section 8 |
| **Text and numbers** | |
| `ctx.t(key, **fmt)` | string of this module (`STRINGS[lang][key]`), `str.format` |
| `ctx.ui(key, **fmt)` | shared UI string (`common/i18n.py UI`): `level`, `type`, `power`, `accuracy`, `pp`, `move`, `ability`, `item`, `price`, `location`, `region`, `method`, `time`, `rate`, `levels`, `trainer`, `team`, `nature`, `shiny`, `total`, `note`/`tip`/`warning`, `cat_<physical\|special\|status>`, `time_<morning\|day\|evening\|night>`, `enc_<land\|cave\|water\|rock_smash\|old_rod\|good_rod\|super_rod>`, `region_<kanto\|johto\|hoenn>`, `learn_<level\|tm\|tutor\|egg>`, `stat_<hp…>`, `any_time`, `none`, … |
| `ctx.num(1234.5)` | `1.234,5` / `1,234.5` (ints with separators; floats up to `digits=1` decimals) |
| `ctx.pct(12.5)` | `12,5 %` / `12.5%` |
| `ctx.money(3000)` | `3.000 ₽` / `₽3,000` |
| `ctx.mult(0.5)` | `×½` (also ×¼, ×2, ×0, ×1,5) |
| `ctx.level(5)`, `ctx.level_range(3, 5)` | `Lv. 5`, `Lv. 3–5` (equal ends give one level) |
| **Rendering** | |
| `ctx.begin(path)` / `ctx.begin(kind, key)` | start a registered page of this module |
| `ctx.end(body, *, title=None, eyebrow=None, lead=None, chips=None, aside=None, outline=True, prev=None, next=None, wide=False, cls=None, scripts=(), description=None)` | wrap `body` into the shell and write the file. `title` plain text (default: registered title); `eyebrow` small line above the title (plain text); `lead` HTML of the intro paragraph; `chips` HTML under the title; `aside` HTML right of the header (sprite plates); `outline` “on this page” from the `H.section` headings when there are 3 or more; `prev`/`next` a page path or `(kind, key)`, unknown ones are skipped; `wide` full width; `scripts` extra data files below `assets/` loaded before `site.js`; `description` meta description. |
| **Notes** | |
| `ctx.todo(text)` | a fact that could not be determined from the source → report file. Leave the content out. |
| `ctx.warn(text)` | build warning (fails with `--strict`) |
| **Files** | |
| `ctx.write_asset(rel, data)`, `ctx.write_image(rel, img)` | own file below `assets/` (str/bytes, PIL image). Language-specific data must carry the language in its name (`"moves-%s.js" % ctx.lang`). Data files assign to a global (`window.X = …`) – no fetch, the site must work from file://. |

## 4. URLs and slugs (`common/slugs.py` – the only place that defines them)

* Layout: `<lang>/<path>.html`. Switching language swaps only the first segment, so paths are language
  neutral and derived from constants, never from display names.
* `slugs.slug(const)`: prefix cut (`SPECIES_ MOVE_ ABILITY_ ITEM_ MAPSEC_ MAP_ TRAINER_ TYPE_`), lower case,
  everything else → `-`: `SPECIES_HO_OH` → `ho-oh`, `MOVE_U_TURN` → `u-turn`, `MAPSEC_ROUTE_1` → `route-1`.
* `slugs.entity_path(kind, const)` (what `add_entity` uses):

| kind | key | page |
|---|---|---|
| `species` | `SPECIES_…` | `pokedex/<slug>` |
| `move` | `MOVE_…` | `data/moves/<slug>` |
| `ability` | `ABILITY_…` | `data/abilities/<slug>` |
| `item` | `ITEM_…` | `data/items/<slug>` |
| `location` | `MAPSEC_…` (a place = a map section); a building or floor with its own page: its `MAP_…` id | `world/<slug>` (set `parent="world/kanto"` etc.) |
| `trainer` | `TRAINER_…` | `battles/trainers/<slug>` if a module gives trainers own pages; otherwise register them with `add_anchor` on the page that shows them |
| `page` | the path | the path |

* Other modules link with `H.link(ctx, kind, key, text)` / `ctx.url_for` – so **use exactly these keys**
  (the game constants). Two registrations of the same key or path stop the build.
* Anchors: `slugs.anchor("Wilde Pokémon")` → `wilde-pokemon` (what `H.section` uses when no `id` is given).
  Give sections a fixed `id` so anchors are the same in both languages.
* Image file names are the loaders' own slugs with underscores (`species.slug` = `ho_oh`); they are not URL slugs.

## 5. Fixed pages (sitemap, `common/i18n.py SITEMAP`)

Claim them with `ctx.add_page(path)`. Titles (de / en) and sidebar order are fixed; a page appears in the
sidebar, on the start page and in breadcrumbs as soon as a module registers it.

| Section | Paths |
|---|---|
| home | `index` |
| game | `game/features` (Neuerungen / What's new), `game/start` (Erste Schritte & FAQ), `game/settings`, `game/levels`, `game/changelog`, `game/credits` |
| pokedex | `pokedex/index` + `pokedex/<species>` |
| world | `world/index`, `world/kanto`, `world/johto`, `world/hoenn` + `world/<location>` |
| battles | `battles/index`, `battles/kanto`, `battles/johto`, `battles/hoenn` (gyms & league), `battles/rivals`, `battles/rematches`, `battles/trainers` |
| data | `data/moves/index` + `data/moves/<move>`, `data/abilities/index` + …, `data/items/index` + `data/items/<item>`, `data/tms`, `data/berries`, `data/typechart` |
| guides | `guides/breeding`, `guides/shiny`, `guides/legendaries`, `guides/gifts`, `guides/pokeblocks`, `guides/completion`, `guides/walkthrough` |

Further pages are allowed (`ctx.add_page("guides/walkthrough-kanto", title, parent="guides/walkthrough")`,
with `nav=71` if it should be in the sidebar); report sitemap wishes.
The start page links `world/<region>` and `battles/<region>` on the journey cards and shows tiles for
`pokedex/index, data/typechart, data/moves/index, data/abilities/index, data/items/index, data/tms,
guides/walkthrough, game/start, battles/trainers, guides/breeding` when they exist; its counters come
from the registry (number of species, moves, abilities, items, locations, trainers).

## 6. Search

Every registered entry with `search=True` goes into `assets/search-<lang>.js`
(`[title, kind, url, keywords, icon, sub]`), in kind order, inside a kind in registration order
(register in the order you want ties to appear, e.g. Pokédex order).

* `title` what is matched first and shown; `sub` a short second line shown at the right
  (region of a place, class of a trainer, description of an ability) and also searched;
  `keywords` extra words that are searched but not shown (types, number “#001”, alternative names);
  `icon` small image: `ctx.asset_rel("icon", sp.slug)` (32 px) or `ctx.asset_rel("item", it.slug)` (24 px).
* Client: opens with the top-bar field, `/` or Ctrl/Cmd+K; ↑ ↓ Enter Esc; accent and umlaut insensitive
  (`gluh`, `glueh` and `glüh` find “Glühbirne”); every word of the query must match; ranking exact title >
  title prefix > word start > inside the title > keywords/sub; grouped by kind (7 per group, 40 if only one
  kind matches).

## 7. Components (`from common import html as H`)

Text parameters named `text/title/label/name` are escaped by the helper; `html/body/inner/cells` are inserted
as given (escape foreign text with `H.esc`). All link helpers return plain text when the target is not
registered. The gallery shows each one: `OUT/de/dev/gallery.html`.

### Basics, links, chips
| Call | Emits |
|---|---|
| `H.esc(s)`, `H.attrs({...})`, `H.sr(text)`, `H.dash(ctx)` | escaping; ` name="v"`; `<span class="sr">` (screen reader only); `<span class="none">—</span>` |
| `H.img(src, w, h, cls, alt)` | `<img … width height loading="lazy" decoding="async">` |
| `H.link(ctx, kind, key, text=None, cls=None, html=None)` | `<a href="…">text</a>` or the bare text; `text` defaults to the registered title |
| `H.page_link(ctx, path, text=None)` | same for a page path |
| `H.species_link(ctx, sp, icon=False)` | `<a class="mon-link"><img class="px mon-ic"><span>Name</span></a>` with icon, plain link without |
| `H.move_link(ctx, mv)`, `H.ability_link(ctx, ab)`, `H.item_link(ctx, it, icon=False)`, `H.location_link(ctx, key, text)` | links; `item_link(icon=True)` → `<a class="item-link"><img class="px item-ic"><span>…` |
| `H.chip(text, tone=None)` | `<span class="chip chip-<tone>">`; tones `jade gold muted warn kanto johto hoenn` |
| `H.chips([html…])`, `H.region_chip(ctx, "kanto")` | `<span class="chips">…`; region name as a chip |
| `H.type_chip(ctx, ty)`, `H.types(ctx, sp.types)` | `<span class="type t-fire">Feuer</span>`; `<span class="types">` (a doubled single type once). `ty`: Type, id or `"TYPE_FIRE"` |
| `H.cat_chip(ctx, "physical", icon_only=False)` | `<span class="cat"><img class="px" 16×16>Physisch</span>` (the game's category icon) |
| `H.time_chip(ctx, "night")` | `<span class="tod tod-night">Nachts</span>` |

### Images (pixel art, whole-number scales, class `px`)
| Call | Emits |
|---|---|
| `H.sprite(ctx, sp, shiny=False, scale=2)` | front sprite, 64 px × scale |
| `H.sprite_plate(ctx, sp, shiny=False, scale=2, caption=None)` | `<figure class="plate [plate-shiny]"><img><figcaption>` |
| `H.sprite_pair(ctx, sp, scale=2)` | `<div class="plates">` regular + shiny plate with captions |
| `H.mon_icon(ctx, sp, scale=1)`, `H.item_icon(ctx, it, scale=1)`, `H.trainer_pic(ctx, tr_or_pic_id, scale=1)` | 32 px box icon, 24 px bag icon, 64 px trainer picture |
| `H.plate(inner_html, caption_html=None)` | the plate around any image |

### Page structure and text
| Call | Emits |
|---|---|
| `H.section(title, body, id=None, intro=None)` | `<section class="sec" id><h2>…</h2><p class="sec-intro">…</p>body</section>` – feeds the outline |
| `H.sub(title, body, id=None)` | `<section class="sub"><h3>` |
| `H.prose(html)`, `H.p(text, cls=None)`, `H.ul([html…])` | `<div class="prose">` (comfortable line length), paragraph, list |
| `H.steps([html…])` | `<ol class="steps">` numbered steps with a connecting line (walkthrough, how-to) |
| `H.callout(ctx, "note"\|"tip"\|"warning", html, title=None)` | `<aside class="callout callout-tip" role="note"><p class="callout-title">Tipp</p><div class="callout-body">` |
| `H.details(summary, body, open=False)` | `<details class="fold"><summary>` (FAQ; works without JS) |
| `H.card(body, title=None, cls=None, id=None)` | `<div class="card"><h3 class="card-title">` |
| `H.grid([html…], size="s"\|"m"\|"l")` | `<div class="grid grid-m">` (min column 9 / 15 / 22 rem) |
| `H.split(main, side)` | two columns (3:2) from 768 px, stacked below |
| `H.tile(href, title, text=None, media=None, meta=None)` | `<a class="tile"><span class="tile-media"><span class="tile-body"><span class="tile-title">…` (`href=None`: not a link) |
| `H.page_tile(ctx, path, text=None, media=None, meta=None, title=None)` | tile for a registered page, **`None` if it does not exist** (filter before `H.grid`) |
| `H.kv([(label, value_html)…])` | `<dl class="kv"><div><dt><dd>` responsive key-value grid; pairs with value `None` are dropped |
| `H.meter(value, maximum, label=None)` | `<span class="meter"><i style="width:…%">` |
| prev/next, breadcrumbs, title, eyebrow, lead, chips, aside, outline, footer | `ctx.end(...)` |

### Tables, tabs, filters
`H.table(cols, rows, *, caption=None, cls=None, stack=True, id=None, row_attrs=None, foot=None)`
* `cols`: `[label]` or `[(label, flags)]`; flags: `num` (right aligned), `main` (the row's title cell),
  `min` (narrow), `c` (centred), `hide-s` (hidden on phones). `rows`: `[[cell_html or None]]` (None → dash).
* Emits `<div class="tbl-wrap"><table class="tbl tbl-stack"><thead>…<td class="num" data-l="Label">`. Below
  640 px every row becomes a small card: the `main` cell on top, the other cells as labelled values in three
  columns. `stack=False` keeps the table and scrolls it inside its own frame (matrices).
* `row_attrs`: one dict per row, e.g. `H.filter_attrs(...)`.

`H.tabs([(label, html[, key])…], id)` → `<div class="tabs" data-tabs id><section class="tab" id="<id>-<key>"><h3 class="tab-h">`.
Without JS all panels are shown under their headings; with JS a tab list (arrow keys, Home/End); a link to
`#<id>-<key>` or to an element inside a panel opens that tab.

`H.filter_bar(ctx, target_id, *, text=True, facets=(), placeholder=None, label=None)` – client-side filter of
the element with that id. Every descendant with `data-text` is one item; a `[data-group]` ancestor is hidden
while it has no visible item. Hidden without JS. State in the URL (`?q=…&type=fire`).
* Item attributes: `H.filter_attrs(text=[name, "#001"], type=["grass", "poison"], region="kanto", **custom)`
  → `{"data-text": folded words, "data-type": "grass poison", …}`; pass them as `data=` / `row_attrs`.
* Facets: `H.type_facet(ctx)` (key `type`, type slugs), `H.region_facet(ctx)` (key `region`), or
  `{"key": "use", "label": "…", "options": [(value, label)…], "style": "chips"|"select"}` (default chips up to
  6 options). One value per facet at a time; an item matches when the value is one of its space-separated values.

### Entity grids
| Call | Emits |
|---|---|
| `H.ent(href, title, media=None, meta=None, data=None, note=None, aside=None)` | `<li data-…><a class="ent"><span class="ent-m">media</span><span class="ent-b"><span class="ent-t">title</span><span class="ent-x">meta</span><span class="ent-n">note</span></span><span class="ent-a">aside</span></a></li>` |
| `H.species_tile(ctx, sp, number=None, note=None, region=None, extra_text=())` | the same for a Pokémon: box icon, `#001`, name, types; filter attributes (`text`, `type`, `region`) included |
| `H.ent_grid(items, id=None, cls=None, group=None)` | `<ul class="ents">`; `cls="ents-wide"` for wider tiles; `group` sets `data-group` |

### Game components
| Call | Input → output |
|---|---|
| `H.stat_bars(ctx, sp.stats, total=True)` | `{"hp","atk","def","spa","spd","spe"}` → `<dl class="stats">` rows with value and bar (five colour tiers), total row. Stat names are the game's (`H.stat_names(ctx)`). |
| `H.type_matchups(ctx, sp.types)` | damage taken by a Pokémon with these types, grouped by multiplier (×1 left out) → `<dl class="matchups"><div class="mu xhi"><dt>×2</dt><dd>chips` |
| `H.ability_list(ctx, [(ability, hidden)…])` | `<ul class="abils">` name (linked), “hidden” chip, description |
| `H.evolution_chain(ctx, root, current=None)` | `root = {"species": sp, "how": None, "children": [{"species": sp2, "how": "Lv. 16", "children": […]}]}` → horizontal tree with sprites and arrows (vertical on phones); `current` is marked and not linked. You write the `how` texts. |
| `H.move_table(ctx, rows, first=None, id=None, row_attrs=None)` | `rows = [(first_cell_html, Move)]` or `[Move]` → table Move, Type, Category, Power, Accuracy, PP (phones: two lines per move). Cells per move are cached. |
| `H.learnset(ctx, id, level=[(lv, Move)], tm=[(label, Move)], tutor=[Move], egg=[Move], extra=())` | the learnsets as tabs (empty ones left out) |
| `H.encounter_block(ctx, method, rows, times=None, title=None, note=None)` / `H.encounters(ctx, blocks)` | `rows = [{"species": sp, "lo": 3, "hi": 5, "rate": 20, "note": …}]`, `times` None or `["night"]`, `method` one of `land cave water rock_smash old_rod good_rod super_rod` → heading with method marker and time chips, table Pokémon / types / level / rate with bar (phones: one line per Pokémon). A method whose table changes with the time of day = several blocks (see `_gallery_data.enc_blocks`). |
| `H.where_table(ctx, rows, id=None)` | `rows = [{"key": mapsec const, "name": …, "region": "kanto", "method": "land" or "method_text": …, "times": None\|[…], "lo", "hi", "rate", "note"}]` → table Location / Region / Method / Time / Level / Rate with filter attributes |
| `H.team_member(ctx, m, detail=True)` | `m = {"species": sp, "level": 12 or "level_text": "Lv. 44–48", "item": Item, "ability": Ability, "nature": text, "moves": [Move], "shiny": bool, "note": text}` |
| `H.trainer_card(ctx, name, team, *, cls_name=None, pic=None, id=None, detail=True, double=False, reward=None, meta=(), note=None, data=None)` | `<article class="trainer" id>` header (picture, class, name, chips) + `<ol class="team">`; `detail=False` gives the compact card (icon, name, level per line) for route trainers. Levels must be the effective ones (`trainers.effective_team`). |
| `H.trainer_list([cards…], id=None)` | cards in columns |
| `H.item_list(ctx, [{"item": it, "qty": 1, "hidden": False, "how": text, "note": text}…])` | `<ul class="items">` icon, linked name, ×qty, “hidden” chip, where/how |
| `H.shop_table(ctx, [{"item": it, "price": None, "note": text}…], caption=None)` | table Item / Price (/ Note); `price=None` = the item's own price |

Not components but ready in the stylesheet: type chart classes (`pages/typechart.py`), start page classes
(`pages/home.py`). Colours of types come from the game's type labels (`.t-<slug>` sets `--t`).

## 8. Images

`ctx.asset(kind, name)` / the image helpers export on demand (shared by both languages, pruned when unused):

| kind | name | size |
|---|---|---|
| `mon`, `shiny` | `species.slug` | 64×64 front sprite (regular / shiny palette) |
| `icon` | `species.slug` | 32×32 box icon |
| `item` | `item.slug` | 24×24 bag icon |
| `trainer` | `trainer.pic` | 64×64 |
| `category` | `physical` `special` `status` | 16×16 |
| `types` | type slug | 32×16, the game's own label graphic (language of the graphic; the site uses `H.type_chip` instead) |
| fixed | `assets/img/mark.png`, `favicon-32.png`, `favicon-180.png`, `title.png` (720×480), `title-2x.png` (480×320), `logo.png` | always present |

A missing graphic is a build warning. Own images: `ctx.write_image("pokeblock/red.png", img)` then
`ctx.asset("pokeblock", "red")`. Always give width/height (the helpers do); scale pixel art by whole factors.

## 9. Design rules the components already follow (keep them when composing)

* One `h1` (from `ctx.end`), sections with `H.section` (h2), inside them `H.sub` (h3). No own headings by hand.
* No inline styles, no own classes, no own scripts in page HTML. Long lists get an `H.filter_bar`.
* Pages must read completely without JavaScript (tabs unfold, filters disappear, lists are complete).
* Phone first: nothing may scroll sideways at 360 px. Use `H.table` (stacks) instead of hand-made tables;
  keep chips short; long German compounds wrap automatically.
* Type colours only through `H.type_chip`/`H.types`; region colours only through `H.region_chip`.
* Theme, language switch, search, menu, focus styles, reduced motion: handled by the shell.

## 10. What the checks look at (`common/checks.py`)

* Visible text and `alt/title/aria-label/placeholder` of every page (not of `dev/…` pages): checksums;
  ROM/patch file endings and tools; constants (`SPECIES_…`, `FLAG_…`, any `AAA_BBB_CCC`), code symbols
  (`gText_…`), source file names (`*.c .h .inc .json .py …`); tool names; leftover placeholders (`[OFFEN`,
  `TODO`, `{name}`).
* Links: every `href`/`src` must resolve (pages of the language, anchors, assets on disk, the same page in
  the other language); external addresses are errors unless listed in `site_config.COMMUNITY_LINKS`.
* Both languages register exactly the same paths; every registered page is rendered; `STRINGS` keys match.
