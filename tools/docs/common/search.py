"""Text folding shared by the search index, the filter bars and site.js.

fold() must stay in step with fold() in static/site.js:
  * lower case, accents dropped (é -> e), ä/ö/ü -> a/o/u, ß -> ss,
  * everything that is not a-z or 0-9 becomes a single space.
The client additionally matches the ae/oe/ue spelling ("glueh" finds
"Glühbirne"); alt_fold() gives that second form for data attributes.

    fold("Glühbirne!")          -> "gluhbirne"
    filter_text("Ho-Oh", "Glühbirne") -> "ho oh hooh gluhbirne gluehbirne"
"""
import json
import re
import unicodedata

_UML = {"ä": "ae", "ö": "oe", "ü": "ue"}
_NON = re.compile(r"[^a-z0-9]+")


def _strip(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def fold(s):
    """Folded form: "Flammenwurf (Stärke 90)" -> "flammenwurf starke 90"."""
    s = _strip(str(s).lower().replace("ß", "ss"))
    return _NON.sub(" ", s).strip()


def alt_fold(s):
    """Folded form with ae/oe/ue for umlauts, or None when it equals fold(s)."""
    low = str(s).lower()
    if not any(u in low for u in _UML):
        return None
    for u, r in _UML.items():
        low = low.replace(u, r)
    return fold(low)


def filter_text(*texts):
    """data-text value for filter bars: folded words of all texts, each once,
    plus joined forms of hyphenated names ("ho oh" + "hooh") and the ae/oe/ue
    spelling of umlaut words."""
    seen, out = set(), []

    def add(w):
        if w and w not in seen:
            seen.add(w)
            out.append(w)
    for t in texts:
        if t is None or t == "":
            continue
        for raw in str(t).split():
            for f in (fold(raw), alt_fold(raw)):
                if not f:
                    continue
                parts = f.split()
                for p in parts:
                    add(p)
                if len(parts) > 1:
                    add("".join(parts))
    return " ".join(out)


def index_js(lang, kinds, entries):
    """Text of assets/search-<lang>.js.

    entries: [(title, kind, url, keywords, icon, sub)] - url relative to the language
    folder, icon relative to assets/ or "", sub = short second line or "".
    Row: [title, kind index, url, keywords, icon, sub] with trailing empty values cut.
    One entry per line keeps diffs small."""
    kidx = {k: i for i, k in enumerate(kinds)}
    lines = []
    for title, kind, url, keywords, icon, sub in entries:
        row = [title, kidx[kind], url, keywords or "", icon or "", sub or ""]
        while len(row) > 3 and not row[-1]:
            row.pop()
        lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    return ("window.OJ_SEARCH={lang:%s,kinds:%s,e:[\n%s\n]};\n"
            % (json.dumps(lang), json.dumps(list(kinds)), ",\n".join(lines)))
