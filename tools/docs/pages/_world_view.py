"""Rendering of the location pages (pages/world.py): turns the facts of
pages/_world_data.py into the components of common.html, in the language of the page.
All texts are strings of pages/world.py (ctx.t) or names from the data layer.
"""
import functools
import re

from common import html as H
from common import i18n
from gamedata import abilities as AB
from gamedata import items as IT
from gamedata import levels
from gamedata import locations as LOC
from gamedata import maprender
from gamedata import maps
from gamedata import moves as MV
from gamedata import species as SP
from gamedata import trainers as T
from gamedata import trainers_scriptdb as SDB
from gamedata import wild_maps as WM

from pages import _world_areas as A
from pages import _world_data as D

REMATCH_PAGE = "battles/rematches"
REGION_NAMES = ("Kanto", "Johto", "Hoenn")       # keys of the data layer, in story order
def region_ui(ctx, region):
    return ctx.ui("region_" + region)


def loc_name(ctx, loc):
    """Name of a location as the game shows it (the ferry: its name in the dialogue)."""
    if loc.mapsec == "MAPSEC_DYNAMIC":
        return maps.by_id(loc.key, ctx.lang).display
    return maps.mapsec_name(loc.mapsec, ctx.lang)


@functools.lru_cache(maxsize=None)
def _titles(lang):
    """{location key: page title}: the place name; places of one region that share a name get
    the places they lead to in brackets."""
    raw = {}
    for loc in LOC.all_locations():
        raw[loc.key] = (maps.by_id(loc.key, lang).display if loc.mapsec == "MAPSEC_DYNAMIC"
                        else maps.mapsec_name(loc.mapsec, lang))
    out = dict(raw)
    seen = {}
    for loc in LOC.all_locations():
        seen.setdefault((loc.region, raw[loc.key]), []).append(loc)
    for (_reg, name), locs in seen.items():
        if len(locs) < 2:
            continue
        for n, loc in enumerate(locs):
            conn, warps = D.neighbours(loc.key)
            near = [raw[k] for _d, k in conn] + [raw[k] for k in warps]
            near = [x for i, x in enumerate(near) if x not in near[:i] and x != name][:2]
            out[loc.key] = "%s (%s)" % (name, " – ".join(near)) if near else "%s (%d)" % (name, n + 1)
    # the same name in several regions (each region has its Victory Road): the region in brackets
    regions = {}
    for loc in LOC.all_locations():
        regions.setdefault(raw[loc.key], set()).add(loc.region)
    for loc in LOC.all_locations():
        if len(regions[raw[loc.key]]) > 1 and out[loc.key] == raw[loc.key]:
            out[loc.key] = "%s (%s)" % (raw[loc.key], i18n.ui(lang, "region_" + loc.region))
    return out


@functools.lru_cache(maxsize=None)
def _short_titles(lang):
    """{location key: name without the region in brackets} for lists inside one region."""
    out = {}
    for loc in LOC.all_locations():
        t = _titles(lang)[loc.key]
        tail = " (%s)" % i18n.ui(lang, "region_" + loc.region)
        out[loc.key] = t[:-len(tail)] if t.endswith(tail) else t
    return out


def short_title(ctx, loc):
    return _short_titles(ctx.lang)[loc.key]


def title(ctx, loc):
    return _titles(ctx.lang)[loc.key]


def loc_link(ctx, key, text=None):
    loc = LOC.by_key(key)
    return H.link(ctx, "location", key, text if text is not None else _titles(ctx.lang)[loc.key])


# ------------------------------------------------------------------ sub-areas
def area_labels(ctx, loc):
    """{map id: label} of the sub-areas of a location ("" = the place itself)."""
    return A.labels(ctx, loc)


def area_of(ctx, loc, mid):
    return area_labels(ctx, loc).get(mid, "")


# ------------------------------------------------------------------ wild Pokémon
def _rock_title(ctx, group):
    rock = MV.by_const("MOVE_ROCK_SMASH", ctx.lang).name
    head = MV.by_const("MOVE_HEADBUTT", ctx.lang).name
    trees, rocks = D.rock_spots(tuple(group))
    if trees and rocks:
        return ctx.t("rock_both", rock=rock, head=head), None
    return (head if trees else rock), None


def _method(ctx, area, group):
    """(component method, title or None, note or None) of an encounter area on these maps."""
    m = maps.by_id(group[0])
    if area == "land":
        if m.map_type == "MAP_TYPE_UNDERGROUND":
            return "cave", None, None
        if m.map_type == "MAP_TYPE_INDOOR":
            return "cave", ctx.t("enc_indoor"), None
        return "land", None, None
    if area == "water":
        if m.map_type == "MAP_TYPE_UNDERWATER":
            return "water", MV.by_const("MOVE_DIVE", ctx.lang).name, None
        return "water", None, None
    if area == "rock_smash":
        t, note = _rock_title(ctx, group)
        return "rock_smash", t, note
    return area, None, None


