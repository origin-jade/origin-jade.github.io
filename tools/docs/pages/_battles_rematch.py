"""battles/rematches: the phone rematch system and every rematch trainer.

Rules mirrored (constants are read from the C sources below, each with a shape check
that stops the build when the code changes):
  * registering: RegisterTrainerInMatchCall (src/battle_setup.c);
  * who asks for a rematch and when: TryUpdateRandomTrainerRematches /
    UpdateRandomTrainerRematches, IncrementRematchStepCounter, HasEnoughBadgesForRematchOf
    (src/battle_setup.c); HnsUpdateRouteStepCounter, TryStartMatchCall,
    SelectMatchCallTrainer and the gift table sHnsMatchCallTrainers (src/match_call.c);
  * which team: GetMaxRematchStageForBadges, GetRematchTrainerIdFromTable
    (through gamedata.trainers_rematch);
  * which levels: ApplyRematchLevelBand with REMATCH_BAND_PLAYER_LEVELS (gamedata.levels);
  * Hoenn leaders: UpdateGymLeaderRematch (src/gym_leader_rematch.c) and its two callers
    in src/battle_setup.c.
"""
import functools
import re

from common import html as H
from gamedata import hand_menus
from gamedata import items as IT
from gamedata import levels
from gamedata import repo_path
from gamedata import species as SP
from gamedata import trainers as T
from gamedata import trainers_rematch as RM

from pages import _battles_data as D
from pages import _battles_view as V

PATH = "battles/rematches"
CALL_OPTION_DE = "Anrufe"     # name of the option in the German options menu (finds its position)


class RuleError(RuntimeError):
    pass


def _src(*path):
    return open(repo_path(*path), encoding="utf-8").read()


def _need(src, pattern, what):
    m = re.search(pattern, src, re.S)
    if not m:
        raise RuleError("rematch rules changed shape: " + what)
    return m


@functools.lru_cache(maxsize=None)
def call_rules():
    """Numbers of the rematch call rules, read from the C sources:
    steps (walking counter of the map-visit rule), chance (percent per trainer on a map
    visit), route_steps (steps on the trainer's own map before a call from there),
    gift_one_in (a gift instead of a rematch: one call in N), call_steps / call_minutes /
    call_chance / call_chance_ability (random calls: checked every N steps, at most one
    per M minutes, percent, percent with the ability that doubles it; ability constant),
    home_percent (caller from the current region), away_rematch (percent that a caller
    elsewhere asks for a rematch), leader_trainer_battles / leader_wild_battles /
    leader_chance (Hoenn leaders)."""
    bs = _src("src", "battle_setup.c")
    mc = _src("src", "match_call.c")
    gl = _src("src", "gym_leader_rematch.c")
    out = {}
    out["steps"] = int(_need(bs, r"#define STEP_COUNTER_MAX (\d+)", "STEP_COUNTER_MAX").group(1))
    out["chance"] = int(_need(bs, r"IsRematchRegistered\(i\) && \(\(Random\(\) % 100\) <= (\d+)\)",
                              "map visit chance").group(1)) + 1
    for needle in ("if (IsRematchStepCounterMaxed() && UpdateRandomTrainerRematches(gRematchTable, mapGroup, mapNum) == TRUE)",
                   "if (!HasEnoughBadgesForRematchOf(i))",
                   "if (FlagGet(FLAG_HAS_MATCH_CALL) && TRAINER_BATTLE_PARAM.opponentA != TRAINER_NONE)",
                   "SetRematchRegistered(rematchIdx);"):
        if needle not in bs:
            raise RuleError("src/battle_setup.c: rematch rule missing: " + needle)
    out["route_steps"] = int(_need(mc, r"#define ROUTE_STEP_COUNTER_MAX (\d+)", "ROUTE_STEP_COUNTER_MAX").group(1))
    out["gift_one_in"] = int(_need(mc, r"itemFlag != 0 && \(Random\(\) % (\d+)\) == 0", "gift chance").group(1))
    out["call_steps"] = int(_need(mc, r"#if IS_HNS\s+if \(\+\+sMatchCallState\.stepCounter >= (\d+)\)",
                                  "call step counter").group(1))
    m = _need(mc, r"curMinutes - sMatchCallState\.minutes > \(UseFakeRtc\(\) \? (\d+) : (\d+)\)", "call minutes")
    out["call_minutes"] = int(m.group(2)) + 1
    out["call_minutes_fast"] = int(m.group(1)) + 1
    m = _need(mc, r"int callChance = 1;.*?GetMonAbility\(&gPlayerParty\[0\]\) == (ABILITY_\w+)\)\s*"
                  r"callChance = (\d+);\s*if \(Random\(\) % 10 < callChance \* (\d+)\)", "call chance")
    out["call_ability"] = m.group(1)
    out["call_chance"] = int(m.group(3)) * 10
    out["call_chance_ability"] = int(m.group(3)) * int(m.group(2)) * 10
    for needle in ("fromHome = (Random() % 100) < OW_MATCH_CALL_HOME_REGION_PERCENT;",
                   "if (!TrainerIsEligibleForRematch(i) && (Random() % 100) < OW_MATCH_CALL_REMATCH_CHANCE)",
                   "&& HnsMapAllowsMatchCall()"):
        if needle not in mc:
            raise RuleError("src/match_call.c: call rule missing: " + needle)
    t = RM._t()
    out["home_percent"] = t.need("OW_MATCH_CALL_HOME_REGION_PERCENT")
    out["away_rematch"] = t.need("OW_MATCH_CALL_REMATCH_CHANCE")
    out["leader_trainer_battles"] = int(_need(
        bs, r"GetGameStat\(GAME_STAT_TRAINER_BATTLES\) % (\d+) == 0\)\s*UpdateGymLeaderRematch\(\);",
        "leader rematch, trainer battles").group(1))
    out["leader_wild_battles"] = int(_need(
        bs, r"GetGameStat\(GAME_STAT_WILD_BATTLES\) % (\d+) == 0\)\s*UpdateGymLeaderRematch\(\);",
        "leader rematch, wild battles").group(1))
    out["leader_chance"] = int(_need(
        gl, r"FlagGet\(FLAG_IS_HOENN_CHAMPION\) && \(Random\(\) % 100\) <= (\d+)\)", "leader chance").group(1)) + 1
    return out


