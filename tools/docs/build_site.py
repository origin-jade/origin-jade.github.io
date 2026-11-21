#!/usr/bin/env python3
"""Build the player documentation site of Pokémon Origin Jade (German and English).

    python3 -I -B tools/docs/build_site.py --out DIR [--lang de|en] [--only MODULE[,MODULE]]
                                           [--fast] [--skip-assets] [--dev] [--strict] [--report FILE]
                                           [--en-src DIR|none] [--en-name-style title|game]

Output:  DIR/index.html (forwards to the remembered or browser language),
         DIR/de/..., DIR/en/... (same pages in both), DIR/assets/... (shared).
Each language is built in its own process (in parallel). A page module in
tools/docs/pages/ is run twice per language: register(ctx), then render(ctx);
see FRAMEWORK2.md. The same sources give byte-identical output.

  --only     render only these modules (all modules still register, so links resolve)
  --fast     with --only: skip the register pass of the other modules and take their
             pages from the last full build into the same --out (quick iteration)
  --skip-assets  do not re-export images that already exist
  --dev      also build development pages (component gallery, stubs for missing pages)
  --strict   warnings fail the build
  --report   write notes (ctx.todo), warnings, timings and sizes to this file
  --en-src   source tree of the English version of the game: English names and texts are
             taken from it (default: site_config.EN_TEXT_SOURCE if it exists; "none" = the
             English build of this repository as it is). Same as $OJ_DOCS_EN_SRC.
  --en-name-style  "title" (Bulbasaur) or "game" (BULBASAUR); default site_config.EN_NAME_STYLE
"""
import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import site_config  # noqa: E402
from common import bundle, i18n, slugs  # noqa: E402

PAGES_DIR = os.path.join(HERE, "pages")
PAGE_BUDGET = 150 * 1024          # a typical page stays below this
SITE_BUDGET = 250 * 1024 * 1024


# ---------------------------------------------------------------------- modules
def discover(dev):
    """[(name, module)] of tools/docs/pages/*.py in name order (files starting with _ are helpers)."""
    mods, problems = [], []
    for f in sorted(os.listdir(PAGES_DIR)):
        if not f.endswith(".py") or f.startswith("_"):
            continue
        name = f[:-3]
        mod = importlib.import_module("pages." + name)
        if not callable(getattr(mod, "register", None)) or not callable(getattr(mod, "render", None)):
            problems.append("pages/%s: needs register(ctx) and render(ctx)" % f)
            continue
        problems += i18n.check_strings("pages/" + f, getattr(mod, "STRINGS", None))
        if getattr(mod, "DEV", False) and not dev:
            continue
        mods.append((name, mod))
    if problems:
        raise SystemExit("\n".join("ERROR: " + p for p in problems))
    return mods


class _Stubs:
    """Development only: a plain page for every fixed page no module has claimed yet."""
    STRINGS = None

    def __init__(self):
        self.paths = []

    def register(self, ctx):
        for path in i18n.SITEMAP:
            if path not in ctx.pages:
                ctx.add_page(path, search=False)
                self.paths.append(path)

    def render(self, ctx):
        from common import html as H
        for path in self.paths:
            ctx.begin(path)
            ctx.end(H.callout(ctx, "note", H.esc(ctx.ui("dev_stub"))))


def cache_file(out, lang):
    d = os.path.join(HERE, ".cache", hashlib.sha1(out.encode("utf-8")).hexdigest()[:12])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "registry-%s.json" % lang)


