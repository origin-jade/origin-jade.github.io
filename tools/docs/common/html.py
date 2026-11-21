"""Component library of the site (v2). Every helper returns an HTML string.

Helpers that link, show images or need words take the build context `ctx`
first. Link helpers fall back to plain text when the target is not registered.
The catalogue with the emitted HTML is in FRAMEWORK2.md; the dev gallery
(pages/gallery.py, --dev) shows every component with real data.

Text arguments are escaped by the helper when the parameter is called `text`,
`title`, `label` or `name`; parameters called `html`, `body`, `inner` or
`cells` are inserted as they are (escape foreign text with H.esc).
"""
import html as _html

from . import search as _search
from . import slugs as _slugs

# Runs before the first paint: stored theme (no flash) and the "js" class.
HEAD_SCRIPT = ('<script>(function(d){try{var t=localStorage.getItem("oj-theme");'
               'if(t==="light"||t==="dark")d.setAttribute("data-theme",t)}catch(e){}'
               'd.className+=" js"})(document.documentElement)</script>')

STAT_KEYS = ("hp", "atk", "def", "spa", "spd", "spe")
TIMES = ("morning", "day", "evening", "night")
METHODS = ("land", "cave", "water", "rock_smash", "old_rod", "good_rod", "super_rod")
CATEGORIES = ("physical", "special", "status")
REGIONS = ("kanto", "johto", "hoenn")


# ------------------------------------------------------------------ basics
def esc(s):
    """Escape text for HTML content and attribute values (None -> "")."""
    return _html.escape("" if s is None else str(s), quote=True)


def attrs(d):
    """{name: value} -> ' name="value"' (None/False dropped, True -> bare name)."""
    if not d:
        return ""
    out = []
    for k, v in d.items():
        if v is None or v is False:
            continue
        out.append(" %s" % k if v is True else ' %s="%s"' % (k, esc(v)))
    return "".join(out)


def _cls(*names):
    c = " ".join(n for n in names if n)
    return ' class="%s"' % c if c else ""


def img(src, width, height, cls=None, alt="", lazy=True):
    """<img> with fixed size (no layout shift); pixel art gets cls "px"."""
    return "<img%s>" % attrs({"class": cls, "src": src, "alt": alt, "width": width, "height": height,
                              "loading": "lazy" if lazy else None, "decoding": "async"})


def sr(text):
    """Text for screen readers only."""
    return '<span class="sr">%s</span>' % esc(text)


def dash(ctx):
    return '<span class="none">%s</span>' % esc(ctx.ui("none"))


# ------------------------------------------------------------------ links
def link(ctx, kind, key, text=None, cls=None, html=None):
    """Link to a registered entity; plain text when nobody registered it.
    text defaults to the registered title."""
    e = ctx.entry(kind, key)
    inner = html if html is not None else esc(text if text is not None else (e.title if e else ""))
    if e is None:
        return inner
    return '<a%s href="%s">%s</a>' % (_cls(cls), ctx.url_for(kind, key), inner)


def page_link(ctx, path, text=None, cls=None, html=None):
    """Link to a page path ("guides/breeding"); plain text when it is not registered."""
    return link(ctx, "page", path, text, cls, html)


def species_link(ctx, sp, icon=False, text=None):
    """Pokémon name linked to its page; icon=True puts the box icon in front."""
    inner = esc(text if text is not None else sp.name)
    if icon:
        inner = mon_icon(ctx, sp) + "<span>%s</span>" % inner
        return link(ctx, "species", sp.const, html=inner, cls="mon-link") if ctx.has("species", sp.const) \
            else '<span class="mon-link">%s</span>' % inner
    return link(ctx, "species", sp.const, html=inner)


def move_link(ctx, mv, text=None):
    return link(ctx, "move", mv.const, text if text is not None else mv.name)


def ability_link(ctx, ab, text=None):
    return link(ctx, "ability", ab.const, text if text is not None else ab.name)


def item_link(ctx, item, icon=False, text=None):
    """Item name linked to its page; icon=True puts the bag icon in front."""
    inner = esc(text if text is not None else item.name)
    if icon:
        inner = item_icon(ctx, item) + "<span>%s</span>" % inner
        return link(ctx, "item", item.const, html=inner, cls="item-link") if ctx.has("item", item.const) \
            else '<span class="item-link">%s</span>' % inner
    return link(ctx, "item", item.const, html=inner)


def location_link(ctx, key, text):
    """Place name linked to its page (key: map section constant)."""
    return link(ctx, "location", key, text)


# ------------------------------------------------------------------ chips
def chip(text, tone=None, title=None):
    """Small label. tone: None, "jade", "gold", "muted", "warn", "kanto", "johto", "hoenn"."""
    return "<span%s%s>%s</span>" % (_cls("chip", tone and "chip-" + tone), attrs({"title": title}), esc(text))


def chips(items):
    """Row of chips: items are HTML strings (H.chip, H.type_chip ...)."""
    return '<span class="chips">%s</span>' % "".join(i for i in items if i)


def region_chip(ctx, region):
    """region: "kanto" | "johto" | "hoenn"."""
    return chip(ctx.ui("region_" + region), region)


def _type(ty):
    if hasattr(ty, "slug"):
        return ty
    from gamedata import typeinfo
    t = typeinfo.by_id(ty) if isinstance(ty, int) else typeinfo.by_const(ty)
    if t is None:
        raise ValueError("unknown type %r" % (ty,))
    return t