def _merge_times(blocks):
    """Tables of one method that differ by the time of day become one table: Pokémon that
    are the same at every time come first, the others carry their time of day."""
    out = []
    for b in blocks:
        prev = out[-1] if out else None
        if not (prev and b["times"] and prev.get("parts") and prev["method"] == b["method"]
                and prev["title"] == b["title"] and prev["note"] == b["note"]):
            nb = dict(b)
            nb["parts"] = [(b["times"], b["rows"])] if b["times"] else None
            out.append(nb)
            continue
        prev["parts"].append((b["times"], b["rows"]))
    for b in out:
        parts = b.pop("parts")
        if not parts or len(parts) < 2:
            continue
        key = lambda r: (r["species"].const, r["rate"])
        common = [r for r in parts[0][1] if all(any(key(r) == key(x) for x in rows) for _t, rows in parts[1:])]
        shared = {key(r) for r in common}
        rows = list(common)
        for times, part in parts:
            rows += [dict(r, times=times) for r in part if key(r) not in shared]
        b["rows"] = rows
        b["times"] = None
    return out


def wild_section(ctx, loc):
    """(HTML of the section body, [names for the search]) or ("", [])."""
    lang = ctx.lang
    clusters = D.wild_clusters(loc.key)
    if not clusters:
        return ""
    labels = area_labels(ctx, loc)
    fb = D.feebas()
    out = []
    used_times = False
    cl_labels = []
    for group in clusters:
        labs = []
        for mid in group:
            lab = labels.get(mid, "")
            if lab and lab not in labs:
                labs.append(lab)
        cl_labels.append(", ".join(labs))
    # clusters with the same label (or none) get a number
    cnt = {}
    for lab in cl_labels:
        cnt[lab] = cnt.get(lab, 0) + 1
    seen = {}
    for i, lab in enumerate(cl_labels):
        if len(clusters) > 1 and (not lab or cnt[lab] > 1):
            seen[lab] = seen.get(lab, 0) + 1
            base = lab or title(ctx, loc)
            cl_labels[i] = "%s (%d)" % (base, seen[lab]) if cnt[lab] > 1 else base
    for group, lab in zip(clusters, cl_labels):
        blocks = []
        for area, times, rows in D.cluster_blocks(tuple(group)):
            method, ttl, note = _method(ctx, area, group)
            if times:
                used_times = True
            blocks.append({"method": method, "times": times, "title": ttl,
                           "note": H.esc(note) if note else None,
                           "rows": [{"species": SP.by_id(r.species, lang), "lo": r.eff_min, "hi": r.eff_max,
                                     "rate": r.pct} for r in rows]})
        if fb and fb["map_id"] in group:
            blocks.append({"method": "super_rod", "times": None, "title": ctx.t("feebas_title"),
                           "note": H.esc(ctx.t("feebas_note", spots=fb["spots"])),
                           "rows": [{"species": SP.by_id(fb["species"], lang), "lo": fb["lo"], "hi": fb["hi"],
                                     "rate": fb["pct"]}]})
        if not blocks:
            continue
        body = H.encounters(ctx, _merge_times(blocks))
        extra = D.altering_extra(group[0])
        if extra:
            body += H.callout(ctx, "note", H.p(ctx.t("altering_note", n=extra)))
        out.append(H.sub(lab, body) if len(clusters) > 1 else body)
    if not out:
        return ""
    intro = ctx.t("wild_intro")
    if used_times:
        hrs = WM.time_hours()
        if "TIME_DAY" in hrs and "TIME_NIGHT" in hrs:
            day = [hrs[t] for t in ("TIME_MORNING", "TIME_DAY", "TIME_EVENING") if t in hrs]
            intro += " " + ctx.t("wild_times", d0=day[0][0], d1=day[-1][1], n0=hrs["TIME_NIGHT"][0],
                                 n1=hrs["TIME_NIGHT"][1])
    return H.section(ctx.t("sec_wild"), "".join(out), id="wild", intro=H.esc(intro))