# ---------------------------------------------------------------------- one language (child process)
def build_language(a):
    import gamedata
    from gamedata import REPO
    from common import checks, search
    from common.context import BuildError, Context, Entry, Page

    lang = a.lang
    gamedata.set_lang(lang)              # what lang=None means in every loader of this process
    out = os.path.abspath(a.out)
    only = [s for s in a.only.split(",") if s]
    ctx = Context(REPO, out, lang, bundle.versions(), dev=a.dev, strict=a.strict)
    external = [url for _k, _l, url in site_config.COMMUNITY_LINKS if url]
    checker = checks.Checker(lang, external)
    ctx._checks = checker
    modules = discover(a.dev)
    names = [n for n, _ in modules]
    for s in only:
        if s not in names:
            raise SystemExit("--only %s: no such page module (have: %s)" % (s, ", ".join(names)))
    if a.dev:
        modules.append(("_stubs", _Stubs()))
    selected = [(n, m) for n, m in modules if not only or n in only or (n == "_stubs" and not a.fast)]
    fast = bool(a.fast and only)
    try:
        if fast:
            cf = cache_file(out, lang)
            if os.path.exists(cf):
                with open(cf, encoding="utf-8") as f:
                    data = json.load(f)
                for p in data["pages"]:
                    if p["module"] not in only:
                        ctx.pages[p["path"]] = Page(**p)
                for e in data["entries"]:
                    if e["module"] not in only:
                        ctx.entries[(e["kind"], e["key"])] = Entry(**e)
            else:
                ctx.warnings.append("--fast: no registry of a full build for this --out yet; "
                                    "links to other modules are plain text")
            for n, m in selected:
                ctx.run("register", n, m)
        else:
            for n, m in modules:
                ctx.run("register", n, m)
            with open(cache_file(out, lang), "w", encoding="utf-8") as f:
                json.dump({"pages": [{k: getattr(p, k) for k in Page.__slots__ if k != "rendered"}
                                     for p in ctx.pages.values()],
                           "entries": [{k: getattr(e, k) for k in Entry.__slots__} for e in ctx.entries.values()]},
                          f, ensure_ascii=False)
        for n, m in selected:
            ctx.run("render", n, m)
    except BuildError as e:
        raise SystemExit("ERROR (%s): %s" % (lang, e))

    sel_names = {n for n, _ in selected}
    for p in ctx.pages.values():
        if p.module in sel_names and not p.rendered:
            ctx.problem("%s: page %r was registered but not rendered" % (p.module, p.path))
    outside = checker.verify(ctx, rendered_only=not only)

    n_search = 0
    if not fast:
        entries = []
        korder = {k: i for i, k in enumerate(slugs.KINDS)}
        # the game's own spelling of a name is always findable (English names are shown
        # in natural capitalisation; a few differ from the game by more than case)
        from gamedata import namestyle
        spellings = namestyle.game_spellings(lang)
        for e in sorted(ctx.entries.values(), key=lambda e: korder[e.kind]):   # stable: registration order
            if e.search:
                kw = e.keywords
                game = spellings.get((e.kind, e.key))
                if game and search.fold(game) not in search.fold("%s %s %s" % (e.title, kw or "", e.sub or "")):
                    kw = ("%s %s" % (kw, game)).strip() if kw else game
                entries.append((e.title, e.kind, e.url, kw, e.icon, e.sub))
                if e.icon:
                    ctx.used_assets.setdefault("assets/" + e.icon, "search")
        ctx.write_asset("search-%s.js" % lang, search.index_js(lang, slugs.KINDS, entries))
        n_search = len(entries)

    result = {
        "lang": lang,
        "pages": sorted(ctx.written),
        "registered": sorted(ctx.pages),
        "sizes": ctx.written,
        "used_assets": ctx.used_assets,
        "written_assets": sorted(ctx.written_assets),
        "outside": outside,
        "problems": ctx.problems,
        "warnings": ctx.warnings,
        "todos": ctx.todos,
        "reviews": ctx.reviews,
        "timings": ctx.timings,
        "search_entries": n_search,
        "modules": [n for n, _ in selected],
    }
    with open(a.child, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)