def type_chip(ctx, ty):
    """Type label with its colour: accepts a Type, a type id or "TYPE_FIRE"."""
    t = _type(ty)
    return '<span class="type t-%s">%s</span>' % (t.slug, esc(t.name))


def types(ctx, tys):
    """Chips of a Pokémon's types (a doubled single type is shown once)."""
    seen, out = set(), []
    for ty in tys:
        t = _type(ty)
        if t.id not in seen:
            seen.add(t.id)
            out.append(type_chip(ctx, t))
    return '<span class="types">%s</span>' % "".join(out)


def cat_chip(ctx, cat, icon_only=False):
    """Damage category with the game's icon: "physical" | "special" | "status"."""
    label = ctx.ui("cat_" + cat)
    pic = img(ctx.asset("category", cat), 16, 16, "px", alt=label if icon_only else "")
    if icon_only:
        return '<span class="cat cat-icon" title="%s">%s</span>' % (esc(label), pic)
    return '<span class="cat">%s%s</span>' % (pic, esc(label))


def day_night(times):
    """Times of day as the player needs them: morning, day and evening together are "day"
    (the game's wild tables only differ between that span and the night)."""
    ts = list(times or ())
    if {"morning", "day", "evening"} <= set(ts):
        ts = ["day"] + [x for x in ts if x not in ("morning", "day", "evening")]
    return ts


def time_chips(ctx, times):
    return "".join(time_chip(ctx, x) for x in day_night(times))


def time_chip(ctx, time):
    """Time of day: "morning" | "day" | "evening" | "night"."""
    return '<span class="tod tod-%s">%s</span>' % (time, esc(ctx.ui("time_" + time)))


# ------------------------------------------------------------------ images
def sprite(ctx, sp, shiny=False, scale=2, lazy=True):
    """Front sprite (64 px native) at an integer scale."""
    alt = ctx.ui("sprite_shiny_alt" if shiny else "sprite_alt", name=sp.name)
    return img(ctx.asset("shiny" if shiny else "mon", sp.slug), 64 * scale, 64 * scale, "px", alt, lazy)


def mon_icon(ctx, sp, scale=1):
    """Box icon (32 px native)."""
    return img(ctx.asset("icon", sp.slug), 32 * scale, 32 * scale, "px mon-ic")


def item_icon(ctx, item, scale=1):
    """Bag icon (24 px native)."""
    return img(ctx.asset("item", item.slug), 24 * scale, 24 * scale, "px item-ic")


def trainer_pic(ctx, tr, scale=1):
    """Trainer front picture (64 px native); tr is a trainer or its pic id."""
    pic = tr if isinstance(tr, str) else tr.pic
    return img(ctx.asset("trainer", pic), 64 * scale, 64 * scale, "px trainer-pic")


def plate(inner, caption=None, cls=None):
    """Quiet framed plate for pixel art, optional caption below."""
    cap = "<figcaption>%s</figcaption>" % caption if caption else ""
    return "<figure%s>%s%s</figure>" % (_cls("plate", cls), inner, cap)


def sprite_plate(ctx, sp, shiny=False, scale=2, caption=None, lazy=True):
    """Sprite on a plate. caption: text below (None: no caption)."""
    return plate(sprite(ctx, sp, shiny, scale, lazy), esc(caption) if caption else None,
                 "plate-shiny" if shiny else None)


def sprite_pair(ctx, sp, scale=2, lazy=True):
    """Regular and shiny sprite side by side, each with its caption."""
    return '<div class="plates">%s%s</div>' % (
        sprite_plate(ctx, sp, False, scale, ctx.ui("normal_form"), lazy),
        sprite_plate(ctx, sp, True, scale, ctx.ui("shiny"), lazy))


# ------------------------------------------------------------------ structure
def section(title, body, id=None, intro=None, cls=None):
    """Main section of a page (h2). Sections feed the "on this page" outline."""
    sid = id or _slugs.anchor(title)
    lead = '<p class="sec-intro">%s</p>' % intro if intro else ""
    return '<section class="sec%s" id="%s"><h2>%s</h2>%s%s</section>\n' % (
        " " + cls if cls else "", esc(sid), esc(title), lead, body)


def sub(title, body, id=None, cls=None):
    """Sub-section (h3)."""
    return "<section%s%s><h3>%s</h3>%s</section>" % (_cls("sub", cls), attrs({"id": id}), esc(title), body)


def prose(html):
    """Running text at a comfortable line length (wrap paragraphs, lists)."""
    return '<div class="prose">%s</div>' % html


def p(text, cls=None):
    return "<p%s>%s</p>" % (_cls(cls), esc(text))


def ul(items, cls=None):
    """Bullet list from HTML items."""
    return "<ul%s>%s</ul>" % (_cls(cls), "".join("<li>%s</li>" % i for i in items))


def steps(items):
    """Numbered steps (walkthrough, how-to): items are HTML strings."""
    return '<ol class="steps">%s</ol>' % "".join("<li>%s</li>" % i for i in items)


def card(body, title=None, cls=None, id=None):
    """Bordered block for a self-contained piece of content; optional h3 title."""
    head = '<h3 class="card-title">%s</h3>' % esc(title) if title else ""
    return "<div%s%s>%s%s</div>" % (_cls("card", cls), attrs({"id": id}), head, body)


