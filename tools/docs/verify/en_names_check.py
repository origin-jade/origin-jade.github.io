#!/usr/bin/env python3
"""Compare the English names and texts of the docs data layer with the ROM of the
English version of the game.

    python3 -I -B tools/docs/verify/rom_dump.py --lang en --names-only --repo EN_TREE \\
        --elf EN_TREE/Pokemon_Origin_Jade_EN.elf --gba EN_TREE/Pokemon_Origin_Jade_EN.gba --out dump_en_branch.json
    python3 -I -B tools/docs/verify/en_names_check.py --dump dump_en_branch.json [--max N]

The data layer takes its English texts from the source tree of the English version
(gamedata/entext.py, OJ_DOCS_EN_SRC); this tool checks them against that version's
compiled ROM. The English version can be some commits apart from this repository, so
only names and texts are compared, entry by entry by the constant name (the numbers
of the constants are the ROM's own). Entries the ROM does not have (added to this
repository later) are counted as "not in the ROM"; entries where the data layer
deliberately keeps this repository's wording are listed with the reason
(entext.report()).

Output: one line per table (entries compared, equal, different, not in the ROM), then
every difference. Exit status 1 if a text differs without a reason.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, DOCS)
from romlib import Charmap  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dump", required=True, help="JSON of rom_dump.py --names-only for the English version's ROM")
    ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args()
    os.environ["OJ_DOCS_LANG"] = "en"
    os.environ["OJ_DOCS_EN_NAME_STYLE"] = "game"      # names as the game writes them
    import gamedata
    from gamedata import (abilities, entext, items, maps, moves, natures, species, text, trainers, typeinfo,
                          wild_statics)
    gamedata.set_lang("en")
    root = entext.root()
    if not root:
        raise SystemExit("no English text source configured (OJ_DOCS_EN_SRC / site_config.EN_TEXT_SOURCE)")
    d = json.load(open(a.dump, encoding="utf-8"))
    K = d["constants"]
    cmap = os.path.join(root, "charmap.txt")       # a sparse checkout of that tree may not have it
    cm = Charmap(cmap if os.path.exists(cmap) else os.path.join(gamedata.REPO, "charmap.txt"))
    rows = []       # [table, compared, equal, [differences], [not in the ROM], [kept on purpose]]

    def canon(s):
        return None if s is None else cm.canon(s)

    def table(name):
        rows.append([name, 0, 0, [], [], []])
        return rows[-1]

    def cmp(row, key, field, rom, dl, kept=None):
        row[1] += 1
        if canon(rom) == canon(dl):
            row[2] += 1
        elif kept:
            row[5].append("%s %s: ROM %r, data layer %r (%s)" % (key, field, rom, dl, kept))
        else:
            row[3].append("%s %s: ROM %r, data layer %r" % (key, field, rom, dl))

    def name(s):
        return text.name(s, "en")

    def desc(s):
        return text.clean(s, "en")

    # why the data layer may differ from the English ROM on purpose: this repository's
    # wording moved on (entext.pick: wt_diverged) - filled after the loaders ran
    def reason(kind, key):
        for origin, keys in entext.KEYS.get(kind, {}).items():
            if origin == "wt_diverged" and key in keys:
                return "this repository has its own, newer text"
        return None

    for label, kind, allx, dump_key, fields in (
            ("species", "species", species.all_species("en"), "species",
             (("name", "name_game", name), ("category", "category", name), ("description", "description", desc))),
            ("moves", "move", moves.all_moves("en"), "moves",
             (("name", "name_game", name), ("description", "description", desc))),
            ("abilities", "ability", abilities.all_abilities("en"), "abilities",
             (("name", "name_game", name), ("description", "description", desc))),
            ("items", "item", items.all_items("en"), "items",
             (("name", "name_game", name), ("description", "description", desc)))):
        row = table(label)
        for x in allx.values():
            num = K.get(x.const)
            e = d[dump_key].get(str(num)) if num is not None else None
            if e is None or not (e.get("name") or "").strip():
                row[4].append(x.const)
                continue
            for field, attr, fn in fields:
                cmp(row, x.const, field, fn(e[field]), getattr(x, attr), reason("%s.%s" % (kind, field), x.const))
    row = table("types")
    for t in typeinfo.all_types("en"):
        e = d["types"].get(str(K.get(t.const)))
        if e is None:
            row[4].append(t.const)
            continue
        cmp(row, t.const, "name", name(e["name"]), t.name_game)
        cmp(row, t.const, "generic move name", name(e["generic"]), t.generic)
    row = table("natures")
    for n in natures.all_natures("en"):
        e = d["natures"].get(str(K.get(n.const)))
        if e is None:
            row[4].append(n.const)
            continue
        cmp(row, n.const, "name", name(e["name"]), n.name_game)
    row = table("trainer classes")
    for c in trainers.classes("en"):
        e = d["trainer_classes"].get(str(K.get(c)))
        if e is None:
            row[4].append(c)
            continue
        cmp(row, c, "name", name(e["name"]), trainers.class_name_game(c, "en"))
    for label, allx, dump_key in (("trainers", trainers.all_trainers("en"), "trainers"),
                                  ("battle partners", trainers.partners("en"), "partners")):
        row = table(label)
        for c, tr in allx.items():
            num = K.get(c)
            e = d[dump_key].get(str(num)) if num is not None else None
            if e is None:
                row[4].append(c)
                continue
            cmp(row, c, "name", e["name"], tr.name_game, reason("trainer.name", c) or (
                "a placeholder in this repository: the name the player chose" if "{" in tr.name_game else None))
    row = table("map sections")
    for sec in sorted(maps._sections()):
        num = K.get(sec)
        e = d["mapsecs"].get(str(num)) if num is not None else None
        if e is None:
            row[4].append(sec)
            continue
        got = maps.mapsec_name_game(sec, "en")
        cmp(row, sec, "name", e["name"], "" if got == sec else got)
    row = table("in-game trades")
    rom_trades = d.get("trades") or []
    seen = set()
    for en in wild_statics.entries("en"):
        tr = en.trade
        if not tr or tr["const"] in seen:
            continue
        seen.add(tr["const"])
        num = K.get(tr["const"])
        if num is None:
            # the constant is not among the ROM's evaluated constants: same row number,
            # accepted only when that row trades the same species there
            from gamedata import tu
            num = tu.load("src/trade.c", lang="de").const(tr["const"])
            sp = species.by_id(en.species, "en")
            if num is None or num >= len(rom_trades) or sp is None or \
                    d["names"]["SPECIES_"].get(str(rom_trades[num]["species"])) != sp.const:
                num = None
        if num is None or num >= len(rom_trades):
            row[4].append(tr["const"])
            continue
        cmp(row, tr["const"], "nickname", rom_trades[num]["nickname"], tr["nickname_game"])
        cmp(row, tr["const"], "ot name", rom_trades[num]["ot_name"], tr["ot_name_game"])

    print("English text source: %s; ROM dump: %s (%s)" % (root, a.dump, d["meta"]["elf"]))
    bad = 0
    for name_, n, eq, diffs, missing, kept in rows:
        print("%-16s %5d texts compared, %5d equal, %3d different, %3d kept on purpose, %3d entries not in that ROM"
              % (name_ + ":", n, eq, len(diffs), len(kept), len(missing)))
        bad += len(diffs)
    print("total: %d texts compared, %d different" % (sum(r[1] for r in rows), bad))
    for name_, n, eq, diffs, missing, kept in rows:
        for title, lst in (("different", diffs), ("kept on purpose", kept), ("not in that ROM", missing)):
            if lst:
                print("\n== %s: %d %s ==" % (name_, len(lst), title))
                for x in lst[:a.max]:
                    print("  " + x)
                if len(lst) > a.max:
                    print("  ... %d more (use --max)" % (len(lst) - a.max))
    rep = entext.report()
    print("\nwhere the English texts of the data layer came from (entext.report):")
    for kind, st in rep["stats"].items():
        print("  %-22s %s" % (kind, ", ".join("%s %d" % kv for kv in sorted(st.items()))))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
