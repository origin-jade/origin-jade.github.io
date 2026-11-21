"""The two static files of the site, put together from tools/docs/static:

    assets/site.css = static/site.css + the type colours (sampled from the game's type labels)
    assets/site.js  = static/site.js with the UI strings of both languages injected

    bundle.build() -> {"site.css": text, "site.js": text}
    bundle.versions(files) -> {"css": "1a2b3c4d", "js": "..."}   (cache-busting ids)
"""
import functools
import hashlib
import json
import os

from . import i18n

STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
JS_MARK = "/*@STRINGS@*/{}"


def type_css():
    """.t-<slug>{--t:r g b} for every type; the colour is the main colour of the
    game's own type label."""
    from gamedata import graphics, typeinfo
    out = ["/* type colours */"]
    for ty in typeinfo.battle_types():
        out.append(".t-%s{--t:%d %d %d}" % ((ty.slug,) + tuple(graphics.type_color(ty))))
    return "\n".join(out) + "\n"


@functools.lru_cache(maxsize=None)
def build():
    with open(os.path.join(STATIC, "site.css"), encoding="utf-8") as f:
        css = f.read()
    with open(os.path.join(STATIC, "site.js"), encoding="utf-8") as f:
        js = f.read()
    if JS_MARK not in js:
        raise SystemExit("static/site.js: marker %s is missing" % JS_MARK)
    strings = json.dumps(i18n.js_strings(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    js = js.replace(JS_MARK, strings, 1)
    return {"site.css": css.rstrip("\n") + "\n" + type_css(), "site.js": js}


def versions(files=None):
    files = files or build()
    return {"css": hashlib.sha1(files["site.css"].encode("utf-8")).hexdigest()[:8],
            "js": hashlib.sha1(files["site.js"].encode("utf-8")).hexdigest()[:8]}