def split(main, side, cls=None):
    """Two columns on wide screens (main about 60 %), stacked on phones."""
    return "<div%s><div>%s</div><div>%s</div></div>" % (_cls("split", cls), main, side)


def grid(items, size="m", cls=None):
    """Responsive grid. size: "s" (min 9 rem), "m" (min 15 rem), "l" (min 22 rem)."""
    return "<div%s>%s</div>" % (_cls("grid", "grid-" + size, cls), "".join(items))


def tile(href, title, text=None, media=None, meta=None, cls=None):
    """Link tile: optional media (icon/sprite HTML) left, title, text, meta line.
    href None gives a tile that is not a link."""
    inner = []
    if media:
        inner.append('<span class="tile-media">%s</span>' % media)
    body = ['<span class="tile-title">%s</span>' % esc(title)]
    if text:
        body.append('<span class="tile-text">%s</span>' % esc(text))
    if meta:
        body.append('<span class="tile-meta">%s</span>' % meta)
    inner.append('<span class="tile-body">%s</span>' % "".join(body))
    if href:
        return '<a%s href="%s">%s</a>' % (_cls("tile", cls), esc(href), "".join(inner))
    return "<div%s>%s</div>" % (_cls("tile", "tile-static", cls), "".join(inner))


def page_tile(ctx, path, text=None, media=None, meta=None, title=None):
    """Tile for a registered page; None when the page does not exist (filter with H.grid(filter(None, ...)))."""
    url = ctx.url(path)
    if url is None:
        return None
    return tile(url, title or ctx.pages[path].title, text, media, meta)


def kv(pairs, cls=None):
    """Key-value list: [(label text, value HTML)]; pairs with value None are left out."""
    return "<dl%s>%s</dl>" % (_cls("kv", cls), "".join(
        "<div><dt>%s</dt><dd>%s</dd></div>" % (esc(k), v) for k, v in pairs if v is not None))


def callout(ctx, kind, html, title=None):
    """Highlighted note. kind: "note" | "tip" | "warning"."""
    if kind not in ("note", "tip", "warning"):
        raise ValueError("callout kind %r" % kind)
    return ('<aside class="callout callout-%s" role="note"><p class="callout-title">%s</p>'
            '<div class="callout-body">%s</div></aside>' % (kind, esc(title or ctx.ui(kind)), html))


def details(summary, body, open=False, cls=None):
    """Collapsible block (FAQ answer, long list); works without JavaScript."""
    return "<details%s%s><summary>%s</summary><div class=\"details-body\">%s</div></details>" % (
        _cls("fold", cls), " open" if open else "", esc(summary), body)


def meter(value, maximum, cls=None, label=None):
    """Thin horizontal bar (rate, share). value/maximum numbers; label for screen readers."""
    pct = 0 if not maximum else max(0.0, min(100.0, 100.0 * value / maximum))
    return '<span%s%s><i style="width:%s%%"></i></span>' % (
        _cls("meter", cls), attrs({"role": "img", "aria-label": label} if label else {"aria-hidden": "true"}),
        ("%.1f" % pct).rstrip("0").rstrip("."))


# ------------------------------------------------------------------ tables
def table(cols, rows, *, caption=None, cls=None, stack=True, id=None, row_attrs=None, foot=None):
    """Data table.

    cols  [label] or [(label, flags)]; flags (space separated): "num" right-aligned
          numbers, "main" the row's title cell (bold; heads the card on phones),
          "min" as narrow as possible, "hide-s" hidden on phones, "c" centred
    rows  [[cell HTML or None]]  (None is shown as a dash)
    stack True: on phones every row becomes a small card with labelled values;
          False: the table keeps its shape and scrolls inside its own frame
    row_attrs  optional [dict] per row (H.filter_attrs(...) for filter bars)
    """
    heads, flags = [], []
    for c in cols:
        label, fl = (c, "") if isinstance(c, str) else (c[0], c[1] if len(c) > 1 else "")
        heads.append(label)
        flags.append(fl)
    th = "".join('<th scope="col"%s>%s</th>' % (_cls(f), esc(h)) for h, f in zip(heads, flags))
    tds = ['<td%s%s>' % (_cls(f), (' data-l="%s"' % esc(h)) if stack and h and "main" not in f else "")
           for h, f in zip(heads, flags)]
    body = []
    for i, r in enumerate(rows):
        ra = attrs(row_attrs[i]) if row_attrs else ""
        body.append("<tr%s>%s</tr>" % (ra, "".join(
            "%s%s</td>" % (tds[j], '<span class="none">—</span>' if c is None else c) for j, c in enumerate(r))))
    cap = "<caption>%s</caption>" % esc(caption) if caption else ""
    tfoot = "<tfoot>%s</tfoot>" % foot if foot else ""
    return ('<div class="tbl-wrap%s"><table%s%s>%s<thead><tr>%s</tr></thead><tbody>%s</tbody>%s</table></div>'
            % ("" if stack else " tbl-scroll", _cls("tbl", "tbl-stack" if stack else None, cls),
               attrs({"id": id}), cap, th, "\n".join(body), tfoot))


