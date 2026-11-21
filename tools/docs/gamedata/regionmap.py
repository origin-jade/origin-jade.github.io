"""Region map pictures (Town Map) and their map section grids.

    regionmap.REGIONS              -> ("kanto", "johto", "hoenn")
    regionmap.render(region)       -> Image "RGB", 240x160 (the map BG as shown on screen)
    regionmap.grid(region)         -> {"x0", "y0", "cell", "cols", "rows"}
    regionmap.cells(region)        -> {"MAPSEC_...": [(col, row), ...]}   (layout + markers)
    regionmap.layout_cells(region) -> the cells of the layout grid only
    regionmap.marker_cells(region) -> the cells of places that are not on the grid
    regionmap.entries(region)      -> {"MAPSEC_...": (x, y, width, height)}
    regionmap.region_of(mapsec)    -> "kanto" | "johto" | "hoenn" | None

Source files that define the format:

    src/region_map.c
        gRegionMapInfos: palette, tile sheet and tilemap per map type
        (REGION_MAP_HOENN -> map.*, REGION_MAP_KANTO -> map_kanto.*,
        REGION_MAP_JOHTO -> map_johto.*, REGION_MAP_JK -> map_jk.*, all in
        graphics/pokenav/region_map/).
        LoadRegionMapGfx: the map is BG2 as an affine background, screen size 2
        (64x64 tiles, one byte per tilemap entry, no flips, no palette bits),
        256 colour tiles; the .pal file is loaded to BG colours 0x70-0x9F
        (LoadPalette(..., BG_PLTT_ID(7), 3 * PLTT_SIZE_4BPP)), so pixel value
        p shows colour p - 0x70 of the .pal file. Unzoomed the BG is shown
        1:1 without scroll (CalcZoomScrollParams(0, 0, 0, 0, 0x100, 0x100, 0)),
        so the screen is the top-left 240x160 pixels of the BG.
        MAP_WIDTH 28, MAP_HEIGHT 15, MAPCURSOR_X_MIN 1, MAPCURSOR_Y_MIN 2:
        GetMapSecIdAt(x, y) reads layout[y - 2][x - 1], x and y in 8 px tiles
        of the screen, so layout cell (0, 0) is at pixel (8, 16).
    src/data/region_map/region_map_layout.h         Hoenn grid
    src/data/region_map/region_map_layout_kanto.h   Kanto grid
    src/data/region_map/region_map_layout_johto.h   Johto grid
    src/data/region_map/region_map_layout_jk.h      combined Johto + Kanto grid
        Every grid is one layer of MAP_HEIGHT rows x MAP_WIDTH map sections.
        There is no second layer for caves: places that are not on the grid
        only have an entry rectangle (struct RegionMapLocation x, y, width,
        height, in grid cells).
    src/data/region_map/region_map_sections.json
        "hns_map_sections" becomes gRegionMapEntries (and, in this order from
        1, the MAPSEC_ enum). Its rectangles are in the coordinates of the
        Hoenn, the Kanto and the Johto map, each for its own map sections.
    src/region_map.c sRegionMapEntries_Johto
        The rectangles on the combined Johto + Kanto map
        (GetActiveRegionMapEntries).
    src/pokedex_area_screen.c
        Maps of the towns-and-routes groups: BuildAreaGlowTilemap marks every
        cell whose GetRegionMapSecIdAt() equals the map section of the map.
        Maps of the dungeon and special-area groups: CreateAreaMarkerSprites
        puts one round marker on the centre of the entry rectangle
        (x = 8 * (entry.x + 1) + 4 + 4 * (width - 1), the same for y). The
        screen shows the map 8 px lower than the Town Map and moves glow and
        markers with it, so the cell geometry is the same as here.
    src/level_scaling.c IsHoennMapsec, constants in
    src/data/region_map/region_map_sections.constants.json.txt
        Which map sections belong to Hoenn, Kanto (KANTO_MAPSEC_START..END)
        and Johto (JOHTO_MAPSEC_START..END).

cells() is the layout grid plus, for the map sections of that region that
have no cell on the grid (caves, towers, forests), the cells of their entry
rectangle - the place where the Pokedex area screen puts the marker.

The game itself (IS_HNS, GetRegionMapType) shows three maps: Hoenn, Kanto
(until Johto was visited) and the combined Johto + Kanto map afterwards. The
Johto-only map is kept in gRegionMapInfos but no code path selects it. This
module draws Kanto and Hoenn as the game does and uses the Johto-only picture
and grid for "johto"; "jk" (the combined map) is available as an extra key
that is not part of REGIONS.
"""
import json
import re

