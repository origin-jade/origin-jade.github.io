"""Which rematch team (stage) the game offers when, and at which progress steps.

Mirrors src/battle_setup.c (IS_HNS):
    GetMaxRematchStageForBadges  stage 1 always; stage i >= 2 only while every stage
                                 2..i has a data-level maximum (GetTrainerPartyMaxLevel)
                                 <= sRematchLevelCeilingByBadges[badges of the trainer's
                                 region]; after that region's title every stage is open
    GetRematchTrainerIdFromTable the first stage not beaten yet, up to that maximum
    HasEnoughBadgesForRematchOf  a phone trainer asks only once his own region
                                 (GetRegionForSectionId of the row's map) has
                                 OW_REMATCH_BADGE_COUNT badges
    IsRematchForbidden           Elite Four rows (>= REMATCH_ELITE_FOUR_ENTRIES): only
                                 after FLAG_IS_HOENN_CHAMPION; Wally: after his Victory Road battle
    UpdateGymLeaderRematch       (src/gym_leader_rematch.c) Hoenn leaders: only after
                                 FLAG_IS_HOENN_CHAMPION

Progress steps are those of GetRematchProgressStep (levels.band_steps): Kanto badges
0-8 = steps 0-8; with the Kanto title 10 + Johto badges (10-18); with the Johto title
20 + Hoenn badges (20-28); Hoenn title 29. Steps 9 and 19 do not occur in the game
(levels.reachable_steps). The regions are played in that order, so a trainer of region
R with b badges of R stands at step offset(R) + b, and R's title is step
levels.TITLE_STEPS (10, 20, 29).

    trainers_rematch.row_stages(row) -> [Stage(index, const, unlock_step, steps)]
        index 1..4 (trainerIds[1..4]), unlock_step = first progress step at which the
        stage can be offered, steps = the reachable steps from unlock_step on
    trainers_rematch.region_offset("Johto") -> 10
    trainers_rematch.ceilings() -> sRematchLevelCeilingByBadges
    trainers_rematch.step_label(step, lang) / steps_label(steps, lang) -> progress text of the site
        ("Johto: 3 Orden" / "Johto: 3 badges"; STRINGS holds the wording, not game text)
    trainers_rematch.step_fact(step) -> (region, badges, title) for pages that word it themselves
"""
import functools

from . import tu as TU
from . import maps
from . import levels
from . import trainers

SRC = "src/battle_setup.c"
OFFSETS = {"Kanto": 0, "Johto": 10, "Hoenn": 20}


class Stage:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "Stage(%d %s from %d)" % (self.index, self.const, self.unlock_step)


def _t():
    return TU.load(SRC, lang="de")


@functools.lru_cache(maxsize=None)
def ceilings():
    """sRematchLevelCeilingByBadges (index = badges of the trainer's region)."""
    return [int(x) for x in _t().array("sRematchLevelCeilingByBadges")]


@functools.lru_cache(maxsize=None)
def badge_count_needed():
    """OW_REMATCH_BADGE_COUNT (include/config/overworld.h, IS_HNS branch)."""
    return _t().need("OW_REMATCH_BADGE_COUNT")


def rematches_count():
    return _t().need("REMATCHES_COUNT")


def region_of_row(row):
    m = maps.by_id(row.map_id) if row.map_id else None
    r = m.region if m else "Kanto"
    return r if r in OFFSETS else "Kanto"   # GetRegionBadgeCount: default = Kanto


def region_offset(region):
    return OFFSETS.get(region, 0)


def _party_max(const):
    tr = trainers.by_const(const)
    return max((m.level for m in tr.mons), default=0) if tr else 0


def max_stage(row, badges):
    """GetMaxRematchStageForBadges before the region's title."""
    ids = row.trainer_consts
    ceil = ceilings()[min(badges, len(ceilings()) - 1)]
    best = 1
    for i in range(2, rematches_count()):
        if i >= len(ids) or not ids[i] or ids[i] == "TRAINER_NONE":
            break
        if _party_max(ids[i]) > ceil:
            break
        best = i
    return best


