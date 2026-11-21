"""English texts from the source tree of the English version of the game.

This repository's English build (-DLANG_ENGLISH) still shows German names in
almost every table. The English version is kept on its own branch; its tree has
the same sources with every name and text in both languages (`#if GERMAN ... #else
... #endif`, DE_EN(de, en) in the .party files, "name_en" in the map section JSON).
That tree can be some commits apart from this one, so it is only ever a source of
TEXT. Values, tables and structure always come from this repository; a text of the
other tree is attached to an entry by its key (constant, symbol or script label).

Where the tree is:
    $OJ_DOCS_EN_SRC         a path; "", "0", "none" or "off" switch the source off
    build_site.py --en-src  sets that variable for the build
    site_config.EN_TEXT_SOURCE   default (relative to the repository), used when it exists
                                 and this repository has no English names of its own
                                 (own_english(): once the English version is merged in,
                                 the loaders need no second tree)
entext.root() is the tree in use or None. The tree does not have to be built: headers
that a build generates are taken from this repository (tu.cpp), they hold no text
that is read from there.

Rule for one string (pick): WT = this repository, SRC = the English tree.
    1. SRC has an English text for the key (its English and German branch differ):
       it is used - unless the German text of the entry is no longer the same in the
       two trees AND this repository has an English text of its own for it; then
       the text that belongs to this repository's wording wins.
    2. SRC has one text for both languages: it is used only when it is in the English
       game's capitals and this repository's is not (a name that tree no longer
       translates, "BROCK" where this repository says "Rocko").
    3. otherwise the English build of this repository (which may be German).
Every loader does this for lang="en"; text_lang of the objects stays truthful
("de" when the result is the German string).

    entext.root()                        -> path or None
    entext.texts("species")              -> {const: {"name": [en, de], ...}} of the English tree
    entext.resolve("species", const, raw_en, raw_de) -> the dict of texts to show
    entext.pick(kind, key, wt_en, wt_de, src)        -> one string (src = [en, de] or None)
    entext.cstring(path, symbol)         -> [en, de] of a named C string, or None
    entext.script_text(label)            -> [en, de] of a script text, or None
    entext.trainer_names()               -> {TRAINER_* / PARTNER_*: [en, de]}
    entext.mapsec_names()                -> {MAPSEC_*: [en, de]}
    entext.patch(path, text)             -> a preprocessed English TU with the English tree's literals
                                            (used by tu.TU for every English TU, see "whole translation units")
    entext.report()                      -> what was taken from where (counts, keys that fell back)

Results are cached on disk (tools/docs/.cache/entext/<fingerprint of that tree and of
this code>/), because reading two builds of a dozen translation units takes a while.
"""
import functools
import hashlib
import importlib.util
import json
import os
import re
import tempfile

from . import REPO
from . import tu as TU

ENV = "OJ_DOCS_EN_SRC"
OFF = ("", "0", "none", "off", "no", "false")
# Files a usable tree must have (sources only, nothing a build creates).
MARKERS = ("include/constants/global.h", "src/data/items.h", "src/data/moves_info.h",
           "src/data/region_map/region_map_sections.json", "data/event_scripts.s")

# kind -> (TU, table, constant prefix, enum tag or None, {text field: where})
#   where: "name" = designated member; 0 = positional member; None = the element itself.
TABLES = {
    "species": ("src/pokemon.c", "gSpeciesInfo", "SPECIES_", None,
                {"name": "speciesName", "category": "categoryName", "description": "description"}),
    "move": ("src/move.c", "gMovesInfo", "MOVE_", "Move", {"name": "name", "description": "description"}),
    "ability": ("src/pokemon.c", "gAbilitiesInfo", "ABILITY_", "Ability",
                {"name": "name", "description": "description"}),
    "item": ("src/item.c", "gItemsInfo", "ITEM_", "Item", {"name": "name", "description": "description"}),
    "type": ("src/battle_main.c", "gTypesInfo", "TYPE_", None, {"name": "name", "generic": "generic"}),
    "nature": ("src/pokemon.c", "gNaturesInfo", "NATURE_", None, {"name": "name"}),
    "trainer_class": ("src/battle_main.c", "gTrainerClasses", "TRAINER_CLASS_", None, {"name": 0}),
    "pocket": ("src/strings.c", "gPocketNamesStringsTable", "POCKET_", None, {"name": None}),
}
PARTY_FILES = ("src/data/trainers_hns.party", "src/data/trainers_frlg.party", "src/data/trainers.party",
               "src/data/battle_partners.party")

