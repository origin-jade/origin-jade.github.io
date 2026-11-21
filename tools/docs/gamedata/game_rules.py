"""Rules behind the challenge menu, the level caps and obedience, read from the source.

    game_rules.challenge_item(tab_const, item_const, lang) -> hand_menus.Item
        the entry of the challenge menu at sTabs[TAB_*] / sTabItems_*[ITEM_*]
    game_rules.challenge_rules() -> {(tab index, position in hand_menus' item list): Rule}
        Rule.lock     "free" | "down" | "full": sMidGameLockPolicy (src/challenge_menu.c).
                      "down": after the start of the game the choice can only move to an
                      earlier entry of its list (ProcessLeftRight); "full": not at all.
        Rule.default  index of the choice a new game starts with
                      (SetDefaultChallengeSettings in src/new_game.c and the way
                      CB2_InitChallengeMenu turns the stored values into list positions)
    game_rules.recommended() -> {position in the first tab: choice index} ApplyRecommendedPresets
    game_rules.one_type_types() -> [TYPE_* names] in the order of the "one type" option
    game_rules.level_caps() -> {"normal": [9 levels], "hard": [9 levels], "after_first_title": n,
                                "max": MAX_LEVEL}   (src/caps.c GetCurrentLevelCap)
    game_rules.obedience() -> {"first": [9 levels], "second": [9 levels]}
                              (src/battle_util.c GetObedienceLevel)

Every statement is pinned to the code with hand_facts.require(), so a change there stops
the build instead of leaving the pages stale.
"""
import functools
import re

from . import tu as TU
from . import hand_facts as F
from . import hand_menus
from . import dex_options

MENU = "src/challenge_menu.c"
NEW_GAME = "src/new_game.c"
TABS = ("TAB_MODE", "TAB_FEATURES", "TAB_RANDOMIZER", "TAB_NUZLOCKE", "TAB_DIFFICULTY", "TAB_CHALLENGES")


class Rule:
    def __init__(self, lock, default):
        self.lock, self.default = lock, default

    def __repr__(self):
        return "Rule(%s, %d)" % (self.lock, self.default)


def _t():
    return TU.load(MENU, lang="de")


@functools.lru_cache(maxsize=None)
def _positions():
    """{tab index: [item index in sTabItems_* of every entry hand_menus keeps]}."""
    t = _t()
    out = {}
    for ti, entry in sorted(t.table("sTabs").items()):
        sym = [x for x in [v for _, v in entry.items][1] if x not in ("(", ")", "&")][0]
        out[ti] = [ii for ii, it in sorted(t.table(sym).items()) if (t.field(it, "numChoices") or 0)]
    tabs = hand_menus.challenge_tabs("de")
    if [len(v) for _, v in sorted(out.items())] != [len(tab.items) for tab in tabs]:
        raise TU.DataError("%s: tab tables and menu entries differ" % MENU)
    for name in TABS:
        if t.need(name) not in out:
            raise TU.DataError("%s: tab %s missing" % (MENU, name))
    return out


def position(tab_const, item_const):
    """(tab index, position in hand_menus' item list) of an entry."""
    t = _t()
    ti, ii = t.need(tab_const), t.need(item_const)
    pos = _positions()[ti]
    if ii not in pos:
        raise TU.DataError("%s: %s is not an entry with choices" % (MENU, item_const))
    return ti, pos.index(ii)


def challenge_item(tab_const, item_const, lang=None):
    ti, p = position(tab_const, item_const)
    return hand_menus.challenge_tabs(lang)[ti].items[p]


@functools.lru_cache(maxsize=None)
def recommended():
    return {position("TAB_MODE", const)[1]: idx for const, idx in dex_options._recommended().items()}


@functools.lru_cache(maxsize=None)
def challenge_rules():
    t = _t()
    F.require(MENU, r"if \(sIsInitialSetup\)\s*return LOCK_FREE;")
    F.require(MENU, r"GetLockPolicy\(sMenu->currentTab, itemIndex\) == LOCK_ONEWAY_DOWN && \*sel > prev")
    names = {t.need("LOCK_FREE"): "free", t.need("LOCK_ONEWAY_DOWN"): "down", t.need("LOCK_FULL"): "full"}
    width = t.need("MAX_ITEMS_PER_TAB")
    policy = {}
    for idx, tokens in t.table("sMidGameLockPolicy").items():
        v = t.value(tokens)
        if v not in names:
            raise TU.DataError("%s: lock policy %r not handled" % (MENU, tokens))
        policy[idx] = names[v]

    # A new game: every stored value is 0 except the ones SetDefaultChallengeSettings sets.
    for field in ("Modern_Moves", "Synchronize", "Sturdy", "New_Citrus", "Fairy_Types", "Legendary_Abilities",
                  "InfiniteTMs", "Mints", "PoisonSurvive"):
        F.require(NEW_GAME, r"challengeSettings\.tx_Mode_%s\s*= 1;" % field)
    F.require(NEW_GAME, r"challengeSettings\.optionStyle = 0;")
    F.require(NEW_GAME, r"challengeSettings\.genOneRecharge = 0;")
    F.require(NEW_GAME, r"challengeSettings\.tx_Challenges_OneTypeChallenge = ONE_TYPE_OFF;")
    F.require(NEW_GAME, r"challengeSettings\.tx_Random_Similar\s*= 1;")
    F.require(NEW_GAME, r"challengeSettings\.tx_Random_MapBased\s*= 1;")
    for field in ("SpeciesClause", "ShinyClause", "Nicknaming"):
        F.require(NEW_GAME, r"challengeSettings\.tx_Nuzlocke_%s\s*= 1;" % field)
        F.require(MENU, r"= !cs->tx_Nuzlocke_%s;" % field)
    F.require(MENU, r"ITEM_RANDOM_SIMILAR\)\s*= !cs->tx_Random_Similar;")
    F.require(MENU, r"ITEM_RANDOM_MAP_BASED\)\s*= cs->tx_Random_MapBased;")
    F.require(MENU, r"ITEM_NUZLOCKE_RARE_CANDY\)\s*= !cs->tx_Nuzlocke_RareCandy;")
    F.require(MENU, r"ITEM_MODE_SPLIT\)\s*= !cs->optionStyle;")
    F.require(MENU, r"oneTypeSel = 19; // OFF")
    if re.search(r"challengeSettings\.tx_(?:Nuzlocke_RareCandy|Nuzlocke_Deletion|Features_Shiny\w+|Challenges_(?!OneType)\w+|Difficulty_\w+)\s*=",
                 F.raw(NEW_GAME)):
        raise TU.DataError("%s: more challenge defaults than the pages know" % NEW_GAME)
    special = {position("TAB_RANDOMIZER", "ITEM_RANDOM_MAP_BASED"): 1,
               position("TAB_NUZLOCKE", "ITEM_NUZLOCKE_RARE_CANDY"): 1}
    one_type = position("TAB_CHALLENGES", "ITEM_CHALLENGES_ONE_TYPE")
    mode = t.need("TAB_MODE")
    rec = recommended()

    out = {}
    tabs = hand_menus.challenge_tabs("de")
    for ti, pos in _positions().items():
        for p, ii in enumerate(pos):
            if (ti, p) == one_type:
                default = tabs[ti].items[p].count - 1
            elif ti == mode:
                default = rec.get(p, 0)
            else:
                default = special.get((ti, p), 0)
            out[(ti, p)] = Rule(policy.get(ti * width + ii, "free"), default)
    return out


