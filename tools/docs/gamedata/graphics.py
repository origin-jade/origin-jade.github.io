"""Palette-correct, transparent PNGs of the game graphics (Pillow).

The indexed PNG keeps its pixels; its palette is replaced by the palette the
game loads, quantized like the hardware (BGR555: c5 = c >> 3, shown as
c5 << 3 | c5 >> 2), and colour index 0 becomes transparent (GBA rule). Scaling
is nearest-neighbour only. Output is an indexed PNG ("P") with transparency
index 0, like the reference site.

    graphics.mon_front(sp, shiny=False)  -> Image 64x64 (first frame of the front sprite)
    graphics.mon_icon(sp)                -> Image 32x32 (first frame of the box icon)
    graphics.item_icon(item, scale=2)    -> Image 48x48
    graphics.trainer_pic(tr)             -> Image 64x64
    graphics.type_icon(type, scale=2)    -> Image 64x32
    graphics.category_icon(i, scale=2)   -> Image 32x32 (0 physical, 1 special, 2 status)
    graphics.type_color(type)            -> (r, g, b) main colour of the type label
    graphics.render(png, pal, crop=None, scale=1) -> Image   (generic; pal None = the PNG's own)
    graphics.save(img, path)             -> writes a deterministic PNG
"""
import os
from collections import Counter

from PIL import Image

from . import repo_path


def _q(c):
    c5 = c >> 3
    return (c5 << 3) | (c5 >> 2)


def read_jasc(path):
    """JASC .pal -> [(r, g, b)] quantized like the ROM."""
    words = open(repo_path(path), encoding="ascii").read().split()
    if words[0] != "JASC-PAL":
        raise ValueError("not a JASC palette: %s" % path)
    n = int(words[2])
    vals = list(map(int, words[3:3 + 3 * n]))
    return [tuple(_q(v) for v in vals[i:i + 3]) for i in range(0, 3 * n, 3)]


def read_gbapal(path):
    data = open(repo_path(path), "rb").read()
    out = []
    for i in range(0, len(data), 2):
        v = data[i] | data[i + 1] << 8
        out.append(tuple((c << 3) | (c >> 2) for c in (v & 31, (v >> 5) & 31, (v >> 10) & 31)))
    return out


def own_palette(png):
    im = Image.open(repo_path(png))
    pal = im.getpalette() or []
    return [tuple(_q(c) for c in pal[i:i + 3]) for i in range(0, min(len(pal), 48), 3)]


def palette(path, png=None):
    """A .pal/.gbapal path, or the PNG's own palette when path is None/missing."""
    if path and os.path.exists(repo_path(path)):
        return read_jasc(path) if path.endswith(".pal") else read_gbapal(path)
    if path and path.endswith(".pal"):
        alt = path[:-4] + ".gbapal"
        if os.path.exists(repo_path(alt)):
            return read_gbapal(alt)
    if png is None:
        raise FileNotFoundError(path)
    return own_palette(png)


def render(png, pal=None, crop=None, scale=1):
    """Indexed image with the game palette and index 0 transparent."""
    im = Image.open(repo_path(png))
    if im.mode != "P":
        raise ValueError("%s is not an indexed PNG (%s)" % (png, im.mode))
    if pal is None:
        pal = own_palette(png)
    im = im.copy()
    if crop:
        im = im.crop(crop)
    flat = []
    for c in list(pal)[:256]:
        flat += list(c)
    flat += [0, 0, 0] * (256 - len(flat) // 3)
    im.putpalette(flat)
    im.info["transparency"] = 0
    if scale != 1:
        im = im.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)
        im.info["transparency"] = 0
    return im


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format="PNG", optimize=True, transparency=0)
    return path


# ------------------------------------------------------------------ helpers per kind
def mon_front(sp, shiny=False, female=False):
    png = (sp.gfx.get("front_female") if female else None) or sp.gfx["front"]
    if not png:
        return None
    pal = palette(sp.gfx["shiny_palette" if shiny else "palette"], png)
    w = Image.open(repo_path(png)).size[0]
    return render(png, pal, crop=(0, 0, w, w))


def mon_icon(sp):
    png = sp.gfx["icon"]
    if not png:
        return None
    pal = read_jasc("graphics/pokemon/icon_palettes/pal%d.pal" % sp.gfx["icon_pal_index"])
    return render(png, pal, crop=(0, 0, 32, 32))


def item_icon(item, scale=2):
    if not item.icon_png:
        return None
    return render(item.icon_png, palette(item.icon_pal, item.icon_png), scale=scale)


def trainer_pic(tr):
    if not tr.pic_png:
        return None
    return render(tr.pic_png, palette(tr.pic_pal, tr.pic_png))


def type_icon(ty, scale=2):
    if not os.path.exists(repo_path(ty.icon_png)):
        return None
    return render(ty.icon_png, read_jasc(ty.icon_pal), scale=scale)


CATEGORY_ICONS = "graphics/interface/category_icons.png"


def category_icon(index, scale=2):
    im = Image.open(repo_path(CATEGORY_ICONS))
    w = im.size[0]
    return render(CATEGORY_ICONS, palette("graphics/interface/category_icons.gbapal", CATEGORY_ICONS),
                  crop=(0, index * w, w, (index + 1) * w), scale=scale)


def type_color(ty):
    """Most frequent opaque colour of the type label (its background plate)."""
    im = type_icon(ty, scale=1)
    if im is None:
        return (128, 128, 128)
    pal = im.getpalette()
    counts = Counter(p for p in im.getdata() if p != 0)
    idx = counts.most_common(1)[0][0]
    return tuple(pal[idx * 3:idx * 3 + 3])
