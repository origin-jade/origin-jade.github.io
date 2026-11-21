#!/usr/bin/env python3
"""Where every English text of the docs data layer comes from.

    python3 -I -B tools/docs/verify/en_source_report.py [--max N]

Asks the loaders for everything they hand out in English - all tables, the menus, every
script text label - and prints what gamedata/entext.py decided per string: the English
version's tree ("src"), or this repository's own English build ("wt"), and why. Lists
the keys that exist only in this repository (added after the English branch was last
updated) and the texts whose German wording differs between the two trees.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXPLAIN = (
    ("src", "text of the English version's tree"),
    ("src_both", "the English tree has one text for both languages, in capitals (this repository: a German name)"),
    ("src_diverged", "English tree's text, although the German text differs between the trees (no English here)"),
    ("wt", "this repository's text: the English tree has the same text in both languages (TM01, names not translated)"),
    ("wt_diverged", "this repository's own English text: its German text differs from the English tree's"),
    ("wt_only", "only in this repository: no such key in the English tree"),
)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--max", type=int, default=30, help="keys printed per group")
    a = ap.parse_args()
    os.environ["OJ_DOCS_LANG"] = "en"
    import gamedata
    from gamedata import (abilities, dex_texts, entext, hand_breeding, hand_menus, hand_pokeblocks, items, maps,
                          moves, natures, species, trainers, trainers_scriptdb as SDB, typeinfo, wild_statics)
    gamedata.set_lang("en")
    root = entext.root()
    if not root:
        raise SystemExit("no English text source configured (OJ_DOCS_EN_SRC / site_config.EN_TEXT_SOURCE)")
    species.all_species("en"); moves.all_moves("en"); abilities.all_abilities("en"); items.all_items("en")
    typeinfo.all_types("en"); natures.all_natures("en"); trainers.all_trainers("en"); trainers.partners("en")
    maps.all_maps(lang="en"); hand_menus.challenge_tabs("en"); hand_menus.option_tabs("en")
    hand_pokeblocks.colors("en"); hand_pokeblocks.flavors("en"); hand_breeding.odd_egg("en")
    wild_statics.entries("en")
    for c in ("EGG_GROUP_MONSTER", "EGG_GROUP_WATER_1"):
        dex_texts.egg_group(c, "en")
    labels = sorted(SDB._texts("en"))
    for label in labels:
        SDB.script_text(label, "en")
    rep = entext.report()
    print("English text source: %s" % root)
    print("script text labels of this repository: %d" % len(labels))
    print()
    print("%-24s %s" % ("kind", "  ".join("%12s" % o for o, _ in EXPLAIN)))
    for kind, st in rep["stats"].items():
        print("%-24s %s" % (kind, "  ".join("%12d" % st.get(o, 0) for o, _ in EXPLAIN)))
    print()
    for o, text in EXPLAIN:
        print("%-13s %s" % (o, text))
    print("\ntranslation units read in English (string literals taken from the English tree where the code is the same):")
    for path, v in rep["tus"].items():
        print("  %-40s %5d literals replaced, %4d definitions identical, %d left as they are%s"
              % (path, v["literals"], v["same"], len(v["differ"]),
                 (": " + "; ".join(h[:50] for h in v["differ"][:4])) if v["differ"] else ""))
    for kind, groups in rep["keys"].items():
        for o in ("wt_only", "wt_diverged", "src_diverged", "src_both"):
            keys = groups.get(o)
            if keys:
                print("\n== %s: %d x %s ==" % (kind, len(keys), o))
                for k in keys[:a.max]:
                    print("  " + k)
                if len(keys) > a.max:
                    print("  ... %d more (use --max)" % (len(keys) - a.max))


if __name__ == "__main__":
    main()
