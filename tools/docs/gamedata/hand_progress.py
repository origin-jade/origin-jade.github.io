"""The route through the game: badges per region and the two region changes,
read from the map scripts. Every step the pages describe is pinned with
hand_facts.require(), so a changed script stops the build.

    hand_progress.badges("Kanto"|"Johto"|"Hoenn") -> [Badge(n, map, leader, permit_move)]
        Kanto: `setflag FLAG_BADGE0n_GET` in the Kanto gym scripts;
        Johto/Hoenn: `setvar VAR_0x8004, n` + `special SetJohtoBadge`/`SetHoennBadge`;
        permit: `setvar VAR_0x8004, PERM_*/LIC_*` + `special SetJohtoPermit`/`SetHoennLicense`
        in the same script (other sites: permit_sites()).
    hand_progress.permit_sites(region) -> [(map, move)] every place that grants a permit/licence
    hand_progress.kanto_to_johto()  -> dict of names for the Kanto -> Johto change (checked)
    hand_progress.johto_to_hoenn()  -> dict of names for the Johto -> Hoenn change (checked)
    hand_progress.hoenn_end()       -> dict for the end of the journey (checked)

Language: every function takes lang="de"|"en" as its last argument (None = the process
language); the maps, trainers, moves and texts in the results are those of that build.

Cross-checked against tools/simulate_progress.py (report "milestones": Region/Orden/Titel),
which is too slow to run in the site build; see PAGES_hand.md.
"""
import functools
import glob
import re

from . import repo_path
from . import tu as TU
from . import maps
from . import moves as MOVES
from . import trainers as TRAINERS
from . import hand_facts as F


class Badge:
    def __init__(self, n, map_, leader, permit):
        self.n, self.map, self.leader, self.permit = n, map_, leader, permit

    def __repr__(self):
        return "Badge(%d %s %s %s)" % (self.n, self.map.display, self.leader and self.leader.name,
                                       self.permit and self.permit.name)


def _scripts(lang=None):
    for path in sorted(glob.glob(repo_path("data", "maps", "*", "scripts.inc"))):
        d = path.split("/")[-2]
        m = maps.by_dir(d, lang)
        if m and m.active:
            yield m, open(path, encoding="utf-8").read()


def _leader(src, lang=None):
    for c in re.findall(r"trainerbattle\w*\s+(TRAINER_\w+)", src):
        tr = TRAINERS.by_const(c, lang)
        if tr and "LEADER" in tr.class_const and "{" not in tr.name:
            return tr
    return None


def _permit_move(const, lang=None):
    suffix = const.split("_", 1)[1]
    mv = MOVES.by_const("MOVE_" + suffix, lang)
    if mv is None:
        raise TU.DataError("permit %s: no move MOVE_%s" % (const, suffix))
    return mv