# ------------------------------------------------------------------ special Pokémon
NOTE_KEYS = {
    ("PalletTown_ProfessorOaksLab_Frlg", "SPECIES_BULBASAUR"): "note_starter",
    ("PalletTown_ProfessorOaksLab_Frlg", "SPECIES_SQUIRTLE"): "note_starter",
    ("PalletTown_ProfessorOaksLab_Frlg", "SPECIES_CHARMANDER"): "note_starter",
    ("NewBarkTown_Lab_hns", "SPECIES_CHIKORITA"): "note_starter",
    ("NewBarkTown_Lab_hns", "SPECIES_CYNDAQUIL"): "note_starter",
    ("NewBarkTown_Lab_hns", "SPECIES_TOTODILE"): "note_starter",
    ("LittlerootTown_ProfessorBirchsLab", "SPECIES_TREECKO"): "note_birch",
    ("LittlerootTown_ProfessorBirchsLab", "SPECIES_TORCHIC"): "note_birch",
    ("LittlerootTown_ProfessorBirchsLab", "SPECIES_MUDKIP"): "note_birch",
    ("RuinsOfAlph_Lab_hns", "SPECIES_KABUTO"): "note_kabuto",
    ("WhirlIslands_LugiaChamber_hns", "SPECIES_LUGIA"): "note_lugia",
    ("TinTower_RoofDay_hns", "SPECIES_HO_OH"): "note_hooh",
    ("Route41_hns", "SPECIES_TENTACRUEL"): "note_tentacruel",
    ("IlexForest_hns", "SPECIES_CELEBI"): "note_celebi",
    ("LakeOfRage_hns", "SPECIES_GYARADOS"): "note_gyarados",
}


def _static_note(ctx, e, m, sp):
    key = NOTE_KEYS.get((m.dir, sp.const)) if m else None
    if not key:
        return None
    names = {"lugia": SP.by_const("SPECIES_LUGIA", ctx.lang).name,
             "hooh": SP.by_const("SPECIES_HO_OH", ctx.lang).name,
             "name": sp.name}
    if key == "note_birch":
        from gamedata import hand_completion as HC
        names["n"] = len(HC.dex_required("hoenn", ctx.lang))
    return ctx.t(key, **names)


def special_section(ctx, loc):
    """Gifts, eggs, trades, static and legendary encounters and roamers as tiles."""
    lang = ctx.lang
    ents = D.statics_by_location(lang).get(loc.key)
    if not ents:
        return ""
    labels = area_labels(ctx, loc)
    order = {"gift": 0, "egg": 1, "trade": 2, "static": 3, "legendary": 4, "roamer": 5}
    tiles = []
    for e, mid in sorted(ents, key=lambda x: (order[D.static_group(x[0])], bool(x[0].price))):
        sp = SP.by_id(e.species, lang)
        if sp is None:
            continue
        grp = D.static_group(e)
        if e.price and grp == "gift":
            grp = "prize"
        m = maps.by_id(mid) if mid else None
        notes = []
        level = None
        if e.kind == "trade":
            req = SP.by_id(e.trade["requested"], lang) if e.trade["requested"] else None
            notes.append(ctx.t("trade_for", mon=req.name) if req else ctx.t("trade_any"))
            notes.append(ctx.t("trade_names", nick=e.trade["nickname"], ot=e.trade["ot_name"]))
            held = IT.by_id(e.trade["held_item"], lang) if e.trade["held_item"] else None
            if held:
                notes.append(ctx.t("holds", item=held.name))
            level = ctx.t("trade_level")
        elif e.kind == "egg":
            level = ctx.t("egg_level")
        elif e.kind == "roamer":
            level = ctx.t("roamer_level", lv=ctx.level(e.levels[0]))
            flag = e.roamer["release_flag"]
            if flag == "FLAG_RELEASED_BEASTS":
                notes.append(ctx.t("roamer_beasts", place=maps.by_id("MAP_BURNED_TOWER_B1F_HNS", lang).display))
            elif flag == "FLAG_IS_HOENN_CHAMPION":
                notes.append(ctx.t("roamer_hoenn"))
            else:
                notes.append(ctx.t("roamer_other"))
        else:
            lv = [levels.static_level(x) for x in e.levels]
            if lv:
                level = " / ".join(ctx.level(x) for x in lv)
        if e.price:
            notes.append(ctx.t("n_coins", n=ctx.num(e.price)))
        for iid in e.items:
            it = IT.by_id(iid, lang)
            if it:
                notes.append(ctx.t("holds", item=it.name))
        if e.kind == "static_shiny" or e.shiny == "always":
            notes.append(ctx.t("always_shiny"))
        note = _static_note(ctx, e, m, sp)
        if note:
            notes.append(note)
        if m is not None and m.dir == "Route4_PokemonCenter_1F_Frlg" and sp.const == "SPECIES_MAGIKARP":
            money = D.script_money(e.sources[0][0])
            if money:
                notes.append(ctx.t("buy_for", money=ctx.money(money)))
        where = labels.get(mid, "") if mid else ""
        chips = [H.chip(ctx.t("kind_" + grp), "gold" if grp in ("legendary", "roamer") else "jade")]
        if level:
            chips.append(H.chip(level, "muted"))
        if where:
            chips.append(H.chip(where, "muted"))
        tiles.append(H.ent(ctx.url_for("species", sp.const), sp.name, media=H.mon_icon(ctx, sp),
                           meta="".join(chips), note=" · ".join(n.rstrip(".") for n in notes) if notes else None))
    if not tiles:
        return ""
    return H.section(ctx.t("sec_special"), H.ent_grid(tiles, cls="ents-wide"), id="special",
                     intro=H.esc(ctx.t("special_intro")))


