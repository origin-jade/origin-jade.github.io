#!/usr/bin/env python3
"""Export the site's images from the game graphics (palette-correct, Pillow).

Images are shared by both language trees and are exported on demand: only
what the pages refer to (ctx.asset(kind, name)) ends up in the output.

    assets/mon/<species slug>.png        front sprite, first frame, 64x64
    assets/shiny/<species slug>.png      the same with the shiny palette
    assets/icon/<species slug>.png       box icon, first frame, 32x32
    assets/item/<item slug>.png          bag icon, 24x24 (TMs/HMs: tm_<move>.png / hm_<move>.png)
    assets/trainer/<pic id>.png          trainer front picture, 64x64
    assets/category/<physical|special|status>.png  damage category icon, 16x16
    assets/types/<type slug>.png         the game's type label, 32x16
Always present (FIXED):
    assets/img/mark.png                  site mark: box icon of site_config.MASCOT, 32x32
    assets/img/favicon-32.png, favicon-180.png   browser tab icons of the same Pokémon
    assets/img/title.png                 title screen artwork, 720x480 (repo logo.png)
    assets/img/title-2x.png              the same at exactly 2x of the game screen, 480x320
    assets/img/logo.png                  the title screen lettering as the game composes it

All sprites are exported at their native size; pages scale them by whole
factors (CSS class "px": image-rendering pixelated).
Image file names use the loaders' own slugs (species.slug "ho_oh", item.slug,
trainer.pic); they are not the URL slugs of the pages.

    python3 -I -B tools/docs/export_assets.py --out DIR --all      # everything (for inspection)
"""
import argparse
import functools
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gamedata import maprender
from gamedata import REPO, repo_path  # noqa: E402
from gamedata import graphics, items, species, trainers, tu, typeinfo  # noqa: E402
import site_config  # noqa: E402

KINDS = ("mon", "shiny", "icon", "item", "trainer", "category", "types", "map")
FIXED = ("assets/img/mark.png", "assets/img/favicon-32.png", "assets/img/favicon-180.png",
         "assets/img/title.png", "assets/img/title-2x.png", "assets/img/logo.png")
FAVICON_BG = (16, 42, 34, 255)   # deep jade ink (--ink in site.css)
CATEGORIES = ("physical", "special", "status")


