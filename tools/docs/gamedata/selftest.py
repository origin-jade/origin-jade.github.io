#!/usr/bin/env python3
"""Self-test of the data layer: prints sample values of every loader and checks a
few values against the source (DATA_MAP examples). Exit code 1 on a mismatch.

    python3 -I tools/docs/gamedata/selftest.py            everything
    python3 -I tools/docs/gamedata/selftest.py --quick    without the build comparison of every TU

The English checks read their expected values from the source files in the test
itself (raw_* helpers below: the file as written, with the `#if GERMAN` branch
of the language picked by hand), not through the loaders they check.

English has two states, and both are tested:
  * the English build of this repository on its own (names mostly German): a child
    process with OJ_DOCS_EN_SRC=none and OJ_DOCS_EN_NAME_STYLE=game (--english-build);
  * English texts from the tree of the English version (entext.py), when one is
    configured (OJ_DOCS_EN_SRC / site_config.EN_TEXT_SOURCE): expected values are read
    from that tree's files as written.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gamedata import (abilities, encounters, graphics, items, levels, maps, moves,  # noqa: E402
                      species, trainers, typeinfo)
from gamedata import repo_path  # noqa: E402

failures = []
RAW_ROOT = None      # another source tree for the raw_* helpers (the English version's)


def _raw_path(rel):
    return os.path.join(RAW_ROOT, rel) if RAW_ROOT else repo_path(rel)


# ---------------------------------------------------------------- expected values from the raw source
def raw_lines(rel, lang):
    """Lines of a source file as written, with `#if GERMAN` / `#if ENGLISH` blocks reduced
    to the branch of one language. Other conditionals are left alone (both branches kept)."""
    import re
    out, stack = [], []      # stack entries: None (not a language block) or True/False (branch active)
    for line in open(_raw_path(rel), encoding="utf-8"):
        s = line.strip()
        m = re.match(r"#\s*(if|ifdef|ifndef|elif|else|endif)\b\s*(.*)", s)
        if m:
            kind, cond = m.group(1), re.sub(r"\s*(//.*|/\*.*)$", "", m.group(2)).strip()
            if kind in ("if", "ifdef", "ifndef"):
                if kind == "if" and cond in ("GERMAN", "ENGLISH", "!GERMAN", "!ENGLISH"):
                    german = cond in ("GERMAN", "!ENGLISH")
                    stack.append(german == (lang == "de"))
                else:
                    stack.append(None)
                    out.append(line)
            elif kind in ("elif", "else"):
                if stack and stack[-1] is not None:
                    stack[-1] = not stack[-1]
                else:
                    out.append(line)
            else:
                if stack and stack.pop() is None:
                    out.append(line)
            continue
        if all(x is not False for x in stack):
            out.append(line)
    return out


def _join(pieces):
    """Adjacent C string pieces as one display line: \\n, \\l, \\p become spaces."""
    import re
    s = "".join(pieces)
    return re.sub(r"\s+", " ", re.sub(r"\\[nlp]", " ", s)).strip()


def raw_block(rel, lang, start, end=r"^\s*\},?\s*$"):
    """Source lines from the first line matching `start` to the next line matching `end`."""
    import re
    lines = raw_lines(rel, lang)
    for i, line in enumerate(lines):
        if re.search(start, line):
            for j in range(i + 1, len(lines)):
                if re.search(end, lines[j]):
                    return "".join(lines[i:j + 1])
            return "".join(lines[i:])
    raise AssertionError("%s: %s not found" % (rel, start))


def raw_field(rel, lang, entry, field):
    """Text of `.field = ...("...")` inside the table entry `[ENTRY] =` (pieces joined)."""
    import re
    blk = raw_block(rel, lang, r"^\s*\[%s\]\s*=\s*$" % re.escape(entry), r"^\s{0,4}\},?\s*$")
    m = re.search(r"\.%s\s*=\s*\w*\(?\s*((?:\"(?:[^\"\\]|\\.)*\"\s*)+)" % re.escape(field), blk)
    if m:
        return _join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))
    m = re.search(r"\.%s\s*=\s*(\w+)\s*," % re.escape(field), blk)
    if not m:
        raise AssertionError("%s: [%s] has no .%s" % (rel, entry, field))
    return raw_string(rel, lang, m.group(1))


def raw_string(rel, lang, symbol):
    """Text of `symbol[] = _("...")` as written in the branch of one language."""
    import re
    src = "".join(raw_lines(rel, lang))
    m = re.search(r"\b%s\s*\[\s*\]\s*=\s*_\(\s*((?:\"(?:[^\"\\]|\\.)*\"\s*)+)\)" % re.escape(symbol), src)
    if not m:
        raise AssertionError("%s: string %s not found" % (rel, symbol))
    return _join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))


def raw_script_text(rel, lang, label):
    """Text of a script label (.string lines up to the first $) in the branch of one language."""
    import re
    lines = raw_lines(rel, lang)
    for i, line in enumerate(lines):
        if re.match(r"%s::?\s*$" % re.escape(label), line):
            pieces = []
            for nxt in lines[i + 1:]:
                m = re.match(r'\s*\.string\s+"((?:[^"\\]|\\.)*)"', nxt)
                if m:
                    pieces.append(m.group(1))
                    if "$" in m.group(1):
                        break
                elif re.match(r"\w+::?\s*$", nxt):
                    break
            return "".join(pieces).split("$", 1)[0]
    raise AssertionError("%s: label %s not found" % (rel, label))


def check(label, got, want):
    ok = got == want
    print("  [%s] %s: %r" % ("ok" if ok else "FEHLER", label, got) + ("" if ok else " (erwartet %r)" % (want,)))
    if not ok:
        failures.append(label)


def english(quick):
    """Checks of the English build (lang="en") and of the language handling."""
    import json
    import re
    from gamedata import (dex_texts, entext, hand_facts, hand_pokeblocks, natures, text, trainers_scriptdb as SDB,
                          tu, wild_maps)
    own = entext.own_english()      # this repository has the English names itself (English version merged in)

    print("Sprachen: Schalter und Sprachparameter")
    g = "".join(open(repo_path("include", "constants", "global.h"), encoding="utf-8"))
    m = re.search(r"#ifdef LANG_ENGLISH\s+#define GERMAN\s+(\d)\s+#define ENGLISH\s+(\d)\s+#define GAME_LANGUAGE \((\w+)\)"
                  r"\s+#else\s+#define GERMAN\s+(\d)\s+#define ENGLISH\s+(\d)\s+#define GAME_LANGUAGE \((\w+)\)", g)
    want = {"en": (m.group(1), m.group(2), "(%s)" % m.group(3)), "de": (m.group(4), m.group(5), "(%s)" % m.group(6))}
    for lang in ("de", "en"):
        t = tu.load("src/strings.c", lang=lang)
        check("Makros %s" % lang, (t.macros["GERMAN"], t.macros["ENGLISH"], t.macros["GAME_LANGUAGE"]), want[lang])
    mk = open(repo_path("Makefile"), encoding="utf-8").read()
    check("Makefile: GAME_LANG=ENGLISH setzt -DLANG_ENGLISH",
          bool(re.search(r"ifeq \(\$\(GAME_LANG\),ENGLISH\)\s+LANGFLAG := -DLANG_ENGLISH", mk)), True)
    check("tu.LANG_FLAGS", tu.LANG_FLAGS, {"de": [], "en": ["-DLANG_ENGLISH"]})
    check("Standardsprache", (tu.lang(), tu.lang("en")), (os.environ.get("OJ_DOCS_LANG", "de"), "en"))
    old = tu.set_lang("en")
    check("set_lang(en): Standard folgt", moves.by_const("MOVE_MEGA_DRAIN").description,
          moves.by_const("MOVE_MEGA_DRAIN", "en").description)
    tu.set_lang(old)
    check("set_lang zurück", moves.by_const("MOVE_MEGA_DRAIN").lang, old)

    print("EN: Namen und Texte, erwartete Werte aus dem Quelltext gelesen")
    SP_H = "src/data/pokemon/species_info/gen_1_families.h"
    for lang in ("de", "en"):
        b = species.by_const("SPECIES_BULBASAUR", lang)
        check("%s Bisasam Name" % lang, b.name, raw_field(SP_H, lang, "SPECIES_BULBASAUR", "speciesName"))
        check("%s Bisasam Kategorie" % lang, b.category, raw_field(SP_H, lang, "SPECIES_BULBASAUR", "categoryName"))
        check("%s Bisasam Dex-Text" % lang, b.description, raw_field(SP_H, lang, "SPECIES_BULBASAUR", "description"))
        mv = moves.by_const("MOVE_TACKLE", lang)
        check("%s Tackle" % lang, (mv.name, mv.description),
              (raw_field("src/data/moves_info.h", lang, "MOVE_TACKLE", "name"),
               raw_field("src/data/moves_info.h", lang, "MOVE_TACKLE", "description").replace(
                   "- ", "-" if lang == "en" else "- ")))
        check("%s Megasauger (Text über Symbol)" % lang, moves.by_const("MOVE_MEGA_DRAIN", lang).description,
              raw_string("src/data/moves_info.h", lang, "sMegaDrainDescription"))
        ab = abilities.by_const("ABILITY_OVERGROW", lang)
        check("%s Notdünger" % lang, (ab.name, ab.description),
              (raw_field("src/data/abilities.h", lang, "ABILITY_OVERGROW", "name"),
               raw_field("src/data/abilities.h", lang, "ABILITY_OVERGROW", "description")))
        it = items.by_const("ITEM_POTION", lang)
        check("%s Trank" % lang, (it.name, it.description),
              (raw_field("src/data/items.h", lang, "ITEM_POTION", "name"),
               raw_field("src/data/items.h", lang, "ITEM_POTION", "description")))
        check("%s Hyperheiler (Text über Symbol)" % lang, items.by_const("ITEM_FULL_HEAL", lang).description,
              raw_string("src/data/items.h", lang, "sFullHealDesc"))
        check("%s Typ Pflanze" % lang, typeinfo.by_const("TYPE_GRASS", lang).name,
              raw_field("src/data/types_info.h", lang, "TYPE_GRASS", "name"))
        check("%s Wesen Hart" % lang, natures.by_const("NATURE_ADAMANT", lang).name,
              raw_field("src/pokemon.c", lang, "NATURE_ADAMANT", "name"))
        cls = re.search(r'\[TRAINER_CLASS_LEADER_FRLG\]\s*=\s*\{\s*_\("([^"]*)"',
                        "".join(raw_lines("src/battle_main.c", lang))).group(1)
        party = open(repo_path("src", "data", "trainers_frlg.party"), encoding="utf-8").read()
        pm = re.search(r"^=== TRAINER_LEADER_BROCK ===\nName: (.*)\nClass: (.*)$", party, re.M)
        de_en = re.match(r"DE_EN\((.*), (.*)\)$", pm.group(1))     # "Name: DE_EN(Rocko, BROCK)" as cpp resolves it
        want_name = pm.group(1) if not de_en else de_en.group(1 if lang == "de" else 2)
        tr = trainers.by_const("TRAINER_LEADER_BROCK", lang)
        check("%s Arenaleiter Rocko" % lang, (tr.name, tr.class_const, tr.class_name),
              (want_name, trainers.constant("TRAINER_CLASS", pm.group(2)), cls))
        check("%s Trainerklasse" % lang, trainers.class_name("TRAINER_CLASS_LEADER_FRLG", lang), cls)
        secs = json.load(open(repo_path("src", "data", "region_map", "region_map_sections.json"), encoding="utf-8"))
        r1 = [x.get("name_en", x["name"]) if lang == "en" else x["name"]
              for x in secs["hns_map_sections"] if x["id"] == "MAPSEC_ROUTE_1"][0]
        check("%s Route 1" % lang, (maps.by_id("MAP_ROUTE1", lang).display, maps.mapsec_name("MAPSEC_ROUTE_1", lang)), (r1, r1))
        check("%s Eigruppe/Wachstum" % lang, (dex_texts.egg_group("EGG_GROUP_MONSTER", lang),
                                              dex_texts.growth("GROWTH_MEDIUM_SLOW", lang)),
              (raw_string("src/pokedex_plus_hgss.c", lang, "sText_Stats_eggGroup_MONSTER"),
               raw_string("src/pokedex_plus_hgss.c", lang, "sText_Stats_MEDIUM_SLOW")))
        check("%s Geschmack scharf" % lang, (hand_pokeblocks.flavors(lang)[0][1],
                                              hand_facts.c_string("src/strings.c", "gText_Spicy2", lang)),
              (raw_string("src/strings.c", lang, "gText_Spicy2"),) * 2)
        check("%s Stockwerk 1F" % lang, wild_maps.floor_name("1F", lang), raw_string("src/strings.c", lang, "gText_1F"))
        want_txt = raw_script_text("data/event_scripts.s", lang, "Common_Text_ObedienceLevel40")
        check("%s Skripttext" % lang, SDB.script_text("Common_Text_ObedienceLevel40", lang), want_txt)
        check("%s Skripttext (hand_facts)" % lang,
              hand_facts.inc_string("data/event_scripts.s", "Common_Text_ObedienceLevel40", lang), _join([want_txt]))
        for prefix, label, names in maps.DYNAMIC_PLACES:
            check("%s Ortsname %r im Spieltext %s" % (lang, names[lang], label),
                  names[lang] in (SDB.script_text(label, lang) or ""), True)
    check("en MS Tide / Wettbewerbshalle", (maps.by_id("MAP_SS_TIDAL_CORRIDOR", "en").display,
                                             maps.by_id("MAP_CONTEST_HALL_HNS", "en").display),
          tuple(names["en"] for _p, _l, names in maps.DYNAMIC_PLACES))

    print("EN: was der englische Build deutsch zeigt (Zählung)")
    lang_files = sorted(f for f in os.listdir(repo_path("src", "data", "pokemon", "species_info"))
                        if re.search(r"\b(GERMAN|ENGLISH)\b", open(repo_path("src", "data", "pokemon", "species_info", f),
                                                                    encoding="utf-8").read()))
    de_sp, en_sp = species.all_species("de"), species.all_species("en")
    if own:
        print("  dieses Repository enthält die englische Fassung (Sprachzweige in %d species_info-Dateien)" % len(lang_files))
        check("EN Speziesnamen englisch", sum(1 for k in de_sp if de_sp[k].name == en_sp[k].name), 0)
    else:
        check("Sprachzweige in species_info nur in", lang_files, ["shared_dex_text.h"])
        check("EN Speziesnamen = DE", sum(1 for k in de_sp if de_sp[k].name != en_sp[k].name), 0)
    check("EN Zahlen = DE (Spezies)", all(
        (de_sp[k].stats, de_sp[k].types, de_sp[k].abilities, de_sp[k].levelup, de_sp[k].teachable, de_sp[k].egg_moves,
         de_sp[k].catch_rate, de_sp[k].natdex) ==
        (en_sp[k].stats, en_sp[k].types, en_sp[k].abilities, en_sp[k].levelup, en_sp[k].teachable, en_sp[k].egg_moves,
         en_sp[k].catch_rate, en_sp[k].natdex) for k in de_sp) and set(de_sp) == set(en_sp), True)
    for label, de_all, en_all in (("Spezies", de_sp, en_sp), ("Attacken", moves.all_moves("de"), moves.all_moves("en")),
                                  ("Fähigkeiten", abilities.all_abilities("de"), abilities.all_abilities("en")),
                                  ("Items", items.all_items("de"), items.all_items("en"))):
        n = len(en_all)
        name_en = sum(1 for x in en_all.values() if x.text_lang["name"] == "en")
        desc_en = sum(1 for x in en_all.values() if x.text_lang["description"] == "en")
        print("  %s: %d Einträge, im EN-Build englisch: %d Namen, %d Beschreibungen" % (label, n, name_en, desc_en))
        check("%s: text_lang passt zum Vergleich mit DE" % label,
              all((x.text_lang["description"] == "en") == (x.description != de_all[k].description)
                  or x.description == de_all[k].description for k, x in en_all.items()), True)
    mv_de, mv_en = moves.all_moves("de"), moves.all_moves("en")
    check("EN Zahlen = DE (Attacken)", all((mv_de[k].power, mv_de[k].accuracy, mv_de[k].pp, mv_de[k].type, mv_de[k].category,
                                             mv_de[k].priority, mv_de[k].effect, mv_de[k].flags) ==
                                            (mv_en[k].power, mv_en[k].accuracy, mv_en[k].pp, mv_en[k].type, mv_en[k].category,
                                             mv_en[k].priority, mv_en[k].effect, mv_en[k].flags) for k in mv_de), True)
    it_de, it_en = items.all_items("de"), items.all_items("en")
    check("EN Zahlen = DE (Items)", all((it_de[k].price, it_de[k].pocket, it_de[k].tm, it_de[k].hold_effect) ==
                                         (it_en[k].price, it_en[k].pocket, it_en[k].tm, it_en[k].hold_effect) for k in it_de), True)
    check("keine Symbolnamen als Text", [x.const for d in (de_sp, en_sp, mv_de, mv_en, it_de, it_en)
                                         for x in d.values() if re.fullmatch(r"[sg][A-Z]\w*", x.description or "")], [])

    print("text: englische Zeilenenden")
    check("EN Trennung", [text.clean(x, "en") for x in ("Psychic-\\ntype", "sea-\ndwelling", "It is\\nhere.\\pNow")],
          ["Psychic-type", "sea-dwelling", "It is here. Now"])
    check("deutscher Text im EN-Build behält deutsche Regel",
          text.clean_as("Geg-\\nner", "Geg-\\nner", "en"), "Gegner")
    check("übersetzter Text im EN-Build", text.clean_as("well-\\nknown", "wohl-\\nbekannt", "en"), "well-known")

    print("Builds: Unterschiede außerhalb von Texten")
    check("Skripte (ohne .string/.braille) gleich", SDB.nontext_diff(), [])
    # data files: a language switch only in the two forms the loaders read - the DE_EN
    # macro of the .party files (its definition at the top, "Name: DE_EN(de, en)") and
    # "name_en" in the map section list
    hits = []
    preamble = re.compile(r"^#\s*(?:ifdef\s+LANG_ENGLISH|define\s+DE_EN\(de,\s*en\)\s+(?:de|en)|else|endif)\s*$")
    for root in ("src/data", "include/constants", "data/maps", "data/layouts"):
        for dp, _dn, fn in os.walk(repo_path(*root.split("/"))):
            for f in fn:
                if f.endswith((".party", ".json")):
                    rel = os.path.relpath(os.path.join(dp, f), repo_path())
                    for line in open(os.path.join(dp, f), encoding="utf-8", errors="replace"):
                        if f.endswith(".party") and (preamble.match(line.strip())
                                                     or re.match(r"Name: DE_EN\([^()]*\)\s*$", line)):
                            continue
                        if re.search(r"\b(GERMAN|ENGLISH|LANG_ENGLISH|DE_EN)\b", line) or (
                                f.endswith(".party") and line.startswith("#")):
                            hits.append("%s: %s" % (rel, line.strip()[:60]))
                            break
    check(".party/.json: Sprachschalter nur als DE_EN-Name und name_en", hits, [])
    used = sorted(set(TU_PATHS) | set(_loaded_tus(tu)) | set(x for x in os.environ.get("OJ_SELFTEST_TUS", "").split(",") if x))
    if quick:
        used = ["src/pokemon.c", "src/move.c", "src/item.c", "src/battle_main.c"]
    bad = {p: tu.nontext_diff(p)[:3] for p in used if tu.nontext_diff(p)}
    check("%d Übersetzungseinheiten der Datenschicht: nur Texte verschieden" % len(used), bad, {})
    known = {p: len(tu.nontext_diff(p)) for p in ("src/start_menu.c", "src/script_menu.c")}
    print("  bekannte Unterschiede (nicht von der Datenschicht gelesen): %s" % known)
    # the clock of the start menu differs (24 h / 12 h); the prize menu is the same in both builds
    check("bekannte Unterschiede", (bool(known["src/start_menu.c"]), known["src/script_menu.c"]), (True, 0))


# ---------------------------------------------------------------- corrected defects stay corrected
def fixes():
    """Values that were wrong once (cross-check against the compiled game); expected
    values are read from the source files here, not through the loaders."""
    import re
    from gamedata import cparse, trainers_rematch, trainers_scriptdb as SDB, wild_statics
    print("Korrekturen: Konstanten, Oktalzahlen, Preisgeld, DVs, Fortschrittsstufen")

    def enum_value(header, name):
        src = open(repo_path("include", "constants", header), encoding="utf-8").read()
        m = re.search(r"^\s*%s\s*=\s*(\d+)\s*," % re.escape(name), src, re.M)
        return int(m.group(1)) if m else None
    for loader, header, names in ((moves, "moves.h", ("MOVE_DOUBLE_SLAP", "MOVE_GUST", "MOVE_POUND")),
                                  (abilities, "abilities.h", ("ABILITY_COLOR_CHANGE", "ABILITY_STENCH")),
                                  (items, "items.h", ("ITEM_POKE_BALL", "ITEM_HEAL_BALL", "ITEM_FAST_BALL"))):
        for n in names:
            v = enum_value(header, n)
            check("Konstante %s = %s" % (n, v), loader.by_id(v).const, n)
    for label, allx, prefix, enum in (("Attacken", moves.all_moves("de"), "MOVE_", "moves.h"),
                                      ("Fähigkeiten", abilities.all_abilities("de"), "ABILITY_", "abilities.h"),
                                      ("Items", items.all_items("de"), "ITEM_", "items.h")):
        src = open(repo_path("include", "constants", enum), encoding="utf-8").read()
        members = set(re.findall(r"^\s*(%s\w+)\s*(?:=[^,\n]*)?,?\s*(?://.*)?$" % prefix, src, re.M))
        check("%s: jede Konstante ist ein Eintrag der Aufzählung" % label,
              [x.const for x in allx.values() if x.const not in members], [])
    check("Item-Dateinamen (slug)", [items.by_id(i).slug for i in (1, 6, 20)], ["poke_ball", "heal_ball", "fast_ball"])
    setup = open(repo_path("src", "battle_setup.c"), encoding="utf-8").read()
    rows = {r.const: r for r in trainers.rematch_rows()}
    for first in ("TRAINER_JACK_HNS", "TRAINER_CHAD_HNS"):
        m = re.search(r"\[(REMATCH_\w+)\]\s*=\s*REMATCH\(\s*%s\s*,([^)]*)\)" % first, setup)
        want = [first] + [x.strip() for x in m.group(2).split(",")][:4]
        check("Rückkampf-Zeile %s" % m.group(1), rows[m.group(1)].trainer_consts, want)
        check("%s ist Telefon-Rückkampf" % first, trainers.is_phone_rematch(first, "trainerbattle_rematch"), True)
        check("%s: spätere Teams haben einen Kampfort" % first,
              all(trainers.battles(c) for c in want[1:] if c != "TRAINER_NONE"), True)
    check("Oktalzahl 00475", cparse.CEval({}).eval("00475"), 0o475)
    trade_h = open(repo_path("src", "data", "trade.h"), encoding="utf-8").read()
    octal = sorted({int(x, 8) for x in re.findall(r"\.otId\s*=\s*(0\d+)\s*,", trade_h)})
    got = sorted({e.trade["ot_id"] for e in wild_statics.entries("de") if e.trade} & set(octal)) if octal else []
    check("Tausch-OT-Nummern aus Oktalzahlen %s" % octal, got or octal, octal)
    bm = open(repo_path("src", "battle_main.c"), encoding="utf-8").read()
    only_name = re.findall(r"\[(TRAINER_CLASS_\w+)\]\s*=\s*\{\s*_\(\"[^\"]*\"\)\s*\}", bm)
    cl = trainers.classes("de")
    check("Klassen ohne Preisgeld-Angabe (%d): Faktor 0" % len(set(only_name)),
          sorted({cl[c][1] for c in only_name if c in cl}), [0])
    check("kein Preisgeld None", [c for c, v in cl.items() if v[1] is None], [])
    hiker = re.search(r"\[TRAINER_CLASS_HIKER\]\s*=\s*\{\s*_\(\"[^\"]*\"\)\s*,\s*(\d+)", bm)
    check("Wanderer Preisgeld", cl["TRAINER_CLASS_HIKER"][1], int(hiker.group(1)))
    party = open(repo_path("src", "data", "trainers_hns.party"), encoding="utf-8").read()
    blk = re.search(r"^=== TRAINER_JOEY_2_HNS ===\n(.*?)(?=^=== )", party, re.M | re.S).group(1)
    joey = trainers.by_const("TRAINER_JOEY_2_HNS")
    check("Julian 2: keine IVs-Zeile in der Datei", "IVs:" in blk, False)
    check("Julian 2: DVs 31 (Vorgabe des Build-Werkzeugs)",
          [(sorted(set(m.ivs.values())), m.ivs_given) for m in joey.mons], [([31], False)] * len(joey.mons))
    tool = open(repo_path("tools", "trainerproc", "main.c"), encoding="utf-8").read()
    check("trainerproc: Vorgabe 31", bool(re.search(r"\.default_ivs\s*=\s*\{\s*31,\s*31,\s*31,\s*31,\s*31,\s*31\s*\}", tool)), True)
    saw = trainers.by_const("TRAINER_SAWYER_1_HNS")
    check("Sawyer: IVs-Zeile bleibt", (saw.mons[0].ivs, saw.mons[0].ivs_given),
          ({k: 0 for k in ("hp", "atk", "def", "spa", "spd", "spe")}, True))
    check("alle Trainer-Pokémon haben sechs DVs", sum(1 for t in trainers.all_trainers("de").values() for m in t.mons
                                                     if m.ivs is None or len(m.ivs) != 6), 0)
    pp = open(repo_path("src", "data", "battle_partners.party"), encoding="utf-8").read()
    dummy = re.search(r"^=== PARTNER_DUMMY ===\n(.*?)(?=^=== |\Z)", pp, re.M | re.S).group(1)
    check("PARTNER_DUMMY: Party Size 0 -> kein Pokémon", ("Party Size: 0" in dummy,
                                                         len(trainers.partners("de")["PARTNER_DUMMY"].mons)), (True, 0))
    steps = levels.band_steps()
    check("Fortschrittsstufen: 30 Tabellenplätze, 28 erreichbar", (len(steps), len(levels.reachable_steps()),
                                                                 [s.step for s in steps if not s.reachable]), (30, 28, [9, 19]))
    check("Stufe 9/19 = Spielstand der Stufe 10/20", [(steps[i].game_step, steps[i].player_level == steps[i + 1].player_level)
                                                     for i in (9, 19)], [(10, True), (20, True)])
    check("Titel ab Stufe", (levels.TITLE_STEPS, [steps[i].titles for i in (8, 10, 18, 20, 28, 29)]),
          ((10, 20, 29), [0, 1, 1, 2, 2, 3]))
    lsrc = open(repo_path("src", "level_scaling.c"), encoding="utf-8").read()
    check("GetRematchProgressStep wie gespiegelt", all(x in re.sub(r"\s+", " ", lsrc) for x in (
        "return badges < REMATCH_BAND_STEPS_PER_REGION - 1 ? badges : REMATCH_BAND_STEPS_PER_REGION - 2;",
        "return REMATCH_BAND_STEPS_PER_REGION + GetBandBadgeStep(GetJohtoBadgeCount());",
        "return 3 * REMATCH_BAND_STEPS_PER_REGION - 1;")), True)
    check("title_steps ohne 9/19", [x for x in SDB.title_steps({(None, None, None, None)}) if x in (9, 19)], [])
    check("title_steps nach Kanto-Titel ab 10", SDB.title_steps({(True, False, None, None)}), list(range(10, 19)))
    stages = [st for r in trainers.rematch_rows() for st in trainers_rematch.row_stages(r)]
    check("Rückkampf-Stufen nie ab 9/19", [st.const for st in stages if st.unlock_step in (9, 19)
                                           or 9 in st.steps or 19 in st.steps], [])
    check("Stufen-Beschriftung", [trainers_rematch.step_label(i, "de") for i in (0, 8, 10, 11, 20, 29)],
          ["Kanto: 0 Orden", "Kanto: 8 Orden", "Kanto-Titel", "Johto: 1 Orden", "Johto-Titel", "Hoenn-Titel"])
    check("Stufen-Bereich", (trainers_rematch.steps_label([10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25,
                                                           26, 27, 28, 29], "en"),
                             trainers_rematch.steps_label([3, 4, 5], "de")), ("from Kanto title", "Kanto: 3 Orden bis Kanto: 5 Orden"))


# ---------------------------------------------------------------- English names in natural capitalisation
STYLE_SAMPLES = (
    ("BULBASAUR", "Bulbasaur"), ("MR. MIME", "Mr. Mime"), ("HO-OH", "Ho-Oh"), ("FARFETCH'D", "Farfetch'd"),
    ("PORYGON-Z", "Porygon-Z"), ("PORYGON2", "Porygon2"), ("NIDORAN♀", "Nidoran♀"), ("MIME JR.", "Mime Jr."),
    ("HP UP", "HP Up"), ("PP MAX", "PP Max"), ("TM01", "TM01"), ("HM08", "HM08"), ("X ATTACK", "X Attack"),
    ("X SP. ATK", "X Sp. Atk"), ("EXP. SHARE", "Exp. Share"), ("S.S. TICKET", "S.S. Ticket"), ("MT. MOON", "Mt. Moon"),
    ("ROUTE 1", "Route 1"), ("PALLET TOWN", "Pallet Town"), ("PKMN TRAINER", "PKMN Trainer"),
    ("POKé BALL", "Poké Ball"), ("POKéBLOCK CASE", "Pokéblock Case"), ("POKéMON LEAGUE", "Pokémon League"),
    ("POKéMANIAC", "PokéManiac"), ("TMs & HMs", "TMs & HMs"), ("KING'S ROCK", "King's Rock"),
    ("DIGLETT'S CAVE", "Diglett's Cave"), ("LAKE OF RAGE", "Lake of Rage"), ("RUINS OF ALPH", "Ruins of Alph"),
    ("SIS AND BRO", "Sis and Bro"), ("U-TURN", "U-turn"), ("V-CREATE", "V-create"), ("WILL-O-WISP", "Will-O-Wisp"),
    ("DOUBLE-EDGE", "Double-Edge"), ("TRICK-OR-TREAT", "Trick-or-Treat"), ("LIGHT THAT BURNS THE SKY", "Light That Burns the Sky"),
    ("10,000,000 VOLT THUNDERBOLT", "10,000,000 Volt Thunderbolt"), ("RKS SYSTEM", "RKS System"),
    ("GS BALL", "GS Ball"), ("DNA SPLICERS", "DNA Splicers"), ("VS. SEEKER", "Vs. Seeker"), ("TM CASE", "TM Case"),
    ("EXP. CANDY XL", "Exp. Candy XL"), ("LT. SURGE", "Lt. Surge"), ("TATE&LIZA", "Tate&Liza"), ("AMY & LIV", "Amy & Liv"),
    ("{B_RIVAL_NAME}", "{B_RIVAL_NAME}"), ("MAPSEC_DYNAMIC", "MAPSEC_DYNAMIC"), ("???", "???"), ("1F", "1F"),
    ("Rusty", "Rusty"), ("Seed", "Seed"), ("Bisasam", "Bisasam"), ("MED. SLOW", "Med. Slow"), ("S.S. TIDAL", "S.S. Tidal"),
    ("FAKE RTC", "Fake RTC"), ("PLAYER EVs", "Player EVs"), ("GOOD AS GOLD", "Good as Gold"),
)


def name_style():
    import re
    from gamedata import namestyle
    print("Namensstil: englische Namen in natürlicher Schreibweise (%s)" % namestyle.style())
    bad = [(g, namestyle.title(g), w) for g, w in STYLE_SAMPLES if namestyle.title(g) != w]
    check("%d Beispiele" % len(STYLE_SAMPLES), bad, [])
    check("Personennamen ohne Kleinwörter", (namestyle.title("JO & AN", "trainer"), namestyle.title("SIS AND BRO", "trainer_class")),
          ("Jo & An", "Sis and Bro"))
    check("deutsche Namen bleiben", (namestyle.show("Bisasam", "de", "species", "de"), namestyle.show("AKALA CAVE", "de", "place", "de")),
          ("Bisasam", "AKALA CAVE"))
    if namestyle.style() == "title":
        check("englischer Build: Großschrift wird umgesetzt", (namestyle.show("BULBASAUR", "en", "species", "en"),
                                                              namestyle.show("AKALA CAVE", "de", "place", "en")),
              ("Bulbasaur", "Akala Cave"))


def _all_english_names():
    """(kind, game spelling) of every name the loaders hand out in English."""
    from gamedata import hand_menus, hand_pokeblocks, natures, wild_statics
    out = []
    for kind, objs in (("species", species.all_species("en").values()), ("move", moves.all_moves("en").values()),
                       ("ability", abilities.all_abilities("en").values()), ("item", items.all_items("en").values()),
                       ("type", typeinfo.all_types("en")), ("nature", natures.all_natures("en")),
                       ("trainer", trainers.all_trainers("en").values()), ("trainer", trainers.partners("en").values())):
        out += [(kind, o.name_game) for o in objs]
    out += [("trainer_class", trainers.class_name_game(c, "en")) for c in trainers.classes("en")]
    out += [("place", maps.mapsec_name_game(k, "en")) for k, v in maps._sections().items() if v]
    out += [("place", names["en"]) for _p, _l, names in maps.DYNAMIC_PLACES]
    for tabs in (hand_menus.challenge_tabs("en"), hand_menus.option_tabs("en")):
        for tab in tabs:
            out.append(("label", tab.name_game))
            for it in tab.items:
                out.append(("label", it.name_game))
                out += [("label", c.name_game) for c in it.choices]
    out += [("label", c.name_game) for c in hand_pokeblocks.colors("en")]
    for e in wild_statics.entries("en"):
        if e.trade:
            out += [("person", e.trade["nickname_game"]), ("person", e.trade["ot_name_game"])]
    return [(k, n) for k, n in out if n]


def english_build(quick):
    """The English build of this repository without the English version's texts."""
    import subprocess
    from gamedata import tu
    print("EN (Build dieses Repositorys allein, eigener Prozess: OJ_DOCS_EN_SRC=none, Namensstil game)")
    env = dict(os.environ, OJ_DOCS_EN_SRC="none", OJ_DOCS_EN_NAME_STYLE="game", OJ_SELFTEST_TUS=",".join(sorted(tu.LOADED)))
    r = subprocess.run([sys.executable, "-I", "-B", os.path.abspath(__file__), "--english-build"] + (["--quick"] if quick else []),
                       env=env, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr[-3000:])
        failures.append("englischer Build dieses Repositorys (Kindprozess)")