def _fmt(ctx, key, **kw):
    """Module string with HTML values (the text itself is escaped)."""
    s = ctx.t(key)
    out, pos = [], 0
    for m in re.finditer(r"\{(\w+)\}", s):
        out.append(H.esc(s[pos:m.start()]))
        out.append(str(kw[m.group(1)]))
        pos = m.end()
    out.append(H.esc(s[pos:]))
    return "".join(out)


# ------------------------------------------------------------------ trainers
def trainer_name(ctx, tr):
    if D.rival_named(tr):
        return ctx.t("rival_name")
    return tr.name or tr.class_name or ""


def trainer_title(ctx, tr):
    name = trainer_name(ctx, tr)
    if tr.class_name and tr.class_name != name:
        return "%s %s" % (tr.class_name, name)
    return name


def _line(sid):
    """Species ids of the whole evolution line a species belongs to."""
    base, seen = sid, {sid}
    while True:
        prev = SP.evolves_from(base)
        if not prev or prev[0][0].id in seen:
            break
        base = prev[0][0].id
        seen.add(base)
    out, todo = set(), [base]
    while todo:
        x = todo.pop()
        if x in out:
            continue
        out.add(x)
        sp = SP.by_id(x)
        for evo in (sp.evolutions if sp else ()):
            todo.append(evo.target)
    return out


@functools.lru_cache(maxsize=None)
def _starter_line(const):
    sp = SP.by_const("SPECIES_" + const)
    return frozenset(_line(sp.id)) if sp else frozenset()


def _team(ctx, tr, b, detail):
    """([member dicts], last level or None, level range or None)."""
    lang = ctx.lang
    out = []
    if b.mode in ("leader", "phone"):
        team = T.effective_team(tr, b.map_id, b.mode, steps=b.steps)
        los, his = [], []
        for em in team.mons:
            opts = getattr(em, "species_options", None) or [em.species]
            sps = [SP.by_id(x, lang) for x in opts if x]
            sps = [x for x in sps if x is not None]
            if not sps:
                continue
            lo, hi = em.level_range
            los.append(lo)
            his.append(hi)
            m = {"species": sps[0], "level_text": ctx.level_range(lo, hi), "shiny": bool(em.mon.shiny)}
            if len(sps) > 1:
                m["note"] = ctx.t("evolves_later", names=", ".join(x.name for x in sps[1:]))
            if detail:
                _detail(ctx, m, em.mon, sps[0].id, None)
            out.append(m)
        rng = (min(los), max(his)) if los else None
        return out, None, rng
    team = T.effective_team(tr, b.map_id, "normal", count=T.party_count(tr, b.command))
    last = None
    for em in team.mons:
        sp = SP.by_id(em.species, lang) if em.species else None
        if sp is None:
            continue
        m = {"species": sp, "level": em.level, "shiny": bool(em.mon.shiny)}
        if detail:
            _detail(ctx, m, em.mon, em.species, em.level)
        out.append(m)
        last = em.level
    return out, last, None


def _detail(ctx, m, mon, sid, level):
    lang = ctx.lang
    if mon.item:
        it = IT.by_id(mon.item, lang)
        if it:
            m["item"] = it
    ab = D.ability_of(mon, sid)
    if ab:
        a = AB.by_id(ab, lang)
        if a:
            m["ability"] = a
    if mon.nature:
        n = T.nature_name(mon, lang)
        if n:
            m["nature"] = n
    if any(mon.moves):
        mv = [MV.by_id(x, lang) for x in mon.moves if x]
    elif level is not None:
        mv = [MV.by_id(x, lang) for x in D.default_moves(SP.by_id(sid), level)]
    else:
        mv = []
    mv = [x for x in mv if x]
    if mv:
        m["moves"] = mv


def _cond_chips(ctx, b):
    chips = []
    cond = SDB.title_condition(b.states) if b.states else []
    after = [k for k, v in cond if v]
    before = [k for k, v in cond if not v]
    if after:
        chips.append(H.chip(ctx.t("cond_after", region=REGION_NAMES[max(after)]), "muted"))
    if before:
        chips.append(H.chip(ctx.t("cond_before", region=REGION_NAMES[min(before)]), "muted"))
    if b.league_change:
        chips.append(H.chip(ctx.t("cond_league"), "muted"))
    if getattr(b, "daily", False):
        chips.append(H.chip(ctx.t("cond_daily"), "jade"))
    return chips


