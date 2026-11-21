"""Names of the sub-areas of a location (pages/world.py): floors, rooms, houses, gates.

The game has no text for most of them (only the floor labels, wild_maps.floor_name), so a
map gets its label from what it is: the floor code and the kind of room. The words are
strings of this module in both languages; names of game facilities that the game writes
on its own signs (battle tents, the Bug-Catching Contest, the Seashore House) are quoted
from there.

    labels(ctx, loc) -> {map id: label}    ("" = the place itself)
"""
import re

from gamedata import locations as LOC
from gamedata import maps
from gamedata import wild_maps as WM

STRINGS = {
    "de": {
        "a_building": "Gebäude", "a_area": "Nebenbereich", "a_center": "Pokémon-Center", "a_dept": "Kaufhaus",
        "a_mart": "Markt", "a_gym": "Arena", "a_gamecorner": "Spielhalle", "a_prizeroom": "Preisschalter",
        "a_radiotower": "Radioturm", "a_bikeshop": "Fahrradladen", "a_daycare": "Pension", "a_station": "Bahnhof",
        "a_cablecar": "Seilbahnstation", "a_lighthouse": "Leuchtturm", "a_museum": "Museum", "a_fanclub": "Fanclub",
        "a_contest": "Wettbewerbshalle", "a_harbor": "Hafen", "a_pier": "Anleger", "a_elevator": "Aufzug",
        "a_halloffame": "Ruhmeshalle", "a_champion": "Raum des Champs", "a_school": "Schule",
        "a_resthouse": "Rasthaus", "a_flats": "Wohnblock", "a_flat": "Wohnung", "a_motel": "Motel",
        "a_institute": "Wetterinstitut", "a_spacecenter": "Raumfahrtzentrum", "a_shipyard": "Werft",
        "a_company": "Firmengebäude", "a_theater": "Theater", "a_cafe": "Café", "a_barn": "Stall",
        "a_workshop": "Werkstatt", "a_battleroom": "Kampfraum", "a_lobby": "Empfang", "a_corridor": "Gang",
        "a_lounge": "Aufenthaltsraum", "a_courtyard": "Hof", "a_basement": "Keller", "a_roof": "Dach",
        "a_summit": "Gipfel", "a_top": "Spitze", "a_bottom": "Grund", "a_outside": "Außenbereich",
        "a_inside": "Inneres", "a_deck": "Deck", "a_tunnel": "Tunnel", "a_cave": "Höhle", "a_chamber": "Kammer",
        "a_shrine": "Schrein", "a_gate_n": "Durchgang Nord", "a_gate_s": "Durchgang Süd",
        "a_gate_e": "Durchgang Ost", "a_gate_w": "Durchgang West", "a_entrance": "Eingang", "a_gate": "Durchgang",
        "a_lab": "Labor", "a_shop": "Laden", "a_office": "Büro", "a_house": "Haus", "a_rooms": "Räume",
        "a_room": "Raum", "a_hall": "Halle", "a_floor": "Etage", "a_puzzle": "Rätselraum",
        "a_underwater": "Unter Wasser", "a_north": "Norden", "a_south": "Süden", "a_east": "Osten",
        "a_west": "Westen", "a_northwest": "Nordwesten", "a_northeast": "Nordosten", "a_southwest": "Südwesten",
        "a_southeast": "Südosten", "a_middle": "Mitte", "a_end": "Ende", "a_descent": "Abstieg",
        "a_fork": "Gabelung", "a_snow": "Schneefeld", "a_slope": "Berghang", "a_yourhouse": "Dein Zuhause",
        "a_rivalhouse": "Haus des Rivalen", "a_kitchen": "Küche", "a_restaurant": "Restaurant", "a_hotel": "Hotel",
        "a_dojo": "Dojo", "a_cottage": "Haus am Meer", "a_flowershop": "Blumenladen", "a_herbshop": "Kräuterladen",
        "a_underground": "Untergrund", "a_switchroom": "Schalterraum", "a_storage": "Lager",
        "a_bugcontest": "Käferturnier", "a_path_to": "Weg: {place}", "a_cabin": "Kabine", "a_cabins": "Kabinen",
        "a_captain": "Kapitänskajüte", "a_yourcabin": "Deine Kabine", "a_lowerdeck": "Unterdeck",
        "a_seashore": "Strandhaus", "a_tent_factory": "Kampfzelt: Fabrik", "a_tent_palace": "Kampfzelt: Palast",
        "a_tent_arena": "Kampfzelt: Arena", "a_entrance_room": "Eingangsraum", "a_inner_room": "Innerer Raum",
        "a_stairs_room": "Treppenraum", "a_lower_room": "Unterer Raum", "a_ice_room": "Eisraum",
        "a_entrance_area": "Eingangsbereich", "a_trickhouse": "Rätselhaus", "a_league": "Liga",
    },
    "en": {
        "a_building": "Building", "a_area": "Side area", "a_center": "Pokémon Center", "a_dept": "Department Store",
        "a_mart": "Poké Mart", "a_gym": "Gym", "a_gamecorner": "Game Corner", "a_prizeroom": "Prize counter",
        "a_radiotower": "Radio Tower", "a_bikeshop": "Bike Shop", "a_daycare": "Day Care", "a_station": "Station",
        "a_cablecar": "Cable Car station", "a_lighthouse": "Lighthouse", "a_museum": "Museum",
        "a_fanclub": "Fan Club", "a_contest": "Contest Hall", "a_harbor": "Harbor", "a_pier": "Pier",
        "a_elevator": "Elevator", "a_halloffame": "Hall of Fame", "a_champion": "Champion's room",
        "a_school": "School", "a_resthouse": "Rest house", "a_flats": "Apartments", "a_flat": "Apartment",
        "a_motel": "Motel", "a_institute": "Weather Institute", "a_spacecenter": "Space Center",
        "a_shipyard": "Shipyard", "a_company": "Company building", "a_theater": "Theater", "a_cafe": "Café",
        "a_barn": "Barn", "a_workshop": "Workshop", "a_battleroom": "Battle room", "a_lobby": "Lobby",
        "a_corridor": "Corridor", "a_lounge": "Lounge", "a_courtyard": "Courtyard", "a_basement": "Basement",
        "a_roof": "Roof", "a_summit": "Summit", "a_top": "Top", "a_bottom": "Bottom", "a_outside": "Outside",
        "a_inside": "Inside", "a_deck": "Deck", "a_tunnel": "Tunnel", "a_cave": "Cave", "a_chamber": "Chamber",
        "a_shrine": "Shrine", "a_gate_n": "North gate", "a_gate_s": "South gate", "a_gate_e": "East gate",
        "a_gate_w": "West gate", "a_entrance": "Entrance", "a_gate": "Gate", "a_lab": "Lab", "a_shop": "Shop",
        "a_office": "Office", "a_house": "House", "a_rooms": "Rooms", "a_room": "Room", "a_hall": "Hall",
        "a_floor": "Floor", "a_puzzle": "Puzzle room", "a_underwater": "Underwater", "a_north": "North",
        "a_south": "South", "a_east": "East", "a_west": "West", "a_northwest": "Northwest",
        "a_northeast": "Northeast", "a_southwest": "Southwest", "a_southeast": "Southeast", "a_middle": "Center",
        "a_end": "End", "a_descent": "Descent", "a_fork": "Fork", "a_snow": "Snowfield", "a_slope": "Mountainside",
        "a_yourhouse": "Your home", "a_rivalhouse": "Rival's house", "a_kitchen": "Kitchen",
        "a_restaurant": "Restaurant", "a_hotel": "Hotel", "a_dojo": "Dojo", "a_cottage": "Sea Cottage",
        "a_flowershop": "Flower shop", "a_herbshop": "Herb shop", "a_underground": "Underground",
        "a_switchroom": "Switch room", "a_storage": "Warehouse", "a_bugcontest": "Bug-Catching Contest",
        "a_path_to": "Path: {place}", "a_cabin": "Cabin", "a_cabins": "Cabins", "a_captain": "Captain's cabin",
        "a_yourcabin": "Your cabin", "a_lowerdeck": "Lower deck", "a_seashore": "Seashore House",
        "a_tent_factory": "Battle Tent: Factory", "a_tent_palace": "Battle Tent: Palace",
        "a_tent_arena": "Battle Tent: Arena", "a_entrance_room": "Entrance room", "a_inner_room": "Inner room",
        "a_stairs_room": "Stairs room", "a_lower_room": "Lower room", "a_ice_room": "Ice room",
        "a_entrance_area": "Entrance area", "a_trickhouse": "Trick House", "a_league": "League",
    },
}