def badges(region, lang=None):
    return list(_badges(region, TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _badges(region, lang):
    out = {}
    for m, src in _scripts(lang):
        if region == "Kanto":
            if m.region != "Kanto":
                continue
            hits = [int(x) - 1 for x in re.findall(r"^\tsetflag FLAG_BADGE0([1-8])_GET", src, re.M)]
        else:
            special = "SetJohtoBadge" if region == "Johto" else "SetHoennBadge"
            hits = [int(x) for x in re.findall(r"setvar VAR_0x8004, (\d+)\s*\n\s*special %s\b" % special, src)]
        for n in hits:
            if n in out:
                raise TU.DataError("%s badge %d set in two places" % (region, n + 1))
            perm = re.search(r"setvar VAR_0x8004, ((?:PERM|LIC)_\w+)\s*\n\s*special Set(?:JohtoPermit|HoennLicense)", src)
            out[n] = Badge(n + 1, m, _leader(src, lang), _permit_move(perm.group(1), lang) if perm else None)
    if sorted(out) != list(range(8)):
        raise TU.DataError("%s: badges found %s, expected 1-8" % (region, [n + 1 for n in sorted(out)]))
    # A badge handed out away from the gym (Johto 8: after the gym battle the leader sends the
    # player on, "..._GoTo<Place>"): the leader is the one whose battle is followed by that message.
    for b in out.values():
        b.fight_map = None
        if b.leader:
            continue
        prefix = b.map.dir.split("_")[0]
        for m, src in _scripts(lang):
            mm = re.search(r"trainerbattle\w*\s+(TRAINER_\w+)[^\n]*\n\s*msgbox \w*GoTo%s" % re.escape(prefix), src)
            if mm:
                b.leader, b.fight_map = TRAINERS.by_const(mm.group(1), lang), m
                break
    return tuple(out[n] for n in range(8))


def permit_sites(region, lang=None):
    return list(_permit_sites(region, TU.lang(lang)))


@functools.lru_cache(maxsize=None)
def _permit_sites(region, lang):
    special = "SetJohtoPermit" if region == "Johto" else "SetHoennLicense"
    out = []
    for m, src in _scripts(lang):
        for c in re.findall(r"setvar VAR_0x8004, ((?:PERM|LIC)_\w+)\s*\n\s*special %s\b" % special, src):
            out.append((m, _permit_move(c, lang)))
    return tuple(out)


def _text_anywhere(label, lang=None):
    """Text of a script label defined in data/scripts or data/text, in build lang."""
    for path in sorted(glob.glob(repo_path("data", "scripts", "*.inc")) + glob.glob(repo_path("data", "text", "*.inc"))):
        src = open(path, encoding="utf-8").read()
        if re.search(r"^%s::?\s*$" % re.escape(label), src, re.M):
            return F.inc_string(path[len(repo_path("")):], label, lang)
    raise TU.DataError("text %s not found" % label)


def kanto_to_johto(lang=None):
    hof = "data/scripts/hall_of_fame_frlg.inc"
    F.require(hof, r"^\tsetflag FLAG_IS_KANTO_CHAMPION")
    F.require(hof, r"call_if_eq VAR_JOHTO_HANDOVER, 0, EventScript_ArmJohtoHandover")
    F.require("data/maps/IndigoPlateau_Exterior_Frlg/scripts.inc", r"msgbox IndigoPlateau_Exterior_Text_OakComeToMyLab")
    lab = "data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc"
    F.require(lab, r"goto_if_eq VAR_JOHTO_HANDOVER, 1, PalletTown_ProfessorOaksLab_EventScript_GiveGsBall")
    F.require(lab, r"giveitem_msg PalletTown_ProfessorOaksLab_Text_ReceivedGsBall, ITEM_GS_BALL")
    gate = "data/maps/ReceptionGate_hns/scripts.inc"
    F.require(gate, r"goto_if_set FLAG_SYS_GAME_CLEAR, ReceptionGate_EventScript_CheckGsBall")
    F.require(gate, r"goto_if_ne VAR_JOHTO_HANDOVER, 1, ReceptionGate_EventScript_PassJohto")
    F.require("data/maps/ReceptionGate_hns/map.json", r'"dest_map": "MAP_ROUTE26NORTH_HNS"')
    F.require("data/maps/ReceptionGate_hns/map.json", r'"dest_map": "MAP_ROUTE22_NORTH_ENTRANCE"')
    elm = "data/maps/NewBarkTown_Lab_hns/scripts.inc"
    F.require(elm, r"removeitem ITEM_GS_BALL\n\tsetvar VAR_JOHTO_HANDOVER, 3")
    return {
        "oak_lab": F.map_name("PalletTown_ProfessorOaksLab_Frlg", lang),
        "indigo": F.map_name("IndigoPlateau_Exterior_Frlg", lang),
        "gs_ball": F.item("ITEM_GS_BALL", lang).name,
        "route22": F.map_by_id("MAP_ROUTE22", lang).display,
        "gate": F.map_name("ReceptionGate_hns", lang),
        "route26": F.map_by_id("MAP_ROUTE26NORTH_HNS", lang).display,
        "elm_town": F.map_name("NewBarkTown_Lab_hns", lang),
        "gate_closed": F.inc_string(gate, "ReceptionGate_Text_JohtoClosed", lang),
        "gate_oak": F.inc_string(gate, "ReceptionGate_Text_SeeOakFirst", lang),
    }


def johto_to_hoenn(lang=None):
    lab = "data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc"
    F.require(lab, r"call_if_set FLAG_IS_JOHTO_CHAMPION, PalletTown_ProfessorOaksLab_EventScript_TryArmTroyScene")
    F.require(lab, r"giveitem_norandom ITEM_HOENN_TICKET\n\tsetvar VAR_HOENN_TICKET_STATE, 3")
    arr = "data/scripts/hoenn_arrival.inc"
    F.require(arr, r"goto_if_lt VAR_HOENN_TICKET_STATE, 3, Common_EventScript_HoennNoTicket")
    F.require(arr, r"warpsilent MAP_ROUTE104, ")
    F.require(arr, r"warpsilent MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB, ")
    F.require(arr, r"warpsilent MAP_SLATEPORT_CITY_HARBOR, ")
    F.require(arr, r"warpsilent MAP_LILYCOVE_CITY_HARBOR, ")
    F.require(arr, r"goto_if_unset FLAG_VISITED_SLATEPORT_CITY, Common_EventScript_NopReturn")
    F.require(arr, r"goto_if_unset FLAG_VISITED_LILYCOVE_CITY, Common_EventScript_NopReturn")
    F.require(arr, r"call_if_set FLAG_IS_HOENN_CHAMPION, Common_EventScript_ShipMenuPushBattleFrontier")
    F.require(arr, r"checkitem ITEM_AURORA_TICKET\n\tgoto_if_eq VAR_RESULT, FALSE, Common_EventScript_NopReturn\n\tdynmultipush gText_BirthIsland")
    olv = "data/maps/OlivineCity_PortInside_hns/scripts.inc"
    ver = "data/maps/VermilionCity_PortInside_Frlg/scripts.inc"
    F.require(olv, r"SHIP_PORT_OLIVINE")
    F.require(ver, r"SHIP_PORT_VERMILION")
    F.require("data/maps/LilycoveCity_Harbor/scripts.inc", r"goto_if_unset FLAG_IS_HOENN_CHAMPION|goto_if_set FLAG_IS_HOENN_CHAMPION")
    return {
        "oak_lab": F.map_name("PalletTown_ProfessorOaksLab_Frlg", lang),
        "troy": F.trainer("TRAINER_STEVEN", lang).name,
        "ticket": F.item("ITEM_HOENN_TICKET", lang).name,
        "ss_ticket": F.item("ITEM_SS_TICKET", lang).name,
        "aurora": F.item("ITEM_AURORA_TICKET", lang).name,
        "vermilion": F.map_name("VermilionCity_PortInside_Frlg", lang),
        "olivine": F.map_name("OlivineCity_PortInside_hns", lang),
        "route104": F.map_by_id("MAP_ROUTE104", lang).display,
        "birch_town": F.map_by_id("MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", lang).display,
        "slateport": F.map_by_id("MAP_SLATEPORT_CITY_HARBOR", lang).display,
        "lilycove": F.map_by_id("MAP_LILYCOVE_CITY_HARBOR", lang).display,
        "frontier": maps.mapsec_name("MAPSEC_BATTLE_FRONTIER", lang),
        "birth_island": maps.mapsec_name("MAPSEC_BIRTH_ISLAND", lang),
        "no_ticket": _text_anywhere("Common_Text_HoennNeedTicket", lang),
    }


def hoenn_end(lang=None):
    F.require("data/maps/EverGrandeCity_ChampionsRoom/scripts.inc", r"setflag FLAG_IS_HOENN_CHAMPION")
    hof = "data/maps/EverGrandeCity_HallOfFame/scripts.inc"
    F.require(hof, r"EventScript_GameClearOriginJade:\n\t@[^\n]*\n\tsetflag FLAG_END_NUZLOCKE\n\tsetrespawn HEAL_LOCATION_LITTLEROOT_TOWN_LAB")
    F.require(hof, r"goto_if_set FLAG_ROLLED_ENDING_CREDITS, EverGrandeCity_HallOfFame_EventScript_GameClearNoCredits\n"
                   r"\tsetflag FLAG_ROLLED_ENDING_CREDITS\n\tspecial GameClear")
    return {"hof": F.map_name("EverGrandeCity_HallOfFame", lang),
            "birch_town": F.map_by_id("MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", lang).display}