@functools.lru_cache(maxsize=None)
def visible_battles(loc_key):
    """Battles of a location that field at least one Pokémon of this build:
    (cards, phone) - cards: [Battle] shown as a card; phone: {first const: [Battle]} rematch stages."""
    cards, phone = [], {}
    for b in D.battles_by_location().get(loc_key, ()):
        tr = T.by_const(b.const)
        if tr is None or not any(SP.by_id(m.species) for m in tr.mons if m.species):
            continue
        if b.mode == "phone":
            phone.setdefault(b.row.trainer_consts[0], []).append(b)
        else:
            cards.append(b)
    have = {b.const for b in cards if b.mode == "normal"}
    phone = {k: v for k, v in phone.items() if k in have}
    return tuple(cards), phone


def _variant_key(b, tr):
    """Group key of battles that differ only by the starter chosen, or None."""
    st = D.starter_of(b.const)
    if not st:
        return None
    if not (D.role_of(tr) in ("rival", "champion") or "RIVAL" in b.const
            or b.const.startswith(("TRAINER_BRENDAN_", "TRAINER_MAY_"))):
        return None
    return (b.const.replace("_" + st, "_*", 1), b.map_id, b.mode)


def _rematch_variants(ctx, loc_cards, phone):
    """Which battles are further teams of a trainer already shown at this place.
    -> ({base battle index: [(label key, n, Battle)]}, indexes folded into another row)"""
    lang = ctx.lang
    base = {}                       # (const, map) -> index of the first normal battle
    for i, b in enumerate(loc_cards):
        if b.mode == "normal":
            base.setdefault((b.const, b.map_id), i)
    extra, folded = {}, set()
    leaders = {}                    # (map, name) -> index of the leader's first battle
    for i, b in enumerate(loc_cards):
        tr = T.by_const(b.const, lang)
        if b.mode == "normal" and D.role_of(tr) == "leader":
            leaders.setdefault((b.map_id, trainer_name(ctx, tr)), i)
    for i, b in enumerate(loc_cards):
        tr = T.by_const(b.const, lang)
        if b.mode == "special" and b.row is not None:
            j = base.get((b.row.trainer_consts[0], b.map_id))
            if j is not None:
                extra.setdefault(j, []).append(("rematch_n", b.stage[0], b))
                folded.add(i)
        elif b.mode == "leader":
            j = leaders.get((b.map_id, trainer_name(ctx, tr)))
            if j is not None:
                extra.setdefault(j, []).append(("rematch_n", None, b))
                folded.add(i)
    for j, lst in extra.items():    # number the leader rematches in the order of the game
        n = 0
        for k, (key, num, b) in enumerate(lst):
            n = num if num is not None else n + 1
            lst[k] = (key, n, b)
    return extra, folded