_FLOOR = re.compile(r"^B?\d+F$")
_ROOM_NO = re.compile(r"^(\d+)R$")
_NUM = re.compile(r"^(.*?)(\d+)$")
_VARIANT = re.compile(r"(?<=[a-z0-9])(Day|Night)$|^(LowTide|HighTide)")
_POSSESSIVE_ROOM = re.compile(r"^[A-Z][a-z]+sRoom$")

# Whole map folders (without build suffix) -> parts of the label. A part is a string key,
# (key, number), ("floor", code), ("place", key, map section) or "" for the place itself.
FOLDERS = {
    "Route2_EastBuilding": ["a_gate_e"],
    "Route25_SeaCottage": ["a_cottage"],
    "Route26North": ["a_north"],
    "CeladonCity_GameCorner_PrizeRoom": ["a_gamecorner", "a_prizeroom"],
    "GoldenrodCity_UndergroundEntrance": ["a_underground", "a_entrance"],
    "GoldenrodCity_UndergroundTunnel": ["a_underground", "a_tunnel"],
    "GoldenrodCity_UndergroundSwitches": ["a_underground", "a_switchroom"],
    "GoldenrodCity_UndergroundStorage": ["a_underground", "a_storage"],
    "GoldenrodCity_DepartmentStoreBasement": ["a_dept", "a_basement"],
    "GoldenrodCity_DepartmentStoreElevator": ["a_dept", "a_elevator"],
    "GoldenrodCity_DepartmentStore_7FNight": ["a_dept", ("floor", "7F")],
    "LilycoveCity_DepartmentStoreRooftop": ["a_dept", "a_roof"],
    "LilycoveCity_DepartmentStoreElevator": ["a_dept", "a_elevator"],
    "NationalPark_Normal": [""],
    "NationalPark_BugContest": ["a_bugcontest"],
    "BellchimeTrail": [("place", "a_path_to", "MAPSEC_TIN_TOWER")],
    "LakeOfRageLowTide": [""],
    "IndigoPlateau_Exterior": [""],
    "CianwoodPokecenter": ["a_center"],
    "CianwoodHouse1": [("a_house", 1)],
    "CianwoodHouse2": [("a_house", 2)],
    "CianwoodHouse3": [("a_house", 3)],
    "CianwoodShop": ["a_shop"],
    "CianwoodGym": ["a_gym"],
    "CliffEdgeCave": ["a_cave"],
    "SafariZoneGate_SafariZoneEntrance": ["a_entrance"],
    "SafariZone_Enterance": ["a_entrance_area"],
    "SafariZone_Top_Left": ["a_northwest"],
    "SafariZone_Top_Mid": ["a_north"],
    "SafariZone_Top_Right": ["a_northeast"],
    "SafariZone_Low_Left": ["a_southwest"],
    "SafariZone_Low_Mid": ["a_south"],
    "SafariZone_Low_Right": ["a_southeast"],
    "SSAqua_CaptainsRoom": ["a_captain"],
    "SSAqua_PlayersRoom": ["a_yourcabin"],
    "SSAqua_RoomNW": [("a_cabin", 1)],
    "SSAqua_RoomNE": [("a_cabin", 2)],
    "SSAqua_RoomNNE": [("a_cabin", 3)],
    "SSAqua_RoomSSW": [("a_cabin", 4)],
    "SSAqua_RoomSSE": [("a_cabin", 5)],
    "SSAqua_RoomSE": [("a_cabin", 6)],
    "SSAqua_RoomSW": [("a_cabin", 7)],
    "SSAnne_CaptainsOffice": ["a_captain"],
    "AbandonedShip_CaptainsOffice": ["a_captain"],
    "SSTidalLowerDeck": ["a_lowerdeck"],
    "SSTidalRooms": ["a_cabins"],
    "SlateportCity_BattleTentLobby": ["a_tent_factory", "a_lobby"],
    "SlateportCity_BattleTentCorridor": ["a_tent_factory", "a_corridor"],
    "SlateportCity_BattleTentBattleRoom": ["a_tent_factory", "a_battleroom"],
    "VerdanturfTown_BattleTentLobby": ["a_tent_palace", "a_lobby"],
    "VerdanturfTown_BattleTentCorridor": ["a_tent_palace", "a_corridor"],
    "VerdanturfTown_BattleTentBattleRoom": ["a_tent_palace", "a_battleroom"],
    "FallarborTown_BattleTentLobby": ["a_tent_arena", "a_lobby"],
    "FallarborTown_BattleTentCorridor": ["a_tent_arena", "a_corridor"],
    "FallarborTown_BattleTentBattleRoom": ["a_tent_arena", "a_battleroom"],
    "VermilionCity_PortOutside": ["a_pier"],
    "VermilionCity_PortInside": ["a_harbor"],
    "OlivineCity_PortOutside": ["a_pier"],
    "OlivineCity_PortInside": ["a_harbor"],
    "EverGrandeCity_PokemonLeague_1F": ["a_league", ("floor", "1F")],
    "EverGrandeCity_PokemonLeague_2F": ["a_league", ("floor", "2F")],
    "Route110_TrickHouseEntrance": ["a_trickhouse", "a_entrance"],
    "Route110_TrickHouseEnd": ["a_trickhouse", "a_end"],
    "Route110_TrickHouseCorridor": ["a_trickhouse", "a_corridor"],
}
# Folder tokens -> string key (exact match first, then suffix match in this order).
TOKENS = (
    ("PlayersHouse", "a_yourhouse"), ("RivalsHouse", "a_rivalhouse"), ("BrendansHouse", "a_house"),
    ("MaysHouse", "a_house"), ("SeashoreHouse", "a_seashore"), ("Kitchen", "a_kitchen"),
    ("Restaurant", "a_restaurant"), ("Hotel", "a_hotel"), ("Dojo", "a_dojo"), ("FlowerShop", "a_flowershop"),
    ("HerbShop", "a_herbshop"),
    ("EntranceRoom", "a_entrance_room"), ("InnerRoom", "a_inner_room"), ("StairsRoom", "a_stairs_room"),
    ("LowerRoom", "a_lower_room"), ("IceRoom", "a_ice_room"),
    ("PokemonCenter", "a_center"), ("DepartmentStore", "a_dept"), ("Mart", "a_mart"), ("Gym", "a_gym"),
    ("GameCorner", "a_gamecorner"), ("RadioTower", "a_radiotower"), ("BikeShop", "a_bikeshop"),
    ("DayCare", "a_daycare"), ("TrainStation", "a_station"), ("CableCarStation", "a_cablecar"),
    ("Lighthouse", "a_lighthouse"), ("Museum", "a_museum"), ("FanClub", "a_fanclub"),
    ("ContestLobby", "a_contest_lobby"), ("ContestHall", "a_contest"), ("Harbor", "a_harbor"),
    ("Elevator", "a_elevator"),
    ("HallOfFame", "a_halloffame"), ("ChampionsRoom", "a_champion"), ("School", "a_school"),
    ("RestHouse", "a_resthouse"), ("RestStop", "a_resthouse"), ("Condominiums", "a_flats"),
    ("Flat", "a_flat"), ("Motel", "a_motel"), ("Institute", "a_institute"), ("SpaceCenter", "a_spacecenter"),
    ("Shipyard", "a_shipyard"), ("DevonCorp", "a_company"), ("Theater", "a_theater"), ("Cafe", "a_cafe"),
    ("FarmHouse", "a_house"), ("Barn", "a_barn"), ("Workshop", "a_workshop"),
    ("BattleRoom", "a_battleroom"), ("Lobby", "a_lobby"), ("Corridor", "a_corridor"), ("Corridors", "a_corridor"),
    ("Lounge", "a_lounge"), ("Courtyard", "a_courtyard"), ("Basement", "a_basement"), ("Rooftop", "a_roof"),
    ("Roof", "a_roof"), ("Summit", "a_summit"), ("Top", "a_top"), ("Bottom", "a_bottom"),
    ("Exterior", "a_outside"), ("Outside", "a_outside"), ("Interior", "a_inside"), ("Inner", "a_inside"),
    ("Inside", "a_inside"),
    ("Deck", "a_deck"), ("Tunnel", "a_tunnel"), ("Cave", "a_cave"), ("Cavern", "a_cave"),
    ("Chamber", "a_chamber"), ("Chambers", "a_chamber"), ("Shrine", "a_shrine"),
    ("NorthEntrance", "a_gate_n"), ("SouthEntrance", "a_gate_s"), ("EastEntrance", "a_gate_e"),
    ("WestEntrance", "a_gate_w"), ("Entrance", "a_entrance"), ("Enterance", "a_entrance"),
    ("Gate", "a_gate"), ("Lab", "a_lab"), ("Shop", "a_shop"), ("Office", "a_office"),
    ("House", "a_house"), ("Rooms", "a_rooms"), ("Room", "a_room"), ("Hall", "a_hall"),
    ("Floor", "a_floor"), ("Puzzle", "a_puzzle"), ("Underwater", "a_underwater"),
    ("Northwest", "a_northwest"), ("Northeast", "a_northeast"), ("Southwest", "a_southwest"),
    ("Southeast", "a_southeast"),
    ("North", "a_north"), ("South", "a_south"), ("East", "a_east"), ("West", "a_west"),
    ("NorthSide", "a_north"), ("SouthSide", "a_south"), ("Center", "a_middle"), ("Mid", "a_middle"),
    ("End", "a_end"), ("Descent", "a_descent"), ("Fork", "a_fork"), ("Snow", "a_snow"),
    ("MountainSide", "a_slope"),
)
_EXACT = dict(TOKENS)