def _title_step(region):
    """First progress step with the title of that region (10, 20, 29)."""
    return levels.TITLE_STEPS[("Kanto", "Johto", "Hoenn").index(region)]


def row_stages(row):
    """Stages 1..REMATCHES_COUNT-1 of a gRematchTable row with the first progress step
    at which each can be offered (see module doc)."""
    region = region_of_row(row)
    off = region_offset(region)
    need = badge_count_needed()
    out = []
    for i in range(1, min(rematches_count(), len(row.trainer_consts))):
        unlock = None
        if row.special:
            unlock = _title_step(region)  # Hoenn leaders / Elite Four / Wally: after the Hoenn title
        else:
            for b in range(need, 9):
                if i <= max_stage(row, b):
                    unlock = off + b
                    break
            if unlock is None:
                unlock = _title_step(region)   # the region's title opens every stage
        out.append(Stage(index=i, const=row.trainer_consts[i], unlock_step=unlock,
                         steps=[x for x in levels.reachable_steps() if x >= unlock]))
    return out


STRINGS_DE = {
    "badges": "{region}: {n} Orden",
    "badges_1": "{region}: 1 Orden",
    "title": "{region}-Titel",
    "range": "{a} bis {b}",
    "from": "ab {a}",
}
STRINGS_EN = {
    "badges": "{region}: {n} badges",
    "badges_1": "{region}: 1 badge",
    "title": "{region} title",
    "range": "{a} to {b}",
    "from": "from {a}",
}
# Site wording (not game text) of the progress labels, per language.
STRINGS = {"de": STRINGS_DE, "en": STRINGS_EN}


def _strings(lang, S):
    return S if S is not None else STRINGS[TU.lang(lang)]


def step_fact(step):
    """(region, badges, title) of a progress step - the facts behind step_label.
    region/badges: the region whose badges count at that step and how many; title:
    True on the Hoenn title step (29) and on the two table entries the game skips
    (9, 19). Steps 10-18 mean "Kanto title held", 20-28 "Johto title held"
    (levels.band_steps()[step].titles)."""
    s = levels.band_steps()[step]
    return s.region, s.badges, bool(s.title)


_REGIONS = ("Kanto", "Johto", "Hoenn")


def step_label(step, lang=None, S=None):
    """Site wording of a progress step: "Kanto: 3 Orden", "Kanto-Titel" (step 10: the
    Kanto title is held and no Johto badge yet; also the skipped entry 9),
    "Johto: 3 Orden" (steps 11-18; the Kanto title is implied by the play order),
    "Hoenn-Titel" (29)."""
    if isinstance(lang, dict):          # old call form step_label(step, STRINGS_DE)
        lang, S = None, lang
    S = _strings(lang, S)
    s = levels.band_steps()[step]
    if s.title:
        return S["title"].format(region=s.region)
    if s.badges == 0 and s.titles:
        return S["title"].format(region=_REGIONS[s.titles - 1])
    if s.badges == 1:
        return S["badges_1"].format(region=s.region)
    return S["badges"].format(region=s.region, n=s.badges)


def steps_label(steps, lang=None, S=None):
    if isinstance(lang, dict):
        lang, S = None, lang
    S = _strings(lang, S)
    steps = sorted(levels.game_step(x) for x in set(steps))
    steps = sorted(set(steps))
    if not steps:
        return ""
    if steps[-1] == 29 and steps[0] != 29 and steps == [x for x in levels.reachable_steps() if x >= steps[0]]:
        return S["from"].format(a=step_label(steps[0], S=S))
    if len(steps) == 1:
        return step_label(steps[0], S=S)
    return S["range"].format(a=step_label(steps[0], S=S), b=step_label(steps[-1], S=S))