# What happened to each string that was asked for: kind -> origin -> count, and the keys.
#   src            text of the English tree
#   src_both       the English tree's single text for both languages, written in capitals
#   src_diverged   text of the English tree although the German text differs between the trees
#   wt             this repository's English build (the English tree has the same German/neutral text)
#   wt_diverged    this repository's own English text (German differs between the trees)
#   wt_only        the key does not exist in the English tree
STATS = {}
KEYS = {}


def _site_config():
    try:
        import site_config
        return site_config
    except ImportError:
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site_config.py")
        spec = importlib.util.spec_from_file_location("site_config", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


def usable(path):
    """True when path looks like a source tree of the game with a language switch."""
    if not path or not all(os.path.exists(os.path.join(path, m)) for m in MARKERS):
        return False
    with open(os.path.join(path, MARKERS[0]), encoding="utf-8", errors="replace") as f:
        return "LANG_ENGLISH" in f.read()


@functools.lru_cache(maxsize=None)
def own_english():
    """True when this repository's own English build already has the English names
    (the English version merged in): species names behind `#if GERMAN ... #else`."""
    p = os.path.join(REPO, "src", "data", "pokemon", "species_info", "gen_1_families.h")
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            src = f.read(20000)
    except OSError:
        return False
    return bool(re.search(r"#if GERMAN\s+\.speciesName\s*=.*\n#else\s+\.speciesName\s*=", src))


@functools.lru_cache(maxsize=None)
def english_font():
    """True when English text is drawn with the English version's font graphics
    (graphics_en/fonts: the {POKEBLOCK} ligature reads "POKéBLOCK")."""
    return bool(root()) or os.path.isdir(os.path.join(REPO, "graphics_en", "fonts"))


@functools.lru_cache(maxsize=None)
def root():
    """The tree English texts are read from, or None (see module doc)."""
    v = os.environ.get(ENV)
    if v is not None:
        if v.strip().lower() in OFF:
            return None
        p = os.path.abspath(v)
        if not usable(p):
            raise TU.DataError("%s=%s: not a source tree of the game (%s missing)"
                               % (ENV, v, ", ".join(m for m in MARKERS if not os.path.exists(os.path.join(p, m)))
                                  or "language switch"))
        return None if os.path.samefile(p, REPO) else p
    if own_english():
        return None                  # this repository is the English version: nothing else is needed
    cand = getattr(_site_config(), "EN_TEXT_SOURCE", None) or ()
    for d in ((cand,) if isinstance(cand, str) else cand):
        p = os.path.normpath(d if os.path.isabs(d) else os.path.join(REPO, d))
        if usable(p) and not os.path.samefile(p, REPO):
            return p
    return None


# ------------------------------------------------------------------ disk cache
@functools.lru_cache(maxsize=None)
def _fingerprint():
    h = hashlib.sha1()
    r = root()
    h.update(r.encode("utf-8"))
    n = size = newest = 0
    for top in ("include", "src", "data"):
        for d, dirs, files in os.walk(os.path.join(r, top)):
            dirs.sort()
            for f in files:
                if f.endswith((".o", ".d", ".png", ".bin", ".pal", ".4bpp", ".gbapal", ".lz", ".smol")):
                    continue
                try:
                    st = os.stat(os.path.join(d, f))
                except OSError:
                    continue
                n += 1
                size += st.st_size
                newest = max(newest, st.st_mtime_ns)
    h.update(("%d %d %d" % (n, size, newest)).encode())
    here = os.path.dirname(os.path.abspath(__file__))
    for f in ("entext.py", "tu.py", "cparse.py"):
        with open(os.path.join(here, f), "rb") as fh:
            h.update(fh.read())
    with open(os.path.join(REPO, "tools", "oj_world.py"), "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()[:16]


def _cache_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "entext",
                        _fingerprint())


_MEM = {}


def _cached(name, compute):
    """compute() once per English tree: memory, then disk (JSON), then the real work."""
    if name in _MEM:
        return _MEM[name]
    use_disk = os.environ.get("OJ_DOCS_NO_CACHE") is None
    p = os.path.join(_cache_dir(), re.sub(r"[^\w.-]", "_", name) + ".json")
    if use_disk and os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                _MEM[name] = json.load(f)
            return _MEM[name]
        except (OSError, ValueError):
            pass
    data = compute()
    if use_disk:
        try:
            if not os.path.isdir(os.path.dirname(p)):
                # a new state of that tree (or of this code): drop the older caches
                import shutil
                top = os.path.dirname(os.path.dirname(p))
                for old in (os.listdir(top) if os.path.isdir(top) else ()):
                    shutil.rmtree(os.path.join(top, old), ignore_errors=True)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, p)
        except OSError:
            pass
    _MEM[name] = data
    return data