@functools.lru_cache(maxsize=None)
def one_type_types():
    m = F.require(MENU, r"static const u8 sValidTypes\[\] = \{(.*?)\};", re.S)
    types = re.findall(r"TYPE_\w+", m.group(1))
    item = challenge_item("TAB_CHALLENGES", "ITEM_CHALLENGES_ONE_TYPE", "de")
    F.require(MENU, r"else if \(n == 18\)\s*text = sText_Random;")
    if len(types) != 18 or item.count != 20:
        raise TU.DataError("%s: one-type option changed" % MENU)
    return types


@functools.lru_cache(maxsize=None)
def level_caps():
    t = TU.load("src/caps.c")
    src = "src/caps.c"
    F.require(src, r"u8 badgeCount = GetCurrentBadgeCount\(\);")
    F.require(src, r"if \(FlagGet\(FLAG_IS_JOHTO_CHAMPION\)\)\s*return MAX_LEVEL;\s*"
                   r"if \(FlagGet\(FLAG_IS_KANTO_CHAMPION\)\)\s*return KANTO_MAX_LEVEL;")
    F.require(src, r"if \(challengeLevelCap == 1\)\s*return sLevelCapTable_Normal\[badgeCount\];\s*"
                   r"else\s*return sLevelCapTable_Hard\[badgeCount\];")
    if F.C("B_EXP_CAP_TYPE") != 0 or F.C("B_LEVEL_CAP_TYPE") != 0:
        raise TU.DataError("level caps outside the challenge menu are on: review the level page")
    normal, hard = [int(x) for x in t.array("sLevelCapTable_Normal")], [int(x) for x in t.array("sLevelCapTable_Hard")]
    if len(normal) != 9 or len(hard) != 9:
        raise TU.DataError("%s: level cap tables changed" % src)
    # what the cap does
    F.require("src/battle_script_commands.c",
              r"if \(GetMonData\(&gPlayerParty\[\*expMonId\], MON_DATA_LEVEL\) >= levelCap\)\s*"
              r"gBattleStruct->battlerExpReward = 0;")
    F.require("src/party_menu.c", r"tx_Challenges_LevelCap\) && sInitialLevel >= GetCurrentLevelCap\(\)\)\)")
    F.require("src/daycare.c", r"if \(levelAfter > GetCurrentLevelCap\(\)\)\s*levelAfter = GetCurrentLevelCap\(\);")
    return {"normal": normal, "hard": hard, "after_first_title": t.need("KANTO_MAX_LEVEL"), "max": t.need("MAX_LEVEL")}


@functools.lru_cache(maxsize=None)
def obedience():
    src = "src/battle_util.c"
    t = TU.load(src)
    if not (F.C("B_OBEDIENCE_MECHANICS") < F.C("GEN_8")):
        raise TU.DataError("obedience rule changed: review the level page")
    F.require(src, r"if \(B_OBEDIENCE_MECHANICS < GEN_8 && !IsOtherTrainer\(gBattleMons\[gBattlerAttacker\]\.otId, "
                   r"gBattleMons\[gBattlerAttacker\]\.otName\)\)\s*return OBEYS;")
    F.require(src, r"if \(FlagGet\(FLAG_IS_JOHTO_CHAMPION\)\)\s*return OBEYS;\s*#endif\s*obedienceLevel = GetObedienceLevel\(\);")
    F.require(src, r"if \(FlagGet\(FLAG_IS_KANTO_CHAMPION\)\)\s*\{\s*badgeCount = GetJohtoBadgeCount\(\);")
    F.require(src, r"if \(levelReferenced <= obedienceLevel\)\s*return OBEYS;")
    first = [int(x) for x in t.array("sKantoObedienceLevels")]
    second = [int(x) for x in t.array("sJohtoObedienceLevels")]
    if len(first) != 9 or len(second) != 9:
        raise TU.DataError("%s: obedience tables changed" % src)
    return {"first": first, "second": second}