def english_source():
    """English names and texts from the tree of the English version (entext.py)."""
    global RAW_ROOT
    import json
    import re
    import subprocess
    from gamedata import dex_texts, entext, hand_breeding, hand_menus, namestyle, natures, text, trainers_scriptdb as SDB, tu
    root = entext.root()
    own = entext.own_english()
    print("EN-Quelle: Texte der englischen Version (%s)" % (root or (
        "dieses Repository selbst" if own else "nicht eingerichtet")))
    print("  Regel je Text (entext.pick)")
    for label, args, want in (
            ("Quelle hat Englisch", ("Tackle", "Tackle", ["TACKLE", "Tackle"]), "TACKLE"),
            ("Schlüssel fehlt dort", ("Neu", "Neu", None), "Neu"),
            ("dort unübersetzt", ("Trank", "Trank", ["Trank", "Trank"]), "Trank"),
            ("dort für beide Sprachen englisch", ("Rocko", "Rocko", ["BROCK", "BROCK"]), "BROCK"),
            ("Platzhalter bleibt", ("{B_RIVAL_NAME}", "{B_RIVAL_NAME}", ["BLUE", "BLUE"]), "{B_RIVAL_NAME}"),
            ("Deutsch geändert, hier kein Englisch", ("Neuer Text", "Neuer Text", ["Old text", "Alter Text"]), "Old text"),
            ("Deutsch geändert, hier eigenes Englisch", ("New text", "Neuer Text", ["Old text", "Alter Text"]), "New text"),
            ("gleiches Deutsch, hier anderes Englisch", ("Mine", "Text", ["Theirs", "Text"]), "Theirs")):
        check(label, entext.pick("selftest", label, *args), want)
    chunks = entext._chunks('const u8 gA[] = _("Eins"); static const struct T sT[] = { [X_A] = { .name = _("A" "b"), .n = 1 }, };'
                            ' void f(void) { g("x"); } int y = 3;')
    check("TU-Zerlegung: Definitionen mit Texten", sorted(chunks), ["const u8 gA[]", "static const struct T sT[]", "void f(void)"])
    src = 'static const struct T sT[] = { [X_A] = { .name = _("A"), .d = { _("x"), _("y") } }, [X_B] = { .name = _("B") }, };'
    keyed = entext._keyed(src, 0, len(src))
    check("TU-Zerlegung: Texte nach Bezeichner", sorted((k, v[2]) for k, v in keyed.items()),
          [(("X_A", ("d",), 1), "x"), (("X_A", ("d",), 2), "y"), (("X_A", ("name",), 1), "A"), (("X_B", ("name",), 1), "B")])
    if not root and not own:
        print("  keine englische Quelle eingerichtet (OJ_DOCS_EN_SRC / site_config.EN_TEXT_SOURCE) und keine "
              "englischen Namen in diesem Repository: die Prüfungen gegen ihre Dateien entfallen")
        return
    if root:
        check("Quelle ist ein Quellbaum mit Sprachschalter", (entext.usable(root), os.path.samefile(root, repo_path())), (True, False))
    game = namestyle.style() == "game"

    def shown(s, kind=None):
        return s if game else namestyle.title(s, kind)
    RAW_ROOT = root
    try:
        SP_H = "src/data/pokemon/species_info/gen_1_families.h"
        b = species.by_const("SPECIES_BULBASAUR", "en")
        want = raw_field(SP_H, "en", "SPECIES_BULBASAUR", "speciesName")
        check("Bulbasaur: Name im Spiel", (b.name_game, want), ("BULBASAUR", "BULBASAUR"))
        check("Bulbasaur: gezeigter Name", b.name, shown(want))
        check("Bulbasaur: Kategorie, Dex-Text", (b.category, b.description),
              (raw_field(SP_H, "en", "SPECIES_BULBASAUR", "categoryName"), raw_field(SP_H, "en", "SPECIES_BULBASAUR", "description")))
        check("Bulbasaur: text_lang", b.text_lang, {"name": "en", "category": "en", "description": "en"})
        mv = moves.by_const("MOVE_POUND", "en")
        check("Pound", (mv.name_game, mv.name, mv.description),
              (raw_field("src/data/moves_info.h", "en", "MOVE_POUND", "name"),
               shown(raw_field("src/data/moves_info.h", "en", "MOVE_POUND", "name")),
               raw_field("src/data/moves_info.h", "en", "MOVE_POUND", "description")))
        # a hyphen at a line end is part of the compound in English text: "full-\nbody"
        check("Tackle: Bindestrich am Zeilenende", moves.by_const("MOVE_TACKLE", "en").description,
              raw_field("src/data/moves_info.h", "en", "MOVE_TACKLE", "description").replace("- ", "-"))
        ab = abilities.by_const("ABILITY_OVERGROW", "en")
        check("Overgrow", (ab.name_game, ab.description), (raw_field("src/data/abilities.h", "en", "ABILITY_OVERGROW", "name"),
                                                           raw_field("src/data/abilities.h", "en", "ABILITY_OVERGROW", "description")))
        it = items.by_const("ITEM_POTION", "en")
        check("Potion", (it.name_game, it.name, it.description),
              (raw_field("src/data/items.h", "en", "ITEM_POTION", "name"), shown(raw_field("src/data/items.h", "en", "ITEM_POTION", "name")),
               raw_field("src/data/items.h", "en", "ITEM_POTION", "description")))
        check("Full Heal (Text über Symbol)", items.by_const("ITEM_FULL_HEAL", "en").description,
              raw_string("src/data/items.h", "en", "sFullHealDesc"))
        check("Typ Grass", typeinfo.by_const("TYPE_GRASS", "en").name_game, raw_field("src/data/types_info.h", "en", "TYPE_GRASS", "name"))
        check("Wesen Adamant", natures.by_const("NATURE_ADAMANT", "en").name_game, raw_field("src/pokemon.c", "en", "NATURE_ADAMANT", "name"))
        cls = re.search(r'\[TRAINER_CLASS_LEADER_FRLG\]\s*=\s*\{\s*_\("([^"]*)"', "".join(raw_lines("src/battle_main.c", "en"))).group(1)
        check("Trainerklasse Leader", (trainers.class_name_game("TRAINER_CLASS_LEADER_FRLG", "en"),
                                       trainers.class_name("TRAINER_CLASS_LEADER_FRLG", "en")), (cls, shown(cls)))
        pk = re.search(r'\[TRAINER_CLASS_PKMN_TRAINER_1\]\s*=\s*\{\s*_\("([^"]*)"', "".join(raw_lines("src/battle_main.c", "en"))).group(1)
        check("Trainerklasse mit {PKMN}", (pk, trainers.class_name("TRAINER_CLASS_PKMN_TRAINER_1", "en")),
              ("{PKMN} TRAINER", shown("PKMN TRAINER")))
        party = open(_raw_path("src/data/trainers_frlg.party"), encoding="utf-8").read()
        pm = re.search(r"^=== TRAINER_LEADER_BROCK ===\nName: DE_EN\((.*?), (.*?)\)\n", party, re.M)
        tr = trainers.by_const("TRAINER_LEADER_BROCK", "en")
        check("Leader Brock", (tr.name_game, tr.name, trainers.by_const("TRAINER_LEADER_BROCK", "de").name),
              (pm.group(2), shown(pm.group(2), "trainer"), pm.group(1)))
        secs = json.load(open(_raw_path("src/data/region_map/region_map_sections.json"), encoding="utf-8"))
        for sec in ("MAPSEC_ROUTE_1", "MAPSEC_PALLET_TOWN", "MAPSEC_MT_MOON"):
            en_name = [x["name_en"] for x in secs["hns_map_sections"] if x["id"] == sec][0]
            check("Ort %s" % sec, (maps.mapsec_name_game(sec, "en"), maps.mapsec_name(sec, "en")), (en_name, shown(en_name)))
        check("Karte Route 1", (maps.by_id("MAP_ROUTE1", "en").display, maps.by_id("MAP_ROUTE1", "en").display_game),
              (shown("ROUTE 1"), "ROUTE 1"))
        check("Beuteltasche", items.pocket_name("POCKET_POKE_BALLS", "en"),
              shown(re.search(r'\[POCKET_POKE_BALLS\]\s*=\s*COMPOUND_STRING\("([^"]*)"', "".join(raw_lines("src/strings.c", "en"))).group(1)))
        check("Eigruppe / Wachstum", (dex_texts.egg_group("EGG_GROUP_MONSTER", "en"), dex_texts.growth("GROWTH_MEDIUM_SLOW", "en")),
              (shown(raw_string("src/pokedex_plus_hgss.c", "en", "sText_Stats_eggGroup_MONSTER")),
               shown(raw_string("src/pokedex_plus_hgss.c", "en", "sText_Stats_MEDIUM_SLOW"))))
        check("benannter Text (strings.c)", tu.cstring("src/strings.c", "gText_1F", "en"), raw_string("src/strings.c", "en", "gText_1F"))
        check("Skripttext", SDB.script_text("Common_Text_ObedienceLevel40", "en"),
              raw_script_text("data/event_scripts.s", "en", "Common_Text_ObedienceLevel40"))
        opt = [t for t in hand_menus.option_tabs("en")][0]
        raw_opt = "".join(raw_lines("src/option_menu.c", "en"))
        check("Optionsmenü: erster Reiter steht englisch in der Quelle", '_("%s")' % opt.name_game in raw_opt
              or '"%s"' % opt.name_game in raw_opt, True)
        ec = "".join(raw_lines("src/data/easy_chat/easy_chat_group_battle.h", "en"))
        words = {w for _sp, ws in hand_breeding.odd_egg("en").rows for w in ws}
        check("Kuriosei-Antworten: Wörter der englischen Wortlisten", len(words) > 4 and all(w.upper() == w for w in words), True)
        check("Wortliste (Battle) englisch", 'COMPOUND_STRING("MATCH UP")' in ec, True)
        for _prefix, label, names in maps.DYNAMIC_PLACES:
            check("Ortsname %r im englischen Spieltext %s" % (names["en"], label), names["en"] in (SDB.script_text(label, "en") or ""), True)
    finally:
        RAW_ROOT = None
    print("  Zählung: woher die englischen Texte kommen")
    de_sp, en_sp = species.all_species("de"), species.all_species("en")
    for label, de_all, en_all in (("Spezies", de_sp, en_sp), ("Attacken", moves.all_moves("de"), moves.all_moves("en")),
                                  ("Fähigkeiten", abilities.all_abilities("de"), abilities.all_abilities("en")),
                                  ("Items", items.all_items("de"), items.all_items("en"))):
        n = len(en_all)
        name_en = sum(1 for x in en_all.values() if x.text_lang["name"] == "en")
        desc_en = sum(1 for x in en_all.values() if x.text_lang["description"] == "en")
        print("    %s: %d Einträge, englisch: %d Namen, %d Beschreibungen" % (label, n, name_en, desc_en))
        check("%s: gleiche Einträge wie deutsch" % label, set(de_all) == set(en_all), True)
        same = [x.const for k, x in en_all.items() if x.name_game == de_all[k].name
                and not re.fullmatch(r"(TM|HM)\d+|\?+", x.name_game)]
        check("%s: kein Name bleibt deutsch" % label, same, [])
        check("%s: text_lang ehrlich" % label, all((x.text_lang["name"] == "en") == (x.name_game != de_all[k].name)
                                                    for k, x in en_all.items()), True)
    check("EN Zahlen = DE (Spezies)", all(
        (de_sp[k].stats, de_sp[k].types, de_sp[k].abilities, de_sp[k].levelup, de_sp[k].teachable, de_sp[k].egg_moves,
         de_sp[k].catch_rate, de_sp[k].natdex, de_sp[k].const, de_sp[k].slug) ==
        (en_sp[k].stats, en_sp[k].types, en_sp[k].abilities, en_sp[k].levelup, en_sp[k].teachable, en_sp[k].egg_moves,
         en_sp[k].catch_rate, en_sp[k].natdex, en_sp[k].const, en_sp[k].slug) for k in de_sp), True)
    it_de, it_en = items.all_items("de"), items.all_items("en")
    check("EN Zahlen = DE (Items)", all((it_de[k].price, it_de[k].pocket, it_de[k].tm, it_de[k].hold_effect, it_de[k].slug) ==
                                         (it_en[k].price, it_en[k].pocket, it_en[k].tm, it_en[k].hold_effect, it_en[k].slug) for k in it_de), True)
    tr_de, tr_en = trainers.all_trainers("de"), trainers.all_trainers("en")
    check("EN Teams = DE (Trainer)", all([(m.species, m.level, m.item, m.moves) for m in tr_de[c].mons] ==
                                         [(m.species, m.level, m.item, m.moves) for m in tr_en[c].mons] for c in tr_de), True)
    german_left = sorted({t.name for t in tr_en.values() if t.text_lang["name"] == "de" and re.search(r"[a-zäöü]", t.name)})
    print("    Trainernamen, die auch die englische Version nicht übersetzt: %s" % (", ".join(german_left) or "keine"))
    rep = entext.report()
    only_here = {k: v.get("wt_only", []) for k, v in rep["keys"].items() if v.get("wt_only") and k != "selftest"}
    print("    nur in diesem Repository (Rückfall auf den eigenen Text): %s"
          % ({k: len(v) for k, v in only_here.items()} or "nichts"))
    print("  Namensstil: jeder englische Name aller Tabellen")
    names = _all_english_names()
    allowed = set(namestyle.WORDS.values()) | {"PKMN", "II", "III"}
    bad = []
    for kind, g in sorted(set(names)):
        t = namestyle.title(g, kind)
        if namestyle.title(t, kind) != t:
            bad.append((g, t, "nicht stabil"))
        if re.sub(r"\s", "", t).lower() != re.sub(r"\s", "", g).lower():
            bad.append((g, t, "Buchstaben geändert"))
        if namestyle.is_capitals(g):
            for w in re.findall(r"[A-Za-zÀ-ÿ']+", re.sub(r"\{[^}]*\}", "", t)):
                if re.search(r"[A-Z]{2}", w) and w not in allowed and not re.fullmatch(r"(?:TM|HM)s?|[A-Z]\.?", w) \
                        and w.rstrip("s") not in allowed and g not in namestyle.NAMES:
                    bad.append((g, t, "Großschrift bleibt: %s" % w))
    check("%d Namen (%d verschiedene): stabil, Buchstaben erhalten, keine Großschrift-Reste" % (len(names), len(set(names))), bad[:20], [])
    r = subprocess.run([sys.executable, "-I", "-B", "-c",
                        "import sys; sys.path.insert(0, %r); from gamedata import species, maps; "
                        "print(species.by_const('SPECIES_BULBASAUR', 'en').name, '|', maps.mapsec_name('MAPSEC_PALLET_TOWN', 'en'))"
                        % os.path.dirname(os.path.dirname(os.path.abspath(__file__)))],
                       env=dict(os.environ, OJ_DOCS_EN_NAME_STYLE="game"), capture_output=True, text=True)
    check("Namensstil game (eigener Prozess)", r.stdout.strip(), "BULBASAUR | PALLET TOWN")


