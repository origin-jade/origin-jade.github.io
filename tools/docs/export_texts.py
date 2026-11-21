#!/usr/bin/env python3
"""Write every hand-written text of the site (German and English side by side) to one
text file for proofreading.

    python3 -I -B tools/docs/export_texts.py OUT.txt

Covered: the STRINGS tables of all page modules, the shared interface strings and the
page titles of common/i18n.py. Names and descriptions that come from the game are not
hand-written and are not listed. `{name}` marks a value the build fills in.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from common import i18n  # noqa: E402

PAGES_DIR = os.path.join(HERE, "pages")


def _flat(v):
    if isinstance(v, (tuple, list)):
        return " | ".join(_flat(x) for x in v)
    if isinstance(v, dict):
        return " | ".join("%s: %s" % (k, _flat(x)) for k, x in v.items())
    return str(v)


def main(out):
    lines = []

    def block(title, rows):
        lines.append("=" * 78)
        lines.append(title)
        lines.append("=" * 78)
        for key, de, en in rows:
            lines.append("[%s]" % key)
            lines.append("DE: " + _flat(de))
            lines.append("EN: " + _flat(en))
            lines.append("")

    block("Seitentitel / page titles", [(p, e[2], e[3]) for p, e in i18n.SITEMAP.items()])
    block("Oberfläche / interface", [(k, v[0], v[1]) for k, v in i18n.UI.items()])
    for f in sorted(os.listdir(PAGES_DIR)):
        if not f.endswith(".py") or f.startswith("_"):
            continue
        mod = importlib.import_module("pages." + f[:-3])
        if getattr(mod, "DEV", False):
            continue
        s = getattr(mod, "STRINGS", None)
        if not s:
            continue
        block("Bereich / module: %s" % f[:-3], [(k, s["de"][k], s["en"][k]) for k in s["de"]])
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("%d Zeilen -> %s" % (len(lines), out))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