@functools.lru_cache(maxsize=None)
def gifts():
    """[(trainer const, [item const])] of the trainers who sometimes call with an item
    (sHnsMatchCallTrainers entries with a gift list, src/match_call.c), table order."""
    mc = _src("src", "match_call.c")
    lists = {m.group(1): re.findall(r"ITEM_\w+", m.group(2))
             for m in re.finditer(r"static const u16 (s\w+GiftItems)\[\] = \{([^}]*)\};", mc)}
    out = []
    for m in re.finditer(r"HNS_MC_ITEM\d\(\w+,\s*(TRAINER_\w+),\s*FLAG_\w+,\s*VAR_\w+,\s*(s\w+GiftItems)\)", mc):
        if m.group(2) in lists:
            out.append((m.group(1), lists[m.group(2)]))
    return out


@functools.lru_cache(maxsize=None)
def _call_option_pos():
    for ti, tab in enumerate(hand_menus.option_tabs("de")):
        for ii, item in enumerate(tab.items):
            if item.name_game == CALL_OPTION_DE:
                return ti, ii
    return None


def call_option(ctx):
    """(option name, name of the choice that turns calls off) in the page language."""
    pos = _call_option_pos()
    if pos is None:
        return None
    item = hand_menus.option_tabs(ctx.lang)[pos[0]].items[pos[1]]
    if len(item.choices) < 2:
        return None
    return item.name, item.choices[1].name


@functools.lru_cache(maxsize=None)
def phone_persons():
    """{region: [person]} of the trainers with phone rematches (normal table rows), story order."""
    out = {}
    for es in D.groups():
        if any(e.mode == "phone" for e in es):
            out.setdefault(levels.reader_region(es[0].map_id), []).append(es)
    return out


@functools.lru_cache(maxsize=None)
def person_of_const():
    out = {}
    for es in D.groups():
        for e in es:
            out.setdefault(e.const, es)
    return out