# Translation units the data layer reads (besides the ones loaded during this run).
TU_PATHS = ("src/pokemon.c", "src/move.c", "src/item.c", "src/battle_main.c", "src/battle_setup.c",
            "src/level_scaling.c", "src/wild_encounter.c", "src/strings.c", "src/pokedex_plus_hgss.c",
            "src/pokedex.c", "src/trade.c", "src/challenge_menu.c", "src/option_menu.c", "src/easy_chat.c",
            "src/scrcmd.c", "src/daycare.c", "src/berry.c", "src/pokeblock.c", "src/safari_zone.c",
            "src/shop.c", "src/roamer.c", "src/legendaries_oj.c", "src/rtc.c", "src/fishing.c", "src/dexnav.c",
            "src/battle_script_commands.c", "src/move_relearner.c", "src/graphics.c", "src/region_rule_oj.c",
            "src/data/pokemon/level_up_learnsets_gen3.c", "src/data/pokemon/egg_moves_gen3.c",
            "src/title_screen.c")


def _loaded_tus(tu):
    """Paths of every TU a loader asked for during this run (tu.LOADED)."""
    return sorted(tu.LOADED)


def main():
    quick = "--quick" in sys.argv
    print("levels: mirror of src/level_scaling.c")
    check("check_mirror", levels.check_mirror(), True)

    print("species: Bisasam")
    b = species.by_const("SPECIES_BULBASAUR")
    print("  %s / %s, Typen %s, Basiswerte %s (Summe %d)" % (b.name, b.category,
          [typeinfo.by_id(t).name for t in b.types], b.stats, b.bst))
    print("  Fähigkeiten %s, Eigruppen %s, Fangrate %d, EP %d, Wachstum %s" % (
        [abilities.by_id(a).name if a else "-" for a in b.abilities], b.egg_groups, b.catch_rate,
        b.exp_yield, b.growth_rate))
    print("  Level-Attacken %s" % [(lv, moves.by_id(m).name) for lv, m in b.levelup[:5]])
    print("  Entwicklung %s" % [(e.method, e.param, species.by_id(e.target).name) for e in b.evolutions])
    check("Bisasam Basiswerte", [b.stats[k] for k in ("hp", "atk", "def", "spa", "spd", "spe")], [45, 49, 49, 65, 65, 45])
    check("Bisasam Name", b.name, "Bisasam")
    print("  Dex-Größen: national %d, Kanto %d, Johto %d, Hoenn %d" % tuple(
        len(species.dex(k)) for k in ("national", "kanto", "johto", "hoenn")))

    print("moves / abilities / items / types")
    m = moves.by_const("MOVE_FLAMETHROWER")
    print("  %s: %s %s %d/%d/%d" % (m.name, typeinfo.by_id(m.type).name, m.category, m.power, m.accuracy, m.pp))
    check("Flammenwurf Stärke", m.power, 90)
    tm = moves.tm_hm_moves()
    print("  TM/VM: %d TMs, %d VMs; TM01 = %s" % (sum(1 for x in tm if x[0] == "TM"), sum(1 for x in tm if x[0] == "HM"),
                                               moves.by_id(tm[0][2]).name))
    a = abilities.by_const("ABILITY_OVERGROW")
    print("  %s: %s" % (a.name, a.description))
    it = items.by_const("ITEM_POTION")
    print("  %s: %d, %s" % (it.name, it.price, it.description))
    check("Trank Preis", it.price, 200)
    fire = typeinfo.by_const("TYPE_FIRE")
    print("  Feuer greift an: %s" % ", ".join("%s x%g" % (t.name, typeinfo.effectiveness(fire.id, t.id))
                                             for t in typeinfo.battle_types()
                                             if typeinfo.effectiveness(fire.id, t.id) != 1))

    print("maps / encounters: Route 1 (Kanto) und Route 29 (Johto)")
    for mid in ("MAP_ROUTE1", "MAP_ROUTE29_HNS"):
        mp = maps.by_id(mid)
        print("  %s = %s (%s), Level-Region %s" % (mid, mp.display, mp.region, levels.remap_region(mid)))
        for tms, tabs in encounters.time_groups(mid):
            for area, rows in tabs.items():
                if rows:
                    print("    %s %s: %s" % ("/".join(t[5:].lower() for t in tms), area, ", ".join(
                        "%s %d%% Lv %d-%d" % (species.by_id(r.species).name, r.pct, r.eff_min, r.eff_max) for r in rows)))
    day = encounters.summary("MAP_ROUTE1", "land", "TIME_DAY")
    check("Route 1 Tag", [(species.by_id(r.species).name, r.pct, r.eff_min, r.eff_max) for r in day],
          [("Taubsi", 50, 2, 4), ("Rattfratz", 50, 2, 3)])

    print("trainers: Kanto, Johto, Hoenn mit effektiven Leveln")
    for const in ("TRAINER_LEADER_BROCK", "TRAINER_FALKNER_1_HNS", "TRAINER_ROXANNE_1"):
        tr = trainers.by_const(const)
        b0 = trainers.battles(const)[0]
        team = trainers.effective_team(tr, b0.map_id, trainers.battle_mode(tr, b0))
        print("  %s %s (%s) auf %s [%s]: %s" % (tr.class_name, tr.name, const, maps.by_id(b0.map_id).display,
              team.region, ", ".join("%s Lv %d (Daten %d)" % (species.by_id(x.species).name, x.level, x.data_level)
                                     for x in team.mons)))
    brock = trainers.effective_team(trainers.by_const("TRAINER_LEADER_BROCK"), "MAP_PEWTER_CITY_GYM")
    check("Rocko (Kanto, unverändert)", [(species.by_id(x.species).name, x.level) for x in brock.mons],
          [("Kleinstein", 11), ("Onix", 12)])
    falk = trainers.effective_team(trainers.by_const("TRAINER_FALKNER_1_HNS"), "MAP_VIOLET_CITY_GYM_HNS")
    check("Falk (Johto, Remap + Entwicklung)", [(species.by_id(x.species).name, x.level) for x in falk.mons],
          [("Tauboss", 47), ("Ibitak", 47), ("Noctuh", 47), ("Porenta", 48), ("Xatu", 48), ("Kramurx", 48)])
    bh = trainers.by_const("TRAINER_BROCK_HNS")
    bb = trainers.battles("TRAINER_BROCK_HNS")[0]
    mode = trainers.battle_mode(bh, bb)
    team = trainers.effective_team(bh, bb.map_id, mode, steps=range(19, 30))
    print("  Rocko-Revanche (%s, Band %s): Lv %s nach Johto-Titel bis Hoenn-Titel" % (mode, team.band, team.mons[0].level_range))
    check("Rocko-Revanche Band", (mode, team.mons[0].level_range), ("leader", (74, 97)))
    joey = trainers.by_const("TRAINER_JOEY_2_HNS")
    jb = trainers.battles("TRAINER_JOEY_2_HNS")[0]
    jt = trainers.effective_team(joey, jb.map_id, trainers.battle_mode(joey, jb))
    by = {s.step: [x.level for x in ms] for s, ms in jt.by_step}
    check("Julian 2 Telefon-Band P=55/65/96", (by[13][0], by[18][0], by[29][0]), (54, 59, 90))

    print("trainers: Mehrfachkämpfe (multi_2_vs_2, je Gegner die ersten 3 Pokémon)")
    for const, want in (("TRAINER_ARIANA_1_HNS", [("Arbok", 59), ("Snobilikat", 59), ("Giflor", 59)]),
                        ("TRAINER_GRUNT_23_HNS", [("Golbat", 56), ("Iksbat", 56), ("Arbok", 59)]),
                        ("TRAINER_MAXIE_MOSSDEEP", [("Magnayen", 90), ("Iksbat", 91), ("Camerupt", 92)]),
                        ("TRAINER_TABITHA_MOSSDEEP", [("Camerupt", 87), ("Magnayen", 88), ("Iksbat", 89)])):
        tr = trainers.by_const(const)
        mb = [x for x in trainers.battles(const) if x.command == "multi_2_vs_2" and x.map_id][0]
        team = trainers.effective_team(tr, mb.map_id, "normal", count=trainers.party_count(tr, mb.command))
        check("%s %s" % (tr.name, const), [(species.by_id(x.species).name, x.level) for x in team.mons], want)

    print("maps: MAPSEC_DYNAMIC-Orte und Ortsnamen aus dem Spieltext")
    check("MS Tide", (maps.by_id("MAP_SS_TIDAL_CORRIDOR").display, maps.by_id("MAP_SS_TIDAL_CORRIDOR").region,
                      maps.host_mapsec("MAP_SS_TIDAL_ROOMS")), ("MS Tide", "Hoenn", "MAPSEC_SLATEPORT_CITY"))
    check("Wettbewerbshalle", maps.by_id("MAP_CONTEST_HALL_HNS").display, "Wettbewerbshalle")
    from gamedata import trainers_scriptdb
    for _prefix, label, names in maps.DYNAMIC_PLACES:
        check("Spieltext %s in %s" % (names["de"], label),
              names["de"] in (trainers_scriptdb.script_text(label, "de") or ""), True)

    print("text: Silbentrennung aus dem Spieltext")
    from gamedata import text
    check("Trennung", [text.clean(x) for x in ("bestimm-\\nten", "Feuer-\\nAttacke", "Dies-\\nund", "Geg-\nner")],
          ["bestimmten", "Feuer-Attacke", "Dies- und", "Gegner"])

    print("levels: tatsächliche Bereiche und Skript-Ausnahmen")
    span = encounters.level_span()
    print("  wilde Pokémon: %s" % span)
    check("Johto wild", span[("Johto", False)], (43, 100))
    check("Hoenn wild ab", span[("Hoenn", False)][0], 66)
    check("Skript-Ausnahmen (ScaleWildMonLevel)", [(c, lv) for c, _d, lv, _m, _s in levels.scripted_wild_exceptions()],
          [("SPECIES_RALTS", 68), ("SPECIES_LINOONE", 69)])

    print("graphics")
    for label, img in (("Bisasam vorn", graphics.mon_front(b)), ("Bisasam schillernd", graphics.mon_front(b, True)),
                       ("Bisasam Icon", graphics.mon_icon(b)), ("Trank", graphics.item_icon(it)),
                       ("TM01", graphics.item_icon(items.by_const("ITEM_TM01"))),
                       ("Falk (Trainerbild)", graphics.trainer_pic(trainers.by_const("TRAINER_FALKNER_1_HNS"))),
                       ("Typ Feuer", graphics.type_icon(fire)), ("Kategorie physisch", graphics.category_icon(0))):
        print("  %s: %s %s, Transparenz-Index %s" % (label, img.mode, img.size, img.info.get("transparency")))
    print("  Typfarbe Feuer: %s" % (graphics.type_color(fire),))

    fixes()
    name_style()
    english_build(quick)
    english_source()

    print()
    if failures:
        print("FEHLER: %s" % ", ".join(failures))
        return 1
    print("Alle Prüfungen bestanden.")
    return 0


if __name__ == "__main__":
    if "--english-build" in sys.argv:
        english("--quick" in sys.argv)
        sys.exit(1 if failures else 0)
    sys.exit(main())
