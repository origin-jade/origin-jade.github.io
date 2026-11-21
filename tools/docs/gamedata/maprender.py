"""Flat pictures of whole maps (tile layers only, no object events).

    img = maprender.render("PalletTown_Frlg")     # PIL.Image, mode "RGB", 16 px per block
    w, h = maprender.layout_size("PalletTown_Frlg")   # size in blocks
    maprender.save_png(img, "/tmp/PalletTown_Frlg.png")

The format is defined by these sources:
    data/maps/<dir>/map.json         "layout": id of the layout
    data/layouts/layouts.json        blockdata path, width, height, tilesets, layout_version
    tools/mapjson/mapjson.cpp        layout_version -> MapLayout.layoutVersion (missing = emerald)
    include/global.fieldmap.h        block bits (metatile id = bits 0-9), LAYOUT_VERSION_*
    include/fieldmap.h               NUM_TILES/METATILES/PALS_IN_PRIMARY(_EMERALD), totals,
                                     NUM_TILES_PER_METATILE (8: two layers of 2x2 tiles)
    src/fieldmap.c                   GetNumTilesInPrimary / GetNumMetatilesInPrimary /
                                     GetNumPalsInPrimary (chosen by the layout version),
                                     CopyTilesetToVram, LoadTilesetPalette
    src/field_camera.c               DrawMetatileAt / DrawMetatile
    src/data/tilesets/headers.h      gTileset_X -> tiles, palettes and metatiles symbols
    src/data/tilesets/graphics.h     tiles and palette files of these symbols
    src/graphics.c                   the same for gTileset_General
    src/data/tilesets/metatiles.h    metatiles.bin of these symbols

The primary/secondary split depends on the layout, not on the tileset:
layouts with version "frlg" or "hns" use 640 tiles, 640 metatiles and 7
palettes for the primary tileset, all others ("emerald") 512, 512 and 6.
Tiles are read from the source tiles.png, palettes from the JASC .pal files.
Both layers of a metatile are drawn, whatever its layer type is. Tile
animations, door animations and night palettes are not applied.
"""
import json
import os
import re
import struct

from PIL import Image

try:
    from . import REPO
except ImportError:  # used as a plain script module
    REPO = os.environ.get("OJ_REPO") or os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))

BLOCK_PX = 16
TILE_PX = 8
TILES_PER_METATILE = 8      # NUM_TILES_PER_METATILE
NUM_TILES_TOTAL = 1024
NUM_METATILES_TOTAL = 1024
NUM_PALS_TOTAL = 13
METATILE_ID_MASK = 0x03FF   # MAPGRID_METATILE_ID_MASK

# (tiles, metatiles, palettes) in the primary tileset per layout version,
# see GetNumTilesInPrimary and friends in src/fieldmap.c.
PRIMARY_LIMITS = {
    "emerald": (512, 512, 6),
    "frlg": (640, 640, 7),
    "hns": (640, 640, 7),
}

_BLANK_TILE = bytes(TILE_PX * TILE_PX)
_BLACK_PAL = [(0, 0, 0)] * 16

# Module-level caches.
_layouts = None         # layout id -> layout dict
_map_layout = {}        # map dir -> layout dict
_tileset_files = None   # gTileset_X -> (tiles png, [palette files], metatiles.bin)
_tilesets = {}          # gTileset_X -> _Tileset
_tile_sheets = {}       # tiles png path -> list of 64-byte tiles
_palettes = {}          # .pal path -> list of 16 (r, g, b)
_metatile_sets = {}     # (primary, secondary, version) -> _MetatileSet


def _path(rel):
    return os.path.join(REPO, rel)


