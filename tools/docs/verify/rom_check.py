#!/usr/bin/env python3
"""Compare the docs data layer (tools/docs/gamedata) with a ROM dump.

    python3 -I -B tools/docs/verify/rom_check.py --lang de --dump dump_de.json
    python3 -I -B tools/docs/verify/rom_check.py --lang en --dump dump_en.json

The dump comes from rom_dump.py (the compiled game); the other side is what
the site generator reads through the gamedata loaders. Every value is compared
as the data layer hands it to the pages: ids, numbers, names and texts. Levels
are the raw data levels (the runtime level rules are checked by remap_check.py).

Constant names of the data layer (EGG_GROUP_*, GROWTH_*, EVO_*, MAPSEC_* ...)
are turned into numbers with the constants the compiler evaluated for the
dump, so a wrong name <-> number pairing in the data layer shows up as well.

Texts: the ROM text is decoded with charmap.txt and passed through the same
display clean-up as the data layer's (gamedata/text.py: line breaks, hyphens,
placeholders); characters that share a byte in the charmap count as equal.

Output: one line per table with entries / fields / differences, then every
difference. Exit status 1 if anything differs, 0 otherwise.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(DOCS))
sys.path.insert(0, HERE)
from romlib import Charmap  # noqa: E402

STATS = ("hp", "atk", "def", "spa", "spd", "spe")
AREA_FIELDS = (("land", "land_mons"), ("water", "water_mons"), ("rock_smash", "rock_smash_mons"),
               ("fishing", "fishing_mons"))


def load_gamedata(lang):
    """The gamedata package for one language.

    The language is given to the data layer in every way it accepts: the
    OJ_DOCS_LANG environment variable (read by gamedata/tu.py at import), and
    set_lang()/set_language() of the package, of tu or of an i18n module if they
    exist. One process handles one language."""
    os.environ["OJ_DOCS_LANG"] = lang
    # This check is about the English build of THIS repository (its ROM is the dump):
    # no texts from the English version's tree, names as the game writes them.
    # (The English version's names are checked by en_names_check.py.)
    os.environ["OJ_DOCS_EN_SRC"] = "none"
    os.environ["OJ_DOCS_EN_NAME_STYLE"] = "game"
    sys.path.insert(0, DOCS)
    import gamedata
    from gamedata import tu
    how = ["OJ_DOCS_LANG=%s" % lang]
    mods = [gamedata, tu]
    try:
        from gamedata import i18n
        mods.append(i18n)
    except ImportError:
        pass
    for mod in mods:
        for fn in ("set_lang", "set_language", "use_lang"):
            if callable(getattr(mod, fn, None)):
                getattr(mod, fn)(lang)
                how.append("%s.%s(%r)" % (mod.__name__, fn, lang))
    active = getattr(tu, "LANG", None)
    for mod in mods:
        for fn in ("get_lang", "current_lang", "lang"):
            if callable(getattr(mod, fn, None)):
                try:
                    active = getattr(mod, fn)()
                except TypeError:
                    pass
    if active is not None and active != lang:
        raise SystemExit("data layer runs in language %r, wanted %r" % (active, lang))
    return how


class Report:
    def __init__(self):
        self.tables = []          # [name, entries, set(fields), [diff lines], note]
        self.cur = None

    def table(self, name, note=""):
        self.cur = [name, 0, set(), [], note]
        self.tables.append(self.cur)

    def entry(self, n=1):
        self.cur[1] += n

    def eq(self, key, field, rom, dl):
        """One compared value. rom: from the dump, dl: from the data layer."""
        self.cur[2].add(field)
        if rom != dl:
            self.cur[3].append("%s  %s: ROM %s, data layer %s" % (key, field, _short(rom), _short(dl)))
            return False
        return True

    def diff(self, key, text):
        self.cur[3].append("%s  %s" % (key, text))

    def total(self):
        return sum(len(t[3]) for t in self.tables)

    def print(self, limit):
        for name, entries, fields, diffs, note in self.tables:
            print("%-16s %5d entries, %2d fields each, %d differences%s"
                  % (name + ":", entries, len(fields), len(diffs), ("   (" + note + ")") if note else ""))
        print("total: %d differences" % self.total())
        for name, entries, fields, diffs, note in self.tables:
            if not diffs:
                continue
            print("\n== %s: %d differences ==" % (name, len(diffs)))
            by_field = {}
            for line in diffs:
                f = line.split("  ", 1)[1].split(":")[0] if "  " in line else line
                by_field[f] = by_field.get(f, 0) + 1
            print("  by field: " + ", ".join("%s %d" % kv for kv in sorted(by_field.items(), key=lambda kv: -kv[1])))
            for line in diffs[:limit]:
                print("  " + line)
            if len(diffs) > limit:
                print("  ... %d more (use --max)" % (len(diffs) - limit))


def _short(v):
    s = json.dumps(v, ensure_ascii=False, sort_keys=True) if not isinstance(v, str) else repr(v)
    return s if len(s) <= 300 else s[:300] + "..."


class Checker:
    def __init__(self, dump, lang, dump_de=None):
        self.d = dump
        self.de = dump_de           # German dump, only used to tell translated texts apart
        self.lang = lang
        self.K = dump["constants"]
        self.cm = Charmap(os.path.join(REPO, "charmap.txt"))
        self.r = Report()
        self.game_notes = []        # oddities of the game data itself (both sides agree)
        from gamedata import text
        self.text = text

    # ------------------------------------------------------------ helpers
    def num(self, name):
        """Number of a constant name of the data layer, by the compiler's constants."""
        if name is None:
            return None
        if isinstance(name, int):
            return name
        return self.K.get(name, "?" + str(name))

    def disp(self, s, table=None, key=None, field="description"):
        """ROM text as the pages show a description: the data layer's display
        clean-up (gamedata/text.py) applied to the text of the ROM. For the English
        build the clean-up rules depend on whether a text is translated at all
        (text.clean_as); that is decided with the same text of the German ROM."""
        if s is None:
            return None
        t = self.text
        if self.lang != "de" and hasattr(t, "clean_as"):
            s_de = None
            if self.de is not None and table is not None:
                s_de = (self.de[table].get(str(key)) or {}).get(field)
            out = t.clean_as(s, s_de, self.lang)
        else:
            try:
                out = t.clean(s, self.lang)
            except TypeError:           # clean(s) without a language
                out = t.clean(s)
        return self.cm.canon(out)

    def nm(self, s):
        """ROM text as the pages show a name."""
        return None if s is None else self.cm.canon(self.text.name(s))

    def dl(self, s):
        return None if s is None else self.cm.canon(s)

    def const_name(self, key, prefix, value, const):
        """The constant name the data layer gives an id must be an enumerator of that
        enum with that value (not a macro of another family that has the same number)."""
        allowed = (self.d.get("enumerators", {}).get(prefix) or {}).get(str(value))
        if allowed is None:
            return
        if const in allowed:
            self.r.cur[2].add("constant name")
        else:
            self.r.eq(key, "constant name", allowed, const)

    def sname(self, sid):
        return "%s (%s)" % (self.d["names"]["SPECIES_"].get(str(sid), "?"), sid)

    # ------------------------------------------------------------ species
    def species(self):
        from gamedata import species as SP
        r, d = self.r, self.d
        r.table("species")
        rom = {int(k): v for k, v in d["species"].items()}
        allsp = SP.all_species()
        skip = {0, self.K["SPECIES_EGG"]}
        for sid in sorted(set(rom) | set(allsp)):
            if sid in skip:
                continue
            key = self.sname(sid)
            e, sp = rom.get(sid), allsp.get(sid)
            if e is None or sp is None:
                if e is not None and not e["name"].strip():
                    continue
                r.diff(key, "only in the %s" % ("ROM" if sp is None else "data layer"))
                continue
            r.entry()
            r.eq(key, "name", self.nm(e["name"]), self.dl(sp.name))
            r.eq(key, "constant", sid, self.num(sp.const))
            r.eq(key, "category", self.nm(e["category"]), self.dl(sp.category))
            r.eq(key, "description", self.disp(e["description"], "species", sid), self.dl(sp.description))
            r.eq(key, "types", e["types"], list(sp.types))
            for s in STATS:
                r.eq(key, "base " + s, e["stats"][s], sp.stats[s])
            r.eq(key, "abilities", e["abilities"], list(sp.abilities[:3]))
            r.eq(key, "catch rate", e["catch_rate"], sp.catch_rate)
            r.eq(key, "exp yield", e["exp_yield"], sp.exp_yield)
            r.eq(key, "ev yield", e["ev_yield"], {s: sp.ev_yield[s] for s in STATS})
            r.eq(key, "gender ratio", e["gender_ratio"], sp.gender_ratio)
            r.eq(key, "egg groups", e["egg_groups"], [self.num(x) for x in sp.egg_groups])
            r.eq(key, "egg cycles", e["egg_cycles"], sp.egg_cycles)
            r.eq(key, "growth rate", e["growth_rate"], self.num(sp.growth_rate))
            r.eq(key, "friendship", e["friendship"], sp.friendship)
            r.eq(key, "held item common", e["held_common"], sp.held_common)
            r.eq(key, "held item rare", e["held_rare"], sp.held_rare)
            r.eq(key, "national dex number", e["natdex"], sp.natdex)
            r.eq(key, "height", e["height"], sp.height)
            r.eq(key, "weight", e["weight"], sp.weight)
            r.eq(key, "flags", e["flags"], {k: int(v) for k, v in sp.flags.items() if k != "tmIlliterate"})
            r.eq(key, "level-up moves", e["levelup"], [list(x) for x in sp.levelup])
            r.eq(key, "teachable moves", e["teachable"], list(sp.teachable))
            r.eq(key, "egg moves", e["egg_moves"], list(sp.egg_moves))
            evs = []
            for ev in sp.evolutions:
                conds = []
                for name, args in ev.conditions:
                    a = [self.num(x) if isinstance(x, str) else x for x in args]
                    conds.append([self.num(name)] + (a + [0, 0, 0])[:3])
                evs.append(dict(method=self.num(ev.method), param=ev.param, target=ev.target, conditions=conds))
            r.eq(key, "evolutions", e["evolutions"], evs)
            r.eq(key, "forms", [x for x in e["forms"] if x in allsp], [x.id for x in SP.forms(sid)])
        # regional dex orders
        r.table("dex orders")
        nat = {}
        for sid in sorted(rom):
            if sid not in skip and rom[sid]["natdex"]:
                nat.setdefault(rom[sid]["natdex"], sid)
        for kind in ("kanto", "johto", "hoenn"):
            want = [[i + 1, nat[n]] for i, n in enumerate(d["dex"][kind]) if n in nat]
            got = [[n, sp.id] for n, sp in SP.dex(kind)]
            r.entry(len(want))
            if want != got:
                r.eq(kind, "number -> species", want, got)
            else:
                r.cur[2].add("number -> species")

    # ------------------------------------------------------------ moves
    def moves(self):
        from gamedata import moves as MV
        from rom_dump import MOVE_FLAGS
        r, d = self.r, self.d
        r.table("moves")
        rom = {int(k): v for k, v in d["moves"].items()}
        allmv = MV.all_moves()
        cat = {"physical": self.K["DAMAGE_CATEGORY_PHYSICAL"], "special": self.K["DAMAGE_CATEGORY_SPECIAL"],
               "status": self.K["DAMAGE_CATEGORY_STATUS"]}
        extra_flags = set()
        for mid in sorted(set(rom) | set(allmv)):
            if mid == 0:
                continue
            key = "%s (%d)" % (d["names"]["MOVE_"].get(str(mid), "?"), mid)
            e, m = rom.get(mid), allmv.get(mid)
            if e is None or m is None:
                if e is not None and not e["name"]:
                    continue
                r.diff(key, "only in the %s" % ("ROM" if m is None else "data layer"))
                continue
            r.entry()
            r.eq(key, "name", self.nm(e["name"]), self.dl(m.name))
            self.const_name(key, "MOVE_", mid, m.const)
            r.eq(key, "description", self.disp(e["description"], "moves", mid), self.dl(m.description))
            r.eq(key, "type", e["type"], m.type)
            r.eq(key, "category", e["category"], cat.get(m.category))
            r.eq(key, "power", e["power"], m.power)
            r.eq(key, "accuracy", e["accuracy"], m.accuracy)
            r.eq(key, "pp", e["pp"], m.pp)
            r.eq(key, "priority", e["priority"], m.priority)
            r.eq(key, "target", e["target"], self.num(m.target))
            r.eq(key, "effect", e["effect"], self.num(m.effect))
            r.eq(key, "critical hit stage", e["crit_stage"], m.crit_stage)
            r.eq(key, "flags", sorted(e["flags"]), sorted(f for f in m.flags if f in MOVE_FLAGS))
            extra_flags |= {f for f in m.flags if f not in MOVE_FLAGS}
        self.move_extra_flags = sorted(extra_flags)
        r.table("tm/hm list")
        n_tm = self.K["NUM_TECHNICAL_MACHINES"]
        want = []
        for idx, (item, move) in enumerate(d["tmhm"]):
            if idx == 0 or not item:
                continue
            want.append(["TM", idx, move] if idx <= n_tm else ["HM", idx - n_tm, move])
        got = [list(x) for x in MV.tm_hm_moves()]
        r.entry(len(want))
        if want != got:
            r.eq("list", "machine -> move", want, got)
        else:
            r.cur[2].add("machine -> move")
        from gamedata import items as IT
        for idx, (item, move) in enumerate(d["tmhm"]):
            if idx == 0 or not item:
                continue
            it = IT.by_id(item)
            w = ("TM", idx, move) if idx <= n_tm else ("HM", idx - n_tm, move)
            r.eq("item %d" % item, "machine item", list(w), list(it.tm) if it and it.tm else None)
        r.table("tutor moves")
        r.entry(len(d["tutor_moves"]))
        r.eq("list", "moves", [x for x in d["tutor_moves"] if x], list(MV.tutor_moves()))

    # ------------------------------------------------------------ abilities
    def abilities(self):
        from gamedata import abilities as AB
        r, d = self.r, self.d
        r.table("abilities")
        rom = {int(k): v for k, v in d["abilities"].items()}
        allab = AB.all_abilities()
        for aid in sorted(set(rom) | set(allab)):
            if aid == 0:
                continue
            key = "%s (%d)" % (d["names"]["ABILITY_"].get(str(aid), "?"), aid)
            e, a = rom.get(aid), allab.get(aid)
            if e is None or a is None:
                if e is not None and not e["name"].strip():
                    continue
                r.diff(key, "only in the %s" % ("ROM" if a is None else "data layer"))
                continue
            r.entry()
            r.eq(key, "name", self.nm(e["name"]), self.dl(a.name))
            self.const_name(key, "ABILITY_", aid, a.const)
            r.eq(key, "description", self.disp(e["description"], "abilities", aid), self.dl(a.description))

    # ------------------------------------------------------------ items
    def items(self):
        from gamedata import items as IT
        r, d = self.r, self.d
        r.table("items")
        rom = {int(k): v for k, v in d["items"].items()}
        allit = IT.all_items()
        for iid in sorted(set(rom) | set(allit)):
            if iid == 0:
                continue
            key = "%s (%d)" % (d["names"]["ITEM_"].get(str(iid), "?"), iid)
            e, it = rom.get(iid), allit.get(iid)
            if e is None or it is None:
                if e is not None and not e["name"]:
                    continue
                r.diff(key, "only in the %s" % ("ROM" if it is None else "data layer"))
                continue
            r.entry()
            r.eq(key, "name", self.nm(e["name"]), self.dl(it.name))
            self.const_name(key, "ITEM_", iid, it.const)
            r.eq(key, "description", self.disp(e["description"], "items", iid), self.dl(it.description))
            r.eq(key, "price", e["price"], it.price)
            r.eq(key, "pocket", e["pocket"], self.num(it.pocket))
            r.eq(key, "hold effect", e["hold_effect"], self.num(it.hold_effect) if it.hold_effect else 0)
            r.eq(key, "hold effect param", e["hold_effect_param"], it.hold_effect_param or 0)
            r.eq(key, "secondary id", e["secondary_id"], it.secondary_id or 0)

    # ------------------------------------------------------------ types
    def types(self):
        from gamedata import typeinfo as TY
        r, d = self.r, self.d
        r.table("types")
        rom = {int(k): v for k, v in d["types"].items()}
        allty = {t.id: t for t in TY.all_types()}
        for tid in sorted(set(rom) | set(allty)):
            key = "%s (%d)" % (d["names"]["TYPE_"].get(str(tid), "?"), tid)
            e, t = rom.get(tid), allty.get(tid)
            if e is None or t is None:
                r.diff(key, "only in the %s" % ("ROM" if t is None else "data layer"))
                continue
            r.entry()
            r.eq(key, "name", self.nm(e["name"]), self.dl(t.name))
            r.eq(key, "generic move name", self.nm(e["generic"]), self.dl(t.generic))
            r.eq(key, "palette", e["palette"], t.palette)
            r.eq(key, "special case", bool(e["special"]), bool(t.special))
            r.eq(key, "damage category", e["damage_category"], t.damage_category or 0)
            r.eq(key, "constant", tid, self.num(t.const))
            self.const_name(key, "TYPE_", tid, t.const)
        r.table("type chart")
        chart = d["type_chart"]
        for a in range(len(chart)):
            for b in range(len(chart)):
                r.entry()
                r.eq("%s -> %s" % (d["names"]["TYPE_"].get(str(a)), d["names"]["TYPE_"].get(str(b))),
                     "multiplier", chart[a][b] / 4096.0, TY.effectiveness(a, b))

    # ------------------------------------------------------------ trainers
    def _party(self, key, rom_party, mons, K):
        r = self.r
        for i, e in enumerate(rom_party):
            if e["species"] and str(e["species"]) not in self.d["species"]:
                self.game_notes.append("%s slot %d: species %s is not in this build (its gSpeciesInfo entry is empty)"
                                       % (key, i + 1, self.sname(e["species"])))
        r.eq(key, "party size", len(rom_party), len(mons))
        gender = {None: K["TRAINER_MON_RANDOM_GENDER"], "M": K["TRAINER_MON_MALE"], "F": K["TRAINER_MON_FEMALE"]}
        for i, (e, m) in enumerate(zip(rom_party, mons)):
            k = "%s slot %d" % (key, i + 1)
            r.eq(k, "species", e["species"], m.species)
            r.eq(k, "level", e["level"], m.level)
            r.eq(k, "held item", e["item"], m.item or 0)
            r.eq(k, "moves", e["moves"], (list(m.moves) + [0, 0, 0, 0])[:4])
            r.eq(k, "ability", e["ability"], m.ability or 0)
            r.eq(k, "nature", e["nature"], self.num("NATURE_" + m.nature.strip().upper().replace(" ", "_")) if m.nature else K["NATURE_HARDY"])
            # IVs/EVs as stored: a missing "IVs:" line leaves the field 0; within a line a
            # missing stat is 31 (IVs) / 0 (EVs) (tools/trainerproc)
            if m.ivs is None:
                r.eq(k, "ivs", e["iv_raw"], 0)
            else:
                r.eq(k, "ivs", e["ivs"], {s: m.ivs[s] for s in STATS})
            if m.evs is None:
                r.eq(k, "evs", e["evs"], None)
            else:
                r.eq(k, "evs", e["evs"], {s: m.evs.get(s, 0) for s in STATS})
            r.eq(k, "nickname", self.nm(e["nickname"]), self.dl(m.nickname))
            r.eq(k, "gender", e["gender"], gender.get(m.gender, m.gender))
            r.eq(k, "shiny", bool(e["shiny"]), bool(m.shiny))

    def trainers(self):
        from gamedata import trainers as TR
        r, d, K = self.r, self.d, self.K
        r.table("trainer classes")
        rom = {int(k): v for k, v in d["trainer_classes"].items()}
        classes = TR.classes() if hasattr(TR, "classes") else TR._classes()
        seen, class_money_diff = set(), set()
        for const, (name, money) in sorted(classes.items(), key=lambda kv: str(kv[0])):
            cid = self.num(const)
            e = rom.get(cid)
            if e is None:
                r.diff(str(const), "only in the data layer")
                continue
            seen.add(cid)
            r.entry()
            r.eq(const, "name", self.nm(e["name"]), self.dl(name))
            if not r.eq(const, "prize money factor", e["money"], money):
                class_money_diff.add(cid)
        for cid, e in sorted(rom.items()):
            if cid not in seen and (e["name"].strip() or e["money"]):
                r.diff("class %d %r" % (cid, e["name"]), "only in the ROM")

        for label, table, loader in (("trainers", "trainers", TR.all_trainers), ("battle partners", "partners", TR.partners)):
            r.table(label)
            rom = {int(k): v for k, v in d[table].items()}
            seen = set()
            for const, tr in loader().items():
                key = "%s (%s)" % (const, tr.id)
                e = rom.get(tr.id)
                if e is None or tr.id != K.get(const):
                    r.diff(key, "id %r: ROM constant %r, entry %s" % (tr.id, K.get(const), "missing" if e is None else "there"))
                    continue
                seen.add(tr.id)
                r.entry()
                r.eq(key, "name", self.nm(e["name"]), self.dl(tr.name))
                r.eq(key, "class", e["trainer_class"], self.num(tr.class_const))
                cls = d["trainer_classes"].get(str(e["trainer_class"]), {})
                r.eq(key, "class name", self.nm(cls.get("name")), self.dl(tr.class_name))
                if e["trainer_class"] not in class_money_diff:      # reported once, in "trainer classes"
                    r.eq(key, "prize money factor", cls.get("money"), tr.money)
                r.eq(key, "picture", e["pic"], self.num(tr.pic_const))
                r.eq(key, "double battle", e["battle_type"] == K["TRAINER_BATTLE_TYPE_DOUBLES"], bool(tr.double))
                r.eq(key, "items", e["items"], (list(tr.items) + [0] * 4)[:len(e["items"])])
                r.eq(key, "gender", e["gender"],
                     {"male": K["TRAINER_GENDER_MALE"], "female": K["TRAINER_GENDER_FEMALE"]}.get(
                         (tr.gender or "male").lower(), tr.gender))
                self._party(key, e["party"], tr.mons, K)
            for tid, e in sorted(rom.items()):
                if tid not in seen and (e["party_size"] or e["name"].strip()):
                    r.diff("trainer %d %r" % (tid, e["name"]), "in the ROM (party of %d), not in the data layer" % e["party_size"])

        r.table("rematch table")
        rows = TR.rematch_rows()
        rom = d["rematch"]
        r.eq("table", "rows", len(rom), len(rows))
        from gamedata import maps as MP
        for row, e in zip(rows, rom):
            key = "row %d %s" % (row.index, row.const)
            r.entry()
            r.eq(key, "trainers", e["trainers"], [self.num(x) for x in row.trainer_consts])
            # the names the data layer gives the row's trainers must be its own trainers
            known = TR.all_trainers()
            by_id = {t.id: c for c, t in known.items()}
            want = [by_id.get(x, "trainer %d" % x) if x else "TRAINER_NONE" for x in e["trainers"]]
            got = [x if (x in known or self.num(x) == 0) else "%s (not a trainer of the data layer)" % x
                   for x in row.trainer_consts]
            if any("not a trainer" in str(x) for x in got):
                r.eq(key, "trainer constants", want, got)
            else:
                r.cur[2].add("trainer constants")
            m = MP.by_id(row.map_id) if row.map_id else None
            r.eq(key, "map", [e["group"], e["num"]], [m.group_index, m.map_num] if m else None)
            r.eq(key, "map constant", e["num"] | e["group"] << 8, self.num(row.map_id))
            r.eq(key, "special row", row.index >= K["REMATCH_SPECIAL_TRAINER_START"], bool(row.special))

    # ------------------------------------------------------------ wild
    def wild(self):
        from gamedata import encounters as EN
        r, d, K = self.r, self.d, self.K
        r.table("wild tables")
        heads = EN.headers()
        rom = d["wild"]
        r.eq("gWildMonHeaders", "header count", len(rom), len(heads))
        times = [t for t, _ in EN.times()]
        r.eq("times of day", "order", [K[t] for t in times], list(range(len(times))))
        for e in rom:
            for ti, tabs in enumerate(e["times"]):
                for area, t in sorted(tabs.items()):
                    for i, m in enumerate(t["mons"]):
                        if m[2] and str(m[2]) not in d["species"]:
                            self.game_notes.append("wild table %s slot %d: species %s is not in this build"
                                                   % (t["symbol"], i, self.sname(m[2])))
        for h, e in zip(heads, rom):
            key = "header %d %s" % (e["index"], h.map_id)
            r.eq(key, "map", e["num"] | e["group"] << 8, self.num(h.map_id))
            for ti, tname in enumerate(times):
                tabs = e["times"][ti]
                src = h.tables.get(tname) or {}
                for area, field in AREA_FIELDS:
                    k = "%s %s %s" % (key, tname, area)
                    rt, st = tabs.get(area), src.get(field)
                    if rt is None and st is None:
                        continue
                    r.entry()
                    if rt is None or st is None:
                        r.diff(k, "table only in the %s" % ("ROM" if st is None else "data layer"))
                        continue
                    r.eq(k, "encounter rate", rt["rate"], st["encounter_rate"])
                    r.eq(k, "slots", rt["mons"],
                         [[m["min_level"], m["max_level"], self.num(m["species"])] for m in st["mons"]])
                if "hidden" in tabs:
                    r.diff(key, "%s: hidden table in the ROM, the data layer has no hidden area" % tname)
        r.table("wild slot rates", "ROM side: ENCOUNTER_CHANCE_* of the build, see ORACLE.md")
        flds = EN._fields()
        for area, field in (("land", "land_mons"), ("water", "water_mons"), ("rock_smash", "rock_smash_mons")):
            rates = flds[field]["encounter_rates"]
            r.entry()
            r.eq(area, "slot rates", [d["wild_rates"][area][str(i)] for i in range(len(d["wild_rates"][area]))],
                 list(rates))
        for rod in ("old_rod", "good_rod", "super_rod"):
            rates = flds["fishing_mons"]["encounter_rates"]
            idx = flds["fishing_mons"]["groups"][rod]
            r.entry()
            r.eq(rod, "slot rates", {int(k): v for k, v in d["wild_rates"][rod].items()},
                 {i: rates[i] for i in idx})
        # the table() view the pages use: raw levels, species and rates of the slots
        r.table("wild as shown", "table(): slots per map, area and time, raw levels")
        first = {}
        for e in rom:
            first.setdefault((e["group"], e["num"]), e)
        fb = K["OW_TIME_OF_DAY_FALLBACK"]
        rod_area = {"old_rod": "fishing", "good_rod": "fishing", "super_rod": "fishing"}
        for mid in EN.map_ids():
            v = self.num(mid)
            e = first.get((v >> 8, v & 0xFF))
            if e is None:
                r.diff(mid, "map has tables in the data layer, no header in the ROM")
                continue
            for ti, tname in enumerate(times):
                for area in EN.AREAS:
                    tb = EN.table(mid, area, tname)
                    ra = rod_area.get(area, area)
                    rt = e["times"][ti].get(ra) or e["times"][fb].get(ra)
                    k = "%s %s %s" % (mid, tname, area)
                    if tb is None and rt is None:
                        continue
                    r.entry()
                    if tb is None or rt is None:
                        r.diff(k, "table only in the %s" % ("ROM" if tb is None else "data layer"))
                        continue
                    rates = d["wild_rates"][area]
                    want = [[int(i), rt["mons"][int(i)][2], min(rt["mons"][int(i)][:2]), max(rt["mons"][int(i)][:2]), rates[i]]
                            for i in sorted(rates, key=int)]
                    got = [[s.index, self.num(s.species_const), s.min_level, s.max_level, s.rate] for s in tb.slots]
                    r.eq(k, "slots (index, species, min, max, rate)", want, got)
                    r.eq(k, "encounter rate", rt["rate"], tb.rate)

    # ------------------------------------------------------------ maps
    def maps(self):
        from gamedata import maps as MP
        r, d, K = self.r, self.d, self.K
        r.table("maps")
        rom = {(e["group"], e["num"]): e for e in d["maps"]}
        seen = set()
        for mid, m in sorted(MP.all_maps().items()):
            e = rom.get((m.group_index, m.map_num))
            if e is None:
                r.diff(mid, "no map header in the ROM at group %d number %d" % (m.group_index, m.map_num))
                continue
            seen.add((m.group_index, m.map_num))
            r.entry()
            r.eq(mid, "map constant", m.map_num | m.group_index << 8, K.get(mid))
            r.eq(mid, "map section", e["mapsec"], m.mapsec_num)
            r.eq(mid, "map section constant", e["mapsec"], self.num(m.mapsec))
            r.eq(mid, "map type", e["map_type"], self.num(m.map_type) if m.map_type else 0)
        for k in sorted(set(rom) - seen):
            r.diff("group %d number %d" % k, "map header in the ROM, not an active map of the data layer")
        r.table("map sections")
        rom = {int(k): v for k, v in d["mapsecs"].items()}
        for sec, name in sorted(MP._sections().items()):
            v = K.get(sec)
            if v is None or v not in rom:
                if name:
                    r.diff(sec, "named %r in the data layer, not in the ROM table" % name)
                continue
            r.entry()
            shown = MP.mapsec_name(sec)
            r.eq(sec, "name", self.nm(rom[v]["name"]) or None, self.dl(shown if shown != sec else None) or None)

    # ------------------------------------------------------------ level tables
    def scaling(self):
        from gamedata import levels as LV
        from gamedata import trainers_rematch as RM
        r, d = self.r, self.d
        s = d["scaling"]
        r.table("level rule tables")
        r.entry(len(s["johto_corridors"]))
        r.eq("sJohtoCorridors", "map sections", [c["mapsec"] for c in s["johto_corridors"]], list(LV.johto_corridor_mapsecs()))
        r.entry(len(s["band_player_levels"]))
        r.eq("sRematchBandPlayerLevels", "levels", s["band_player_levels"], list(LV.band_player_levels()))
        r.entry(len(s["trainer_evo_levels"]))
        r.eq("sTrainerEvoLevels", "species -> level", {str(a): b for a, b in s["trainer_evo_levels"]},
             {str(a): b for a, b in LV.trainer_evo_levels().items()})
        if "rematch_level_ceilings" in s:
            r.entry(len(s["rematch_level_ceilings"]))
            r.eq("sRematchLevelCeilingByBadges", "levels", s["rematch_level_ceilings"], list(RM.ceilings()))

    # ------------------------------------------------------------ trades
    def trades(self):
        r, d = self.r, self.d
        try:
            from gamedata import wild_statics as WS
            try:
                t, table = WS._trade_table(self.lang)
            except TypeError:
                t, table = WS._trade_table()
        except Exception as ex:      # loader missing or changed: say so, do not guess
            r.table("in-game trades", "not compared: %s" % ex)
            return
        r.table("in-game trades")

        def get(src, field, default=None):
            try:
                return t.field(src, field, default)
            except Exception as ex:
                raw = src.get(field)
                return "cannot be evaluated by the data layer (%s: %s; source text %r)" % (
                    type(ex).__name__, ex, raw if isinstance(raw, str) else str(raw))

        for idx, e in enumerate(d["trades"]):
            key = "trade %d" % idx
            src = table.get(idx)
            if src is None:
                r.diff(key, "only in the ROM")
                continue
            r.entry()
            r.eq(key, "species", e["species"], get(src, "species"))
            r.eq(key, "requested species", e["requested_species"], get(src, "requestedSpecies"))
            r.eq(key, "nickname", self.nm(e["nickname"]), self.dl(self.text.name(WS._string(src.get("nickname")))))
            r.eq(key, "ot name", self.nm(e["ot_name"]), self.dl(self.text.name(WS._string(src.get("otName")))))
            r.eq(key, "ivs", e["ivs"], get(src, "ivs"))
            r.eq(key, "ability number", e["ability_num"], get(src, "abilityNum", 0))
            r.eq(key, "held item", e["held_item"], get(src, "heldItem", 0))
            r.eq(key, "ot id", e["ot_id"], get(src, "otId"))
            r.eq(key, "personality", e["personality"], get(src, "personality"))
        if len(table) != len(d["trades"]):
            r.diff("table", "ROM has %d trades, data layer %d" % (len(d["trades"]), len(table)))

    def natures(self):
        r, d = self.r, self.d
        try:
            from gamedata import natures as NA
        except ImportError:
            r.table("natures", "dumped (%d), no loader in the data layer to compare; trainer natures are "
                    "compared by constant" % len(d["natures"]))
            return
        r.table("natures")
        allna = {n.id: n for n in NA.all_natures()}
        for nid, e in sorted((int(k), v) for k, v in d["natures"].items()):
            n = allna.get(nid)
            key = d["names"]["NATURE_"].get(str(nid), str(nid))
            if n is None:
                r.diff(key, "only in the ROM")
                continue
            r.entry()
            r.eq(key, "name", self.nm(e["name"]), self.dl(n.name))
            r.eq(key, "constant", nid, self.num(n.const))
            self.const_name(key, "NATURE_", nid, n.const)
            r.eq(key, "raised stat", e["stat_up"], self.num(n.up))
            r.eq(key, "lowered stat", e["stat_down"], self.num(n.down))
        for nid in sorted(set(allna) - {int(k) for k in d["natures"]}):
            r.diff(allna[nid].const, "only in the data layer")

    def run(self, only=None):
        steps = [("species", self.species), ("moves", self.moves), ("abilities", self.abilities),
                 ("items", self.items), ("types", self.types), ("natures", self.natures),
                 ("trainers", self.trainers), ("wild", self.wild), ("maps", self.maps),
                 ("scaling", self.scaling), ("trades", self.trades)]
        for name, fn in steps:
            if only and name not in only:
                continue
            fn()
        return self.r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lang", choices=("de", "en"), required=True)
    ap.add_argument("--dump", required=True, help="JSON written by rom_dump.py for the same language")
    ap.add_argument("--dump-de", help="German dump; needed with --lang en to tell translated texts from "
                    "untranslated ones (default: dump_de.json next to --dump)")
    ap.add_argument("--max", type=int, default=60, help="differences printed per table")
    ap.add_argument("--fields", action="store_true", help="also list the compared fields of every table")
    ap.add_argument("--only", nargs="*", help="species moves abilities items types natures trainers wild maps scaling trades")
    a = ap.parse_args()
    dump = json.load(open(a.dump, encoding="utf-8"))
    if dump["meta"]["lang"] != a.lang:
        raise SystemExit("dump is of language %r, asked for %r" % (dump["meta"]["lang"], a.lang))
    how = load_gamedata(a.lang)
    print("language %s (%s); dump %s" % (a.lang, ", ".join(how), a.dump))
    dump_de = None
    if a.lang != "de":
        p = a.dump_de or os.path.join(os.path.dirname(os.path.abspath(a.dump)), "dump_de.json")
        if os.path.exists(p):
            dump_de = json.load(open(p, encoding="utf-8"))
        else:
            print("warning: no German dump (%s); untranslated texts cannot be told apart" % p)
    ck = Checker(dump, a.lang, dump_de)
    rep = ck.run(a.only)
    rep.print(a.max)
    if a.fields:
        print("\ncompared fields:")
        for name, entries, fields, diffs, note in rep.tables:
            print("  %s: %s" % (name, ", ".join(sorted(fields)) or "-"))
    if ck.game_notes:
        print("\n== notes on the game data itself (ROM and data layer agree): %d ==" % len(ck.game_notes))
        for n in ck.game_notes[:a.max]:
            print("  " + n)
    if getattr(ck, "move_extra_flags", None):
        print("\nnote: the data layer's move flags also hold fields that are not yes/no flags of the "
              "game's move table: %s" % ", ".join(ck.move_extra_flags))
    sys.exit(1 if rep.total() else 0)


if __name__ == "__main__":
    main()
