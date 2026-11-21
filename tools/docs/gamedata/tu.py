"""Preprocessed translation units of the German or the English build.

The C tables are read from the translation unit that really includes them,
preprocessed with the Makefile's CPPFLAGS (Makefile, CPPFLAGS). Without a
language flag that is the German build (include/constants/global.h: GERMAN 1);
with -DLANG_ENGLISH (make GAME_LANG=ENGLISH) it is the English build. Every #if
of the configs and every `#if GERMAN` is then resolved exactly like in that ROM.

Language: every loader takes lang="de" | "en"; lang=None means the language of
the process (tu.LANG: "de", or $OJ_DOCS_LANG, or what tu.set_lang() chose).
Caches are keyed by the resolved language, so both can be used side by side.

    t = tu.load("src/pokemon.c")                 # process language (German by default)
    t = tu.load("src/move.c", lang="en")         # the English build
    tu.cstring("src/strings.c", "gText_Pokemon", "en")   -> raw text of a named string
    tu.nontext_diff("src/move.c")                -> [] when only string literals differ
    t.const("SPECIES_BULBASAUR")        -> 1
    t.table("gSpeciesInfo")             -> {id: Init}
    t.field(entry, "baseHP")            -> 45
    t.incbin["gMonFrontPic_Bulbasaur"]  -> "graphics/pokemon/bulbasaur/anim_front_gba.4bpp.smol"
    t.names("TYPE_")                    -> {value: "TYPE_NORMAL", ...}

Compiler: arm-none-eabi-gcc (as the build); $OJ_CPP_CC overrides it, and
cc/gcc are a fallback (same result for -E -P on these sources).
"""
import functools
import os
import re
import shutil
import subprocess

from . import REPO
from . import cparse as C

LANG_FLAGS = {"de": [], "en": ["-DLANG_ENGLISH"]}
CPPFLAGS = ["-iquote", "include", "-Wno-trigraphs", "-DMODERN=1", "-DTESTING=0",
            "-DPOKEMON_HNS", "-std=gnu17"]

LANGS = ("de", "en")
# Language of the process: what lang=None means in every loader.
LANG = os.environ.get("OJ_DOCS_LANG", "de")

_LITERALS = r'((?:"(?:[^"\\\n]|\\.)*"\s*)+)'
_ONE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')

_NUMERIC_BODY = re.compile(r"^[\w\s()+\-*/<>|&~^?:!=.%]+$")


class DataError(RuntimeError):
    """A source table changed shape; the docs must not guess."""


def compiler():
    for cc in (os.environ.get("OJ_CPP_CC"), "arm-none-eabi-gcc", "cc", "gcc"):
        if cc and shutil.which(cc):
            return cc
    raise DataError("no C compiler for the preprocessor found (arm-none-eabi-gcc)")


def lang(l=None):
    """Resolve a language argument: None -> the process language; checks the value."""
    l = LANG if l is None else l
    if l not in LANG_FLAGS:
        raise DataError("unknown language %r (use %s)" % (l, " or ".join(LANGS)))
    return l


def set_lang(l):
    """Set the process language (what lang=None means). Returns the previous one."""
    global LANG
    old, LANG = LANG, lang(l)
    return old


def cpp(path, extra=(), stdin=None, lang=None, repo=None):
    """Preprocessed text of a translation unit (path relative to the repo).

    repo: another source tree to read instead (the tree of the English version, see
    entext.py). Headers that only exist after a build (generated tables) are then
    taken from this repository when that tree has none, so the other tree does not
    have to be built; they contain no text that is read from there."""
    lang = globals()["lang"](lang)
    fallback = []
    foreign = repo is not None and os.path.abspath(repo) != os.path.abspath(REPO)
    if foreign:
        fallback = ["-iquote", os.path.join(REPO, "include"), "-iquote", os.path.join(REPO, "src")]
    for _ in range(40):
        args = [compiler(), "-E", "-P", *CPPFLAGS, *fallback, *LANG_FLAGS[lang], *extra, "-x", "c",
                path if stdin is None else "-"]
        out = subprocess.run(args, cwd=repo or REPO, capture_output=True, text=True, input=stdin)
        if not out.returncode or not foreign:
            break
        # a generated header that tree does not have, included from a file next to it
        # (include/constants/maps.h -> "map_groups.h"): the same place in this repository
        m = re.search(r"^(\S+?):\d+:\d+: fatal error: (\S+): No such file or directory", out.stderr, re.M)
        if not m:
            break
        here = os.path.join(REPO, os.path.dirname(m.group(1)))
        if not os.path.exists(os.path.join(here, m.group(2))) or here in fallback:
            break
        fallback += ["-iquote", here]
    if out.returncode:
        raise DataError("cpp %s failed:\n%s" % (path, out.stderr[:3000]))
    return out.stdout