def filter_attrs(text=(), **facets):
    """data attributes of a filterable item.

        H.filter_attrs(text=[sp.name, "#001"], type=["grass", "poison"], region="kanto")
        -> {"data-text": "bisasam 001", "data-type": "grass poison", "data-region": "kanto"}
    """
    if isinstance(text, str):
        text = (text,)
    d = {"data-text": _search.filter_text(*text)}
    for k, v in facets.items():
        if v is None:
            continue
        d["data-" + k.replace("_", "-")] = v if isinstance(v, str) else " ".join(str(x) for x in v)
    return d


def filter_bar(ctx, target, *, text=True, facets=(), placeholder=None, label=None):
    """Client-side filter for the element with id `target`.

    Every descendant of the target that carries data-text is one item; items
    get their attributes from H.filter_attrs. A [data-group] ancestor is
    hidden while none of its items is shown.
    facets  [{"key": "type", "label": "Typ", "options": [(value, label)], "style": "select"|"chips"}]
            style default: chips up to 6 options, otherwise a select box
    Hidden without JavaScript (the list is simply complete then). The state is
    kept in the URL (?q=...&type=fire), so filtered lists can be linked.
    """
    o = ['<form class="filter" data-filter="%s" role="search" aria-label="%s" hidden>'
         % (esc(target), esc(label or ctx.ui("filter")))]
    if text:
        o.append('<label class="filter-text"><span class="sr">%s</span><span class="i i-search" aria-hidden="true">'
                 '</span><input type="search" name="q" autocomplete="off" spellcheck="false" placeholder="%s">'
                 '</label>' % (esc(ctx.ui("filter_text")), esc(placeholder or ctx.ui("filter_placeholder"))))
    for f in facets:
        opts = f["options"]
        style = f.get("style") or ("chips" if len(opts) <= 6 else "select")
        if style == "select":
            o.append('<label class="filter-sel"><span>%s</span><select name="%s"><option value="">%s</option>%s'
                     '</select></label>' % (esc(f["label"]), esc(f["key"]), esc(ctx.ui("filter_all")),
                                            "".join('<option value="%s">%s</option>' % (esc(v), esc(l))
                                                    for v, l in opts)))
        else:
            o.append('<fieldset class="filter-chips" data-key="%s"><legend>%s</legend>%s</fieldset>'
                     % (esc(f["key"]), esc(f["label"]),
                        "".join('<button type="button" aria-pressed="false" data-value="%s">%s</button>'
                                % (esc(v), esc(l)) for v, l in opts)))
    o.append('<output class="filter-count" aria-live="polite"></output>')
    o.append('<button type="reset" class="filter-reset" hidden>%s</button>' % esc(ctx.ui("filter_reset")))
    o.append("</form>")
    return "".join(o)


def type_facet(ctx):
    """Ready-made facet: the 18 types (key "type", values = type slugs)."""
    from gamedata import typeinfo
    tys = sorted(typeinfo.battle_types(), key=lambda t: _search.fold(t.name))
    return {"key": "type", "label": ctx.ui("filter_type"), "options": [(t.slug, t.name) for t in tys],
            "style": "select"}


def region_facet(ctx):
    """Ready-made facet: Kanto / Johto / Hoenn (key "region")."""
    return {"key": "region", "label": ctx.ui("filter_region"),
            "options": [(r, ctx.ui("region_" + r)) for r in REGIONS], "style": "chips"}


# ------------------------------------------------------------------ tabs
def tabs(panels, id, label=None):
    """Tabs. panels: [(label text, body HTML)] or [(label, body, key)].

    Without JavaScript every panel is shown below its heading; with JavaScript
    the headings become a tab list (arrow keys, Home/End). A link to
    #<id>-<key> opens that tab. key default: position (1, 2, ...)."""
    out = []
    for i, pnl in enumerate(panels):
        key = pnl[2] if len(pnl) > 2 else str(i + 1)
        out.append('<section class="tab" id="%s-%s"><h3 class="tab-h">%s</h3>%s</section>'
                   % (esc(id), esc(key), esc(pnl[0]), pnl[1]))
    return '<div class="tabs" data-tabs id="%s"%s>%s</div>' % (esc(id), attrs({"aria-label": label}), "".join(out))


def letter_groups(entries, make_body, id):
    """A long alphabetical list as one folding group per first letter.

    entries    [(title text, payload)] in display order (already sorted)
    make_body  function([payload]) -> HTML of one group
    id         id of the wrapper (the target of a filter bar)
    Returns the letter bar and the groups. Groups start folded; a filter opens them.
    Umlauts and accents sort under their base letter; anything else under "#"."""
    groups, order = {}, []
    for title, x in entries:
        f = _search.fold(title)
        letter = f[0].upper() if f and f[0].isalpha() else "#"
        if letter not in groups:
            groups[letter] = []
            order.append(letter)
        groups[letter].append(x)
    order.sort(key=lambda c: (c == "#", c))
    bar = '<nav class="letters">%s</nav>' % "".join(
        '<a href="#l-%s">%s</a>' % ("0" if c == "#" else c.lower(), esc(c)) for c in order)
    out = []
    for c in order:
        key = "0" if c == "#" else c.lower()
        out.append('<div data-group="%s">%s</div>' % (key, sub(
            "%s (%d)" % (c, len(groups[c])), make_body(groups[c]), id="l-" + key, cls="start-closed")))
    return bar + '<div id="%s">%s</div>' % (esc(id), "".join(out))