def _stage_cell(ctx, es):
    """The rematch teams of a person: one line per team; consecutive teams that read the
    same (same Pokémon, same start, same levels) share a line."""
    lines = []          # [first stage, last stage, start step, (lo, hi), names html]
    for e in es:
        if e.mode != "phone":
            continue
        tm = D.team_of(e)
        names = []
        lo_all, hi_all = 10 ** 6, 0
        for em in tm.mons:
            sps = [SP.by_id(s, ctx.lang) for s in em.species_options if s]
            if not sps or any(s is None for s in sps):
                V._missing.add((e.const, em.mon.species_const))
                continue
            names.append(" / ".join(H.species_link(ctx, s) for s in sps))
            lo_all, hi_all = min(lo_all, em.level_range[0]), max(hi_all, em.level_range[1])
        if not names:
            continue
        row = [e.stage[0], e.stage[-1], min(e.steps), (lo_all, hi_all), ", ".join(names)]
        if lines and lines[-1][2:] == row[2:] and lines[-1][1] + 1 == row[0]:
            lines[-1][1] = row[1]
        else:
            lines.append(row)
    out = []
    for a, b, step, (lo, hi), names in lines:
        label = ctx.t("v_rematch_n", n=a) if a == b else ctx.t("v_rematch_range", a=a, b=b)
        out.append("%s · %s · %s" % (
            H.esc(label), H.esc(ctx.t("from_step", step=V.step_text(ctx, step))),
            H.esc(ctx.level_range(lo, hi))))
    return "<br>".join(out)


def _region_cards(ctx, region, persons):
    """One table row per trainer: who, where, the level of the first battle, when each rematch
    team becomes available. The teams themselves are on the trainer's place page."""
    rows, attrs = [], []
    for es in persons:
        h = D.head_entry(es)
        tr = V.trainer(ctx, h.const)
        name = V.trainer_name(ctx, tr)
        place = V.place_name(ctx, h.map_id)
        rows.append([V.trainer_link(ctx, es, name), H.esc(tr.class_name or ""), V.place_link(ctx, h.map_id),
                     H.esc(ctx.level(D.max_level(h))), _stage_cell(ctx, es)])
        attrs.append(H.filter_attrs([name, tr.class_name or "", place], region=V.REGION_KEY.get(region)))
    return H.table([(ctx.ui("trainer"), "main"), ctx.t("col_class"), ctx.ui("location"),
                    (ctx.t("col_first"), "min"), ctx.t("col_rematches")], rows, row_attrs=attrs)


def _gift_table(ctx):
    rows = []
    by_const = person_of_const()
    for const, item_consts in gifts():
        es = by_const.get(const)
        tr = V.trainer(ctx, const)
        if tr is None or es is None:
            continue
        its = [IT.by_const(c, ctx.lang) for c in item_consts]
        its = [x for x in its if x is not None]
        if not its:
            continue
        name = V.trainer_name(ctx, tr)
        rows.append(["%s <span class=\"none\">%s</span>" % (V.trainer_link(ctx, es, name), H.esc(tr.class_name or "")),
                     V.place_link(ctx, D.head_entry(es).map_id),
                     " ".join(H.item_link(ctx, x, icon=True) for x in its)])
    if not rows:
        return ""
    return H.table([(ctx.ui("trainer"), "main"), ctx.ui("location"), ctx.t("col_gifts")], rows)