def trainer_section(ctx, loc):
    lang = ctx.lang
    cards, phone = visible_battles(loc.key)
    if not cards:
        return ""
    labels = area_labels(ctx, loc)
    rematch_url = ctx.url(REMATCH_PAGE)
    extra, folded = _rematch_variants(ctx, cards, phone)
    used_ids = set()
    groups, order = {}, []           # area label -> [(kind, payload, leader?)]
    variants, vorder = {}, []        # variant key -> [(starter, card html)]
    any_phone = False
    for idx, b in enumerate(cards):
        if idx in folded:
            continue
        tr = T.by_const(b.const, lang)
        detail = D.has_detail(tr) or b.mode in ("leader", "special") or D.role_of(tr) is not None
        team, last, rng = _team(ctx, tr, b, detail)
        if not team:
            continue
        meta = list(_cond_chips(ctx, b))
        notes = []
        if b.mode == "special":
            meta.append(H.chip(ctx.t("rematch_n", n=b.stage[0]), "jade"))
        elif b.mode == "leader":
            meta.append(H.chip(ctx.t("rematch"), "jade"))
            notes.append(H.esc(ctx.t("leader_note")) + _rematch_link(ctx, rematch_url))
        st = D.starter_of(b.const)
        vkey = _variant_key(b, tr)
        vlabel = None
        if vkey:
            ssp = SP.by_const("SPECIES_" + st, lang)
            line = _starter_line(st)
            mine = any(SP.by_id(m.species) and m.species in line for m in tr.mons if m.species)
            vlabel = ctx.t("tab_rival" if mine else "tab_you", name=ssp.name)
            meta.append(H.chip(ctx.t("rival_has" if mine else "you_chose", name=ssp.name), "gold"))
        rew = None
        if b.command in T.MULTI_COMMANDS:
            _partner, pteam = T.partner_team(b.partner, b.map_id)
            pname = _partner.name if _partner else ""
            foes = [T.by_const(c, lang) for c in b.opponents]
            foes = ctx.t("and").join(trainer_name(ctx, x) for x in foes if x)
            two = b.command in T.TWO_OPPONENT_COMMANDS
            notes.append(H.esc(ctx.t("multi_2v2" if two else "multi_2v1", partner=pname, foes=foes)))
            pm = []
            for em in pteam:
                x = SP.by_id(em.species, lang)
                if x:
                    pm.append("%s %s" % (H.species_link(ctx, x), H.esc(ctx.level(em.level))))
            if pm:
                notes.append(_fmt(ctx, "partner_team", partner=H.esc(pname), team=", ".join(pm)))
            if last is not None:
                rew = D.reward(tr, last, two_opponents=two)
        elif last is not None and b.mode in ("normal", "special"):
            rew = D.reward(tr, last)
        if tr.items:
            its = [IT.by_id(x, lang) for x in tr.items]
            its = [x for x in its if x]
            if its:
                notes.append(_fmt(ctx, "carries", items=", ".join(H.item_link(ctx, x) for x in its)))
        # further teams of the same trainer: gym leader rematches, fixed rematch stages, phone rematches
        more = []
        for _key, n, vb in extra.get(idx, ()):
            vtr = T.by_const(vb.const, lang)
            vteam, _vl, _vr = _team(ctx, vtr, vb, True)
            if not vteam:
                continue
            vnote = []
            if vb.mode == "leader":
                vnote.append("<p>%s%s</p>" % (H.esc(ctx.t("leader_note")), _rematch_link(ctx, rematch_url)))
            for c in _cond_chips(ctx, vb):
                vnote.append(c)
            more.append((ctx.t("rematch_n", n=n), vteam, "".join(vnote) or None))
        if b.mode == "normal" and b.const in phone:
            pn = 0
            for pb in phone[b.const]:
                ptr = T.by_const(pb.const, lang)
                pteam, _l, prng = _team(ctx, ptr, pb, D.has_detail(ptr))
                if not pteam:
                    continue
                pn += 1
                more.append((ctx.t("phone_n", n=pn), pteam, None))
            if pn:
                any_phone = True
                notes.append(H.esc(ctx.t("phone_note", n=pn)) + _rematch_link(ctx, rematch_url))
        fid = None
        if b.const not in used_ids:
            used_ids.add(b.const)
            fid = D.frag(b.const)
        card = H.trainer_card(ctx, trainer_name(ctx, tr), team, cls_name=tr.class_name, pic=tr, id=fid,
                              detail=detail, double=bool(tr.double), reward=rew, meta=meta,
                              note="".join("<p>%s</p>" % n for n in notes) if notes else None,
                              variants=more)
        last_in_group = D.role_of(tr) == "leader"
        lab = labels.get(b.map_id, "")
        if lab not in groups:
            groups[lab] = []
            order.append(lab)
        if vkey:
            if vkey not in variants:
                variants[vkey] = []
                vorder.append(vkey)
                groups[lab].append(("variant", vkey, last_in_group))
            variants[vkey].append((vlabel, card))
        else:
            groups[lab].append(("card", card, last_in_group))
    if not order:
        return ""
    out = []
    tabn = 0
    for lab in order:
        parts, run = [], []
        entries = sorted(groups[lab], key=lambda e: e[2])        # stable: the gym leader comes last
        for kind, x, _last in entries:
            if kind == "card":
                run.append(x)
                continue
            if run:
                parts.append(H.trainer_list(run))
                run = []
            vs = variants[x]
            if len(vs) == 1:
                parts.append(H.trainer_list([vs[0][1]]))
            else:
                tabn += 1
                parts.append(H.tabs([(name, H.trainer_list([c]), str(i + 1)) for i, (name, c) in enumerate(vs)],
                                    "starter-%d" % tabn, label=ctx.t("starter_tabs")))
        if run:
            parts.append(H.trainer_list(run))
        body = "".join(parts)
        if lab or len(order) > 1:
            out.append(H.sub(lab or title(ctx, loc), body))
        else:
            out.append(body)
    n = D.counts(loc.key).trainers
    intro = ctx.t("trainers_intro_1") if n == 1 else ctx.t("trainers_intro", n=n)
    if any_phone:
        intro += " " + ctx.t("trainers_phone")
    return H.section(ctx.t("sec_trainers"), "".join(out), id="trainers", intro=H.esc(intro))


def _rematch_link(ctx, url):
    if not url:
        return ""
    return ' <a href="%s">%s</a>' % (url, H.esc(ctx.t("rematch_link")))


# ------------------------------------------------------------------ items
def _tm_move(ctx, it):
    if it.tm:
        mv = MV.by_id(it.tm[2], ctx.lang)
        return mv.name if mv else None
    return None