# ------------------------------------------------------------------ entity tiles
def ent(href, title, media=None, meta=None, data=None, note=None, aside=None):
    """One item of an entity grid: media (icon), title, meta HTML (chips), a short note
    and an aside (HTML at the right edge, e.g. a count)."""
    inner = "%s<span class=\"ent-b\"><span class=\"ent-t\">%s</span>%s%s</span>%s" % (
        '<span class="ent-m">%s</span>' % media if media else "", esc(title),
        '<span class="ent-x">%s</span>' % meta if meta else "",
        '<span class="ent-n">%s</span>' % esc(note) if note else "",
        '<span class="ent-a">%s</span>' % aside if aside else "")
    if href:
        return '<li%s><a class="ent" href="%s">%s</a></li>' % (attrs(data), esc(href), inner)
    return '<li%s><span class="ent">%s</span></li>' % (attrs(data), inner)


def species_tile(ctx, sp, number=None, note=None, region=None, extra_text=()):
    """Entity tile of a Pokémon: box icon, name, types; filter attributes included
    (text: name + number, type, region)."""
    from gamedata import typeinfo
    tslugs = []
    for t in sp.types:
        s = typeinfo.by_id(t).slug
        if s not in tslugs:
            tslugs.append(s)
    data = filter_attrs([sp.name] + ([str(number)] if number is not None else []) + list(extra_text),
                        type=tslugs, region=region)
    title = sp.name
    meta = types(ctx, sp.types)
    num = '<span class="ent-no">#%03d</span>' % number if isinstance(number, int) else ""
    inner = '<span class="ent-m">%s</span><span class="ent-b">%s<span class="ent-t">%s</span>' \
            '<span class="ent-x">%s</span>%s</span>' % (
                mon_icon(ctx, sp), num, esc(title), meta, '<span class="ent-n">%s</span>' % esc(note) if note else "")
    url = ctx.url_for("species", sp.const)
    if url:
        return '<li%s><a class="ent" href="%s">%s</a></li>' % (attrs(data), url, inner)
    return '<li%s><span class="ent">%s</span></li>' % (attrs(data), inner)


def ent_grid(items, id=None, cls=None, group=None):
    """Grid of H.ent / H.species_tile items. group: value of data-group (for filter bars)."""
    return "<ul%s%s>%s</ul>" % (_cls("ents", cls), attrs({"id": id, "data-group": group}), "".join(items))


# ------------------------------------------------------------------ stats
def stat_names(ctx):
    """{"hp": "KP", ...}: the game's stat names where the build has them."""
    from . import terms
    return terms.stat_names(ctx)


def _tier(v):
    return 1 if v < 50 else 2 if v < 80 else 3 if v < 100 else 4 if v < 130 else 5


def stat_bars(ctx, stats, total=True, maximum=255):
    """Base stats with bars. stats: {"hp": 45, "atk": 49, "def": ..., "spa", "spd", "spe"}."""
    names = stat_names(ctx)
    rows = []
    for k in STAT_KEYS:
        v = stats[k]
        w = max(2.0, min(100.0, 100.0 * v / maximum))
        rows.append('<div class="stat"><dt>%s</dt><dd><span class="stat-v">%d</span><span class="stat-bar">'
                    '<i class="s%d" style="width:%s%%"></i></span></dd></div>'
                    % (esc(names[k]), v, _tier(v), ("%.1f" % w).rstrip("0").rstrip(".")))
    if total:
        rows.append('<div class="stat stat-total"><dt>%s</dt><dd><span class="stat-v">%d</span></dd></div>'
                    % (esc(ctx.ui("total")), sum(stats[k] for k in STAT_KEYS)))
    return '<dl class="stats">%s</dl>' % "".join(rows)


def type_matchups(ctx, defending):
    """How much damage a Pokémon with these types takes, grouped by multiplier
    (the neutral ×1 group is left out). defending: type ids / Types."""
    from gamedata import typeinfo
    dts = []
    for t in defending:
        t = _type(t)
        if t.id not in [d.id for d in dts]:
            dts.append(t)
    groups = {}
    for a in typeinfo.battle_types():
        m = 1.0
        for d in dts:
            m *= typeinfo.effectiveness(a.id, d.id)
        groups.setdefault(m, []).append(a)
    rows = []
    for m in sorted(groups, reverse=True):
        if m == 1.0:
            continue
        cls = "x0" if m == 0 else "xhi" if m > 1 else "xlo"
        rows.append('<div class="mu %s"><dt>%s</dt><dd>%s</dd></div>'
                    % (cls, esc(ctx.mult(m)), "".join(type_chip(ctx, t) for t in groups[m])))
    return '<dl class="matchups">%s</dl>' % "".join(rows)


def ability_list(ctx, entries):
    """Abilities of a Pokémon with their descriptions. entries: [(Ability, hidden bool)]."""
    out = []
    for ab, hidden in entries:
        out.append('<li><span class="abil-n">%s%s</span><span class="abil-d">%s</span></li>'
                   % (ability_link(ctx, ab), " " + chip(ctx.ui("hidden_short"), "gold") if hidden else "",
                      esc(ab.description)))
    return '<ul class="abils">%s</ul>' % "".join(out)