def render(ctx):
    t = ctx.t
    ctx.begin(PATH)
    rules = call_rules()
    need = RM.badge_count_needed()
    plo, phi = levels.phone_band()
    llo, lhi = levels.leader_band()
    how = H.steps([H.esc(t("how_1")), H.esc(t("how_2", need=need)), H.esc(t("how_3")), H.esc(t("how_4"))])
    body = [H.section(t("sec_how"), how, id="how", intro=H.esc(t("how_intro")))]

    # ---- when a trainer gets in touch
    from gamedata import abilities as AB
    ab = AB.by_const(rules["call_ability"], ctx.lang)
    # the texts say "more often" and "usually" instead of the numbers
    if not (rules["call_chance_ability"] > rules["call_chance"] and rules["home_percent"] > 50
            and 0 < rules["away_rematch"] < 100):
        raise ValueError("rematch calls: the call rules changed, review the call texts")
    calls = [
        H.esc(t("call_map", steps=rules["steps"], chance=rules["chance"])),
        H.esc(t("call_route", steps=rules["route_steps"])),
        V.fmt(ctx, "call_random", every=rules["call_steps"], minutes=rules["call_minutes"],
              fast=rules["call_minutes_fast"],
              chance=rules["call_chance"], chance2=rules["call_chance_ability"],
              ability=H.ability_link(ctx, ab) if ab else "", home=rules["home_percent"],
              rematch=rules["away_rematch"]),
    ]
    inner = H.prose(H.ul(calls))
    opt = call_option(ctx)
    if opt:
        inner += H.callout(ctx, "tip", "<p>%s</p>" % H.esc(t("call_option", option=opt[0], off=opt[1])))
    else:
        ctx.todo("battles/rematches: the option that turns phone calls off was not found in the options menu")
    gt = _gift_table(ctx)
    if gt:
        inner += H.sub(t("sub_gifts"), H.prose("<p>%s</p>" % H.esc(t("gifts_intro", n=rules["gift_one_in"]))) + gt,
                       id="gifts")
    body.append(H.section(t("sec_calls"), inner, id="calls", intro=H.esc(t("calls_intro"))))

    # ---- which team
    body.append(H.section(t("sec_teams"), H.prose("".join("<p>%s</p>" % H.esc(t(k)) for k in (
        "teams_p1", "teams_p2", "teams_p3"))), id="teams"))

    # ---- level band
    steps = levels.band_steps()
    rows = []
    for s in levels.reachable_steps():
        p = steps[s].player_level
        phone = H.esc(ctx.level_range(max(2, p + plo), p + phi)) if s >= need else None
        leader = H.esc(ctx.level_range(p + llo, min(100, p + lhi))) if s >= levels.TITLE_STEPS[0] else None
        rows.append([H.esc(V.step_text(ctx, s)), H.esc(str(p)), phone, leader])
    band = H.prose("<p>%s</p><p>%s</p><p>%s</p>" % (
        H.esc(t("band_p1", lo=-phi, hi=-plo)), H.esc(t("band_p2")),
        H.esc(t("band_p3", n=len(steps), need=need)))) + H.table(
        [(t("col_progress"), "main"), (t("col_p"), "num"), (t("col_phone_ace"), "num"),
         (t("col_leader_ace"), "num")], rows, stack=False)
    body.append(H.section(t("sec_band"), band, id="levels", intro=H.esc(t("band_intro"))))

    # ---- other rematches
    other = H.ul([
        V.fmt(ctx, "other_kanto", lo=llo, hi=lhi, page=H.page_link(ctx, "battles/kanto", V.region_name(ctx, "Kanto"))),
        V.fmt(ctx, "other_johto", page=H.page_link(ctx, "battles/johto", V.region_name(ctx, "Johto"))),
        V.fmt(ctx, "other_hoenn", page=H.page_link(ctx, "battles/hoenn", V.region_name(ctx, "Hoenn")),
              tb=rules["leader_trainer_battles"], wb=rules["leader_wild_battles"], chance=rules["leader_chance"]),
    ])
    body.append(H.section(t("sec_other"), H.prose(other), id="leaders", intro=H.esc(t("other_intro"))))

    # ---- the list
    pp = phone_persons()
    total = sum(len(v) for v in pp.values())
    bar = H.filter_bar(ctx, "rematch-list", placeholder=t("rematch_placeholder"), facets=[H.region_facet(ctx)])
    tables = []
    for region in V.REGIONS:
        persons = pp.get(region, [])
        if not persons:
            continue
        tables.append('<div data-group="%s">%s</div>' % (V.REGION_KEY[region], H.sub(
            "%s (%s)" % (V.region_name(ctx, region), ctx.num(len(persons))),
            _region_cards(ctx, region, persons), id="list-" + V.REGION_KEY[region])))
    body.append(H.section(t("sec_list"), bar + '<div id="rematch-list">%s</div>' % "".join(tables), id="trainers",
                          intro=H.esc(t("list_intro", n=ctx.num(total)))))
    ctx.end("".join(body), lead=H.esc(t("lead_rematches", n=ctx.num(total))), prev="battles/rivals",
            next="battles/trainers")