class TU:
    """One preprocessed translation unit with its constants."""

    def __init__(self, path, extra=(), lang=None, repo=None):
        self.path = path
        self.repo = repo                # None: this repository; else the other source tree
        self.lang = lang = globals()["lang"](lang)
        self.text = cpp(path, extra, lang=lang, repo=repo)
        if lang == "en" and repo is None:
            # English texts of the English version's tree, where one is configured
            from . import entext
            self.text = entext.patch(path, self.text, tuple(extra))
        self.consts = C.Enums(self.text)          # enum constants (in enum order)
        self.ev = C.CEval(self.consts)
        self.macros = {}                           # object-like #defines: name -> body
        for line in cpp(path, ["-dM", *extra], lang=lang, repo=repo).splitlines():
            m = re.match(r"#define (\w+) (.*)$", line)
            if m:
                self.macros[m.group(1)] = m.group(2).strip()
        pending = {k: v for k, v in self.macros.items()
                   if k not in self.consts and v and _NUMERIC_BODY.match(v) and not k.startswith("__")}
        # Macros may use macros that -dM prints later (FRLG_TRAINER_OFFSET): several passes.
        for _ in range(6):
            done = []
            for k, body in pending.items():
                try:
                    v = self.ev.eval(body)
                except Exception:
                    continue
                if isinstance(v, (int, float)) and not isinstance(v, C.Sym):
                    self.consts[k] = v
                    done.append(k)
            for k in done:
                del pending[k]
            if not done:
                break
        self.incbin = dict(re.findall(r"\b(\w+)\s*\[\s*\]\s*=\s*INCBIN_\w+\(\s*\"([^\"]+)\"", self.text))
        self._names = {}
        self._inits = None
        self._strings = None
        self._literals = None

    def _init_pos(self, name):
        """Start of the initializer `name[...] = {` / `name = {` (one scan per TU)."""
        if self._inits is None:
            self._inits = {}
            for m in re.finditer(r"\b(\w+)\s*(?:\[[^\]\n]*\]\s*)*=\s*\{", self.text):
                self._inits.setdefault(m.group(1), m.end() - 1)
        return self._inits.get(name)

    # ------------------------------------------------------------ constants
    def const(self, name, default=None):
        """Value of an enum constant or numeric #define (None if unknown)."""
        return self.consts.get(name, default)

    def need(self, name):
        if name not in self.consts:
            raise DataError("%s: constant %s not found" % (self.path, name))
        return self.consts[name]

    def names(self, prefix):
        """{value: first constant name with that prefix} (enum order first)."""
        if prefix not in self._names:
            rev = {}
            for n, v in self.consts.items():
                if n.startswith(prefix) and isinstance(v, int):
                    rev.setdefault(v, n)
            self._names[prefix] = rev
        return self._names[prefix]

    def enum_names(self, tag):
        """{value: name} of one tagged enum (enum BattleMoveEffects {...})."""
        return {self.consts[n]: n for n in reversed(self.consts.by_enum.get(tag, []))}

    def canonical(self, prefix, enum=None):
        """{value: constant name} of one family of constants. Deterministic.

        enum="Move": only the enumerators of that tagged enum that start with the
        prefix, the first one of a value in enum order (MOVE_GUST, never an unrelated
        #define such as MOVE_NAME_LENGTH that happens to share prefix and number).
        Use this for every family that is an enum (Move, Ability, Item).

        Without enum (families made of #defines, SPECIES_*): the name whose #define
        is a plain number (SPECIES_CASTFORM_NORMAL over its alias SPECIES_CASTFORM),
        then enum order. Only safe when no unrelated macro shares the prefix."""
        key = "canon:%s:%s" % (prefix, enum)
        if key not in self._names:
            rev = {}
            if enum is not None:
                members = self.consts.by_enum.get(enum)
                if not members:
                    raise DataError("%s: enum %s not found" % (self.path, enum))
                for n in members:
                    v = self.consts[n]
                    if n.startswith(prefix) and isinstance(v, int):
                        rev.setdefault(v, n)
            else:
                for n, body in self.macros.items():
                    if n.startswith(prefix) and body.isdigit():
                        rev.setdefault(int(body), n)
                for v, n in self.names(prefix).items():
                    rev.setdefault(v, n)
            self._names[key] = rev
        return self._names[key]

    def has_symbol(self, name):
        """True if the TU defines an initialized array/object of that name."""
        return self._init_pos(name) is not None

    # ------------------------------------------------------------ tables
    def init(self, name):
        """Parsed initializer of `name[] = {...}` (Init) - DataError if missing."""
        pos = self._init_pos(name)
        src = C.find_init_at(self.text, pos) if pos is not None else None
        if src is None:
            raise DataError("%s: table %s not found" % (self.path, name))
        return C.parse_init(src)

    def table(self, name):
        """{index: entry} of an array initializer; designated keys evaluated."""
        out = {}
        for i, (k, v) in enumerate(self.init(name).items):
            if k is None:
                out[i] = v
            elif "][" in k:
                cut = k.index("][")
                out[(self.eval(k[:cut]), self.eval(k[cut + 1:]))] = v
            else:
                out[self.eval(k)] = v
        return out

    def array(self, name):
        """Values of a flat array initializer, evaluated."""
        return [self.value(v) for v in self.init(name).positional()]

    def eval(self, expr):
        return self.ev.eval(expr)

    def value(self, v):
        """Evaluate a parsed value: Init -> list (recursively), tokens -> value."""
        if v is None:
            return None
        if isinstance(v, C.Init):
            return [self.value(x) for x in v.positional()]
        if not v:
            return None
        return self.ev.eval(v)

    def field(self, entry, key, default=None):
        """Evaluated field of a designated-initializer entry (default if absent)."""
        if entry is None:
            return default
        v = entry.get(key)
        if v is None:
            return default
        return self.value(v)

    # ------------------------------------------------------------ texts
    def strings(self):
        """{symbol: text} of every named string `sym[] = _("...")` of the TU
        (adjacent literals joined, escapes resolved like parsed string values)."""
        if self._strings is None:
            self._strings = {}
            for m in re.finditer(r"\b(\w+)\s*\[[^\]\n]*\]\s*=\s*_\s*\(\s*%s\)\s*;" % _LITERALS, self.text):
                self._strings.setdefault(m.group(1), C._unescape("".join(_ONE.findall(m.group(2)))))
        return self._strings

    def literals(self):
        """Every string literal of the TU as a set (adjacent literals joined, escapes
        resolved like parsed string values)."""
        if self._literals is None:
            self._literals = {C._unescape("".join(_ONE.findall(m.group(0))))
                              for m in re.finditer(_LITERALS, self.text)}
        return self._literals

    def text_value(self, v):
        """A parsed value as text: a string literal as it is, a symbol that names a
        string of this TU (.description = sFullHealDesc) resolved to that string;
        None for anything else."""
        if v is None:
            return None
        if isinstance(v, C.Init) or isinstance(v, list):
            v = self.value(v)
        if isinstance(v, C.Sym):
            return self.strings().get(str(v))
        return v if isinstance(v, str) else None

    def text_field(self, entry, key, default=None):
        """Text of a field of a designated-initializer entry (see text_value)."""
        if entry is None:
            return default
        v = entry.get(key)
        if v is None:
            return default
        t = self.text_value(v)
        return default if t is None else t