def where_table(ctx, rows, id=None):
    """Where a Pokémon is found.

    rows  [{"key": map section constant, "name": place name, "region": "kanto"|"johto"|"hoenn"|None,
            "method": "land"|..., "method_text": text (overrides), "times": None or ["night", ...],
            "lo": 3, "hi": 5, "rate": 20.0 or None, "note": text}]
    """
    body, ra = [], []
    for r in rows:
        place = location_link(ctx, r["key"], r["name"]) if r.get("key") else esc(r["name"])
        if r.get("note"):
            place += ' <span class="muted">%s</span>' % esc(r["note"])
        times = time_chips(ctx, r["times"]) if r.get("times") else esc(ctx.ui("any_time"))
        body.append([place, region_chip(ctx, r["region"]) if r.get("region") else None,
                     esc(r.get("method_text") or ctx.ui("enc_" + r["method"])), times,
                     esc(ctx.pct(r["rate"])) if r.get("rate") is not None else None])
        ra.append(filter_attrs([r["name"]], region=r.get("region")))
    cols = [(ctx.ui("location"), "main"), (ctx.ui("region"), ""), (ctx.ui("method"), ""), (ctx.ui("time"), ""),
            (ctx.ui("rate"), "num")]
    return table(cols, body, cls="tbl-where", id=id, row_attrs=ra)


# ------------------------------------------------------------------ evolution
def evolution_chain(ctx, root, current=None):
    """Evolution line as a tree.

    root     {"species": Species, "how": text or None, "children": [node, ...]}
             ("how" = condition to reach this stage, e.g. "Lv. 16")
    current  the species of the page (marked, not linked)
    """
    def node(n, top):
        sp = n["species"]
        is_cur = current is not None and sp.id == current.id
        pic = sprite(ctx, sp, scale=1)
        inner = '%s<span class="evo-name">%s</span>' % (pic, esc(sp.name))
        url = None if is_cur else ctx.url_for("species", sp.const)
        if url:
            mon = '<a class="evo-mon" href="%s">%s</a>' % (url, inner)
        else:
            mon = '<span class="evo-mon"%s>%s</span>' % (' aria-current="true"' if is_cur else "", inner)
        how = "" if top else '<span class="evo-how">%s</span>' % esc(n.get("how") or "")
        kids = n.get("children") or []
        nxt = '<ol class="evo-next">%s</ol>' % "".join(node(k, False) for k in kids) if kids else ""
        return '<li class="evo-stage">%s%s%s</li>' % (how, mon, nxt)
    return '<div class="evo" role="group" aria-label="%s"><ol class="evo-root">%s</ol></div>' % (
        esc(ctx.ui("evo_chain_label")), node(root, True))


# ------------------------------------------------------------------ learnsets
_MOVE_TAIL = {}


def _move_cells(ctx, mv):
    """[name, type, category, power, accuracy, pp] cells of a move (cached per page depth)."""
    key = (ctx.lang, ctx.root, mv.id)
    c = _MOVE_TAIL.get(key)
    if c is None:
        c = [move_link(ctx, mv), type_chip(ctx, mv.type), cat_chip(ctx, mv.category),
             str(mv.power) if mv.power and mv.power > 1 else None,
             str(mv.accuracy) if mv.accuracy else None, str(mv.pp)]
        _MOVE_TAIL[key] = c
    return c


def move_table(ctx, rows, first=None, id=None, row_attrs=None):
    """Table of moves with type, category, power, accuracy and PP.

    rows   [(first cell HTML or None, Move)] - or [Move] when first is None
    first  label of the leading column ("Lv.", "TM"); None: no leading column
    """
    cols = ([(first, "num min m-lv")] if first else []) + [
        (ctx.ui("move"), "main"), (ctx.ui("type"), "m-type"), (ctx.ui("category"), "m-cat"),
        (ctx.ui("power"), "num m-n"), (ctx.ui("accuracy"), "num m-n"), (ctx.ui("pp"), "num m-n")]
    out = []
    for r in rows:
        if first:
            out.append([r[0]] + _move_cells(ctx, r[1]))
        else:
            out.append(_move_cells(ctx, r[1] if isinstance(r, tuple) else r))
    return table(cols, out, cls="tbl-moves", id=id, row_attrs=row_attrs)


def learnset(ctx, id, level=None, tm=None, tutor=None, egg=None, extra=()):
    """The four learnsets of a Pokémon as tabs.

    level  [(level int or text, Move)]      tm  [(label "TM01", Move)]
    tutor  [Move]                            egg [Move]
    extra  further tabs [(label, html, key)]
    Empty or None lists are left out."""
    panels = []
    if level:
        panels.append((ctx.ui("learn_level"),
                       move_table(ctx, [(esc(l), m) for l, m in level], first=ctx.ui("level")), "level"))
    if tm:
        panels.append((ctx.ui("learn_tm"),
                       move_table(ctx, [(esc(l), m) for l, m in tm], first=ctx.ui("learn_tm")), "tm"))
    if tutor:
        panels.append((ctx.ui("learn_tutor"), move_table(ctx, list(tutor)), "tutor"))
    if egg:
        panels.append((ctx.ui("learn_egg"), move_table(ctx, list(egg)), "egg"))
    panels.extend(extra)
    if not panels:
        return p(ctx.ui("learn_none"), "muted")
    return tabs(panels, id)