# ------------------------------------------------------------------ the rule
_NOTED = set()


def _note(kind, origin, key):
    """Count one decision; a string that is asked again is counted once."""
    if (kind, key) in _NOTED:
        return
    _NOTED.add((kind, key))
    STATS.setdefault(kind, {}).setdefault(origin, 0)
    STATS[kind][origin] += 1
    if origin != "src":
        KEYS.setdefault(kind, {}).setdefault(origin, []).append(key)


def pick(kind, key, wt_en, wt_de, src):
    """The English text for one string (module doc, "Rule"). wt_en / wt_de: the string
    in this repository's English and German build; src: [english, german] of the same
    key in the English tree, or None when the key does not exist there."""
    if src is None or src[0] is None:
        _note(kind, "wt_only", key)
        return wt_en
    s_en, s_de = src
    if s_en == s_de:                       # not translated there either, or the same in both languages
        if wt_en == wt_de and s_en != wt_en and _capitals(s_en) and not _capitals(wt_en) and "{" not in (wt_en or ""):
            # one text for both languages there, in the English game's capitals, where
            # this repository has a German name (trainer "BROCK" / "Rocko"): English
            _note(kind, "src_both", key)
            return s_en
        _note(kind, "wt", key)
        return wt_en
    if s_de != wt_de:                      # the German wording differs between the trees
        if wt_en is not None and wt_en != wt_de:
            _note(kind, "wt_diverged", key)
            return wt_en
        _note(kind, "src_diverged", key)
        return s_en
    _note(kind, "src", key)
    return s_en


def _capitals(s):
    from . import namestyle
    return bool(s) and "{" not in s and namestyle.is_capitals(s)


def resolve(kind, const, raw_en, raw_de):
    """raw_en with every text replaced by the English tree's (pick per field).
    raw_en / raw_de: {field: text} of the entry in this repository's two builds."""
    if not root():
        return raw_en
    src = texts(kind).get(const)
    out = dict(raw_en)
    for f in raw_en:
        out[f] = pick(kind + "." + f, const, raw_en[f], raw_de.get(f), src.get(f) if src else None)
    return out


def report():
    """{"root": ..., "stats": {kind: {origin: n}}, "keys": {kind: {origin: [keys]}}} of
    everything asked so far in this process."""
    return {"root": root(), "stats": {k: dict(v) for k, v in sorted(STATS.items())},
            "keys": {k: {o: sorted(set(x)) for o, x in v.items()} for k, v in sorted(KEYS.items())},
            "tus": {k: dict(v) for k, v in sorted(PATCHED.items())}}


# ------------------------------------------------------------------ C tables
def _tu(path, lang):
    return TU.load(path, lang=lang, repo=root())


def _table(kind):
    path, table, prefix, enum, fields = TABLES[kind]
    out = {}
    for li, lang in enumerate(("en", "de")):
        t = _tu(path, lang)
        names = {}
        for n, v in t.consts.items():
            if n.startswith(prefix) and isinstance(v, int) and not isinstance(v, bool):
                names.setdefault(v, []).append(n)
        if enum:
            members = set(t.consts.by_enum.get(enum, ()))
            names = {v: [n for n in ns if n in members] for v, ns in names.items()}
        for idx, e in t.table(table).items():
            for f, where in fields.items():
                if where is None:
                    s = t.text_value(e)
                elif isinstance(where, int):
                    pos = e.positional() if hasattr(e, "positional") else []
                    s = t.text_value(pos[where]) if len(pos) > where else None
                else:
                    s = t.text_field(e, where) if hasattr(e, "get") else None
                if s is None:
                    continue
                for n in names.get(idx, ()):
                    out.setdefault(n, {}).setdefault(f, [None, None])[li] = s
    return out


