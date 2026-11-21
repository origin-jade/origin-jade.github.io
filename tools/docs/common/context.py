"""Build context of one language: registry, strings, URLs and the page shell.

A page module gets the same Context twice (see FRAMEWORK2.md):

    def register(ctx):   # pass 1: say which pages and entities exist
        ctx.add_page("data/abilities/index")
        ctx.add_entity("ability", a.const, a.name)
    def render(ctx):     # pass 2: write them
        ctx.begin("ability", a.const)
        ctx.end(body, lead=...)

Registration
    ctx.add_page(path, title=None, *, nav=None, nav_title=None, parent=None, section=None,
                 search=True, keywords="", icon="", sub="", kind="page", key=None)
    ctx.add_entity(kind, const, title, *, keywords="", icon="", sub="", search=True, parent=None, path=None)
    ctx.add_anchor(kind, key, page_path, frag, title, *, keywords="", icon="", sub="", search=True)
Lookup (render pass)
    ctx.url_for(kind, key)   relative URL of an entity or None      ctx.url(path)  the same for a page path
    ctx.title_of(kind, key)  registered title or None               ctx.has(kind, key)
    ctx.asset(kind, name, ext="png")   relative URL of a shared image (exported on demand)
Strings and numbers
    ctx.t(key, **fmt) module string    ctx.ui(key, **fmt) shared UI string
    ctx.num(x) ctx.pct(x) ctx.money(n) ctx.mult(m) ctx.level(n) ctx.level_range(lo, hi)
Rendering
    ctx.begin(path) / ctx.begin(kind, key)     start a page: relative URLs now refer to it
    ctx.end(body, *, title, eyebrow, lead, chips, aside, outline, prev, next, wide, cls, scripts)
Notes
    ctx.todo(text)   content that could not be verified -> report file, never the site
    ctx.warn(text)   build warning (fails with --strict)
Files
    ctx.write_asset(rel, data)   extra file below assets/ (str or bytes)
    ctx.write_image(rel, img)    PIL image below assets/
"""
import os
import re
import time

from . import i18n, slugs
from . import html as H

_HEAD_RE = re.compile(r'<section class="sec[^"]*" id="([^"]+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>', re.S)
_TAG_RE = re.compile(r"<[^>]+>")


class BuildError(Exception):
    """A module broke the contract; the build stops with this message."""


class Page:
    __slots__ = ("path", "title", "section", "nav", "nav_title", "parent", "module", "kind", "key",
                 "rendered")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class Entry:
    __slots__ = ("kind", "key", "path", "frag", "title", "keywords", "icon", "search", "module", "sub")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    @property
    def url(self):
        return self.path + ".html" + ("#" + self.frag if self.frag else "")