@functools.lru_cache(maxsize=None)
def _load(path, extra, lang, repo=None):
    return TU(path, extra, lang, repo)


# Paths of every TU loaded in this process (selftest compares the two builds of each).
LOADED = set()


def load(path, extra=(), lang=None, repo=None):
    """Cached TU (path relative to the repo, extra = tuple of cpp flags, lang "de"/"en";
    None = the process language). repo: another source tree (see cpp()); such a TU is
    only a source of texts."""
    if repo is None:
        LOADED.add(path)
        return _load(path, tuple(extra), globals()["lang"](lang))
    return _load(path, tuple(extra), globals()["lang"](lang), repo)


def x_macro(header, macro):
    """Expand an X-macro list (FOREACH_TM) to its arguments, in order."""
    src = '#include "global.h"\n#include "%s"\n#define X_ITEM(m) @@X m\n%s(X_ITEM)\n' % (header, macro)
    text = cpp("-", stdin=src, lang="de")
    return re.findall(r"@@X\s+(\w+)", text)


# ------------------------------------------------------------------ strings


def cstring_of(t, symbol):
    """Text of the named string `symbol[] = _("...")` in the TU t (adjacent literals
    joined; \\n as a real newline, \\l and \\p kept as codes - text.clean reads
    both); None when the TU has no such string."""
    s = t.strings().get(symbol)
    if s is not None:
        return s
    m = re.search(r"\b%s\s*(?:\[[^\]\n]*\]\s*)?=\s*(?:\([^()\n]*\)\s*)?_?\(?\s*%s"
                  % (re.escape(symbol), _LITERALS), t.text)
    if not m:
        return None
    return C._unescape("".join(_ONE.findall(m.group(1))))


