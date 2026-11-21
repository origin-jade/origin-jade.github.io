"""Items (src/item.c: gItemsInfo, gTMHMItemMoveIds) and their icons.

    it = items.by_const("ITEM_POTION")
    it.name "Trank", it.description, it.price, it.pocket ("POCKET_ITEMS"), it.slug ("potion";
    TMs/HMs "tm_focus_punch"/"hm_cut" like the reference site), it.tm (("TM", 1, move_id) or None),
    it.hold_effect ("HOLD_EFFECT_*" or None), it.secondary_id, it.icon_png / it.icon_pal (repo paths
    following GetItemIconPic/GetItemIconPalette in src/item_icon.c), it.entry
    items.all_items()  -> {id: Item} without ITEM_NONE and unnamed entries
    items.by_name("Trank"), items.by_tm("TM", 1)
    items.pockets()    -> [(POCKET_* const, name)] the bag pockets in bag order (gPocketNamesStringsTable)
    items.pocket_name("POCKET_ITEMS") -> "Items"

Language: every function takes lang="de"|"en" (None = the process language). it.lang is the
build, it.text_lang = {"name": .., "description": ..} the language each text is written in there
("de": the English build shows the German string). it.pocket_name is the bag pocket's name.
"""
import functools
import os

from . import repo_path
from . import tu as TU
from . import text
from . import entext
from . import namestyle

SRC = "src/item.c"


class Item:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Item(%s %s)" % (self.const, self.name)


def _t(lang=None):
    return TU.load(SRC, lang=lang)


def _gfx(sym):
    """INCBIN symbol (graphics.c) -> checked-in .png / .pal path."""
    if not sym:
        return None
    p = TU.load("src/graphics.c", lang="de").incbin.get(str(sym))
    if not p:
        return None
    for a, b in ((".4bpp.smol", ".png"), (".4bpp.lz", ".png"), (".4bpp", ".png"),
                 (".gbapal.lz", ".pal"), (".gbapal", ".pal")):
        if p.endswith(a):
            p = p[:-len(a)] + b
            break
    return p if os.path.exists(repo_path(p)) else None


@functools.lru_cache(maxsize=None)
def _tm_table():
    t = _t("de")
    n_tm = t.need("NUM_TECHNICAL_MACHINES")
    out = {}
    for idx, v in t.table("gTMHMItemMoveIds").items():
        item, move = t.value(v)
        if idx == 0 or not item:
            continue
        kind, num = ("TM", idx) if idx <= n_tm else ("HM", idx - n_tm)
        out[item] = (kind, num, move)
    return out


@functools.lru_cache(maxsize=None)
def _pockets(lang):
    """gPocketNamesStringsTable (src/strings.c): {POCKET_* const: name}, in bag order."""
    t = TU.load("src/strings.c", lang=lang)
    de_t = TU.load("src/strings.c", lang="de")
    de_table = de_t.table("gPocketNamesStringsTable")
    names = t.names("POCKET_")
    out = {}
    for pid, v in sorted(t.table("gPocketNamesStringsTable").items()):
        const = names.get(pid, pid)
        raw = {"name": t.text_value(v)}
        raw_de = {"name": de_t.text_value(de_table.get(pid))}
        if lang == "en":
            raw = entext.resolve("pocket", const, raw, raw_de)
        written = text.written_in(raw["name"], raw_de["name"], lang)
        out[const] = namestyle.show(text.name(raw["name"], written), written, "pocket", lang)
    return out


def pockets(lang=None):
    return list(_pockets(TU.lang(lang)).items())


def pocket_name(const, lang=None):
    """Name of a bag pocket as the bag shows it (None for a pocket without a name)."""
    return _pockets(TU.lang(lang)).get(const)


def _load(lang=None):
    return _load_lang(TU.lang(lang))


@functools.lru_cache(maxsize=None)
def _load_lang(lang):
    from . import moves, typeinfo
    t = _t(lang)
    de_t = _t("de")
    de_table = de_t.table("gItemsInfo") if lang != "de" else {}
    pocket_names = _pockets(lang)
    names = t.canonical("ITEM_", "Item")
    pockets = t.names("POCKET_")
    holds = t.names("HOLD_EFFECT_")
    tms = _tm_table()
    tm_pic, hm_pic = _gfx("gItemIcon_TM"), _gfx("gItemIcon_HM")
    out = {}
    for iid, e in t.table("gItemsInfo").items():
        if iid == 0:
            continue
        name = t.text_field(e, "name")
        if not name:
            continue
        raw = {"name": name, "description": t.text_field(e, "description")}
        de_e = de_table.get(iid)
        raw_de = raw if lang == "de" else {"name": de_t.text_field(de_e, "name"),
                                           "description": de_t.text_field(de_e, "description")}
        const = names.get(iid, "ITEM_%d" % iid)
        if lang == "en":
            raw = entext.resolve("item", const, raw, raw_de)
        text_lang = {k: text.written_in(raw[k], raw_de[k], lang) for k in raw}
        slug = const[5:].lower()
        tm = tms.get(iid)
        if tm:
            mv = moves.by_id(tm[2], lang)
            slug = "%s_%s" % (tm[0].lower(), mv.const[5:].lower())
            icon = tm_pic if tm[0] == "TM" else hm_pic
            icon_pal = _gfx(typeinfo.by_id(mv.type, lang).palette_tmhm)
        else:
            icon = _gfx(t.field(e, "iconPic"))
            icon_pal = _gfx(t.field(e, "iconPalette"))
        he = t.field(e, "holdEffect", 0)
        pocket = pockets.get(t.field(e, "pocket", 0))
        out[iid] = Item(
            id=iid, const=const, slug=slug,
            name=namestyle.show(text.name(raw["name"], text_lang["name"]), text_lang["name"], "item", lang),
            name_game=text.name(raw["name"], text_lang["name"]), lang=lang, text_lang=text_lang,
            description=text.clean(raw["description"], text_lang["description"]),
            price=t.field(e, "price", 0) or 0, pocket=pocket, pocket_name=pocket_names.get(pocket),
            hold_effect=holds.get(he) if he else None, hold_effect_param=t.field(e, "holdEffectParam", 0),
            secondary_id=t.field(e, "secondaryId", 0), tm=tm,
            icon_png=icon, icon_pal=icon_pal, entry=e)
    return out


def all_items(lang=None):
    return dict(_load(lang))


def by_id(iid, lang=None):
    return _load(lang).get(iid)


def by_const(const, lang=None):
    v = _t("de").const(const)
    return _load(lang).get(v) if v is not None else None


def by_name(name, lang=None):
    for it in sorted(_load(lang).values(), key=lambda x: x.id):
        if it.name == name:
            return it
    return None


def by_tm(kind, num, lang=None):
    for it in _load(lang).values():
        if it.tm and it.tm[0] == kind and it.tm[1] == num:
            return it
    return None


def field(it, key, default=None):
    return _t(it.lang).field(it.entry, key, default)