class Context:
    def __init__(self, repo, out, lang, version, dev=False, strict=False):
        self.repo = repo
        self.out = out                      # site root (holds de/, en/, assets/)
        self.lang = lang
        self.other_langs = [l for l in i18n.LANGS if l != lang]
        self.version = version              # {"css": "abcd1234", "js": "..."} cache-busting ids
        self.dev = dev
        self.strict = strict
        self.pages = {}                     # path -> Page
        self.entries = {}                   # (kind, key) -> Entry
        self.module = None                  # module being registered / rendered
        self.module_name = None
        self.phase = "init"                 # "register" | "render"
        self.cur = None                     # Page being rendered
        self.root = ""                      # relative prefix from the current page to the language folder
        self.warnings = []
        self.todos = []
        self.problems = []
        self.reviews = []                   # phrases to look at by hand (report only)
        self.used_assets = {}               # "assets/..." -> first page
        self.written_assets = set()
        self.written = {}                   # page path -> size in bytes
        self.page_ids = {}                  # page path -> frozenset(ids)
        self.page_links = {}                # page path -> [(raw, target path|None, frag)]
        self.timings = {}
        self._nav_cache = None
        self._nav_active = {}
        self._checks = None

    # ------------------------------------------------------------ strings
    def ui(self, key, **fmt):
        return i18n.ui(self.lang, key, **fmt)

    def t(self, key, **fmt):
        """String of the current module (STRINGS[lang][key])."""
        strings = getattr(self.module, "STRINGS", None)
        try:
            s = strings[self.lang][key]
        except (KeyError, TypeError):
            raise BuildError("%s: string %r missing in STRINGS[%r]" % (self.module_name, key, self.lang)) from None
        return s.format(**fmt) if fmt else s

    def num(self, x, digits=1):
        return i18n.num(self.lang, x, digits)

    def pct(self, x, digits=1):
        return i18n.pct(self.lang, x, digits)

    def money(self, n):
        return i18n.money(self.lang, n)

    def mult(self, m):
        return i18n.mult(self.lang, m)

    def level(self, n):
        return i18n.ui(self.lang, "level_n", n=n)

    def level_range(self, lo, hi):
        if lo == hi:
            return self.level(lo)
        return i18n.ui(self.lang, "level_range", lo=lo, hi=hi)

    # ------------------------------------------------------------ notes
    def _where(self):
        if self.cur is not None:
            return "%s [%s]" % (self.module_name, self.cur.path)
        return self.module_name or "build"

    def todo(self, text):
        """Something that could not be determined from the source: goes to the report."""
        self.todos.append("%s: %s" % (self._where(), text))

    def warn(self, text):
        self.warnings.append("%s: %s" % (self._where(), text))

    def problem(self, text):
        self.problems.append(text)

    # ------------------------------------------------------------ registration
    def _need_phase(self, phase, what):
        if self.phase != phase:
            raise BuildError("%s: %s is only allowed in %s(ctx)" % (self.module_name, what, phase))

    def add_page(self, path, title=None, *, nav=None, nav_title=None, parent=None, section=None,
                 search=True, keywords="", icon="", sub="", kind="page", key=None):
        """Register a page this module renders. Pages listed in i18n.SITEMAP take
        title, section and sidebar position from there.

        nav       sidebar position inside its section (a number; None: not in the sidebar)
        parent    page path of the parent (breadcrumbs, active sidebar entry); default <folder>/index
        search    False keeps the page out of the global search
        keywords  extra search words (text or list), not shown
        icon      small image in the search results: ctx.asset_rel("icon", sp.slug)
        sub       short second line in the search results ("Kanto", "Route 6")"""
        self._need_phase("register", "add_page")
        slugs.check_path(path)
        fixed = i18n.SITEMAP.get(path)
        if fixed is not None:
            if section is None:
                section = fixed[0]
            if nav is None:
                nav = fixed[1]
            if title is None:
                title = i18n.sitemap_title(self.lang, path)
            if nav_title is None:
                nav_title = i18n.sitemap_title(self.lang, path, nav=True)
        if not title:
            raise BuildError("%s: add_page(%r) needs a title" % (self.module_name, path))
        if section is None:
            head = path.split("/", 1)[0]
            section = head if head in slugs.SECTIONS else None
        if path in self.pages:
            raise BuildError("%s: page %r is already registered by %s"
                             % (self.module_name, path, self.pages[path].module))
        if key is None:
            key = path
        self.pages[path] = Page(path=path, title=title, section=section, nav=nav, nav_title=nav_title or title,
                                parent=parent, module=self.module_name, kind=kind, key=key, rendered=False)
        self._add_entry(kind, key, path, None, title, keywords, icon, search, sub)
        return path

    def add_entity(self, kind, const, title, *, keywords="", icon="", sub="", search=True, parent=None,
                   path=None):
        """Register the page of one entity (Pokémon, move, ability, item, location, trainer).
        The path follows slugs.entity_path unless given."""
        key = slugs.const_of(const)
        if path is None:
            path = slugs.entity_path(kind, key)
        return self.add_page(path, title, parent=parent, search=search, keywords=keywords, icon=icon,
                             sub=sub, kind=kind, key=key)

    def add_anchor(self, kind, key, page_path, frag, title, *, keywords="", icon="", sub="", search=True):
        """Register an entity that has no page of its own: it lives at #frag on page_path."""
        self._need_phase("register", "add_anchor")
        slugs.check_path(page_path)
        self._add_entry(kind, slugs.const_of(key), page_path, frag, title, keywords, icon, search, sub)

    def _add_entry(self, kind, key, path, frag, title, keywords, icon, search, sub=""):
        if kind not in slugs.KINDS:
            raise BuildError("%s: unknown kind %r (have: %s)" % (self.module_name, kind, ", ".join(slugs.KINDS)))
        if (kind, key) in self.entries:
            raise BuildError("%s: %s %r is already registered by %s"
                             % (self.module_name, kind, key, self.entries[(kind, key)].module))
        if isinstance(keywords, (list, tuple)):
            keywords = " ".join(str(k) for k in keywords if k)
        self.entries[(kind, key)] = Entry(kind=kind, key=key, path=path, frag=frag, title=title,
                                          keywords=keywords or "", icon=icon or "", search=bool(search),
                                          module=self.module_name, sub=sub or "")

    # ------------------------------------------------------------ lookup
    def has(self, kind, key):
        return (kind, slugs.const_of(key)) in self.entries

    def entry(self, kind, key):
        return self.entries.get((kind, slugs.const_of(key)))

    def title_of(self, kind, key):
        e = self.entry(kind, key)
        return e.title if e else None

    def _need_page(self, what):
        if self.cur is None:
            raise BuildError("%s: %s needs an open page - call ctx.begin(...) first (relative URLs depend "
                             "on the page)" % (self.module_name, what))

    def url_for(self, kind, key):
        """Relative URL (from the page being rendered) of an entity, or None if no module registered it."""
        self._need_page("url_for")
        e = self.entries.get((kind, slugs.const_of(key)))
        return None if e is None else self.root + e.url

    def url(self, path):
        """Relative URL of a page path, or None if it is not registered."""
        self._need_page("url")
        return self.root + path + ".html" if path in self.pages else None

    def asset(self, kind, name, ext="png"):
        """Relative URL of assets/<kind>/<name>.<ext>; the image is exported when it is used."""
        self._need_page("asset")
        rel = "assets/%s/%s.%s" % (kind, name, ext)
        if rel not in self.used_assets:
            self.used_assets[rel] = self.cur.path if self.cur else (self.module_name or "")
        return self.root + "../" + rel

    def asset_rel(self, kind, name, ext="png"):
        """Path below assets/ for registry icons ("icon/bulbasaur.png"); marks the image as used."""
        rel = "assets/%s/%s.%s" % (kind, name, ext)
        self.used_assets.setdefault(rel, self.module_name or "")
        return rel[len("assets/"):]

    # ------------------------------------------------------------ files
    def _path(self, rel):
        p = os.path.join(self.out, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    def write_asset(self, rel, data):
        """Write assets/<rel> (str or bytes). Language-specific data needs the language in its name."""
        if rel.startswith("assets/"):
            rel = rel[len("assets/"):]
        p = self._path("assets/" + rel)
        if isinstance(data, bytes):
            with open(p, "wb") as f:
                f.write(data)
        else:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(data)
        self.written_assets.add("assets/" + rel)
        return rel

    def write_image(self, rel, img):
        from gamedata import graphics
        if rel.startswith("assets/"):
            rel = rel[len("assets/"):]
        graphics.save(img, self._path("assets/" + rel))
        self.written_assets.add("assets/" + rel)
        return rel

    # ------------------------------------------------------------ rendering
    def begin(self, kind_or_path, key=None):
        """Start rendering a registered page: ctx.begin("data/typechart") or ctx.begin("ability", const)."""
        self._need_phase("render", "begin")
        if self.cur is not None:
            raise BuildError("%s: begin() while %r is still open (missing ctx.end)"
                             % (self.module_name, self.cur.path))
        if key is None:
            path = kind_or_path
        else:
            e = self.entries.get((kind_or_path, slugs.const_of(key)))
            if e is None or e.frag:
                raise BuildError("%s: begin(%r, %r): no such entity page registered"
                                 % (self.module_name, kind_or_path, key))
            path = e.path
        page = self.pages.get(path)
        if page is None:
            raise BuildError("%s: begin(%r): page is not registered" % (self.module_name, path))
        if page.module != self.module_name:
            raise BuildError("%s: page %r belongs to module %s" % (self.module_name, path, page.module))
        if page.rendered:
            raise BuildError("%s: page %r rendered twice" % (self.module_name, path))
        self.cur = page
        self.root = "../" * path.count("/")
        return page

    def end(self, body, *, title=None, eyebrow=None, lead=None, chips=None, aside=None, outline=True,
            prev=None, next=None, wide=False, cls=None, scripts=(), description=None):
        """Finish the page started with begin(): wrap body in the shell and write the file.

        title     plain text, default: the registered title
        eyebrow   small line above the title (plain text), e.g. "#001 · Kanto"
        lead      HTML of the intro paragraph below the title
        chips     HTML shown under the title (type chips, badges)
        aside     HTML at the right of the header (sprite plate)
        outline   True: "on this page" list from the H.section headings (3 or more)
        prev/next neighbours: a page path or a (kind, key) tuple; unknown ones are skipped
        wide      use the full width (big tables, charts)
        scripts   extra data scripts: asset paths below assets/ (loaded before site.js)
        """
        page = self.cur
        if page is None:
            raise BuildError("%s: end() without begin()" % self.module_name)
        doc = self._shell(page, body, title or page.title, eyebrow, lead, chips, aside, outline,
                          prev, next, wide, cls, scripts, description)
        rel = "%s/%s.html" % (self.lang, page.path)
        with open(self._path(rel), "w", encoding="utf-8", newline="\n") as f:
            f.write(doc)
        self.written[page.path] = len(doc.encode("utf-8"))
        page.rendered = True
        if self._checks is not None:
            self._checks.page(self, page, doc)
        self.cur = None
        self.root = ""

    # ------------------------------------------------------------ shell parts
    def _nav_parent(self, page):
        """Parent page (Page or None): explicit, else <dir>/index, else <section>/index."""
        if page.parent:
            p = self.pages.get(page.parent)
            if p is not None and p is not page:
                return p
        parts = page.path.split("/")
        for n in range(len(parts) - 1, 0, -1):
            cand = "/".join(parts[:n]) + "/index"
            p = self.pages.get(cand)
            if p is not None and p is not page:
                return p
        return None

    def _chain(self, page):
        """[ancestors..., page] following parents (cycle safe)."""
        chain, seen = [page], {page.path}
        cur = page
        while True:
            cur = self._nav_parent(cur)
            if cur is None or cur.path in seen:
                break
            chain.append(cur)
            seen.add(cur.path)
        chain.reverse()
        return chain

    def nav_tree(self):
        """[(section id, [Page...])] of the pages with a sidebar position."""
        by = {s: [] for s in slugs.SECTIONS}
        for p in self.pages.values():
            if p.nav is not None and p.section in by:
                by[p.section].append(p)
        return [(s, sorted(by[s], key=lambda p: (p.nav, p.path))) for s in slugs.SECTIONS]

    def _nav_html(self):
        """Sidebar tree with \x00 in front of every URL (replaced by the page's root prefix)."""
        if self._nav_cache is None:
            out = []
            for sec, pages in self.nav_tree():
                if sec == "home":
                    for p in pages:
                        out.append('<a class="side-home" href="\x00%s.html">%s</a>' % (p.path, H.esc(p.nav_title)))
                    continue
                if not pages:
                    continue
                items = "".join('<li><a href="\x00%s.html">%s</a></li>' % (p.path, H.esc(p.nav_title))
                                for p in pages)
                out.append('<details class="side-sec" data-sec="%s"><summary>%s</summary><ul>%s</ul></details>'
                           % (sec, H.esc(self.ui("sec_" + sec)), items))
            self._nav_cache = "".join(out)
        return self._nav_cache

    def _sidebar(self, page, chain):
        nav = self._nav_html().replace("\x00", self.root)
        active = None
        for p in reversed(chain):
            if p.nav is not None:
                active = p
                break
        if active is not None:
            href = 'href="%s%s.html"' % (self.root, active.path)
            cur = "page" if active is page else "true"
            nav = nav.replace(href, '%s aria-current="%s"' % (href, cur), 1)
        if page.section == "home":
            nav = nav.replace('<details class="side-sec"', '<details open class="side-sec"')
        elif page.section:
            nav = nav.replace('data-sec="%s">' % page.section, 'data-sec="%s" open>' % page.section, 1)
        return nav

    def _crumbs(self, page, chain):
        if page.path == "index":
            return ""
        items = []
        if "index" in self.pages:
            items.append('<li><a href="%sindex.html">%s</a></li>' % (self.root, H.esc(self.ui("sec_home"))))
        if page.section and page.section != "home":
            sec_index = self.pages.get(page.section + "/index")
            if sec_index is None or sec_index not in chain:
                items.append("<li>%s</li>" % H.esc(self.ui("sec_" + page.section)))
        for p in chain[:-1]:
            title = self.ui("sec_" + p.section) if p.path == "%s/index" % p.section else p.title
            items.append('<li><a href="%s%s.html">%s</a></li>' % (self.root, p.path, H.esc(title)))
        items.append('<li aria-current="page">%s</li>' % H.esc(chain[-1].title))
        return '<nav class="crumbs" aria-label="%s"><ol>%s</ol></nav>' % (H.esc(self.ui("crumbs_label")),
                                                                            "".join(items))

    def _neighbour(self, ref):
        """(url, title) of a prev/next reference or None."""
        if ref is None:
            return None
        if isinstance(ref, tuple):
            e = self.entries.get((ref[0], slugs.const_of(ref[1])))
            if e is None:
                return None
            return self.root + e.url, e.title
        p = self.pages.get(ref)
        return (self.root + p.path + ".html", p.title) if p is not None else None

    def _shell(self, page, body, title, eyebrow, lead, chips, aside, outline, prev, nxt, wide, cls,
               scripts, description):
        ui = self.ui
        root = self.root
        assets = root + "../assets/"
        lang = self.lang
        chain = self._chain(page)
        is_home = page.path == "index"
        if is_home:
            doc_title = "%s%s%s" % (ui("site_name"), ui("title_sep"), ui("site_tagline"))
        else:
            doc_title = "%s%s%s" % (title, ui("title_sep"), ui("site_name"))

        heads = _HEAD_RE.findall(body) if outline else []
        outline_html = ""
        if len(heads) >= 3:
            lis = "".join('<li><a href="#%s">%s</a></li>' % (i, _TAG_RE.sub("", t).strip()) for i, t in heads)
            outline_html = ('<nav class="outline" aria-label="%s"><p class="outline-title">%s</p><ol>%s</ol></nav>'
                            % (H.esc(ui("outline_label")), H.esc(ui("outline_label")), lis))

        other = self.other_langs[0]
        switch = []
        for l in i18n.LANGS:
            if l == lang:
                switch.append('<span class="lang-cur" aria-current="true">%s</span>' % l.upper())
            else:
                switch.append('<a href="%s../%s/%s.html" hreflang="%s" lang="%s" data-lang="%s" title="%s">%s</a>'
                              % (root, l, page.path, l, l, l,
                                 H.esc(ui("lang_switch_to", name=i18n.LANG_NAMES[l])), l.upper()))
        home_url = root + "index.html"

        o = []
        o.append("<!doctype html>")
        o.append('<html lang="%s" data-lang="%s" data-root="%s" data-theme="dark">' % (i18n.HTML_LANG[lang], lang, root))
        o.append("<head>")
        o.append('<meta charset="utf-8">')
        o.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
        import site_config
        if getattr(site_config, "NOINDEX", False):
            o.append('<meta name="robots" content="noindex, nofollow">')
        o.append("<title>%s</title>" % H.esc(doc_title))
        if description:
            o.append('<meta name="description" content="%s">' % H.esc(description))
        o.append('<meta name="color-scheme" content="light dark">')
        o.append(H.HEAD_SCRIPT)
        o.append('<link rel="alternate" hreflang="%s" href="%s../%s/%s.html">' % (other, root, other, page.path))
        o.append('<link rel="icon" type="image/png" sizes="32x32" href="%simg/favicon-32.png">' % assets)
        o.append('<link rel="apple-touch-icon" sizes="180x180" href="%simg/favicon-180.png">' % assets)
        o.append('<link rel="stylesheet" href="%ssite.css?v=%s">' % (assets, self.version["css"]))
        o.append("</head>")
        body_cls = " ".join(c for c in ("home" if is_home else "", "wide" if wide else "", cls or "") if c)
        o.append("<body%s>" % (' class="%s"' % body_cls if body_cls else ""))
        o.append('<a class="skip" href="#main">%s</a>' % H.esc(ui("skip")))
        o.append('<header class="topbar"><div class="topbar-in">')
        o.append('<a class="menu-btn" href="#nav" data-menu aria-label="%s"><span class="i i-menu" '
                 'aria-hidden="true"></span></a>' % H.esc(ui("menu")))
        o.append('<a class="brand" href="%s"><img class="brand-mark px" src="%simg/mark.png" alt="" width="32" '
                 'height="32"><span class="brand-name">%s</span></a>' % (home_url, assets, H.esc(ui("site_short"))))
        o.append('<button class="search-btn" type="button" data-search-open aria-haspopup="dialog" '
                 'aria-keyshortcuts="/ Control+K Meta+K"><span class="i i-search" aria-hidden="true"></span>'
                 '<span class="search-btn-text">%s</span><span class="sr">%s</span><kbd aria-hidden="true">/</kbd>'
                 '</button>' % (H.esc(ui("search_placeholder")), H.esc(ui("search_open"))))
        o.append('<div class="top-actions"><div class="lang" role="group" aria-label="%s">%s</div>'
                 '<button class="theme-btn" type="button" data-theme-toggle aria-label="%s" title="%s">'
                 '<span class="i i-theme" aria-hidden="true"></span></button></div>'
                 % (H.esc(ui("lang_label")), "".join(switch), H.esc(ui("theme_toggle")), H.esc(ui("theme_toggle"))))
        o.append("</div></header>")
        o.append('<div class="layout">')
        o.append('<nav class="sidebar" id="nav" aria-label="%s"><div class="side-in">%s</div></nav>'
                 % (H.esc(ui("nav_label")), self._sidebar(page, chain)))
        o.append('<main id="main" class="page">')
        o.append('<div class="page-top">')
        crumbs = self._crumbs(page, chain)
        if crumbs:
            o.append(crumbs)
        if not is_home:
            head = ['<header class="page-head%s">' % (" has-aside" if aside else ""), '<div class="page-head-main">']
            if eyebrow:
                head.append('<p class="eyebrow">%s</p>' % H.esc(eyebrow))
            head.append("<h1>%s</h1>" % H.esc(title))
            if chips:
                head.append('<div class="page-chips">%s</div>' % chips)
            if lead:
                head.append('<p class="lead">%s</p>' % lead)
            head.append("</div>")
            if aside:
                head.append('<div class="page-aside">%s</div>' % aside)
            head.append("</header>")
            o.append("".join(head))
        o.append("</div>")
        if outline_html:
            o.append(outline_html)
        o.append('<div class="page-body">')
        o.append(body.strip("\n"))
        o.append("</div>")
        pn = [self._neighbour(prev), self._neighbour(nxt)]
        o.append('<footer class="page-foot">')
        if pn[0] or pn[1]:
            parts = []
            for i, n in enumerate(pn):
                if n is None:
                    parts.append("<span></span>")
                else:
                    parts.append('<a class="pn pn-%s" href="%s" rel="%s"><span class="pn-dir">%s</span>'
                                 '<span class="pn-title">%s</span></a>'
                                 % ("prev" if i == 0 else "next", n[0], "prev" if i == 0 else "next",
                                    H.esc(ui("prev" if i == 0 else "next")), H.esc(n[1])))
            o.append('<nav class="prevnext" aria-label="%s">%s</nav>' % (H.esc(ui("prevnext_label")), "".join(parts)))
        o.append(self._footer())
        o.append("</footer>")
        o.append("</main>")
        o.append("</div>")
        for s in scripts or ():
            rel = s[len("assets/"):] if s.startswith("assets/") else s
            self.used_assets.setdefault("assets/" + rel, page.path)
            o.append('<script src="%s%s"></script>' % (assets, rel))
        o.append('<script src="%ssite.js?v=%s" defer></script>' % (assets, self.version["js"]))
        o.append("</body>")
        o.append("</html>")
        return "\n".join(o) + "\n"

    def _footer(self):
        import site_config
        ui = self.ui
        links = []
        for key, labels, url in site_config.COMMUNITY_LINKS:
            if url:
                links.append('<a href="%s" rel="noopener">%s</a>' % (H.esc(url), H.esc(labels[i18n.LANG_INDEX[self.lang]])))
        community = ('<p class="foot-links"><span>%s:</span> %s</p>' % (H.esc(ui("community")), " ".join(links))
                     if links else "")
        return ('<div class="site-foot"><p class="foot-brand"><strong>%s</strong> <span>%s</span></p>'
                '%s<p>%s</p><p>%s</p></div>'
                % (H.esc(ui("site_name")), H.esc(site_config.VERSION[self.lang]), community,
                   H.esc(ui("footer_note")), H.esc(ui("footer_fan"))))

    # ------------------------------------------------------------ module driver (used by build_site)
    def run(self, phase, name, module):
        self.phase = phase
        self.module = module
        self.module_name = name
        t0 = time.time()
        try:
            getattr(module, phase)(self)
            if self.cur is not None:
                raise BuildError("%s: render() ended while page %r is still open (missing ctx.end)"
                                 % (name, self.cur.path))
        finally:
            self.timings.setdefault(name, {})[phase] = round(time.time() - t0, 2)
            self.module = None
            self.module_name = None
            self.phase = "idle"