def _read_text(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return f.read()


class _Tileset:
    """Tiles, palettes and metatile entries of one tileset."""

    def __init__(self, label, tiles, palettes, metatiles):
        self.label = label
        self.tiles = tiles          # list of 64-byte strings (colour index per pixel)
        self.palettes = palettes    # list of lists of 16 (r, g, b)
        self.metatiles = metatiles  # tuple of u16 tile entries, 8 per metatile


def _load_tileset_files():
    """Read the tileset tables of the source: label -> files."""
    global _tileset_files
    if _tileset_files is not None:
        return _tileset_files
    headers = _read_text("src/data/tilesets/headers.h")
    # gTileset_General has its tiles and palettes in src/graphics.c.
    graphics = _read_text("src/data/tilesets/graphics.h") + _read_text("src/graphics.c")
    metatiles = _read_text("src/data/tilesets/metatiles.h")

    # Symbol -> file for tiles: the built file is tiles.4bpp[.lz|.smol|...],
    # its source is the PNG next to it.
    tiles_of = {}
    for m in re.finditer(r'\b(gTilesetTiles_\w+)\[\]\s*=\s*INCBIN_U\d+\("([^"]+)"\)', graphics):
        tiles_of[m.group(1)] = re.sub(r"\.4bpp(\.\w+)?$", ".png", m.group(2))

    # Symbol -> ordered palette files (.gbapal is built from the .pal).
    pals_of = {}
    for m in re.finditer(r"\b(gTilesetPalettes_\w+)\[\]\[16\]\s*=\s*\{(.*?)\};", graphics, re.S):
        files = re.findall(r'INCBIN_U16\("([^"]+)"\)', m.group(2))
        pals_of[m.group(1)] = [re.sub(r"\.gbapal$", ".pal", f) for f in files]

    metatiles_of = {}
    for m in re.finditer(r'\b(gMetatiles_\w+)\[\]\s*=\s*INCBIN_U16\("([^"]+)"\)', metatiles):
        metatiles_of[m.group(1)] = m.group(2)

    table = {}
    for m in re.finditer(r"const struct Tileset (gTileset_\w+)\s*=\s*\{(.*?)\};", headers, re.S):
        body = m.group(2)
        fields = dict(re.findall(r"\.(\w+)\s*=\s*([^,\s]+)\s*,", body))
        table[m.group(1)] = (
            tiles_of.get(fields.get("tiles")),
            pals_of.get(fields.get("palettes")),
            metatiles_of.get(fields.get("metatiles")),
        )
    _tileset_files = table
    return table


def _load_tile_sheet(rel):
    """Split an indexed tiles.png into 8x8 tiles of colour indices 0-15."""
    sheet = _tile_sheets.get(rel)
    if sheet is not None:
        return sheet
    if not os.path.isfile(_path(rel)):
        raise ValueError("tile sheet not found: %s" % rel)
    with Image.open(_path(rel)) as img:
        if img.mode not in ("P", "L", "1"):
            raise ValueError("tile sheet is not an indexed image: %s (mode %s)" % (rel, img.mode))
        if img.mode == "1":
            img = img.convert("L").point(lambda v: 1 if v else 0)
        width, height = img.size
        # Only the low 4 bits of a pixel are kept by the 4bpp conversion.
        data = img.tobytes().translate(bytes(i & 15 for i in range(256)))
    sheet = []
    for ty in range(height // TILE_PX):
        for tx in range(width // TILE_PX):
            start = ty * TILE_PX * width + tx * TILE_PX
            sheet.append(b"".join(data[start + row * width: start + row * width + TILE_PX]
                                  for row in range(TILE_PX)))
    _tile_sheets[rel] = sheet
    return sheet


def _load_palette(rel):
    """Read a JASC palette file: 16 (r, g, b) tuples."""
    pal = _palettes.get(rel)
    if pal is not None:
        return pal
    if not os.path.isfile(_path(rel)):
        raise ValueError("palette not found: %s" % rel)
    lines = _read_text(rel).split()
    if lines[:1] != ["JASC-PAL"]:
        raise ValueError("not a JASC palette: %s" % rel)
    count = int(lines[2])
    values = [int(v) for v in lines[3:3 + count * 3]]
    pal = [tuple(values[i:i + 3]) for i in range(0, len(values), 3)]
    pal = (pal + _BLACK_PAL)[:16]
    _palettes[rel] = pal
    return pal


def _load_tileset(label):
    tileset = _tilesets.get(label)
    if tileset is not None:
        return tileset
    files = _load_tileset_files().get(label)
    if files is None:
        raise ValueError("tileset %s is not defined in src/data/tilesets/headers.h" % label)
    tiles_png, pal_files, metatiles_bin = files
    if not tiles_png or pal_files is None or not metatiles_bin:
        raise ValueError("tileset %s: tiles, palettes or metatiles symbol not found" % label)
    if not os.path.isfile(_path(metatiles_bin)):
        raise ValueError("metatiles not found: %s" % metatiles_bin)
    with open(_path(metatiles_bin), "rb") as f:
        raw = f.read()
    count = len(raw) // 2
    tileset = _Tileset(
        label,
        _load_tile_sheet(tiles_png),
        [_load_palette(p) for p in pal_files],
        struct.unpack("<%dH" % count, raw[:count * 2]),
    )
    _tilesets[label] = tileset
    return tileset


class _MetatileSet:
    """Metatile pictures of one primary/secondary pair, drawn on demand."""

    def __init__(self, primary, secondary, version):
        self.primary = primary
        self.secondary = secondary
        self.num_tiles, self.num_metatiles, self.num_pals = PRIMARY_LIMITS[version]
        self.images = {}
        # Backdrop: colour 0 of palette 0.
        self.backdrop = self._palette(0)[0]

    def _palette(self, index):
        """Palette slot as loaded by LoadTilesetPalette: the low slots come
        from the primary tileset, the others from the same slot numbers of
        the secondary tileset."""
        source = self.primary if index < self.num_pals else self.secondary
        if index < len(source.palettes):
            return source.palettes[index]
        return _BLACK_PAL

    def _tile(self, index):
        """Tile as placed in VRAM by CopyTilesetToVram: primary tiles first,
        secondary tiles from the primary limit on."""
        if index < self.num_tiles:
            tiles = self.primary.tiles
        else:
            tiles = self.secondary.tiles
            index -= self.num_tiles
            if index >= NUM_TILES_TOTAL - self.num_tiles:
                return _BLANK_TILE
        return tiles[index] if index < len(tiles) else _BLANK_TILE

    def image(self, metatile_id):
        img = self.images.get(metatile_id)
        if img is None:
            img = self.images[metatile_id] = self._draw(metatile_id)
        return img

    def _draw(self, metatile_id):
        # Same choice as DrawMetatileAt in src/field_camera.c.
        if metatile_id < self.num_metatiles:
            entries = self.primary.metatiles
        else:
            entries = self.secondary.metatiles
            metatile_id -= self.num_metatiles
        start = metatile_id * TILES_PER_METATILE
        entries = entries[start:start + TILES_PER_METATILE]

        pixels = [self.backdrop] * (BLOCK_PX * BLOCK_PX)
        for n, entry in enumerate(entries):
            tile = self._tile(entry & 0x3FF)
            hflip = entry & 0x400
            vflip = entry & 0x800
            palette = self._palette(entry >> 12)
            # Entries 0-3 are the bottom layer (opaque), 4-7 the top layer
            # (colour index 0 is transparent); each layer is 2x2 tiles.
            opaque = n < 4
            ox = (n & 1) * TILE_PX
            oy = ((n >> 1) & 1) * TILE_PX
            for y in range(TILE_PX):
                sy = TILE_PX - 1 - y if vflip else y
                row = tile[sy * TILE_PX:sy * TILE_PX + TILE_PX]
                if hflip:
                    row = row[::-1]
                base = (oy + y) * BLOCK_PX + ox
                for x in range(TILE_PX):
                    c = row[x]
                    if c or opaque:
                        pixels[base + x] = palette[c]
        img = Image.new("RGB", (BLOCK_PX, BLOCK_PX))
        img.putdata(pixels)
        return img


def _metatile_set(primary_label, secondary_label, version):
    key = (primary_label, secondary_label, version)
    mset = _metatile_sets.get(key)
    if mset is None:
        mset = _MetatileSet(_load_tileset(primary_label), _load_tileset(secondary_label), version)
        _metatile_sets[key] = mset
    return mset


def _load_layouts():
    global _layouts
    if _layouts is None:
        rel = "data/layouts/layouts.json"
        if not os.path.isfile(_path(rel)):
            raise ValueError("%s not found" % rel)
        data = json.loads(_read_text(rel))
        _layouts = {l["id"]: l for l in data["layouts"] if l and "id" in l}
    return _layouts


def _layout_of(map_dir):
    """Layout dict of a map folder under data/maps."""
    layout = _map_layout.get(map_dir)
    if layout is not None:
        return layout
    rel = "data/maps/%s/map.json" % map_dir
    if not os.path.isfile(_path(rel)):
        raise ValueError("%s: %s not found" % (map_dir, rel))
    layout_id = json.loads(_read_text(rel)).get("layout")
    if not layout_id:
        raise ValueError("%s: map.json has no layout" % map_dir)
    layout = _load_layouts().get(layout_id)
    if layout is None:
        raise ValueError("%s: layout %s is not in data/layouts/layouts.json" % (map_dir, layout_id))
    for key in ("width", "height", "blockdata_filepath", "primary_tileset", "secondary_tileset"):
        if key not in layout:
            raise ValueError("%s: layout %s has no %s" % (map_dir, layout_id, key))
    _map_layout[map_dir] = layout
    return layout


def _layout_version(layout):
    """Layout version as written by mapjson: a missing value means emerald,
    and so does every value other than frlg and hns."""
    version = layout.get("layout_version") or "emerald"
    return version if version in ("frlg", "hns") else "emerald"


def layout_size(map_dir):
    """(width, height) of the map in blocks."""
    layout = _layout_of(map_dir)
    return int(layout["width"]), int(layout["height"])


def render(map_dir):
    """Draw the whole map at native size (16 px per block), mode "RGB"."""
    layout = _layout_of(map_dir)
    width, height = int(layout["width"]), int(layout["height"])
    if width <= 0 or height <= 0:
        raise ValueError("%s: layout %s has no area (%dx%d)" % (map_dir, layout["id"], width, height))
    rel = layout["blockdata_filepath"]
    if not os.path.isfile(_path(rel)):
        raise ValueError("%s: block data not found: %s" % (map_dir, rel))
    with open(_path(rel), "rb") as f:
        raw = f.read()
    if len(raw) < width * height * 2:
        raise ValueError("%s: block data %s has %d bytes, %dx%d blocks need %d"
                         % (map_dir, rel, len(raw), width, height, width * height * 2))
    blocks = struct.unpack("<%dH" % (width * height), raw[:width * height * 2])

    try:
        mset = _metatile_set(layout["primary_tileset"], layout["secondary_tileset"],
                             _layout_version(layout))
    except ValueError as e:
        raise ValueError("%s: %s" % (map_dir, e)) from None

    img = Image.new("RGB", (width * BLOCK_PX, height * BLOCK_PX), mset.backdrop)
    get = mset.image
    paste = img.paste
    i = 0
    for y in range(0, height * BLOCK_PX, BLOCK_PX):
        for x in range(0, width * BLOCK_PX, BLOCK_PX):
            paste(get(blocks[i] & METATILE_ID_MASK), (x, y))
            i += 1
    return img


GAP_COLOR = (16, 42, 34)     # where no map of the group lies


def _connections(map_dir):
    """[(direction, map id, offset in blocks)] of data/maps/<dir>/map.json."""
    with open(_path("data/maps/%s/map.json" % map_dir), encoding="utf-8") as f:
        data = json.load(f)
    return data["id"], [(c["direction"], c["map"], int(c["offset"])) for c in data.get("connections") or []]


def groups(map_dirs):
    """Split map folders into groups joined by up/down/left/right connections.
    -> [[(map_dir, x, y)]] with positions in blocks, the top left of each group at 0, 0;
    groups and members keep the order of map_dirs."""
    info = {d: _connections(d) for d in map_dirs}
    by_id = {info[d][0]: d for d in map_dirs}
    left, out = list(map_dirs), []
    while left:
        first = left.pop(0)
        pos = {first: (0, 0)}
        todo = [first]
        while todo:
            a = todo.pop(0)
            ax, ay = pos[a]
            aw, ah = layout_size(a)
            for direction, mid, off in info[a][1]:
                b = by_id.get(mid)
                if b is None or b in pos:
                    continue
                bw, bh = layout_size(b)
                if direction == "up":
                    pos[b] = (ax + off, ay - bh)
                elif direction == "down":
                    pos[b] = (ax + off, ay + ah)
                elif direction == "left":
                    pos[b] = (ax - bw, ay + off)
                elif direction == "right":
                    pos[b] = (ax + aw, ay + off)
                else:
                    continue
                left.remove(b)
                todo.append(b)
        x0 = min(x for x, _y in pos.values())
        y0 = min(y for _x, y in pos.values())
        out.append([(d, pos[d][0] - x0, pos[d][1] - y0) for d in map_dirs if d in pos])
    return out


def group_size(group):
    """(width, height) in blocks of one group of groups()."""
    w = max(x + layout_size(d)[0] for d, x, _y in group)
    h = max(y + layout_size(d)[1] for d, _x, y in group)
    return w, h


def render_group(group):
    """One picture of the connected maps of a group."""
    if len(group) == 1:
        return render(group[0][0])
    w, h = group_size(group)
    img = Image.new("RGB", (w * BLOCK_PX, h * BLOCK_PX), GAP_COLOR)
    for d, x, y in group:
        img.paste(render(d), (x * BLOCK_PX, y * BLOCK_PX))
    return img


def group_slug(group):
    """File name of the picture of a group."""
    return "_".join(slug(d) for d, _x, _y in group)


def dirs_of_group_slug(name):
    """Map folders of a picture file name, None when one of them does not exist."""
    dirs = [dir_of_slug(part) for part in name.split("_")]
    return None if None in dirs else dirs


def slug(map_dir):
    """File name of a map picture."""
    return map_dir.lower().replace("_", "-")


_SLUGS = {}


def dir_of_slug(name):
    """Map folder of a picture file name, None when there is no such map."""
    if not _SLUGS:
        for d in os.listdir(_path("data/maps")):
            if os.path.isfile(os.path.join(_path("data/maps"), d, "map.json")):
                _SLUGS[slug(d)] = d
    return _SLUGS.get(name)


def save_png(img, path):
    """Save a rendered map as a small PNG, always with the same bytes for the
    same picture. With at most 256 colours the picture is stored exactly as a
    palette image (palette sorted by colour value); with more colours it is
    stored as RGB."""
    img = img.convert("RGB")
    colors = img.getcolors(256)
    if colors is not None:
        ordered = sorted(c for _, c in colors)
        flat = [v for c in ordered for v in c]
        pal_img = Image.new("P", (1, 1))
        pal_img.putpalette(flat + flat[-3:] * (256 - len(ordered)))
        out = img.quantize(palette=pal_img, dither=Image.Dither.NONE)
        # The mapping must be exact; fall back to RGB if it is not.
        if out.convert("RGB").tobytes() != img.tobytes():
            out = img
        else:
            out.putpalette(flat)
            bits = 1 if len(ordered) <= 2 else 2 if len(ordered) <= 4 else 4 if len(ordered) <= 16 else 8
            out.save(path, format="PNG", optimize=True, bits=bits)
            return
    else:
        out = img
    out.save(path, format="PNG", optimize=True)