def _out(out, rel):
    p = os.path.join(out, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


@functools.lru_cache(maxsize=None)
def _items_by_slug():
    return {it.slug: it for it in sorted(items.all_items().values(), key=lambda x: x.id)}


@functools.lru_cache(maxsize=None)
def _trainers_by_pic():
    out = {}
    for tr in list(trainers.all_trainers().values()) + list(trainers.partners().values()):
        if tr.pic and tr.pic_png:
            out.setdefault(tr.pic, tr)
    return out


@functools.lru_cache(maxsize=None)
def _types_by_slug():
    return {t.slug: t for t in typeinfo.all_types()}


def render(kind, name):
    """PIL image of one asset, or None when the game has no such graphic."""
    if kind in ("mon", "shiny", "icon"):
        sp = species.by_slug(name)
        if sp is None:
            return None
        return graphics.mon_icon(sp) if kind == "icon" else graphics.mon_front(sp, shiny=(kind == "shiny"))
    if kind == "item":
        it = _items_by_slug().get(name)
        return graphics.item_icon(it, scale=1) if it is not None else None
    if kind == "trainer":
        tr = _trainers_by_pic().get(name)
        return graphics.trainer_pic(tr) if tr is not None else None
    if kind == "category":
        return graphics.category_icon(CATEGORIES.index(name), scale=1) if name in CATEGORIES else None
    if kind == "map":
        dirs = maprender.dirs_of_group_slug(name)
        if not dirs:
            return None
        found = maprender.groups(dirs)
        return maprender.render_group(found[0]) if len(found) == 1 else None
    if kind == "types":
        ty = _types_by_slug().get(name)
        return graphics.type_icon(ty, scale=1) if ty is not None else None
    return None


def export_used(out, rels, force=True):
    """Export the referenced assets. rels: iterable of "assets/<kind>/<name>.png".
    force False: only files that do not exist yet. -> (written, [rels the game has no graphic for])."""
    written, missing = 0, []
    for rel in sorted(set(rels)):
        parts = rel.split("/")
        if len(parts) != 3 or parts[0] != "assets" or parts[1] not in KINDS or not parts[2].endswith(".png"):
            continue
        path = _out(out, rel)
        if not force and os.path.exists(path):
            continue
        im = render(parts[1], parts[2][:-4])
        if im is None:
            missing.append(rel)
            continue
        if parts[1] == "map":
            os.makedirs(os.path.dirname(path), exist_ok=True)
            maprender.save_png(im, path)
            written += 1
            continue
        graphics.save(im, path)
        written += 1
    return written, missing


def _rgba(img):
    return img.convert("RGBA")


def export_mascot(out):
    sp = species.by_const(site_config.MASCOT)
    icon = _rgba(graphics.mon_icon(sp))
    icon.save(_out(out, "assets/img/mark.png"), optimize=True)
    icon.save(_out(out, "assets/img/favicon-32.png"), optimize=True)
    front = _rgba(graphics.mon_front(sp))
    front = front.crop(front.getbbox())
    k = max(1, min(150 // front.size[0], 150 // front.size[1]))
    front = front.resize((front.size[0] * k, front.size[1] * k), Image.NEAREST)
    canvas = Image.new("RGBA", (180, 180), FAVICON_BG)
    canvas.alpha_composite(front, ((180 - front.size[0]) // 2, (180 - front.size[1]) // 2))
    canvas.save(_out(out, "assets/img/favicon-180.png"), optimize=True)


def _bgr555(data):
    out = []
    for i in range(0, len(data), 2):
        v = data[i] | data[i + 1] << 8
        out.append(tuple((c << 3) | (c >> 2) for c in (v & 31, (v >> 5) & 31, (v >> 10) & 31)))
    return out


def title_lettering():
    """The title screen's lettering as the game puts it together (src/title_screen.c):
    four 64x64 8bpp pieces of graphics/title_screen/hns/pokemon_logo_obj.bin (OBJ
    palette entries 16-143, pokemon_logo_obj_pal.bin), centres x 21/85/149/213, y 28
    (CreateJadeLogoSprites), and the version banner graphics/title_screen/origin_jade/
    emerald_version.png, two 64x32 halves centred at VERSION_BANNER_LEFT_X/RIGHT_X and
    VERSION_BANNER_Y_GOAL (constants read from the preprocessed src/title_screen.c)."""
    gfx = open(repo_path("graphics", "title_screen", "hns", "pokemon_logo_obj.bin"), "rb").read()
    pal = _bgr555(open(repo_path("graphics", "title_screen", "hns", "pokemon_logo_obj_pal.bin"), "rb").read())
    canvas = Image.new("RGBA", (256, 96), (0, 0, 0, 0))
    banner = Image.open(repo_path("graphics", "title_screen", "origin_jade", "emerald_version.png"))
    bpal = graphics.palette("graphics/title_screen/origin_jade/emerald_version.gbapal",
                            "graphics/title_screen/origin_jade/emerald_version.png")
    banner = graphics.render("graphics/title_screen/origin_jade/emerald_version.png", bpal).convert("RGBA")
    t = tu.load("src/title_screen.c")
    y_goal = t.need("VERSION_BANNER_Y_GOAL")
    for i, cx in enumerate((t.need("VERSION_BANNER_LEFT_X"), t.need("VERSION_BANNER_RIGHT_X"))):
        half = banner.crop((0, i * 32, 64, (i + 1) * 32))
        # sprite x/y are centres; the lettering's left edge (x -11) and top edge
        # (y 28 - 32 = -4) are canvas 0, 0
        canvas.alpha_composite(half, (cx - 32 + 11, y_goal - 16 + 4))
    letters = Image.new("RGBA", (256, 64), (0, 0, 0, 0))
    px = letters.load()
    for piece in range(4):
        base = piece * 4096
        for t in range(64):
            tx, ty = t % 8, t // 8
            for y in range(8):
                for x in range(8):
                    p = gfx[base + t * 64 + y * 8 + x]
                    if p >= 16 and p - 16 < len(pal):
                        px[piece * 64 + tx * 8 + x, ty * 8 + y] = pal[p - 16] + (255,)
    canvas.alpha_composite(letters, (0, 0))
    return canvas.crop(canvas.getbbox())


def export_title(out):
    """Title artwork: the repo's logo.png (the 240x160 title screen at 3x) and an exact 2x version."""
    title_lettering().save(_out(out, "assets/img/logo.png"), optimize=True)
    src = repo_path("logo.png")
    im = Image.open(src).convert("RGB")
    im.save(_out(out, "assets/img/title.png"), optimize=True)
    w, h = im.size
    base = im.resize((w // 3, h // 3), Image.NEAREST)
    base.resize((w // 3 * 2, h // 3 * 2), Image.NEAREST).save(_out(out, "assets/img/title-2x.png"), optimize=True)


def export_fixed(out, force=True):
    """The images every page or the start page needs (FIXED)."""
    if force or not all(os.path.exists(os.path.join(out, *r.split("/"))) for r in FIXED):
        export_mascot(out)
        export_title(out)


def all_rels():
    """Every exportable asset (for --all)."""
    rels = []
    for sp in species.all_species().values():
        rels += ["assets/%s/%s.png" % (k, sp.slug) for k in ("mon", "shiny", "icon")]
    rels += ["assets/item/%s.png" % s for s in _items_by_slug()]
    rels += ["assets/trainer/%s.png" % s for s in _trainers_by_pic()]
    rels += ["assets/category/%s.png" % c for c in CATEGORIES]
    rels += ["assets/types/%s.png" % s for s in _types_by_slug()]
    return rels


def main():
    ap = argparse.ArgumentParser(description="Export the site's images from the game graphics.")
    ap.add_argument("--out", default=os.path.join(REPO, "build", "docs_site"))
    ap.add_argument("--all", action="store_true", help="export every sprite and icon, not only the fixed images")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    export_fixed(out)
    if a.all:
        print("written: %d, without graphic: %d" % tuple(len(x) if isinstance(x, list) else x
                                                         for x in export_used(out, all_rels())))


if __name__ == "__main__":
    main()