# ------------------------------------------------------------------ encounters
def encounter_block(ctx, method, rows, times=None, title=None, note=None):
    """One encounter table.

    method  "land" | "cave" | "water" | "rock_smash" | "old_rod" | "good_rod" | "super_rod"
    rows    [{"species": Species, "lo": 3, "hi": 5, "rate": 20.0, "note": text (optional),
              "times": times of day of this row only (optional; adds a day/night column)}]
    times   None (any time) or a list of "morning" | "day" | "evening" | "night"
    title   overrides the method name; note: HTML below the table
    """
    body = []
    timed = any(r.get("times") for r in rows)
    for r in rows:
        sp = r["species"]
        name = species_link(ctx, sp, icon=True)
        if r.get("note"):
            name += ' <span class="muted">%s</span>' % esc(r["note"])
        row = [name, types(ctx, sp.types),
               '<span class="rate">%s%s</span>' % (meter(r["rate"], 100), esc(ctx.pct(r["rate"])))]
        if timed:
            row.insert(1, time_chips(ctx, r["times"]) if r.get("times") else "")
        body.append(row)
    cols = [(ctx.ui("pokemon"), "main"), (ctx.ui("types"), "hide-s"), (ctx.ui("rate"), "num")]
    if timed:
        cols.insert(1, ctx.ui("col_day_night"))
    tchips = time_chips(ctx, times) if times else ""
    head = '<h3 class="enc-h"><span class="enc-ic enc-%s" aria-hidden="true"></span><span>%s</span>%s</h3>' % (
        method, esc(title or ctx.ui("enc_" + method)), '<span class="enc-times">%s</span>' % tchips if tchips else "")
    return '<div class="enc">%s%s%s</div>' % (head, table(cols, body, cls="tbl-enc tbl-enc-t" if timed else "tbl-enc"),
                                              '<p class="enc-note">%s</p>' % note if note else "")


def encounters(ctx, blocks):
    """Several encounter tables: blocks = [{"method", "rows", "times", "title", "note"}] in display order."""
    return '<div class="encs">%s</div>' % "".join(
        encounter_block(ctx, b["method"], b["rows"], b.get("times"), b.get("title"), b.get("note"))
        for b in blocks)


# ------------------------------------------------------------------ trainers
def team_member(ctx, m, detail=True):
    """One Pokémon of a trainer's team.

    m  {"species": Species, "level": 12 or "level_text": "Lv. 44–48", "item": Item, "ability": Ability,
        "nature": text, "moves": [Move], "shiny": bool, "note": text}  (all but species optional)
    """
    sp = m["species"]
    lv = m.get("level_text") or (ctx.level(m["level"]) if m.get("level") is not None else "")
    name = link(ctx, "species", sp.const, sp.name)
    top = '<div class="tm-top">%s<span class="tm-name">%s%s</span><span class="tm-lv">%s</span></div>' % (
        mon_icon(ctx, sp), name, ' <span class="shiny-mark" title="%s">✦</span>' % esc(ctx.ui("shiny"))
        if m.get("shiny") else "", esc(lv))
    if not detail:
        return '<li class="tm tm-compact">%s</li>' % top
    parts = [top, '<div class="tm-types">%s</div>' % types(ctx, sp.types)]
    pairs = []
    if m.get("ability") is not None:
        pairs.append((ctx.ui("ability"), ability_link(ctx, m["ability"])))
    if m.get("item") is not None:
        pairs.append((ctx.ui("item"), item_link(ctx, m["item"], icon=True)))
    if m.get("nature"):
        pairs.append((ctx.ui("nature"), esc(m["nature"])))
    if pairs:
        parts.append(kv(pairs, "tm-kv"))
    if m.get("moves"):
        from gamedata import typeinfo
        parts.append('<ul class="tm-moves">%s</ul>' % "".join(
            '<li class="t-%s">%s</li>' % (typeinfo.by_id(mv.type).slug, move_link(ctx, mv)) for mv in m["moves"]))
    if m.get("note"):
        parts.append('<p class="tm-note">%s</p>' % esc(m["note"]))
    return '<li class="tm">%s</li>' % "".join(parts)


def _auto_id(name, cls_name, team):
    import zlib
    key = "|".join([name or "", cls_name or ""] + [m["species"].const for m in team])
    return "t%06x" % (zlib.crc32(key.encode("utf-8")) & 0xFFFFFF)


def _team_line(ctx, team):
    """A team on one line: icon, name and level per Pokémon."""
    out = []
    for m in team:
        sp = m["species"]
        lv = m.get("level_text") or (ctx.level(m["level"]) if m.get("level") is not None else "")
        out.append('<span class="tr-mon">%s%s%s<span class="tr-lv">%s</span></span>' % (
            mon_icon(ctx, sp), link(ctx, "species", sp.const, sp.name),
            ' <span class="shiny-mark" title="%s">✦</span>' % esc(ctx.ui("shiny")) if m.get("shiny") else "", esc(lv)))
    return '<span class="tr-team">%s</span>' % "".join(out)


