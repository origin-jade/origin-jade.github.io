"""Checks every written page goes through (and the final link check).

Text hygiene (what must never reach the site):
  * checksums, ROM files, patch tools and sources,
  * names from the code: constants (FLAG_..., SPECIES_...), source file names,
  * words about how the pages were made (tool names fail; looser phrases are listed for review),
  * leftover placeholders ("[OFFEN", "TODO", unformatted "{name}").
Links: every href and src must resolve - inside the language tree to a page
that exists (or is registered, with --only), fragments to an id on the target
page; assets and the other language are handed to the parent build for the
check on disk. External addresses are only allowed for the community links of
site_config.py.
"""
import posixpath
import re

FORBIDDEN = [
    (re.compile(r"\b[0-9a-f]{40}\b", re.I), "checksum (40 hex digits)"),
    (re.compile(r"\bsha-?1\b|\bsha-?256\b|\bmd5\b|\bcrc-?32\b|prüfsumme|checksum", re.I), "checksum"),
    (re.compile(r"\.gba\b|\.bps\b|\.ips\b|\.ups\b|rom[- ]?patcher|floating ips|lunar ips|\bxdelta\b", re.I),
     "ROM file or patch hint"),
    (re.compile(r"\b(?:SPECIES|MOVE|ITEM|ABILITY|TRAINER|MAPSEC|MAP|FLAG|VAR|EVO|TYPE|EFFECT|OBJ_EVENT_GFX|"
                r"TIME|METLOC|NATURE|EGG_GROUP|GROWTH|POCKET|HOLD_EFFECT|B|I|P|OW|GEN)_[A-Z0-9][A-Z0-9_]*\b"),
     "constant from the code"),
    (re.compile(r"\b[A-Z][A-Z0-9]+_[A-Z0-9]+_[A-Z0-9_]+\b"), "constant from the code"),
    (re.compile(r"\b[\w/\-]+\.(?:c|h|inc|json|py|pory|party|mk|pal|4bpp)\b"), "source file name"),
    (re.compile(r"\b[gs][A-Z][A-Za-z0-9]*_[A-Za-z0-9_]+\b"), "symbol from the code"),
    (re.compile(r"build_site|tools/docs|\bpython\b", re.I), "name of an internal tool"),
    (re.compile(r"\[OFFEN|\bTODO\b|\bFIXME\b|\bXXX\b|\bTBD\b|lorem ipsum|\{[a-z_][a-z0-9_]*\}", re.I),
     "leftover placeholder"),
]
SUSPECT = []

_SCRIPT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_ATTR_TEXT_RE = re.compile(r'\b(?:alt|title|aria-label|placeholder|content)="([^"]*)"')
_LINK_RE = re.compile(r'\b(?:href|src)="([^"]*)"')
_ID_RE = re.compile(r'\bid="([^"]+)"')


def text_problems(html):
    """[(what, sample)] and [(warning, sample)] of one document."""
    visible = _TAG_RE.sub(" ", _SCRIPT_RE.sub(" ", html))
    attr_text = " | ".join(_ATTR_TEXT_RE.findall(html))
    problems, warnings = [], []
    for pat, what in FORBIDDEN:
        for hay in (visible, attr_text):
            m = pat.search(hay)
            if m:
                problems.append((what, m.group(0)))
                break
    for pat, what in SUSPECT:
        m = pat.search(visible)
        if m:
            warnings.append((what, m.group(0)))
    return problems, warnings


class Checker:
    """Collects ids and links of the pages of one language; verify() at the end."""

    def __init__(self, lang, allowed_external=()):
        self.lang = lang
        self.allowed_external = set(allowed_external)
        self.ids = {}            # page path -> frozenset of ids
        self.links = {}          # page path -> set of (target, frag)   target relative to the site root
        self.external = {}

    def page(self, ctx, page, doc):
        # development pages (dev/...) show code samples; they are never part of a release build
        problems, warnings = ([], []) if page.path.startswith("dev/") else text_problems(doc)
        for what, sample in problems:
            ctx.problem("%s/%s.html: %s (%r)" % (self.lang, page.path, what, sample))
        for what, sample in warnings:
            ctx.reviews.append("%s/%s.html: %s (%r)" % (self.lang, page.path, what, sample))
        self.ids[page.path] = frozenset(_ID_RE.findall(doc))
        base = posixpath.dirname("%s/%s" % (self.lang, page.path))
        links = set()
        for raw in set(_LINK_RE.findall(doc)):
            raw = raw.replace("&amp;", "&")
            if raw.startswith(("http://", "https://", "//")):
                if raw not in self.allowed_external:
                    ctx.problem("%s/%s.html: external address %r" % (self.lang, page.path, raw))
                continue
            if raw.startswith(("mailto:", "data:", "javascript:")):
                ctx.problem("%s/%s.html: address %r is not allowed" % (self.lang, page.path, raw))
                continue
            url, _, frag = raw.partition("#")
            url = url.split("?", 1)[0]
            if not url:
                links.add((None, frag))
                continue
            target = posixpath.normpath(posixpath.join(base, url))
            links.add((target, frag))
        self.links[page.path] = links

    def verify(self, ctx, rendered_only):
        """Check the collected links. rendered_only: True when every registered page was rendered
        (full build); with --only, pages of other modules count as present when registered.
        -> set of targets outside the language tree (assets, other language) for the parent."""
        outside = {}
        prefix = self.lang + "/"
        for path in sorted(self.links):
            here = "%s/%s.html" % (self.lang, path)
            for target, frag in sorted(self.links[path], key=lambda x: (x[0] or "", x[1])):
                if target is None:
                    if frag and frag not in self.ids[path]:
                        ctx.problem("%s: link to #%s, but the page has no such id" % (here, frag))
                    continue
                if target.startswith(prefix):
                    if not target.endswith(".html"):
                        ctx.problem("%s: link to %s (not a page)" % (here, target))
                        continue
                    p = target[len(prefix):-len(".html")]
                    if p not in ctx.pages:
                        ctx.problem("%s: link to %s, which does not exist" % (here, target))
                    elif frag and p in self.ids and frag not in self.ids[p]:
                        ctx.problem("%s: link to %s#%s, but that page has no such id" % (here, target, frag))
                else:
                    outside.setdefault(target, here)
        return outside