# ---------------------------------------------------------------------- parent
ROOT_HTML = """<!doctype html>
<html lang="%(lang)s" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>%(title)s</title>
<meta name="color-scheme" content="light dark">
<script>(function(){var l=null,d=document.documentElement;try{l=localStorage.getItem("oj-lang");var t=localStorage.getItem("oj-theme");if(t==="light"||t==="dark")d.setAttribute("data-theme",t)}catch(e){}if(%(test)s){var n=navigator.languages||[navigator.language||""];l=null;for(var i=0;i<n.length&&!l;i++){var c=String(n[i]).slice(0,2).toLowerCase();if(%(test_c)s)l=c}l=l||"%(lang)s"}location.replace(l+"/index.html"+location.search+location.hash)})()</script>
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png">
<link rel="stylesheet" href="assets/site.css?v=%(css)s">
</head>
<body class="root">
<main class="root-pick">
<img class="px" src="assets/img/mark.png" alt="" width="64" height="64">
<h1>%(title)s</h1>
<p class="root-links">%(links)s</p>
</main>
</body>
</html>
"""


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def write_root(out, versions):
    links = " ".join('<a href="%s/index.html" lang="%s" hreflang="%s">%s</a>' % (l, l, l, i18n.LANG_NAMES[l])
                     for l in site_config.LANGS)
    test = " && ".join('l!=="%s"' % l for l in site_config.LANGS)
    test_c = " || ".join('c==="%s"' % l for l in site_config.LANGS)
    write_text(os.path.join(out, "index.html"), ROOT_HTML % {
        "lang": site_config.DEFAULT_LANG, "title": i18n.ui(site_config.DEFAULT_LANG, "root_title"),
        "css": versions["css"], "links": links, "test": test, "test_c": test_c})
    open(os.path.join(out, ".nojekyll"), "w").close()


def prune(out, langs, results, keep_assets):
    """Remove files of earlier builds that this (full) build did not produce. -> count"""
    n = 0
    for lang in langs:
        want = {os.path.normpath(os.path.join(out, lang, *(p + ".html").split("/"))) for p in results[lang]["pages"]}
        base = os.path.join(out, lang)
        for root, _dirs, files in os.walk(base, topdown=False):
            for f in files:
                p = os.path.join(root, f)
                if os.path.normpath(p) not in want:
                    os.remove(p)
                    n += 1
            if root != base and not os.listdir(root):
                os.rmdir(root)
    base = os.path.join(out, "assets")
    keep = {os.path.normpath(os.path.join(out, *r.split("/"))) for r in keep_assets}
    for root, _dirs, files in os.walk(base, topdown=False):
        for f in files:
            p = os.path.join(root, f)
            if os.path.normpath(p) not in keep:
                os.remove(p)
                n += 1
        if root != base and not os.listdir(root):
            os.rmdir(root)
    return n


