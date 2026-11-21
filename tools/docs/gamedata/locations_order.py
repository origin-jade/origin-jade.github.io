"""Travel order of the map sections and the maps the play-through model never reaches.

SECTION_ORDER: every active, unlocked map section the repository's play-through model
(tools/simulate_progress.py) reaches, in the order the story makes it reachable: by the
first wave in which a map of the section is reached; inside one wave in the order of a
walk that continues from the places reached last (breadth-first over map connections,
warps and script warps).
UNREACHED_MAPS: folders of active, unlocked maps the model never reaches (event islands
without a ferry, alternative layouts, link rooms ...).

Regenerate after map or story changes (about four minutes):
    python3 -I -B tools/simulate_progress.py --out DIR --quiet
    python3 -I -B <gen_order.py> DIR/report.json > tools/docs/gamedata/locations_order.py

Model revision of this list: e160f672e0
"""

SECTION_ORDER = (
    "MAPSEC_PALLET_TOWN",  # Alabastia (0)
    "MAPSEC_ROUTE_1",  # Route 1 (3)
    "MAPSEC_VIRIDIAN_CITY",  # Vertania City (3)
    "MAPSEC_ROUTE_2",  # Route 2 (3)
    "MAPSEC_ROUTE_22",  # Route 22 (3)
    "MAPSEC_PEWTER_CITY",  # Marmoria City (3)
    "MAPSEC_VIRIDIAN_FOREST",  # Vertania-Wald (3)
    "MAPSEC_ROUTE_3",  # Route 3 (4)
    "MAPSEC_ROUTE_4",  # Route 4 (4)
    "MAPSEC_MT_MOON",  # Mondberg (4)
    "MAPSEC_CERULEAN_CITY",  # Azuria City (5)
    "MAPSEC_SPECIAL_AREA",  # Sonderbereich (6)
    "MAPSEC_ROUTE_24",  # Route 24 (6)
    "MAPSEC_DYNAMIC",  # MAPSEC_DYNAMIC (6)
    "MAPSEC_ROUTE_25",  # Route 25 (7)
    "MAPSEC_ROUTE_5",  # Route 5 (7)
    "MAPSEC_DIGLETTS_CAVE",  # Digdas Höhle (7)
    "MAPSEC_UNDERGROUND_PATH",  # Untergrundpfad (7)
    "MAPSEC_VERMILION_CITY",  # Orania City (7)
    "MAPSEC_ROUTE_6",  # Route 6 (7)
    "MAPSEC_ROUTE_11",  # Route 11 (7)
    "MAPSEC_ROUTE_12",  # Route 12 (7)
    "MAPSEC_S_S_ANNE",  # M.S. Anne (11)
    "MAPSEC_LAVENDER_TOWN",  # Lavandia (14)
    "MAPSEC_ROUTE_9",  # Route 9 (14)
    "MAPSEC_ROUTE_10",  # Route 10 (14)
    "MAPSEC_ROUTE_8",  # Route 8 (14)
    "MAPSEC_POKEMON_TOWER",  # Pokémon-Turm (14)
    "MAPSEC_ROCK_TUNNEL",  # Felstunnel (14)
    "MAPSEC_UNDERGROUND_PATH_2",  # Untergrundpfad (14)
    "MAPSEC_ROUTE_7",  # Route 7 (14)
    "MAPSEC_CELADON_CITY",  # Prismania City (14)
    "MAPSEC_ROUTE_16",  # Route 16 (14)
    "MAPSEC_ROCKET_HIDEOUT",  # Rocket-Versteck (14)
    "MAPSEC_SAFFRON_CITY",  # Saffronia City (16)
    "MAPSEC_SILPH_CO",  # Silph Co. (16)
    "MAPSEC_ROUTE_13",  # Route 13 (23)
    "MAPSEC_ROUTE_14",  # Route 14 (23)
    "MAPSEC_ROUTE_15",  # Route 15 (23)
    "MAPSEC_FUCHSIA_CITY",  # Fuchsania City (23)
    "MAPSEC_ROUTE_19",  # Route 19 (23)
    "MAPSEC_ROUTE_18",  # Route 18 (23)
    "MAPSEC_KANTO_SAFARI_ZONE",  # Safari-Zone (24)
    "MAPSEC_ROUTE_17",  # Route 17 (25)
    "MAPSEC_ROUTE_20",  # Route 20 (25)
    "MAPSEC_POWER_PLANT",  # Kraftwerk (25)
    "MAPSEC_ROUTE_21",  # Route 21 (25)
    "MAPSEC_CINNABAR_ISLAND",  # Zinnoberinsel (25)
    "MAPSEC_SEAFOAM_ISLANDS",  # Seeschauminseln (25)
    "MAPSEC_POKEMON_MANSION",  # Pokémon-Villa (25)
    "MAPSEC_VICTORY_ROAD_HNS",  # Siegesstraße (39)
    "MAPSEC_ROUTE_23",  # Route 23 (40)
    "MAPSEC_KANTO_VICTORY_ROAD",  # Siegesstraße (40)
    "MAPSEC_INDIGO_PLATEAU",  # Indigo Plateau (42)
    "MAPSEC_POKEMON_LEAGUE",  # Pokémon-Liga (43)
    "MAPSEC_CERULEAN_CAVE",  # Azuria-Höhle (51)
    "MAPSEC_ROUTE_26",  # Route 26 (52)
    "MAPSEC_ROUTE_27",  # Route 27 (53)
    "MAPSEC_NEW_BARK_TOWN",  # Neuborkia (53)
    "MAPSEC_TOHJO_FALLS",  # Tohjo-Fälle (53)
    "MAPSEC_ROUTE_29",  # Route 29 (53)
    "MAPSEC_CHERRYGROVE_CITY",  # Rosalia City (53)
    "MAPSEC_ROUTE_46",  # Route 46 (53)
    "MAPSEC_DARK_CAVE",  # Dunkelhöhle (54)
    "MAPSEC_ROUTE_30",  # Route 30 (54)
    "MAPSEC_ROUTE_31",  # Route 31 (54)
    "MAPSEC_VIOLET_CITY",  # Viola City (55)
    "MAPSEC_ROUTE_32",  # Route 32 (55)
    "MAPSEC_ROUTE_36",  # Route 36 (55)
    "MAPSEC_SPROUT_TOWER",  # Knofensa-Turm (55)
    "MAPSEC_RUINS_OF_ALPH",  # Alph-Ruinen (55)
    "MAPSEC_UNION_CAVE",  # Einheitstunnel (56)
    "MAPSEC_ROUTE_33",  # Route 33 (56)
    "MAPSEC_AZALEA_TOWN",  # Azalea City (57)
    "MAPSEC_ILEX_FOREST",  # Steineichenwald (57)
    "MAPSEC_SLOWPOKE_WELL",  # Flegmon-Brunnen (58)
    "MAPSEC_ROUTE_34",  # Route 34 (63)
    "MAPSEC_GOLDENROD_CITY",  # Dukatia City (65)
    "MAPSEC_ROUTE_35",  # Route 35 (66)
    "MAPSEC_NATIONAL_PARK",  # Nationalpark (66)
    "MAPSEC_ROUTE_37",  # Route 37 (72)
    "MAPSEC_ECRUTEAK_CITY",  # Teak City (73)
    "MAPSEC_ROUTE_38",  # Route 38 (73)
    "MAPSEC_ROUTE_42",  # Route 42 (73)
    "MAPSEC_BURNED_TOWER",  # Turmruine (73)
    "MAPSEC_ROUTE_39",  # Route 39 (73)
    "MAPSEC_MT_MORTAR",  # Kesselberg (74)
    "MAPSEC_OLIVINE_CITY",  # Oliviana City (75)
    "MAPSEC_MAHOGANY_TOWN",  # Mahagonia City (75)
    "MAPSEC_ROUTE_40",  # Route 40 (75)
    "MAPSEC_OLIVINE_LIGHTHOUSE",  # Leuchtturm (75)
    "MAPSEC_ROUTE_43",  # Route 43 (75)
    "MAPSEC_ROUTE_44",  # Route 44 (75)
    "MAPSEC_TRAINER_HILL",  # Trainerberg (75)
    "MAPSEC_LAKE_OF_RAGE",  # See des Zorns (75)
    "MAPSEC_ICE_PATH",  # Eispfad (75)
    "MAPSEC_BLACKTHORN_CITY",  # Ebenholz City (76)
    "MAPSEC_ROUTE_45",  # Route 45 (76)
    "MAPSEC_DRAGONS_DEN",  # Drachenhöhle (77)
    "MAPSEC_ROCKET_HIDEOUT_HNS",  # Rocket HQ (77)
    "MAPSEC_ROUTE_41",  # Route 41 (77)
    "MAPSEC_CIANWOOD_CITY",  # Anemonia City (77)
    "MAPSEC_CLIFF_CAVE",  # Felsschlundhöhle (77)
    "MAPSEC_ROUTE_47",  # Route 47 (77)
    "MAPSEC_ROUTE_48",  # Route 48 (77)
    "MAPSEC_SAFARI_ZONE_GATE",  # Safari-Eingang (78)
    "MAPSEC_WHIRL_ISLANDS",  # Strudelinseln (92)
    "MAPSEC_TIN_TOWER",  # Glockenturm (99)
    "MAPSEC_SS_AQUA",  # M.S. Aqua (108)
    "MAPSEC_BIRTH_ISLAND",  # Entstehungsinsel (109)
    "MAPSEC_ROUTE_28",  # Route 28 (109)
    "MAPSEC_MT_SILVER",  # Silberberg (109)
    "MAPSEC_PETALBURG_CITY",  # Blütenburg City (109)
    "MAPSEC_ROUTE_104",  # Route 104 (109)
    "MAPSEC_PETALBURG_WOODS",  # Blütenburgwald (109)
    "MAPSEC_RUSTBORO_CITY",  # Metarost City (110)
    "MAPSEC_ROUTE_102",  # Route 102 (110)
    "MAPSEC_ROUTE_115",  # Route 115 (110)
    "MAPSEC_ROUTE_116",  # Route 116 (110)
    "MAPSEC_OLDALE_TOWN",  # Rosaltstadt (110)
    "MAPSEC_RUSTURF_TUNNEL",  # Metaflurtunnel (110)
    "MAPSEC_ROUTE_103",  # Route 103 (110)
    "MAPSEC_ROUTE_101",  # Route 101 (110)
    "MAPSEC_LITTLEROOT_TOWN",  # Wurzelheim (110)
    "MAPSEC_ROUTE_110",  # Route 110 (111)
    "MAPSEC_ROUTE_105",  # Route 105 (111)
    "MAPSEC_DEWFORD_TOWN",  # Faustauhaven (111)
    "MAPSEC_SLATEPORT_CITY",  # Graphitport City (111)
    "MAPSEC_ROUTE_106",  # Route 106 (111)
    "MAPSEC_ISLAND_CAVE",  # Inselhöhle (111)
    "MAPSEC_ROUTE_107",  # Route 107 (111)
    "MAPSEC_ROUTE_109",  # Route 109 (111)
    "MAPSEC_GRANITE_CAVE",  # Granithöhle (111)
    "MAPSEC_ROUTE_108",  # Route 108 (111)
    "MAPSEC_ABANDONED_SHIP",  # Schiffswrack (111)
    "MAPSEC_MAUVILLE_CITY",  # Malvenfroh City (113)
    "MAPSEC_VERDANTURF_TOWN",  # Wiesenflur (113)
    "MAPSEC_ROUTE_111",  # Route 111 (113)
    "MAPSEC_ROUTE_117",  # Route 117 (113)
    "MAPSEC_ROUTE_118",  # Route 118 (113)
    "MAPSEC_ROUTE_113",  # Route 113 (118)
    "MAPSEC_ROUTE_112",  # Route 112 (118)
    "MAPSEC_ROUTE_114",  # Route 114 (118)
    "MAPSEC_METEOR_FALLS",  # Meteorfälle (118)
    "MAPSEC_FALLARBOR_TOWN",  # Laubwechselfeld (118)
    "MAPSEC_FIERY_PATH",  # Feuriger Pfad (118)
    "MAPSEC_DESERT_UNDERPASS",  # Wüstentunnel (118)
    "MAPSEC_MT_CHIMNEY",  # Schlotberg (120)
    "MAPSEC_JAGGED_PASS",  # Steilpass (122)
    "MAPSEC_LAVARIDGE_TOWN",  # Bad Lavastadt (122)
    "MAPSEC_ROUTE_119",  # Route 119 (122)
    "MAPSEC_ROUTE_123",  # Route 123 (122)
    "MAPSEC_ROUTE_134",  # Route 134 (122)
    "MAPSEC_NEW_MAUVILLE",  # Neu Malvenfroh (122)
    "MAPSEC_ROUTE_122",  # Route 122 (122)
    "MAPSEC_ROUTE_133",  # Route 133 (122)
    "MAPSEC_ROUTE_121",  # Route 121 (122)
    "MAPSEC_MT_PYRE",  # Pyroberg (122)
    "MAPSEC_ROUTE_132",  # Route 132 (122)
    "MAPSEC_LILYCOVE_CITY",  # Seegrasulb City (122)
    "MAPSEC_PACIFIDLOG_TOWN",  # Floßbrunn (122)
    "MAPSEC_ROUTE_124",  # Route 124 (122)
    "MAPSEC_AQUA_HIDEOUT",  # Aquas Versteck (122)
    "MAPSEC_ROUTE_131",  # Route 131 (122)
    "MAPSEC_ROUTE_126",  # Route 126 (122)
    "MAPSEC_ROUTE_125",  # Route 125 (122)
    "MAPSEC_MOSSDEEP_CITY",  # Moosbach City (122)
    "MAPSEC_ROUTE_130",  # Route 130 (122)
    "MAPSEC_ROUTE_127",  # Route 127 (122)
    "MAPSEC_SHOAL_CAVE",  # Küstenhöhle (122)
    "MAPSEC_ROUTE_129",  # Route 129 (122)
    "MAPSEC_ROUTE_128",  # Route 128 (122)
    "MAPSEC_EVER_GRANDE_CITY",  # Prachtpolis City (122)
    "MAPSEC_SKY_PILLAR",  # Himmelturm (123)
    "MAPSEC_SAFARI_ZONE",  # Safari-Zone (123)
    "MAPSEC_MAGMA_HIDEOUT",  # Magmas Versteck (123)
    "MAPSEC_ROUTE_120",  # Route 120 (124)
    "MAPSEC_FORTREE_CITY",  # Baumhausen City (124)
    "MAPSEC_ANCIENT_TOMB",  # Grabmal (124)
    "MAPSEC_SCORCHED_SLAB",  # Sonnengrotte (125)
    "MAPSEC_DESERT_RUINS",  # Wüstenruine (125)
    "MAPSEC_MIRAGE_TOWER",  # Wunderturm (125)
    "MAPSEC_UNDERWATER_128",  # Unterwasser (127)
    "MAPSEC_UNDERWATER_127",  # Unterwasser (127)
    "MAPSEC_UNDERWATER_126",  # Unterwasser (127)
    "MAPSEC_UNDERWATER_124",  # Unterwasser (127)
    "MAPSEC_UNDERWATER_SEALED_CHAMBER",  # Siegelkammer (127)
    "MAPSEC_UNDERWATER_SEAFLOOR_CAVERN",  # Tiefseehöhle (127)
    "MAPSEC_UNDERWATER_SOOTOPOLIS",  # Unterwasser (127)
    "MAPSEC_SEALED_CHAMBER",  # Siegelkammer (128)
    "MAPSEC_SOOTOPOLIS_CITY",  # Xeneroville (128)
    "MAPSEC_SEAFLOOR_CAVERN",  # Tiefseehöhle (128)
    "MAPSEC_CAVE_OF_ORIGIN",  # Urzeithöhle (129)
    "MAPSEC_VICTORY_ROAD",  # Siegesstraße (130)
    "MAPSEC_BATTLE_FRONTIER",  # Kampfzone (140)
    "MAPSEC_ALTERING_CAVE",  # Wandelhöhle (140)
    "MAPSEC_UNDERWATER_MARINE_CAVE",  # Ozeanhöhle (141)
    "MAPSEC_UNDERWATER_129",  # Route 129 (141)
    "MAPSEC_UNDERWATER_125",  # Route 125 (141)
    "MAPSEC_TERRA_CAVE",  # Terrahöhle (141)
    "MAPSEC_UNDERWATER_105",  # Route 105 (141)
    "MAPSEC_MARINE_CAVE",  # Ozeanhöhle (142)
)