def items_section(ctx, loc):
    lang = ctx.lang
    data = D.items_of(loc.key)
    labels = area_labels(ctx, loc)
    subs = []
    if data.found:
        entries = []
        for mid, s, n in data.found:
            it = IT.by_id(s.item, lang)
            if it is None:
                continue
            how = [x for x in (labels.get(mid, ""), _tm_move(ctx, it)) if x]
            note = []
            if s.kind == "hidden" and s.detail == "underfoot":
                note.append(ctx.t("underfoot"))
            if s.kind == "ball" and s.detail == "object":
                note.append(ctx.t("not_a_ball"))
            if n > 1:
                note.append(ctx.t("n_times", n=n))
            entries.append({"item": it, "qty": s.amount or 1, "hidden": s.kind == "hidden",
                            "how": " · ".join(how) if how else None,
                            "note": ("(%s)" % ", ".join(note)) if note else None})
        if entries:
            subs.append((ctx.t("items_found"), ctx.t("items_found_intro"), H.item_list(ctx, entries)))
    if data.gifts:
        entries = []
        for mid, s, n in data.gifts:
            it = IT.by_id(s.item, lang)
            if it is None:
                continue
            how = [x for x in (labels.get(mid, ""), _tm_move(ctx, it)) if x]
            entries.append({"item": it, "qty": s.amount or 1, "how": " · ".join(how) if how else None})
        if entries:
            subs.append((ctx.t("items_gifts"), ctx.t("items_gifts_intro"), H.item_list(ctx, entries)))
    if data.bought:
        entries = []
        for mid, s, (currency, amount) in data.bought:
            it = IT.by_id(s.item, lang)
            if it is None:
                continue
            price = ctx.money(amount) if currency == "money" else ctx.t("n_coins", n=ctx.num(amount))
            how = [x for x in (labels.get(mid, ""), _tm_move(ctx, it)) if x]
            entries.append({"item": it, "qty": s.amount or 1, "how": " · ".join(how) if how else None,
                            "note": "– " + price})
        if entries:
            subs.append((ctx.t("items_bought"), ctx.t("items_bought_intro"), H.item_list(ctx, entries)))
    if data.berries:
        entries = []
        for iid, n in data.berries:
            it = IT.by_id(iid, lang)
            if it:
                entries.append({"item": it, "qty": n})
        if entries:
            subs.append((ctx.t("items_berries"), ctx.t("items_berries_intro"), H.item_list(ctx, entries)))
    if not subs:
        return ""
    if len(subs) == 1:
        return H.section(ctx.t("sec_items"), subs[0][2], id="items", intro=H.esc(subs[0][1]))
    body = "".join(H.sub(t, '<p class="sec-intro">%s</p>' % H.esc(i) + b) for t, i, b in subs)
    return H.section(ctx.t("sec_items"), body, id="items")


def shops_section(ctx, loc):
    lang = ctx.lang
    data = D.items_of(loc.key)
    if not data.shops:
        return ""
    labels = area_labels(ctx, loc)
    out = []
    dynamic = False
    for mid, srcs in data.shops:
        entries = []
        srcs = sorted(srcs, key=lambda s: (s.detail or 0))
        for s in srcs:
            it = IT.by_id(s.item, lang)
            if it is None:
                continue
            note = None
            if s.detail:
                dynamic = True
                note = ctx.t("shop_badges_1") if s.detail == 1 else ctx.t("shop_badges", n=s.detail)
            mv = _tm_move(ctx, it)
            if mv:
                note = mv if not note else "%s · %s" % (mv, note)
            entries.append({"item": it, "price": s.price, "note": note})
        if entries:
            lab = labels.get(mid, "") or title(ctx, loc)
            tbl = H.shop_table(ctx, entries)
            out.append(H.sub(lab, tbl) if len(data.shops) > 1 else tbl)
    if not out:
        return ""
    intro = ctx.t("shops_intro")
    if dynamic:
        intro += " " + ctx.t("shops_badges_intro")
    return H.section(ctx.t("sec_shops"), "".join(out), id="shops", intro=H.esc(intro))


# ------------------------------------------------------------------ move tutors
def tutors_section(ctx, loc):
    lang = ctx.lang
    data = D.tutors_of(loc.key)
    if not data:
        return ""
    labels = area_labels(ctx, loc)
    rows = []
    any_once = any_cost = False
    for mid, t in data:
        mv = MV.by_const(t.move, lang)
        if mv is None:
            continue
        how = []
        if t.cost is not None:
            any_cost = True
            how.append(ctx.t("tutor_bp", n=ctx.num(t.cost)))
        if t.once:
            any_once = True
            how.append(ctx.t("tutor_once"))
        lab = labels.get(mid, "")
        rows.append([H.move_link(ctx, mv), H.type_chip(ctx, mv.type), H.cat_chip(ctx, mv.category),
                     H.esc(lab) if lab else None, H.esc(", ".join(how)) if how else None])
    if not rows:
        return ""
    cols = [(ctx.ui("move"), "main"), (ctx.ui("type"), ""), (ctx.ui("category"), ""), (ctx.t("col_where"), ""),
            (ctx.t("col_tutor"), "")]
    for i in (4, 3):                       # drop a column nobody fills
        if not any(r[i] for r in rows):
            cols.pop(i)
            rows = [r[:i] + r[i + 1:] for r in rows]
    intro = ctx.t("tutors_intro")
    if any_cost:
        intro += " " + ctx.t("tutors_bp_intro")
    if any_once:
        intro += " " + ctx.t("tutors_once_intro")
    return H.section(ctx.t("sec_tutors"), H.table(cols, rows), id="tutors", intro=H.esc(intro))