def texts(kind):
    """{constant: {field: [english, german]}} of one table of the English tree
    (every constant name of an entry's number, so aliases resolve); {} without a tree."""
    if not root():
        return {}
    return _cached("table-" + kind, lambda: _table(kind))


# ------------------------------------------------------------------ named C strings
def _cstrings(path):
    out = {}
    for li, lang in enumerate(("en", "de")):
        try:
            t = _tu(path, lang)
        except TU.DataError:
            return None              # the file does not exist (or does not preprocess) in that tree
        for sym, s in t.strings().items():
            out.setdefault(sym, [None, None])[li] = s
    return out


def cstring(path, symbol):
    """[english, german] of the named string in the English tree; None when that tree
    has no such string."""
    if not root():
        return None
    d = _cached("cstrings-" + path, lambda: _cstrings(path))
    if d is None:
        return None
    if symbol in d:
        return d[symbol]
    # declarations the quick index does not cover (tu.cstring_of's second pattern)
    key = "cstring-%s-%s" % (path, symbol)
    if key not in _MEM:
        pair = [TU.cstring_of(_tu(path, "en"), symbol), TU.cstring_of(_tu(path, "de"), symbol)]
        _MEM[key] = None if pair[0] is None else pair
    return _MEM[key]


def tu_pair(path):
    """(English, German) TU of a file of the English tree, or None when the tree has
    no such file. For loaders that walk a table themselves (menus)."""
    if not root() or not os.path.exists(os.path.join(root(), path)):
        return None
    try:
        return _tu(path, "en"), _tu(path, "de")
    except TU.DataError:
        return None


# ------------------------------------------------------------------ whole translation units
# Besides the big tables (matched by constant, see texts()) the loaders read many small
# things straight from a preprocessed TU: named strings, option menus, trade tables,
# word lists. For those the English build's text of this repository is patched before
# it is parsed: the TU is cut into its top-level definitions; a definition that has
# exactly the same code in both trees (every token outside string literals equal) gets
# the English tree's string literals, one by one - and only where the German literal
# at that place is the same in both trees. Anything else stays as this repository
# has it. Definitions whose shape differs (an entry was added on one side) are left
# alone as a whole; the big tables are covered by constant instead.
_SCAN = re.compile(r'''"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)+'|[{};]''')
_RUN = re.compile(r'''(?:"(?:[^"\\\n]|\\.)*"\s*)+''')
_ONE = re.compile(r'''"((?:[^"\\\n]|\\.)*)"''')
PATCHED = {}          # path -> {"literals": n replaced, "same": n definitions used, "differ": [headers left alone]}


def _chunks(text):
    """{header: (shape, [(start, end, joined literal content)], start, end)} of every top-level
    definition of a preprocessed TU that contains a string literal. header = the text
    before the first `=` or `{` (one line); shape = the definition with every literal
    run replaced by "". A header that occurs twice with literals is dropped."""
    out, dropped = {}, set()
    depth, start, has_lit = 0, 0, False
    first_brace = None

    def close(end):
        nonlocal start, has_lit, first_brace
        if has_lit:
            body = text[start:end]
            cut = len(body)
            for ch in "={":
                i = body.find(ch)
                if i != -1:
                    cut = min(cut, i)
            header = " ".join(body[:cut].split())
            runs = [(start + m.start(), start + m.end(), "".join(_ONE.findall(m.group(0))))
                    for m in _RUN.finditer(body)]
            shape = " ".join(_RUN.sub('"" ', body).split())
            if header in out or header in dropped:
                out.pop(header, None)
                dropped.add(header)
            else:
                out[header] = (shape, runs, start, end)
        start, has_lit, first_brace = end, False, None

    for m in _SCAN.finditer(text):
        c = m.group(0)
        if c[0] == '"':
            has_lit = True
        elif c == "{":
            if depth == 0 and first_brace is None:
                first_brace = m.start()
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and first_brace is not None:
                # a function body ends here; an initializer goes on to its semicolon
                if text[start:first_brace].rstrip().endswith(")") and "=" not in text[start:first_brace]:
                    close(m.end())
        elif c == ";" and depth == 0:
            close(m.end())
    return out