def _word(ctx, key, num=None):
    if key == "a_contest_lobby":
        return "%s, %s" % (ctx.t("a_contest"), ctx.t("a_lobby"))
    w = ctx.t(key)
    return "%s %s" % (w, num) if num else w


def _floor(ctx, code):
    return WM.floor_name(code, ctx.lang) or code


def _token(ctx, tok):
    """Label part for one folder token, or None when the token says nothing."""
    if _FLOOR.match(tok):
        return _floor(ctx, tok)
    m = _ROOM_NO.match(tok)
    if m:
        return _word(ctx, "a_room", m.group(1))
    num = ""
    base = tok
    m = _NUM.match(tok)
    if m and m.group(1):
        base, num = m.group(1), m.group(2)
    if _POSSESSIVE_ROOM.match(base) and base not in _EXACT:
        return _word(ctx, "a_room", num)
    key = _EXACT.get(base)
    if key is None:
        for name, k in TOKENS:
            if base.endswith(name):
                key = k
                break
    if key is None:
        return None
    return _word(ctx, key, num)


def _raw(ctx, loc, m, underwater):
    """Label of one map before the labels of a location are made unique; None = unknown."""
    if underwater or m.map_type == "MAP_TYPE_UNDERWATER":
        return ctx.t("a_underwater")
    base = LOC.base_dir(m.dir)
    parts = FOLDERS.get(base)
    if parts is not None:
        out = []
        for p in parts:
            if p == "":
                return ""
            if isinstance(p, str):
                out.append(_word(ctx, p))
            elif p[0] == "floor":
                out.append(_floor(ctx, p[1]))
            elif p[0] == "place":
                out.append(ctx.t(p[1], place=maps.mapsec_name(p[2], ctx.lang)))
            else:
                out.append(_word(ctx, p[0], p[1]))
        return ", ".join(out)
    if base.startswith("Gate_"):
        return ctx.t("a_gate")
    toks = [_VARIANT.sub("", t) for t in base.split("_")[1:]]
    toks = [t for t in toks if t]
    if not toks:
        return "" if m.id == loc.map_ids[0] else None
    words, unknown = [], False
    for tok in toks:
        w = _token(ctx, tok)
        if w is None:
            unknown = True
        elif w not in words:
            words.append(w)
    if unknown and not words:
        return None
    return ", ".join(words)