def cstring(path, symbol, lang=None):
    """Text of a named C string of a TU in one language (see cstring_of). English: the
    text of the English version's tree when one is configured (entext.py), else the
    English build of this tree."""
    l = globals()["lang"](lang)
    s = cstring_of(load(path, lang=l), symbol)
    if l == "en":
        from . import entext
        if entext.root():
            s = entext.pick("cstring", "%s:%s" % (path, symbol), s,
                            cstring_of(load(path, lang="de"), symbol), entext.cstring(path, symbol))
    return s


def written_in(path, s, lang=None):
    """Language a string taken from the TU `path` of build lang is written in: "de" for
    the German build and for a string of the English build that the German build's TU
    contains as well (not translated, or the same in both languages), else "en"."""
    l = globals()["lang"](lang)
    if l == "de" or s is None or s in load(path, lang="de").literals():
        return "de"
    return "en"


def clean(path, s, lang=None):
    """text.clean of a string from the TU `path` of build lang, with the rules of the
    language the string is written in (see written_in)."""
    from . import text
    return text.clean(s, written_in(path, s, lang))


# ------------------------------------------------------------------ build differences
# A string literal or a character literal (matched first, so that '"' does not open a string).
_LIT = re.compile(r"""'(?:[^'\\\n]|\\.)+'|"(?:[^"\\\n]|\\.)*\"""")
# GAME_LANGUAGE (include/constants/global.h) is the one constant that differs by design.
_GAME_LANGUAGE = re.compile(r"\(LANGUAGE_(?:GERMAN|ENGLISH)\)")


_PLURAL = re.compile(r"\. pluralName = \( const u8 \[ [^,]* \] \) _ \( \"\" \) , ")


def _nontext(text):
    """A preprocessed TU without its string literals, one statement per line."""
    text = _LIT.sub(lambda m: '""' if m.group(0)[0] == '"' else m.group(0), text)
    text = re.sub(r'""(\s*"")+', '""', text)
    text = _GAME_LANGUAGE.sub("(GAME_LANGUAGE)", text)
    text = " ".join(re.findall(r"""'(?:[^'\\\n]|\\.)+'|""|\w+|[^\s\w]""", text))
    # a plural name is text that only one language needs (German item names)
    text = _PLURAL.sub("", text)
    return re.sub(r"([;{}])", r"\1\n", text).split("\n")


@functools.lru_cache(maxsize=None)
def nontext_diff(path, extra=()):
    """Everything but string literals that differs between the German and the English
    preprocessing of a TU: [(german line, english line)] ("" = line missing on that
    side); [] when the two builds differ in text only. GAME_LANGUAGE itself
    (LANGUAGE_GERMAN / LANGUAGE_ENGLISH) is not counted."""
    import difflib
    a = _nontext(cpp(path, extra, lang="de"))
    b = _nontext(cpp(path, extra, lang="en"))
    if a == b:
        return []
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        da, db = a[i1:i2], b[j1:j2]
        for k in range(max(len(da), len(db))):
            out.append((da[k].strip() if k < len(da) else "", db[k].strip() if k < len(db) else ""))
    return out