_KEYSCAN = re.compile(r'''((?:"(?:[^"\\\n]|\\.)*"\s*)+)|'(?:[^'\\\n]|\\.)+'|\[\s*([^\[\]]+?)\s*\]\s*=|\.(\w+)\s*=|([{}])''')


def _keyed(text, start, end):
    """String literals of one table definition by where they stand:
    {(element designator, member path, n-th literal there): (start, end, content)}.
    Only literals inside an element with a designator ([ITEM_POTION] = {...}) are
    listed; a key that occurs twice is dropped."""
    out, dropped = {}, set()
    depth, elem, fields, counts = 0, None, {}, {}
    for m in _KEYSCAN.finditer(text, start, end):
        lit, des, field, brace = m.group(1), m.group(2), m.group(3), m.group(4)
        if brace == "{":
            depth += 1
        elif brace == "}":
            depth -= 1
            fields = {d: f for d, f in fields.items() if d <= depth}
            if depth <= 0:
                elem = None
        elif des is not None:
            if depth == 1:
                elem, fields = "".join(des.split()), {}
        elif field is not None:
            if depth >= 1:
                fields = {d: f for d, f in fields.items() if d < depth}
                fields[depth] = field
        elif lit is not None and elem is not None:
            where = (elem, tuple(f for _, f in sorted(fields.items())))
            n = counts[where] = counts.get(where, 0) + 1
            key = where + (n,)
            if key in out or key in dropped:
                out.pop(key, None)
                dropped.add(key)
            else:
                out[key] = (m.start(1), m.end(1), "".join(_ONE.findall(lit)))
    return out


def patch(path, text_en, extra=()):
    """The preprocessed English build of `path` with the English tree's string literals
    where the code is the same (see above). Without a tree, or when the tree has no
    such file: text_en unchanged."""
    r = root()
    if not r or not os.path.exists(os.path.join(r, path)):
        return text_en
    text_de = TU.load(path, extra, lang="de").text
    key = hashlib.sha1(("%s\0%s\0%s\0%s" % (path, " ".join(extra), text_en, text_de)).encode("utf-8")).hexdigest()[:16]
    name = "tu-%s-%s" % (path, key)

    def compute():
        try:
            src_en = TU.cpp(path, extra, lang="en", repo=r)
            src_de = TU.cpp(path, extra, lang="de", repo=r)
        except TU.DataError:
            return {"text": None, "literals": 0, "same": 0, "differ": []}
        a, b, c, d = _chunks(text_en), _chunks(text_de), _chunks(src_en), _chunks(src_de)
        edits, same, differ = [], 0, []
        for header, (shape, runs, _s, _e) in a.items():
            if header not in c:
                continue
            if not (header in b and header in d and b[header][0] == shape and c[header][0] == shape
                    and d[header][0] == shape):
                # not the same code: a table can still be matched entry by entry, by its
                # designators ([ITEM_POTION] = { .name = ... }), again only where the
                # German literal agrees
                n = 0
                if header in b and header in d and runs:
                    ka = _keyed(text_en, a[header][2], a[header][3])
                    kb = _keyed(text_de, b[header][2], b[header][3])
                    kc = _keyed(src_en, c[header][2], c[header][3])
                    kd = _keyed(src_de, d[header][2], d[header][3])
                    for key, (s0, s1, wt_en) in ka.items():
                        if key in kb and key in kc and key in kd:
                            wt_de, s_en, s_de = kb[key][2], kc[key][2], kd[key][2]
                            if s_en != s_de and s_de == wt_de and s_en != wt_en:
                                edits.append((s0, s1, s_en))
                                n += 1
                if not n:
                    differ.append(header)
                continue
            same += 1
            for (s0, s1, wt_en), (_, _, wt_de), (_, _, s_en), (_, _, s_de) in zip(
                    runs, b[header][1], c[header][1], d[header][1]):
                if s_en != s_de and s_de == wt_de and s_en != wt_en:
                    edits.append((s0, s1, s_en))
        if not edits:
            return {"text": None, "literals": 0, "same": same, "differ": sorted(differ)}
        parts, pos = [], 0
        for s0, s1, lit in sorted(edits):
            tail = text_en[s0:s1]
            ws = tail[len(tail.rstrip()):]
            parts += [text_en[pos:s0], '"', lit, '"', ws]
            pos = s1
        parts.append(text_en[pos:])
        return {"text": "".join(parts), "literals": len(edits), "same": same, "differ": sorted(differ)}

    res = _cached(name, compute)
    PATCHED[path] = {k: res[k] for k in ("literals", "same", "differ")}
    return text_en if res["text"] is None else res["text"]