from PIL import Image

from . import repo_path

REGIONS = ("kanto", "johto", "hoenn")

GFX_DIR = "graphics/pokenav/region_map"
LAYOUT_DIR = "src/data/region_map"

# region -> (base name of .png/.bin/.pal, layout header, layout symbol)
SOURCES = {
    "kanto": ("map_kanto", "region_map_layout_kanto.h", "sRegionMapSections_Kanto"),
    "johto": ("map_johto", "region_map_layout_johto.h", "sRegionMapSections_Johto"),
    "hoenn": ("map", "region_map_layout.h", "sRegionMap_MapSectionLayout"),
    "jk": ("map_jk", "region_map_layout_jk.h", "sRegionMapSections_JK"),
}

# src/region_map.c
MAP_WIDTH = 28
MAP_HEIGHT = 15
MAPCURSOR_X_MIN = 1
MAPCURSOR_Y_MIN = 2

TILE_PX = 8
BG_TILES = 64               # affine BG, screen size 2: 64x64 tiles
SCREEN_W, SCREEN_H = 240, 160
PAL_BASE = 0x70             # BG_PLTT_ID(7)
PAL_COUNT = 48              # 3 * PLTT_SIZE_4BPP

# Preprocessor symbols of the build (Makefile: GAME_VERSION := POKEMON_HNS).
DEFINES = {"IS_HNS": 1, "IS_FRLG": 0}

SECTIONS_JSON = "src/data/region_map/region_map_sections.json"
SECTION_CONSTANTS = "src/data/region_map/region_map_sections.constants.json.txt"
REGION_MAP_C = "src/region_map.c"
LEVEL_SCALING_C = "src/level_scaling.c"

_images = {}
_layout_cells = {}
_marker_cells = {}
_cells = {}
_entries = {}
_region_of = {}
_sections = None
_ranges = None


def _check(region):
    if region not in SOURCES:
        raise ValueError("unknown region: %r" % (region,))


def _q(c):
    """8 bit colour channel as the hardware shows it (5 bits)."""
    c5 = c >> 3
    return (c5 << 3) | (c5 >> 2)


def _read_palette(rel):
    """JASC .pal -> list of (r, g, b)."""
    words = open(repo_path(rel), encoding="ascii").read().split()
    if words[:1] != ["JASC-PAL"]:
        raise ValueError("not a JASC palette: %s" % rel)
    count = int(words[2])
    vals = [int(v) for v in words[3:3 + 3 * count]]
    return [tuple(_q(v) for v in vals[i:i + 3]) for i in range(0, len(vals), 3)]