def dir_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def write_report(path, a, langs, results, problems, warnings, stats):
    o = ["Origin Jade documentation - build report", ""]
    o.append("Options: lang=%s only=%s dev=%s fast=%s" % (",".join(langs), a.only or "-", a.dev, a.fast))
    o.append("Time: %.1f s   Site size: %.1f MB   Images exported: %d" % (
        stats["seconds"], stats["bytes"] / 1048576.0, stats["exported"]))
    o.append("")
    for lang in langs:
        r = results[lang]
        sizes = r["sizes"]
        o.append("== %s: %d pages rendered, %d registered, %d search entries" % (
            lang, len(r["pages"]), len(r["registered"]), r["search_entries"]))
        if sizes:
            big = sorted(sizes.items(), key=lambda kv: (-kv[1], kv[0]))
            over = [p for p, s in big if s > PAGE_BUDGET]
            o.append("   HTML total %.1f MB, largest: %s" % (
                sum(sizes.values()) / 1048576.0, ", ".join("%s %d KB" % (p, s // 1024) for p, s in big[:5])))
            o.append("   pages over %d KB: %d%s" % (PAGE_BUDGET // 1024, len(over),
                                                    (" (" + ", ".join(over[:20]) + ")") if over else ""))
        for name in sorted(r["timings"]):
            t = r["timings"][name]
            o.append("   %-16s register %5.2f s   render %5.2f s" % (name, t.get("register", 0), t.get("render", 0)))
        o.append("")
    o.append("== Problems (%d)" % len(problems))
    o += ["   " + p for p in problems] or ["   none"]
    o.append("")
    o.append("== Warnings (%d)" % len(warnings))
    o += ["   " + w for w in warnings] or ["   none"]
    o.append("")
    for lang in langs:
        todos = results[lang]["todos"]
        o.append("== Open points reported by the modules, %s (%d)" % (lang, len(todos)))
        o += ["   " + t for t in todos] or ["   none"]
        o.append("")
        reviews = results[lang]["reviews"]
        o.append("== Phrases to check by hand, %s (%d): fine in game text, not as a remark about the site"
                 % (lang, len(reviews)))
        o += ["   " + t for t in reviews] or ["   none"]
        o.append("")
    write_text(path, "\n".join(o))


def main():
    ap = argparse.ArgumentParser(description="Build the Origin Jade player documentation (de + en).")
    ap.add_argument("--out", default=None, help="output directory (default: <repo>/build/docs_site)")
    ap.add_argument("--only", default="", help="render only these page modules (comma list of file names)")
    ap.add_argument("--lang", default="", choices=("",) + tuple(site_config.LANGS), help="build one language only")
    ap.add_argument("--fast", action="store_true", help="with --only: reuse the registry of the last full build")
    ap.add_argument("--skip-assets", action="store_true", help="do not re-export images that already exist")
    ap.add_argument("--dev", action="store_true", help="also build development pages")
    ap.add_argument("--strict", action="store_true", help="warnings fail the build")
    ap.add_argument("--report", default="", help="write notes, warnings, timings and sizes to this file")
    ap.add_argument("--en-src", default=None, help="source tree of the English version (English names and texts); "
                    "'none' = this repository's English build only")
    ap.add_argument("--en-name-style", default=None, choices=("title", "game"),
                    help="how English names are written (default: site_config.EN_NAME_STYLE)")
    ap.add_argument("--child", default="", help=argparse.SUPPRESS)
    a = ap.parse_args()
    a.only = ",".join(s.strip() for s in a.only.split(",") if s.strip())
    # the data layer reads both settings from the environment (child processes inherit it)
    if a.en_src is not None:
        os.environ["OJ_DOCS_EN_SRC"] = a.en_src if a.en_src.lower() in ("none", "off", "") else os.path.abspath(a.en_src)
    if a.en_name_style is not None:
        os.environ["OJ_DOCS_EN_NAME_STYLE"] = a.en_name_style
    if a.out is None:
        from gamedata import REPO
        a.out = os.path.join(REPO, "build", "docs_site")
    if a.child:
        build_language(a)
        return

    t0 = time.time()
    out = os.path.abspath(a.out)
    langs = [a.lang] if a.lang else list(site_config.LANGS)
    problems = list(i18n.check())
    if problems:
        raise SystemExit("\n".join("ERROR: " + p for p in problems))
    discover(a.dev)                          # contract and STRINGS check before any work
    from gamedata import levels
    levels.check_mirror()                    # the level rules of the docs must match the game's code
    if "en" in langs:
        from gamedata import entext, namestyle
        print("English texts: %s; names: %s" % (entext.root() or "this repository's English build", namestyle.style()))

    files = bundle.build()
    versions = bundle.versions(files)
    for name, text in files.items():
        write_text(os.path.join(out, "assets", name), text)

    procs = []
    tmp = tempfile.mkdtemp(prefix="oj_docs_")
    for lang in langs:
        res = os.path.join(tmp, "result-%s.json" % lang)
        cmd = [sys.executable, "-I", "-B", os.path.abspath(__file__), "--child", res, "--lang", lang, "--out", out]
        if a.only:
            cmd += ["--only", a.only]
        for flag in ("fast", "dev", "strict"):
            if getattr(a, flag):
                cmd.append("--" + flag)
        env = dict(os.environ, OJ_DOCS_LANG=lang)
        procs.append((lang, res, subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                   text=True)))
    results, failed = {}, False
    for lang, res, proc in procs:
        text, _ = proc.communicate()
        if text.strip():
            print(text.rstrip())
        if proc.returncode or not os.path.exists(res):
            print("ERROR: building %s failed" % lang)
            failed = True
            continue
        with open(res, encoding="utf-8") as f:
            results[lang] = json.load(f)
        os.remove(res)
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    if failed:
        sys.exit(1)

    warnings = []
    for lang in langs:
        problems += results[lang]["problems"]
        warnings += results[lang]["warnings"]

    # ---- images: the fixed ones and everything a page referred to
    import export_assets
    export_assets.export_fixed(out, force=not a.skip_assets)
    used = {}
    for lang in langs:
        for rel, where in results[lang]["used_assets"].items():
            used.setdefault(rel, "%s/%s" % (lang, where))
    written, missing = export_assets.export_used(out, used, force=not a.skip_assets)
    for rel in missing:
        warnings.append("image %s: the game has no such graphic (used on %s)" % (rel, used[rel]))
    write_root(out, versions)

    # ---- the two trees must hold the same pages
    full = not a.only
    if len(langs) > 1:
        sets = {l: set(results[l]["registered"]) for l in langs}
        for i, l1 in enumerate(langs):
            for l2 in langs[i + 1:]:
                for p in sorted(sets[l1] ^ sets[l2]):
                    problems.append("page %s exists in %s but not in %s"
                                    % (p, l1 if p in sets[l1] else l2, l2 if p in sets[l1] else l1))
    # ---- links that leave a language tree: assets on disk, pages of the other language
    for lang in langs:
        for target, where in sorted(results[lang]["outside"].items()):
            first = target.split("/", 1)[0]
            if first in site_config.LANGS and first != lang:
                if first in results:
                    p = target[len(first) + 1:]
                    if not p.endswith(".html") or p[:-5] not in results[first]["registered"]:
                        problems.append("%s: link to %s, which does not exist" % (where, target))
                continue
            if target == "index.html":
                continue
            if not os.path.exists(os.path.join(out, *target.split("/"))):
                problems.append("%s: %s does not exist" % (where, target))

    pruned = 0
    if full and not a.lang:
        keep = set(used) | set(export_assets.FIXED) | {"assets/site.css", "assets/site.js"}
        for lang in langs:
            keep |= set(results[lang]["written_assets"])
        pruned = prune(out, langs, results, keep)

    total = dir_size(out)
    if total > SITE_BUDGET:
        warnings.append("site is %.0f MB (budget %d MB)" % (total / 1048576.0, SITE_BUDGET // 1048576))
    seconds = time.time() - t0
    for lang in langs:
        r = results[lang]
        slow = ", ".join("%s %.1fs" % (n, sum(t.values())) for n, t in sorted(
            r["timings"].items(), key=lambda kv: -sum(kv[1].values()))[:4])
        print("%s: %d pages, %d search entries, %d notes (%s)" % (
            lang, len(r["pages"]), r["search_entries"], len(r["todos"]), slow))
    print("images exported: %d, old files removed: %d, site size: %.1f MB" % (written, pruned, total / 1048576.0))
    for w in warnings:
        print("WARNING: %s" % w)
    for p in problems:
        print("ERROR: %s" % p)
    if a.report:
        write_report(os.path.abspath(a.report), a, langs, results, problems, warnings,
                     {"seconds": seconds, "bytes": total, "exported": written})
    if problems or (a.strict and warnings):
        print("FAILED after %.1f s: %d problems, %d warnings" % (seconds, len(problems), len(warnings)))
        sys.exit(1)
    print("Done in %.1f s: %s" % (seconds, out))


if __name__ == "__main__":
    main()