# ------------------------------------------------------------------ .party files, map sections
_DE_EN = re.compile(r"DE_EN\(\s*(.*?)\s*,\s*([^,()]*?)\s*\)\s*$")


def _party_names():
    out = {}
    for rel in PARTY_FILES:
        p = os.path.join(root(), rel)
        if not os.path.exists(p):
            continue
        cur = None
        with open(p, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"=== (\w+) ===\s*$", line)
                if m:
                    cur = m.group(1)
                    continue
                if cur and line.startswith("Name:"):
                    v = line[len("Name:"):].strip()
                    m = _DE_EN.match(v)
                    out[cur] = [m.group(2), m.group(1)] if m else [v, v]
                    cur = None
    return out


def trainer_names():
    """{TRAINER_* / PARTNER_* constant: [english, german]} from the .party files of the
    English tree ("Name: DE_EN(Falk, FALKNER)")."""
    if not root():
        return {}
    return _cached("party-names", _party_names)


def _mapsecs():
    with open(os.path.join(root(), "src", "data", "region_map", "region_map_sections.json"), encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for group in ("map_sections", "hns_map_sections"):      # the jade build uses the second list
        for s in data.get(group, ()):
            if "name" in s:
                out[s["id"]] = [s.get("name_en", s["name"]), s["name"]]
    return out


def mapsec_names():
    """{MAPSEC_*: [english, german]} ("name_en" / "name" of region_map_sections.json)."""
    if not root():
        return {}
    return _cached("mapsecs", _mapsecs)


# ------------------------------------------------------------------ script texts
_STRING_LINE = re.compile(r'^\s*(?:\w+::?\s*)?\.string\s+"((?:[^"\\]|\\.)*)"')


def _script_texts():
    """{label: [english, german]} of every text label of the English tree's event
    scripts, read with this repository's script reader (tools/oj_world.py) pointed at
    that tree."""
    import copy
    spec = importlib.util.spec_from_file_location("oj_world_entext", os.path.join(REPO, "tools", "oj_world.py"))
    ow = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ow)
    ow.REPO = root()
    macros_de = ow.Macros(ow.event_script_headers())
    if macros_de.defs.get("GERMAN") != "1" or macros_de.defs.get("ENGLISH") != "0":
        raise TU.DataError("%s: include/constants/global.h: language macros changed shape" % root())
    macros_en = copy.copy(macros_de)
    macros_en.defs = dict(macros_de.defs)
    macros_en._cache = {}
    macros_en.defs.update({"GERMAN": "0", "ENGLISH": "1", "GAME_LANGUAGE": "(LANGUAGE_ENGLISH)",
                           "LANG_ENGLISH": "1"})
    out, files = {}, {}
    for li, macros in enumerate((macros_en, macros_de)):
        d = ow.ScriptDB(macros)
        starts = {}
        for name, idx in d.labels.items():
            starts.setdefault(idx, []).append(name)
        cur, pieces = (), {}
        for i, ins in enumerate(d.instrs):
            if i in starts:
                cur = starts[i]
            if ins.cmd != ".string":
                continue
            lines = files.get(ins.file)
            if lines is None:
                with open(os.path.join(root(), ins.file), encoding="utf-8") as f:
                    lines = files[ins.file] = f.read().split("\n")
            m = _STRING_LINE.match(lines[ins.line - 1])
            if not m:
                continue
            for name in cur:
                pieces.setdefault(name, []).append(m.group(1))
        for name, ps in pieces.items():
            out.setdefault(name, [None, None])[li] = "".join(ps).split("$", 1)[0]
    return out


def script_text(label):
    """[english, german] raw text of a script text label in the English tree, or None."""
    if not root():
        return None
    return _cached("script-texts", _script_texts).get(label)