def _read_tiles(rel):
    """Indexed PNG -> list of 8x8 tiles (64 bytes of colour indices each),
    in reading order like the 8bpp conversion."""
    with Image.open(repo_path(rel)) as img:
        if img.mode != "P":
            raise ValueError("%s is not an indexed PNG (%s)" % (rel, img.mode))
        width, height = img.size
        data = img.tobytes()
    tiles = []
    for ty in range(height // TILE_PX):
        for tx in range(width // TILE_PX):
            start = ty * TILE_PX * width + tx * TILE_PX
            tiles.append(b"".join(data[start + row * width: start + row * width + TILE_PX]
                                  for row in range(TILE_PX)))
    return tiles


def render(region):
    """The region map BG as the unzoomed Town Map shows it, 240x160, mode "RGB"."""
    _check(region)
    img = _images.get(region)
    if img is not None:
        return img.copy()
    base = SOURCES[region][0]
    tiles = _read_tiles("%s/%s.png" % (GFX_DIR, base))
    pal = _read_palette("%s/%s.pal" % (GFX_DIR, base))
    with open(repo_path("%s/%s.bin" % (GFX_DIR, base)), "rb") as f:
        tilemap = f.read()
    if len(tilemap) != BG_TILES * BG_TILES:
        raise ValueError("%s.bin: expected %d bytes, found %d" % (base, BG_TILES * BG_TILES, len(tilemap)))

    # BG colours: only 0x70-0x9F come from the map palette; everything else
    # is not part of the map and is drawn black.
    colors = [(0, 0, 0)] * 256
    for i, c in enumerate(pal[:PAL_COUNT]):
        colors[PAL_BASE + i] = c
    flat = []
    for c in colors:
        flat += c

    blank = bytes(TILE_PX * TILE_PX)
    out = Image.new("P", (SCREEN_W, SCREEN_H))
    out.putpalette(flat)
    for ty in range(SCREEN_H // TILE_PX):
        for tx in range(SCREEN_W // TILE_PX):
            index = tilemap[ty * BG_TILES + tx]
            tile = tiles[index] if index < len(tiles) else blank
            out.paste(Image.frombytes("P", (TILE_PX, TILE_PX), tile), (tx * TILE_PX, ty * TILE_PX))
    img = out.convert("RGB")
    _images[region] = img
    return img.copy()


def grid(region):
    """Where the layout grid lies in the rendered picture."""
    _check(region)
    return {
        "x0": MAPCURSOR_X_MIN * TILE_PX,
        "y0": MAPCURSOR_Y_MIN * TILE_PX,
        "cell": TILE_PX,
        "cols": MAP_WIDTH,
        "rows": MAP_HEIGHT,
    }


def _resolve_conditionals(text):
    """Keep the lines the build keeps: #if NAME / #else / #endif with the
    names of DEFINES. Any other directive is an error."""
    out = []
    stack = []      # one bool per open #if: is the current branch kept
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            m = re.match(r"#\s*(if|else|endif)\b\s*(.*)$", s)
            if not m:
                raise ValueError("unsupported preprocessor line: %s" % s)
            word, arg = m.group(1), m.group(2).split("//")[0].strip()
            if word == "if":
                negate = arg.startswith("!")
                name = arg.lstrip("!").strip()
                if name not in DEFINES:
                    raise ValueError("unknown #if condition: %s" % s)
                stack.append(bool(DEFINES[name]) != negate)
            elif word == "else":
                stack[-1] = not stack[-1]
            else:
                stack.pop()
            continue
        if all(stack):
            out.append(line)
    return "\n".join(out)


def _layout(region):
    """The layout table as MAP_HEIGHT rows of MAP_WIDTH constant names."""
    _, header, symbol = SOURCES[region]
    rel = "%s/%s" % (LAYOUT_DIR, header)
    text = open(repo_path(rel), encoding="utf-8").read()
    text = _resolve_conditionals(text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    m = re.search(re.escape(symbol) + r"\s*\[MAP_HEIGHT\]\s*\[MAP_WIDTH\]\s*=\s*\{(.*)\}\s*;", text, re.S)
    if not m:
        raise ValueError("%s: table %s not found" % (rel, symbol))
    rows = [re.findall(r"\w+", row) for row in re.findall(r"\{([^{}]*)\}", m.group(1))]
    if len(rows) != MAP_HEIGHT or any(len(r) != MAP_WIDTH for r in rows):
        raise ValueError("%s: %s is not %d rows of %d map sections" % (rel, symbol, MAP_HEIGHT, MAP_WIDTH))
    return rows


def layout_cells(region):
    """Map section constant -> list of (col, row) cells of the layout grid, row by row."""
    _check(region)
    found = _layout_cells.get(region)
    if found is None:
        found = {}
        for row, names in enumerate(_layout(region)):
            for col, name in enumerate(names):
                if name != "MAPSEC_NONE":
                    found.setdefault(name, []).append((col, row))
        _layout_cells[region] = found
    return {name: list(pos) for name, pos in found.items()}


def _section_list():
    """The "hns_map_sections" of region_map_sections.json (enum order, first is 1)."""
    global _sections
    if _sections is None:
        with open(repo_path(SECTIONS_JSON), encoding="utf-8") as f:
            _sections = json.load(f)["hns_map_sections"]
    return _sections


def _section_ranges():
    """({name: enum value}, {"KANTO": (start, end), "JOHTO": ...}, first Hoenn
    value, set of the extra Hoenn sections)."""
    global _ranges
    if _ranges is not None:
        return _ranges
    number = {s["id"]: i + 1 for i, s in enumerate(_section_list())}
    # The first enum block of the constants template is the IS_HNS one.
    text = open(repo_path(SECTION_CONSTANTS), encoding="utf-8").read()
    text = text[:text.index("#else")]
    spans = {}
    for key in ("KANTO", "JOHTO"):
        start = re.search(r"#define\s+%s_MAPSEC_START\s+(MAPSEC_\w+)" % key, text)
        end = re.search(r"#define\s+%s_MAPSEC_END\s+(MAPSEC_\w+)" % key, text)
        if not start or not end:
            raise ValueError("%s: %s_MAPSEC_START/END not found" % (SECTION_CONSTANTS, key))
        spans[key] = (number[start.group(1)], number[end.group(1)])
    # IsHoennMapsec: everything from one section up to MAPSEC_NONE, plus a few named ones.
    text = open(repo_path(LEVEL_SCALING_C), encoding="utf-8").read()
    m = re.search(r"bool32\s+IsHoennMapsec\s*\([^)]*\)\s*\{(.*?)\n\}", text, re.S)
    first = m and re.search(r"mapSecId\s*>=\s*(MAPSEC_\w+)\s*&&\s*mapSecId\s*<\s*MAPSEC_NONE", m.group(1))
    if not first:
        raise ValueError("%s: IsHoennMapsec has changed" % LEVEL_SCALING_C)
    extra = set(re.findall(r"mapSecId\s*==\s*(MAPSEC_\w+)", m.group(1)))
    _ranges = (number, spans, number[first.group(1)], extra)
    return _ranges


def _is_hoenn(mapsec):
    number, _, first_hoenn, extra = _section_ranges()
    return mapsec in extra or number.get(mapsec, 0) >= first_hoenn


def _belongs(mapsec, region):
    """Is this map section a place of the region (by the game's enum ranges)."""
    number, spans, _, _ = _section_ranges()
    if mapsec not in number:
        return False
    if _is_hoenn(mapsec):
        return region == "hoenn"
    if region == "jk":
        return True
    if region in ("kanto", "johto"):
        lo, hi = spans[region.upper()]
        return lo <= number[mapsec] <= hi
    return False


def entries(region):
    """Map section constant -> (x, y, width, height) in grid cells: the entry
    table the game reads while this map is shown."""
    _check(region)
    found = _entries.get(region)
    if found is None:
        found = {}
        if region == "jk":
            text = open(repo_path(REGION_MAP_C), encoding="utf-8").read()
            start = text.index("sRegionMapEntries_Johto[]")
            body = text[start:text.index("};", start)]
            for m in re.finditer(r"\[(MAPSEC_\w+)\]\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,", body):
                rect = tuple(int(v) for v in m.group(2, 3, 4, 5))
                # Each entry is written once per language, with the same numbers.
                if found.setdefault(m.group(1), rect) != rect:
                    raise ValueError("%s: two rectangles for %s" % (REGION_MAP_C, m.group(1)))
        else:
            for s in _section_list():
                # Sections without coordinates are not on any of these maps.
                if "x" in s and "y" in s:
                    found[s["id"]] = (int(s["x"]), int(s["y"]), int(s.get("width", 1)), int(s.get("height", 1)))
        _entries[region] = found
    return dict(found)


def marker_cells(region):
    """Cells of the entry rectangle of every map section of the region that
    has no cell on the layout grid (where the area screen puts its marker)."""
    _check(region)
    found = _marker_cells.get(region)
    if found is None:
        # A section that is drawn on the grid of any of the maps needs no marker.
        on_grid = set(layout_cells(region))
        if region in REGIONS:
            for other in REGIONS:
                on_grid.update(layout_cells(other))
        found = {}
        for name, (x, y, width, height) in entries(region).items():
            if name in on_grid or not _belongs(name, region):
                continue
            # (0, 0, 1, 1) is the placeholder of sections without a place on the map.
            if (x, y, width, height) == (0, 0, 1, 1):
                continue
            pos = [(col, row) for row in range(y, y + height) for col in range(x, x + width)
                   if 0 <= col < MAP_WIDTH and 0 <= row < MAP_HEIGHT]
            if pos:
                found[name] = pos
        _marker_cells[region] = found
    return {name: list(pos) for name, pos in found.items()}


def cells(region):
    """Map section constant -> list of (col, row): the layout grid and the markers."""
    _check(region)
    found = _cells.get(region)
    if found is None:
        found = layout_cells(region)
        found.update(marker_cells(region))
        _cells[region] = found
    return {name: list(pos) for name, pos in found.items()}


def region_of(mapsec):
    """First region of REGIONS that has a cell for this map section."""
    if mapsec not in _region_of:
        _region_of[mapsec] = next((r for r in REGIONS if mapsec in cells(r)), None)
    return _region_of[mapsec]