UNREACHED_MAPS = frozenset((
    "BattleColosseum_2P_Frlg",
    "BattleColosseum_2P_hns",
    "BattleColosseum_4P_Frlg",
    "BattleFrontier_BattlePyramidTop_hns",
    "BattleFrontier_BattleTowerBattleRoom_hns",
    "BattleFrontier_BattleTowerCorridor_hns",
    "BattleFrontier_BattleTowerElevator_hns",
    "BattleFrontier_BattleTowerMultiBattleRoom_hns",
    "BattleFrontier_BattleTowerMultiCorridor_hns",
    "BattleFrontier_BattleTowerMultiPartnerRoom_hns",
    "BattleFrontier_Lounge9_hns",
    "BattleFrontier_PokemonCenter_2F_hns",
    "BattlePyramidSquare01",
    "BattlePyramidSquare01_hns",
    "BattlePyramidSquare02",
    "BattlePyramidSquare02_hns",
    "BattlePyramidSquare03",
    "BattlePyramidSquare03_hns",
    "BattlePyramidSquare04",
    "BattlePyramidSquare04_hns",
    "BattlePyramidSquare05",
    "BattlePyramidSquare05_hns",
    "BattlePyramidSquare06",
    "BattlePyramidSquare06_hns",
    "BattlePyramidSquare07",
    "BattlePyramidSquare07_hns",
    "BattlePyramidSquare08",
    "BattlePyramidSquare08_hns",
    "BattlePyramidSquare09",
    "BattlePyramidSquare09_hns",
    "BattlePyramidSquare10",
    "BattlePyramidSquare10_hns",
    "BattlePyramidSquare11",
    "BattlePyramidSquare11_hns",
    "BattlePyramidSquare12",
    "BattlePyramidSquare12_hns",
    "BattlePyramidSquare13",
    "BattlePyramidSquare13_hns",
    "BattlePyramidSquare14",
    "BattlePyramidSquare14_hns",
    "BattlePyramidSquare15",
    "BattlePyramidSquare15_hns",
    "BattlePyramidSquare16",
    "BattlePyramidSquare16_hns",
    "BirthIsland_Exterior",
    "BirthIsland_Harbor",
    "BirthIsland_Harbor_hns",
    "ContestHall",
    "ContestHallBeauty",
    "ContestHallBeauty_hns",
    "ContestHallCool",
    "ContestHallCool_hns",
    "ContestHallCute",
    "ContestHallCute_hns",
    "ContestHallSmart",
    "ContestHallSmart_hns",
    "ContestHallTough",
    "ContestHallTough_hns",
    "ContestHall_hns",
    "EmbeddedTower_hns",
    "FarawayIsland_Entrance",
    "FarawayIsland_Entrance_hns",
    "FarawayIsland_Interior",
    "FarawayIsland_Interior_hns",
    "GoldenrodCity_DepartmentStoreElevator_hns",
    "GoldenrodCity_DepartmentStore_7FNight_hns",
    "IndigoPlateau_hns",
    "InsideOfTruck",
    "LakeOfRageLowTide_hns",
    "MossdeepCity_GameCorner_B1F",
    "MtSilver_SummitNight_hns",
    "NavelRock_B1F",
    "NavelRock_Bottom",
    "NavelRock_Down01",
    "NavelRock_Down02",
    "NavelRock_Down03",
    "NavelRock_Down04",
    "NavelRock_Down05",
    "NavelRock_Down06",
    "NavelRock_Down07",
    "NavelRock_Down08",
    "NavelRock_Down09",
    "NavelRock_Down10",
    "NavelRock_Down11",
    "NavelRock_Entrance",
    "NavelRock_Exterior",
    "NavelRock_Fork",
    "NavelRock_Harbor",
    "NavelRock_Top",
    "NavelRock_Up1",
    "NavelRock_Up2",
    "NavelRock_Up3",
    "NavelRock_Up4",
    "RecordCorner",
    "RecordCorner_Frlg",
    "SecretBase_BlueCave1",
    "SecretBase_BlueCave2",
    "SecretBase_BlueCave3",
    "SecretBase_BlueCave4",
    "SecretBase_BrownCave1",
    "SecretBase_BrownCave2",
    "SecretBase_BrownCave3",
    "SecretBase_BrownCave4",
    "SecretBase_RedCave1",
    "SecretBase_RedCave2",
    "SecretBase_RedCave3",
    "SecretBase_RedCave4",
    "SecretBase_Shrub1",
    "SecretBase_Shrub2",
    "SecretBase_Shrub3",
    "SecretBase_Shrub4",
    "SecretBase_Tree1",
    "SecretBase_Tree2",
    "SecretBase_Tree3",
    "SecretBase_Tree4",
    "SecretBase_YellowCave1",
    "SecretBase_YellowCave2",
    "SecretBase_YellowCave3",
    "SecretBase_YellowCave4",
    "ShoalCave_HighTideEntranceRoom",
    "ShoalCave_HighTideInnerRoom",
    "SouthernIsland_Exterior",
    "SouthernIsland_Exterior_hns",
    "SouthernIsland_Interior",
    "SouthernIsland_Interior_hns",
    "TinTower_RoofNight_hns",
    "TradeCenter_hns",
    "UnionRoom_hns",
))