def team_table(ctx, team):
    """A team with everything known about each Pokémon as a table: level, ability, item,
    nature, moves. Columns nobody fills are left out."""
    def lv(m):
        return m.get("level_text") or (ctx.level(m["level"]) if m.get("level") is not None else "")
    has = {k: any(m.get(k) for m in team) for k in ("ability", "item", "nature", "moves", "note")}
    cols = [(ctx.ui("pokemon"), "main"), (ctx.ui("level"), "min")]
    for k, label in (("ability", ctx.ui("ability")), ("item", ctx.ui("item")), ("nature", ctx.ui("nature")),
                     ("moves", ctx.ui("moves"))):
        if has[k]:
            cols.append(label)
    rows = []
    for m in team:
        sp = m["species"]
        name = species_link(ctx, sp, icon=True)
        if m.get("shiny"):
            name += ' <span class="shiny-mark" title="%s">✦</span>' % esc(ctx.ui("shiny"))
        if m.get("note"):
            name += ' <span class="muted">%s</span>' % esc(m["note"])
        r = [name, esc(lv(m))]
        if has["ability"]:
            r.append(ability_link(ctx, m["ability"]) if m.get("ability") is not None else None)
        if has["item"]:
            r.append(item_link(ctx, m["item"], icon=True) if m.get("item") is not None else None)
        if has["nature"]:
            r.append(esc(m["nature"]) if m.get("nature") else None)
        if has["moves"]:
            r.append(", ".join(move_link(ctx, mv) for mv in m["moves"]) if m.get("moves") else None)
        rows.append(r)
    return table(cols, rows, cls="tbl-team")


def trainer_card(ctx, name, team, *, cls_name=None, pic=None, id=None, detail=True, double=False,
                 reward=None, meta=(), note=None, data=None, variants=(), first_label=None):
    """A trainer as one row: class, name, the team on one line. A trainer with details
    (abilities, items, moves) or further teams unfolds on click.

    name      trainer name (text)          cls_name  trainer class ("Arenaleiter")
    pic       trainer object or pic id for H.trainer_pic (shown in the unfolded part)
    team      [member dict] (see H.team_member)
    detail    True: the unfolded part lists abilities, items and moves
    double    show the double-battle chip   reward  prize money (number)
    meta      extra chips (HTML)            note    HTML below the team
    variants  further teams of the same trainer (rematches): [(label, team, note HTML or None)];
              they are shown as tabs next to the first team, which gets first_label
    id        anchor (register it with ctx.add_anchor("trainer", ...))
    data      extra attributes (H.filter_attrs)
    """
    ch = list(meta)
    if double:
        ch.append(chip(ctx.ui("double_battle"), "muted"))
    if reward is not None:
        ch.append('<span class="tr-prize">%s</span>' % esc(ctx.money(reward)))
    who = '<span class="tr-who">%s<strong>%s</strong></span>' % (
        '<span class="tr-class">%s</span> ' % esc(cls_name) if cls_name and cls_name != name else "", esc(name))
    head = who + _team_line(ctx, team) + ('<span class="tr-meta">%s</span>' % "".join(ch) if ch else "")
    a = {"class": "tr", "id": id}
    a.update(data or {})
    fold = detail or variants or note
    if not fold:
        return '<div%s><div class="tr-h">%s</div></div>' % (attrs(a), head)
    first = team_table(ctx, team) if detail else ""
    if note:
        first += '<div class="tr-note">%s</div>' % note
    if variants:
        panels = [(first_label or ctx.ui("first_battle"), first or _team_line(ctx, team))]
        for label, vteam, vnote in variants:
            body = team_table(ctx, vteam) + ('<div class="tr-note">%s</div>' % vnote if vnote else "")
            panels.append((label, body))
        inner = tabs(panels, "%s-teams" % (id or _auto_id(name, cls_name, team)))
    else:
        inner = first
    picture = '<div class="tr-pic">%s</div>' % trainer_pic(ctx, pic) if pic is not None else ""
    return '<details%s><summary class="tr-h">%s</summary><div class="tr-b">%s<div class="tr-main">%s</div></div></details>' % (
        attrs(a), head, picture, inner)


def trainer_list(cards, id=None):
    """Wrapper of a list of trainer rows."""
    return "<div%s%s>%s</div>" % (_cls("trs"), attrs({"id": id}), "".join(cards))


# ------------------------------------------------------------------ items and shops
def item_list(ctx, entries):
    """List of items found at a place.

    entries  [{"item": Item, "qty": 1, "hidden": False, "how": text, "note": text}]
             how: where/how it is obtained ("im Gras nördlich"), note: condition
    """
    out = []
    for e in entries:
        it = e["item"]
        bits = [item_link(ctx, it, icon=True)]
        if e.get("qty", 1) and e.get("qty", 1) > 1:
            bits.append('<span class="qty">×%d</span>' % e["qty"])
        if e.get("hidden"):
            bits.append(chip(ctx.ui("hidden_item"), "muted"))
        tail = " ".join(esc(x) for x in (e.get("how"), e.get("note")) if x)
        out.append('<li><span class="it-main">%s</span>%s</li>'
                   % ("".join(bits), '<span class="it-note">%s</span>' % tail if tail else ""))
    return '<ul class="items">%s</ul>' % "".join(out)


def shop_table(ctx, entries, caption=None):
    """Shop stock. entries: [{"item": Item, "price": 300, "note": text}]
    (price None: the item's own price; note e.g. a badge requirement)."""
    has_note = any(e.get("note") for e in entries)
    rows = []
    for e in entries:
        it = e["item"]
        price = e.get("price")
        if price is None:
            price = it.price
        r = [item_link(ctx, it, icon=True), esc(ctx.money(price))]
        if has_note:
            r.append(esc(e["note"]) if e.get("note") else "")
        rows.append(r)
    cols = [(ctx.ui("item"), "main"), (ctx.ui("price"), "num")] + ([(ctx.ui("note"), "")] if has_note else [])
    return table(cols, rows, caption=caption, cls="tbl-shop")