_CACHE = {}


def labels(ctx, loc):
    """{map id: label} of the sub-areas of a location ("" = the place itself). Labels of
    the maps whose content is shown are unique; a copy the play-through never reaches
    (night layout, low tide) carries the label of its twin."""
    ck = (ctx.lang, loc.key)
    if ck in _CACHE:
        return _CACHE[ck]
    part_of = {mid for _sec, _f, ids in loc.parts for mid in ids}
    raw = {}
    for mid in loc.map_ids:
        m = maps.by_id(mid)
        lab = _raw(ctx, loc, m, mid in part_of)
        if lab is None:
            lab = ctx.t("a_building") if m.map_type == "MAP_TYPE_INDOOR" else ctx.t("a_area")
        raw[mid] = lab
    content = [mid for mid in loc.map_ids if mid in loc.content_ids]
    count = {}
    for mid in content:
        count[raw[mid]] = count.get(raw[mid], 0) + 1
    taken = set(raw.values())
    out, used = dict(raw), {}
    for mid in content:
        lab = raw[mid]
        if lab and count[lab] > 1:
            used[lab] = used.get(lab, 0) + 1
            plain = "%s %d" % (lab, used[lab])
            # "Haus 1" style unless that reads wrong (label ends in a number or has parts) or exists already
            if "," in lab or lab[-1].isdigit() or plain in taken or len(lab) <= 3:
                plain = "%s (%d)" % (lab, used[lab])
            out[mid] = plain
    _CACHE[ck] = out
    return out