# ------------------------------------------------------------------ overview
def gate_note(ctx, loc):
    """The gate between Kanto and Johto: when it opens (gamedata.hand_progress)."""
    if loc.mapsec != "MAPSEC_VICTORY_ROAD_HNS":
        return ""
    from gamedata import hand_progress as HP
    f = HP.kanto_to_johto(ctx.lang)
    text = ctx.t("gate_note", route22=f["route22"], route26=f["route26"], oak_lab=f["oak_lab"],
                 gs_ball=f["gs_ball"], elm_town=f["elm_town"])
    return H.callout(ctx, "note", H.p(text))


def _map_pictures(ctx, loc):
    """[(label, url, width px, height px)]: the outdoor maps of the place joined along their
    connections, or every floor when it has no outdoor map."""
    ms = [maps.by_id(mid, ctx.lang) for mid in loc.map_ids]
    labels = area_labels(ctx, loc)
    seen, kept = set(), []
    for m in ms:
        family = re.sub(r"(Day|Night|LowTide|HighTide)(?=_|$)", "", m.dir)     # one picture per variant family
        if family not in seen:
            seen.add(family)
            kept.append(m)
    by_dir = {m.dir: m for m in kept}
    outdoor = [m for m in kept if LOC._outdoor(m)]
    found = maprender.groups([m.dir for m in outdoor or kept])
    if outdoor:
        # a roof or yard of a building does not stand for the place when the place itself has a map
        found = [g for g in found if any(not labels.get(by_dir[d].id) for d, _x, _y in g)] or found
    out = []
    for g in found:
        w, h = maprender.group_size(g)
        label = next((labels.get(by_dir[d].id, "") for d, _x, _y in g if not labels.get(by_dir[d].id)), None)
        if label is None:
            label = labels.get(by_dir[g[0][0]].id, "")
        out.append((label, ctx.asset("map", maprender.group_slug(g)), w * 16, h * 16))
    return out


def _map_figure(ctx, loc, pic, cls, caption):
    label, src, w, h = pic
    alt = ctx.t("map_alt", place=label or _titles(ctx.lang)[loc.key])
    cap = "<figcaption>%s</figcaption>" % H.esc(label) if caption and label else ""
    return ('<figure class="%s">%s<a href="%s" title="%s"><img src="%s" width="%d" height="%d" alt="%s" '
            'loading="lazy" decoding="async"></a></figure>'
            % (cls, cap, src, H.esc(ctx.t("map_open")), src, w, h, H.esc(alt)))


def map_side(ctx, loc):
    """The small map next to the overview; a click opens it at full size."""
    pics = _map_pictures(ctx, loc)
    return _map_figure(ctx, loc, pics[0], "map map-side", len(pics) > 1) if pics else ""


def map_section(ctx, loc):
    """All pictures of a place that has more than one (floors, separate areas)."""
    pics = _map_pictures(ctx, loc)
    if len(pics) < 2:
        return ""
    return H.section(ctx.t("sec_maps"), "".join(_map_figure(ctx, loc, p, "map", True) for p in pics), id="map")


def overview(ctx, loc):
    conn, warps = D.neighbours(loc.key)
    pairs = [(ctx.ui("region"), H.page_link(ctx, "world/" + loc.region, region_ui(ctx, loc.region)))]
    for d in ("north", "east", "south", "west"):
        there = [k for dd, k in conn if dd == d]
        if there:
            pairs.append((ctx.t("dir_" + d), ", ".join(loc_link(ctx, k) for k in there)))
    if warps:
        pairs.append((ctx.t("k_access"), ", ".join(loc_link(ctx, k) for k in warps)))
    fac = D.facilities(loc.key)
    if fac:
        pairs.append((ctx.t("k_facilities"), H.esc(", ".join(ctx.t("fac_" + f) for f in fac))))
    return H.kv(pairs)


def facts_text(ctx, loc):
    c = D.counts(loc.key)
    bits = []
    if c.wild:
        bits.append(ctx.t("n_wild", n=c.wild))
    if c.trainers:
        bits.append(ctx.t("n_trainers_1") if c.trainers == 1 else ctx.t("n_trainers", n=c.trainers))
    if c.items:
        bits.append(ctx.t("n_items_1") if c.items == 1 else ctx.t("n_items", n=c.items))
    return " · ".join(bits)
