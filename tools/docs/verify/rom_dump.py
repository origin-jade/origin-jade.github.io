#!/usr/bin/env python3
"""Dump the data tables of a compiled game (ELF + ROM image) to JSON.

    python3 -I -B tools/docs/verify/rom_dump.py --lang de \\
        --elf <dir>/Pokemon_Origin_Jade.elf --gba <dir>/Pokemon_Origin_Jade.gba --out dump_de.json

This is the second, independent reading of the game data: nothing here parses
the C sources, the .party files or the JSON files. Symbol addresses come from
the ELF (arm-none-eabi-nm), the bytes from the ROM image (0x08000000 based;
every table is also compared with the ELF segment that holds it), the struct
layouts and the numeric constants from the project's compiler (cprobe.py), and
texts are decoded with charmap.txt.

What is dumped (key in the JSON):
    species      gSpeciesInfo incl. level-up/teachable/egg learnsets, evolutions, form tables
    moves        gMovesInfo
    abilities    gAbilitiesInfo
    items        gItemsInfo
    tmhm         gTMHMItemMoveIds
    tutor_moves  gTutorMoves
    types        gTypesInfo, type_chart gTypeEffectivenessTable
    natures      gNaturesInfo
    trainers     gTrainers[DIFFICULTY_NORMAL] with parties, partners gBattlePartners[DIFFICULTY_NORMAL]
    trainer_classes gTrainerClasses
    wild         gWildMonHeaders with every table, wild_rates (slot rates, see slot_rates())
    maps         gMapGroups -> map headers (map section, type), mapsecs gRegionMapEntries
    trades       sIngameTrades
    rematch      gRematchTable
    scaling      sJohtoCorridors, sRematchBandPlayerLevels, sTrainerEvoLevels, sRematchLevelCeilingByBadges
    dex          sKantoToNationalOrder, sJohtoToNationalOrder, sHoennToNationalOrder
    names        constant names of ids (SPECIES_, MOVE_, ...), for readable reports
    enumerators  for the real enums (moves, items, abilities, types, natures): the enumerator
                 names of every value, to check the constant names the data layer hands out
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cprobe          # noqa: E402
from romlib import Rom, Charmap  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

MOVE_FLAGS = [
    "multiHit", "explosion", "alwaysCriticalHit",
    "makesContact", "ignoresProtect", "magicCoatAffected", "snatchAffected", "ignoresKingsRock",
    "punchingMove", "bitingMove", "pulseMove", "soundMove", "ballisticMove", "powderMove", "danceMove",
    "windMove", "slicingMove", "healingMove", "minimizeDoubleDamage", "ignoresTargetAbility",
    "ignoresTargetDefenseEvasionStages", "damagesUnderground", "damagesUnderwater", "damagesAirborne",
    "damagesAirborneDoubleDamage", "ignoreTypeIfFlyingAndUngrounded", "thawsUser", "ignoresSubstitute",
    "forcePressure", "cantUseTwice", "alwaysHitsInRain", "accuracy50InSun", "alwaysHitsInHailSnow",
    "alwaysHitsOnSameType", "noAffectOnSameTypeTarget", "accIncreaseByTenOnSameType",
    "gravityBanned", "mirrorMoveBanned", "meFirstBanned", "mimicBanned", "metronomeBanned",
    "copycatBanned", "assistBanned", "sleepTalkBanned", "instructBanned", "encoreBanned",
    "parentalBondBanned", "skyBattleBanned", "sketchBanned", "dampBanned", "validApprenticeMove",
    "randomizerInvalid",
]
SPECIES_FLAGS = [
    "isRestrictedLegendary", "isSubLegendary", "isMythical", "isUltraBeast", "isParadox", "isTotem",
    "isMegaEvolution", "isPrimalReversion", "isUltraBurst", "isGigantamax", "isTeraForm", "isAlolanForm",
    "isGalarianForm", "isHisuianForm", "isPaldeanForm", "cannotBeTraded", "perfectIVCount",
    "dexForceRequired", "isFrontierBanned", "isSkyBattleBanned", "randomizerMode", "dexNotRequired",
]
ABILITY_FLAGS = ["cantBeCopied", "cantBeSwapped", "cantBeTraced", "cantBeSuppressed", "cantBeOverwritten",
                 "breakable", "failsOnImposter"]

STRUCTS = {
    "SpeciesInfo": ["baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack", "baseSpDefense",
                    "types[]", "catchRate", "expYield", "evYield_HP", "evYield_Attack", "evYield_Defense",
                    "evYield_Speed", "evYield_SpAttack", "evYield_SpDefense", "itemCommon", "itemRare",
                    "genderRatio", "eggCycles", "friendship", "growthRate", "eggGroups[]", "abilities[]",
                    "safariZoneFleeRate", "categoryName[]", "speciesName[]", "natDexNum", "height", "weight",
                    "description", "bodyColor", "iconPalIndex", "levelUpLearnset", "teachableLearnset",
                    "eggMoveLearnset", "evolutions", "formSpeciesIdTable"] + SPECIES_FLAGS,
    "LevelUpMove": ["move", "level"],
    "Evolution": ["method", "param", "targetSpecies", "params"],
    "EvolutionParam": ["condition", "arg1", "arg2", "arg3"],
    "MoveInfo": ["name", "description", "effect", "type", "category", "power", "accuracy", "target", "pp",
                 "priority", "strikeCount", "criticalHitStage", "numAdditionalEffects", "contestEffect",
                 "contestCategory"] + MOVE_FLAGS,
    "AbilityInfo": ["name[]", "description", "aiRating"] + ABILITY_FLAGS,
    "ItemInfo": ["price", "secondaryId", "description", "name", "pluralName", "holdEffect", "holdEffectParam",
                 "importance", "notConsumed", "pocket", "sortType", "type", "battleUsage", "flingPower"],
    "TmHmIndexKey": ["itemId", "moveId"],
    "TypeInfo": ["name[]", "generic[]", "palette", "damageCategory", "isSpecialCaseType", "isHiddenPowerType"],
    "NatureInfo": ["name", "statUp", "statDown"],
    "Trainer": ["aiFlags", "party", "items[]", "trainerClass", "encounterMusic", "gender", "trainerPic",
                "trainerName[]", "battleType", "mugshotColor", "partySize", "poolSize"],
    "TrainerMon": ["nickname", "ev", "iv", "moves[]", "species", "heldItem", "ability", "lvl", "ball",
                   "friendship", "nature", "gender", "isShiny", "teraType", "gigantamaxFactor",
                   "dynamaxLevel", "tags"],
    "TrainerClass": ["name[]", "money", "ball"],
    "WildPokemon": ["minLevel", "maxLevel", "species"],
    "WildPokemonInfo": ["encounterRate", "wildPokemon"],
    "WildEncounterTypes": ["landMonsInfo", "waterMonsInfo", "rockSmashMonsInfo", "fishingMonsInfo",
                           "hiddenMonsInfo"],
    "WildPokemonHeader": ["mapGroup", "mapNum", "encounterTypes[]"],
    "MapHeader": ["mapLayoutId", "regionMapSectionId", "cave", "weather", "mapType", "battleType"],
    "RegionMapLocation": ["x", "y", "width", "height", "name"],
    "RematchTrainer": ["trainerIds[]", "mapGroup", "mapNum"],
    # defined in .c files; their definitions are taken over verbatim (extract_struct)
    "InGameTrade": ["nickname[]", "species", "ivs[]", "abilityNum", "otId", "conditions[]", "personality",
                    "heldItem", "mailNum", "otName[]", "otGender", "sheen", "requestedSpecies"],
    "ScalingCorridor": ["mapsec", "floor", "ceiling", "storyCeiling", "storyVar", "storyValue"],
    "TrainerEvoLevel": ["species", "level"],
}
C_FILE_STRUCTS = {"InGameTrade": "src/trade.c", "ScalingCorridor": "src/level_scaling.c",
                  "TrainerEvoLevel": "src/level_scaling.c"}
INCLUDES = ["global.h", "main.h", "pokemon.h", "move.h", "item.h", "data.h", "battle.h", "battle_main.h",
            "wild_encounter.h", "region_map.h", "battle_setup.h", "gym_leader_rematch.h", "rtc.h",
            "constants/species.h", "constants/moves.h", "constants/items.h", "constants/abilities.h",
            "constants/pokemon.h", "constants/pokedex.h", "constants/trainers.h", "constants/opponents.h",
            "constants/battle.h", "constants/battle_move_effects.h", "constants/hold_effects.h",
            "constants/maps.h", "constants/map_types.h", "constants/region_map_sections.h",
            "constants/rtc.h", "constants/wild_encounter.h", "constants/tms_hms.h", "constants/difficulty.h",
            "constants/rematches.h", "constants/battle_partner.h", "constants/item.h",
            "constants/contest.h", "constants/weather.h", "constants/flags.h", "constants/vars.h",
            # written by the build; defines the ENCOUNTER_CHANCE_* slot constants next to the tables
            "../src/data/wild_encounters.h"]
CONST_PREFIXES = (
    "SPECIES_", "MOVE_", "ITEM_", "ABILITY_", "TYPE_", "NATURE_", "EGG_GROUP_", "GROWTH_", "EVO_", "IF_",
    "EFFECT_", "TARGET_", "MOVE_TARGET_", "DAMAGE_CATEGORY_", "POCKET_", "HOLD_EFFECT_", "TRAINER_",
    "PARTNER_", "MAPSEC_", "MAP_", "TIME_", "TIMES_", "STAT_", "NATIONAL_DEX_", "OBTAINABLE_DEX_",
    "KANTO_DEX_", "JOHTO_DEX_", "HOENN_DEX_", "REMATCH_", "REMATCHES_", "ENCOUNTER_CHANCE_", "DIFFICULTY_",
    "NUM_", "NUMBER_OF_", "MAX_", "LEVEL_UP_", "EVOLUTIONS_", "CONDITIONS_", "FORM_SPECIES_", "PARTY_",
    "POKEBALL_", "BALL_", "BODY_COLOR_", "CONTEST_", "MON_", "LAND_WILD_", "WATER_WILD_", "ROCK_WILD_",
    "FISH_WILD_", "HIDDEN_WILD_", "BATTLE_TYPE_", "FRLG_", "TRAINERS_", "KANTO_MAPSEC_", "ITEMS_",
    "MOVES_", "ABILITIES_", "POKEMON_NAME_", "TRAINER_NAME_", "OW_", "P_", "B_", "I_", "GEN_",
)
EXPRS = {
    "sizeof_Move": "sizeof(enum Move)",
    "sizeof_NationalDexOrder": "sizeof(enum NationalDexOrder)",
    "sizeof_uq4_12": "sizeof(uq4_12_t)",
    "sizeof_Type": "sizeof(enum Type)",
    "sizeof_Item": "sizeof(enum Item)",
    "sizeof_Ability": "sizeof(enum Ability)",
    "offsetof_encounterTypes": "offsetof(struct WildPokemonHeader, encounterTypes)",
}
NAME_PREFIXES = ("SPECIES_", "MOVE_", "ITEM_", "ABILITY_", "TYPE_", "NATURE_", "EGG_GROUP_", "GROWTH_",
                 "EVO_", "IF_", "EFFECT_", "POCKET_", "HOLD_EFFECT_", "TRAINER_CLASS_", "MAPSEC_", "TIME_",
                 "STAT_", "REMATCH_", "TRAINER_PIC_", "PARTNER_")


def extract_struct(repo, path, name):
    """The definition `struct name {...};` exactly as written in a .c file."""
    src = open(os.path.join(repo, path), encoding="utf-8").read()
    m = re.search(r"^struct %s\s*\{.*?^\};" % re.escape(name), src, re.S | re.M)
    if not m:
        raise RuntimeError("struct %s not found in %s" % (name, path))
    return m.group(0) + "\n"


class Dumper:
    def __init__(self, repo, lang, elf, gba, work):
        self.repo, self.lang = repo, lang
        self.rom = Rom(elf, gba)
        self.cm = Charmap(os.path.join(repo, "charmap.txt"))
        extra = "".join(extract_struct(repo, p, n) for n, p in C_FILE_STRUCTS.items())
        self.lay, self.c, self.dropped, self.enum_names = cprobe.build(
            repo, lang, work, STRUCTS, lambda n: n.startswith(CONST_PREFIXES), INCLUDES,
            extra_source=extra, exprs=EXPRS)
        self.S = {n: cprobe.Struct(self.lay, n) for n in STRUCTS}
        self.sym_at = {}
        for name, (addr, size) in self.rom.syms.items():
            if size and self.rom.in_rom(addr):
                self.sym_at.setdefault(addr, (name, size))
        self.notes = []

    # ------------------------------------------------------------ helpers
    def const(self, name):
        if name not in self.c:
            raise KeyError("constant %s was not evaluated by the compiler" % name)
        return self.c[name]

    def text(self, ptr):
        """Game string at a ROM pointer (None for NULL / outside the ROM)."""
        if not ptr or not self.rom.in_rom(ptr):
            return None
        return self.cm.decode(self.rom.cstr(ptr))

    def fixed(self, st, buf, off, field):
        return self.cm.decode_fixed(st.raw(buf, off, field))

    def table(self, sym, struct):
        """(bytes, struct reader, entry count) of an array symbol."""
        st = self.S[struct]
        b = self.rom.table_bytes(sym)
        if len(b) % st.size:
            raise ValueError("%s: size %d is not a multiple of sizeof(struct %s) = %d"
                             % (sym, len(b), struct, st.size))
        return b, st, len(b) // st.size

    def ints(self, sym, width):
        b = self.rom.table_bytes(sym)
        return [int.from_bytes(b[i:i + width], "little") for i in range(0, len(b) - width + 1, width)]

    def list_until(self, ptr, width, end, limit=4000):
        out = []
        if not ptr or not self.rom.in_rom(ptr):
            return out
        for i in range(limit):
            v = int.from_bytes(self.rom.bytes(ptr + i * width, width), "little")
            if v == end:
                return out
            out.append(v)
        raise ValueError("list at 0x%08X has no terminator" % ptr)

    # ------------------------------------------------------------ tables
    def species(self):
        b, st, n = self.table("gSpeciesInfo", "SpeciesInfo")
        lu, evo, evp = self.S["LevelUpMove"], self.S["Evolution"], self.S["EvolutionParam"]
        w_move = self.const("=sizeof_Move")
        lvl_end = self.const("LEVEL_UP_MOVE_END")
        evo_end, cond_end = self.const("EVOLUTIONS_END"), self.const("CONDITIONS_END")
        out = {}
        for i in range(n):
            off = i * st.size
            if not any(b[off:off + st.size]):
                continue
            g = lambda f: st.get(b, off, f)
            e = dict(
                name=self.fixed(st, b, off, "speciesName"), category=self.fixed(st, b, off, "categoryName"),
                description=self.text(g("description")),
                types=st.array(b, off, "types"),
                stats=dict(hp=g("baseHP"), atk=g("baseAttack"), **{"def": g("baseDefense")},
                           spa=g("baseSpAttack"), spd=g("baseSpDefense"), spe=g("baseSpeed")),
                ev_yield=dict(hp=g("evYield_HP"), atk=g("evYield_Attack"), **{"def": g("evYield_Defense")},
                              spa=g("evYield_SpAttack"), spd=g("evYield_SpDefense"), spe=g("evYield_Speed")),
                abilities=st.array(b, off, "abilities"), catch_rate=g("catchRate"), exp_yield=g("expYield"),
                gender_ratio=g("genderRatio"), egg_groups=st.array(b, off, "eggGroups"),
                egg_cycles=g("eggCycles"), growth_rate=g("growthRate"), friendship=g("friendship"),
                held_common=g("itemCommon"), held_rare=g("itemRare"), natdex=g("natDexNum"),
                height=g("height"), weight=g("weight"), body_color=g("bodyColor"),
                icon_pal_index=g("iconPalIndex"), safari_flee_rate=g("safariZoneFleeRate"),
                flags={f: g(f) for f in SPECIES_FLAGS if g(f)},
            )
            lv = []
            p = g("levelUpLearnset")
            if p and self.rom.in_rom(p):
                for k in range(400):
                    eb = self.rom.bytes(p + k * lu.size, lu.size)
                    mv, lvv = lu.get(eb, 0, "move"), lu.get(eb, 0, "level")
                    if mv == lvl_end:
                        break
                    lv.append([lvv, mv])
                else:
                    raise ValueError("level-up learnset of species %d has no end" % i)
            e["levelup"] = lv
            e["teachable"] = self.list_until(g("teachableLearnset"), w_move, self.const("MOVE_UNAVAILABLE"))
            e["egg_moves"] = self.list_until(g("eggMoveLearnset"), w_move, self.const("MOVE_UNAVAILABLE"))
            evs = []
            p = g("evolutions")
            if p and self.rom.in_rom(p):
                for k in range(64):
                    eb = self.rom.bytes(p + k * evo.size, evo.size)
                    method = evo.get(eb, 0, "method")
                    if method == evo_end:
                        break
                    conds = []
                    pp = evo.get(eb, 0, "params")
                    if pp and self.rom.in_rom(pp):
                        for j in range(16):
                            cb = self.rom.bytes(pp + j * evp.size, evp.size)
                            c = evp.get(cb, 0, "condition")
                            if c == cond_end:
                                break
                            conds.append([c, evp.get(cb, 0, "arg1"), evp.get(cb, 0, "arg2"), evp.get(cb, 0, "arg3")])
                    evs.append(dict(method=method, param=evo.get(eb, 0, "param"),
                                    target=evo.get(eb, 0, "targetSpecies"), conditions=conds))
            e["evolutions"] = evs
            e["forms"] = self.list_until(g("formSpeciesIdTable"), 2, self.const("FORM_SPECIES_END"))
            out[i] = e
        return out

    def moves(self):
        b, st, n = self.table("gMovesInfo", "MoveInfo")
        out = {}
        for i in range(n):
            off = i * st.size
            g = lambda f: st.get(b, off, f)
            out[i] = dict(
                name=self.text(g("name")), description=self.text(g("description")), effect=g("effect"),
                type=g("type"), category=g("category"), power=g("power"), accuracy=g("accuracy"),
                target=g("target"), pp=g("pp"), priority=g("priority"), strike_count=g("strikeCount"),
                crit_stage=g("criticalHitStage"), num_additional_effects=g("numAdditionalEffects"),
                contest_effect=g("contestEffect"), contest_category=g("contestCategory"),
                flags=[f for f in MOVE_FLAGS if g(f)])
        return out

    def abilities(self):
        b, st, n = self.table("gAbilitiesInfo", "AbilityInfo")
        out = {}
        for i in range(n):
            off = i * st.size
            out[i] = dict(name=self.fixed(st, b, off, "name"), description=self.text(st.get(b, off, "description")),
                          ai_rating=st.get(b, off, "aiRating"),
                          flags=[f for f in ABILITY_FLAGS if st.get(b, off, f)])
        return out

    def items(self):
        b, st, n = self.table("gItemsInfo", "ItemInfo")
        out = {}
        for i in range(n):
            off = i * st.size
            g = lambda f: st.get(b, off, f)
            out[i] = dict(name=self.text(g("name")), plural=self.text(g("pluralName")),
                          description=self.text(g("description")), price=g("price"),
                          secondary_id=g("secondaryId"), hold_effect=g("holdEffect"),
                          hold_effect_param=g("holdEffectParam"), importance=g("importance"),
                          not_consumed=g("notConsumed"), pocket=g("pocket"), sort_type=g("sortType"),
                          type=g("type"), battle_usage=g("battleUsage"), fling_power=g("flingPower"))
        return out

    def tmhm(self):
        b, st, n = self.table("gTMHMItemMoveIds", "TmHmIndexKey")
        return [[st.get(b, i * st.size, "itemId"), st.get(b, i * st.size, "moveId")] for i in range(n)]

    def types(self):
        b, st, n = self.table("gTypesInfo", "TypeInfo")
        out = {}
        for i in range(n):
            off = i * st.size
            out[i] = dict(name=self.fixed(st, b, off, "name"), generic=self.fixed(st, b, off, "generic"),
                          palette=st.get(b, off, "palette"), damage_category=st.get(b, off, "damageCategory"),
                          special=st.get(b, off, "isSpecialCaseType"),
                          hidden_power=st.get(b, off, "isHiddenPowerType"))
        w = self.const("=sizeof_uq4_12")
        vals = self.ints("gTypeEffectivenessTable", w)
        nt = self.const("NUMBER_OF_MON_TYPES")
        if nt * nt != len(vals):
            raise ValueError("gTypeEffectivenessTable: %d values, NUMBER_OF_MON_TYPES = %d" % (len(vals), nt))
        chart = [vals[r * nt:(r + 1) * nt] for r in range(nt)]
        return out, chart

    def natures(self):
        b, st, n = self.table("gNaturesInfo", "NatureInfo")
        return {i: dict(name=self.text(st.get(b, i * st.size, "name")), stat_up=st.get(b, i * st.size, "statUp"),
                        stat_down=st.get(b, i * st.size, "statDown")) for i in range(n)}

    def _trainer(self, st, b, off):
        g = lambda f: st.get(b, off, f)
        ms, mons = self.S["TrainerMon"], []
        p, size = g("party"), g("partySize")
        if size and not (p and self.rom.in_rom(p)):
            raise ValueError("trainer with partySize %d has no party" % size)
        for k in range(size):
            mb = self.rom.bytes(p + k * ms.size, ms.size)
            m = lambda f: ms.get(mb, 0, f)
            iv = m("iv")
            evp = m("ev")
            ev = None
            if evp and self.rom.in_rom(evp):
                e = self.rom.bytes(evp, 6)      # TRAINER_PARTY_EVS: hp, atk, def, spatk, spdef, speed
                ev = dict(hp=e[0], atk=e[1], **{"def": e[2]}, spa=e[3], spd=e[4], spe=e[5])
            mons.append(dict(
                species=m("species"), level=m("lvl"), item=m("heldItem"), moves=ms.array(mb, 0, "moves"),
                ability=m("ability"), nature=m("nature"),
                # TRAINER_PARTY_IVS: hp | atk << 5 | def << 10 | speed << 15 | spatk << 20 | spdef << 25
                iv_raw=iv, ivs=dict(hp=iv & 31, atk=iv >> 5 & 31, **{"def": iv >> 10 & 31}, spe=iv >> 15 & 31,
                                    spa=iv >> 20 & 31, spd=iv >> 25 & 31),
                evs=ev, nickname=self.text(m("nickname")), gender=m("gender"), shiny=m("isShiny"),
                ball=m("ball"), friendship=m("friendship"), tera_type=m("teraType"),
                dynamax_level=m("dynamaxLevel"), tags=m("tags")))
        return dict(name=self.fixed(st, b, off, "trainerName"), trainer_class=g("trainerClass"),
                    pic=g("trainerPic"), gender=g("gender"), music=g("encounterMusic"),
                    battle_type=g("battleType"), items=st.array(b, off, "items"), ai_flags=g("aiFlags"),
                    mugshot_color=g("mugshotColor"), party_size=size, pool_size=g("poolSize"), party=mons)

    def trainers(self, sym="gTrainers"):
        b, st, total = self.table(sym, "Trainer")
        nd = self.const("DIFFICULTY_COUNT")
        if total % nd:
            raise ValueError("%s: %d entries, DIFFICULTY_COUNT %d" % (sym, total, nd))
        per = total // nd
        normal = self.const("DIFFICULTY_NORMAL")
        out = {}
        for i in range(per):
            off = (normal * per + i) * st.size
            out[i] = self._trainer(st, b, off)
        other = {}
        for d in range(nd):
            if d != normal:
                other[d] = sum(1 for i in range(per) if any(b[(d * per + i) * st.size:(d * per + i + 1) * st.size]))
        return out, other

    def trainer_classes(self):
        b, st, n = self.table("gTrainerClasses", "TrainerClass")
        return {i: dict(name=self.fixed(st, b, i * st.size, "name"), money=st.get(b, i * st.size, "money"),
                        ball=st.get(b, i * st.size, "ball")) for i in range(n)}

    def wild(self):
        b, st, n = self.table("gWildMonHeaders", "WildPokemonHeader")
        et, info, mon = self.S["WildEncounterTypes"], self.S["WildPokemonInfo"], self.S["WildPokemon"]
        times = self.const("TIMES_OF_DAY_COUNT")
        base = self.const("=offsetof_encounterTypes")
        areas = (("land", "landMonsInfo", "LAND_WILD_COUNT"), ("water", "waterMonsInfo", "WATER_WILD_COUNT"),
                 ("rock_smash", "rockSmashMonsInfo", "ROCK_WILD_COUNT"),
                 ("fishing", "fishingMonsInfo", "FISH_WILD_COUNT"), ("hidden", "hiddenMonsInfo", "HIDDEN_WILD_COUNT"))
        undefined = self.const("MAP_UNDEFINED")
        out = []
        for i in range(n):
            off = i * st.size
            grp, num = st.get(b, off, "mapGroup"), st.get(b, off, "mapNum")
            if (num | grp << 8) == undefined:
                if i != n - 1:
                    raise ValueError("gWildMonHeaders: end marker at %d of %d" % (i, n))
                break
            h = dict(index=i, group=grp, num=num, times=[])
            for t in range(times):
                eo = off + base + t * et.size
                tabs = {}
                for key, field, count_const in areas:
                    p = et.get(b, eo, field)
                    if not p:
                        continue
                    ib = self.rom.bytes(p, info.size)
                    mp = info.get(ib, 0, "wildPokemon")
                    name, size = self.sym_at.get(mp, (None, 0))
                    count = size // mon.size if size else self.const(count_const)
                    if count != self.const(count_const):
                        self.notes.append("wild table %s has %d slots, %s = %d"
                                          % (name, count, count_const, self.const(count_const)))
                    mons = []
                    for k in range(count):
                        mb = self.rom.bytes(mp + k * mon.size, mon.size)
                        mons.append([mon.get(mb, 0, "minLevel"), mon.get(mb, 0, "maxLevel"), mon.get(mb, 0, "species")])
                    tabs[key] = dict(rate=info.get(ib, 0, "encounterRate"), mons=mons,
                                     symbol=self.sym_at.get(p, (None, 0))[0])
                h["times"].append(tabs)
            out.append(h)
        return out

    def slot_rates(self):
        """Slot chances per area. The game has them as immediate numbers inside
        ChooseWildMonIndex_*, not as a table; they are taken from the cumulative
        ENCOUNTER_CHANCE_* constants of the build's generated header as the
        project's compiler evaluates them."""
        out = {}
        for area, pre, slots in (("land", "LAND_MONS", range(12)), ("water", "WATER_MONS", range(5)),
                                 ("rock_smash", "ROCK_SMASH_MONS", range(5)),
                                 ("old_rod", "FISHING_MONS_OLD_ROD", range(0, 2)),
                                 ("good_rod", "FISHING_MONS_GOOD_ROD", range(2, 5)),
                                 ("super_rod", "FISHING_MONS_SUPER_ROD", range(5, 10))):
            prev, rates = 0, {}
            for s in slots:
                cum = self.const("ENCOUNTER_CHANCE_%s_SLOT_%d" % (pre, s))
                rates[s] = cum - prev
                prev = cum
            if prev != self.const("ENCOUNTER_CHANCE_%s_TOTAL" % pre):
                raise ValueError("slot chances of %s do not add up" % area)
            out[area] = rates
        return out

    def maps(self):
        ga, _ = self.rom.sym("gMapGroups")
        ng = self.const("MAP_GROUPS_COUNT")
        ptrs = [self.rom.u32(ga + 4 * i) for i in range(ng)]
        st = self.S["MapHeader"]
        ends = sorted(set(ptrs + [ga]))
        out = []
        for g, p in enumerate(ptrs):
            end = ends[ends.index(p) + 1]
            for k in range((end - p) // 4):
                hp = self.rom.u32(p + 4 * k)
                if hp == 0:          # ".4byte NULL": an unused map number
                    continue
                if not self.rom.in_rom(hp):
                    raise ValueError("map group %d entry %d is not a ROM pointer" % (g, k))
                hb = self.rom.bytes(hp, st.size)
                out.append(dict(group=g, num=k, mapsec=st.get(hb, 0, "regionMapSectionId"),
                                map_type=st.get(hb, 0, "mapType"), layout=st.get(hb, 0, "mapLayoutId"),
                                weather=st.get(hb, 0, "weather"), battle_type=st.get(hb, 0, "battleType"),
                                symbol=self.sym_at.get(hp, (None, 0))[0]))
        return out

    def mapsecs(self):
        b, st, n = self.table("gRegionMapEntries", "RegionMapLocation")
        return {i: dict(name=self.text(st.get(b, i * st.size, "name")), x=st.get(b, i * st.size, "x"),
                        y=st.get(b, i * st.size, "y"), width=st.get(b, i * st.size, "width"),
                        height=st.get(b, i * st.size, "height")) for i in range(n)}

    def trades(self):
        b, st, n = self.table("sIngameTrades", "InGameTrade")
        out = []
        for i in range(n):
            off = i * st.size
            g = lambda f: st.get(b, off, f)
            out.append(dict(nickname=self.fixed(st, b, off, "nickname"), species=g("species"),
                            ivs=st.array(b, off, "ivs"), ability_num=g("abilityNum"), ot_id=g("otId"),
                            conditions=st.array(b, off, "conditions"), personality=g("personality"),
                            held_item=g("heldItem"), mail_num=g("mailNum"),
                            ot_name=self.fixed(st, b, off, "otName"), ot_gender=g("otGender"),
                            sheen=g("sheen"), requested_species=g("requestedSpecies")))
        return out

    def rematch(self):
        b, st, n = self.table("gRematchTable", "RematchTrainer")
        return [dict(trainers=st.array(b, i * st.size, "trainerIds"), group=st.get(b, i * st.size, "mapGroup"),
                     num=st.get(b, i * st.size, "mapNum")) for i in range(n)]

    def scaling(self):
        out = {}
        b, st, n = self.table("sJohtoCorridors", "ScalingCorridor")
        out["johto_corridors"] = [{f: st.get(b, i * st.size, f) for f in STRUCTS["ScalingCorridor"]} for i in range(n)]
        out["band_player_levels"] = list(self.rom.table_bytes("sRematchBandPlayerLevels"))
        b, st, n = self.table("sTrainerEvoLevels", "TrainerEvoLevel")
        out["trainer_evo_levels"] = [[st.get(b, i * st.size, "species"), st.get(b, i * st.size, "level")] for i in range(n)]
        if self.rom.has("sRematchLevelCeilingByBadges"):
            out["rematch_level_ceilings"] = list(self.rom.table_bytes("sRematchLevelCeilingByBadges"))
        return out

    def dex(self):
        w = self.const("=sizeof_NationalDexOrder")
        return {k: self.ints("s%sToNationalOrder" % k.capitalize(), w) for k in ("kanto", "johto", "hoenn")}

    def names(self):
        out = {}
        for pre in NAME_PREFIXES:
            rev = {}
            for n, v in self.c.items():
                if n.startswith(pre) and not n.startswith("="):
                    rev.setdefault(v, n)
            out[pre] = rev
        return out

    def dump_names(self):
        """Only the tables that carry names and texts (for a ROM of another state of the
        game, e.g. the English branch: its data tables may have another shape, and
        symbols this tool reads for the full dump may not exist there)."""
        d = {}
        d["meta"] = dict(lang=self.lang, elf=os.path.basename(self.rom.elf.path), rom_size=len(self.rom.gba),
                         names_only=True)
        skipped = {}
        for key, fn in (("species", self.species), ("moves", self.moves), ("abilities", self.abilities),
                        ("items", self.items), ("types", lambda: self.types()[0]), ("natures", self.natures),
                        ("trainers", lambda: self.trainers("gTrainers")[0]),
                        ("partners", lambda: self.trainers("gBattlePartners")[0]),
                        ("trainer_classes", self.trainer_classes), ("mapsecs", self.mapsecs),
                        ("trades", self.trades), ("names", self.names)):
            try:
                d[key] = fn()
            except Exception as e:      # a table this state of the game does not have in that shape
                skipped[key] = "%s: %s" % (type(e).__name__, e)
        d["constants"] = {k: v for k, v in self.c.items() if not k.startswith("=")}
        d["meta"]["skipped"] = skipped
        d["meta"]["tables_checked_against_elf"] = self.rom.checked
        d["meta"]["notes"] = self.notes
        return d

    def dump(self):
        d = {}
        d["meta"] = dict(lang=self.lang, elf=os.path.basename(self.rom.elf.path), rom_size=len(self.rom.gba),
                         sizeof={k: v["size"] for k, v in self.lay.items()},
                         constants_evaluated=len(self.c), constants_skipped=len(self.dropped))
        d["species"] = self.species()
        d["moves"] = self.moves()
        d["abilities"] = self.abilities()
        d["items"] = self.items()
        d["tmhm"] = self.tmhm()
        d["tutor_moves"] = self.list_until(self.rom.sym("gTutorMoves")[0], self.const("=sizeof_Move"),
                                           self.const("MOVE_UNAVAILABLE"))
        d["types"], d["type_chart"] = self.types()
        d["natures"] = self.natures()
        d["trainers"], d["trainers_other_difficulties"] = self.trainers("gTrainers")
        d["partners"], _ = self.trainers("gBattlePartners")
        d["trainer_classes"] = self.trainer_classes()
        d["wild"] = self.wild()
        d["wild_rates"] = self.slot_rates()
        d["maps"] = self.maps()
        d["mapsecs"] = self.mapsecs()
        d["trades"] = self.trades()
        d["rematch"] = self.rematch()
        d["scaling"] = self.scaling()
        d["dex"] = self.dex()
        d["names"] = self.names()
        # ids of real enums (enum Move, enum Item, enum Ability ...): every enumerator of a value
        en = {}
        for pre in ("MOVE_", "ITEM_", "ABILITY_", "TYPE_", "NATURE_"):
            rev = {}
            for n in sorted(self.enum_names):
                if n.startswith(pre):
                    rev.setdefault(self.c[n], []).append(n)
            en[pre] = rev
        d["enumerators"] = en
        d["constants"] = {k: v for k, v in self.c.items() if not k.startswith("=")}
        d["meta"]["tables_checked_against_elf"] = self.rom.checked
        d["meta"]["notes"] = self.notes
        return d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lang", choices=("de", "en"), required=True)
    ap.add_argument("--elf", required=True)
    ap.add_argument("--gba", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default=REPO, help="source tree the ROM was built from (headers, charmap.txt)")
    ap.add_argument("--work", default=None, help="folder for the probe object (default: next to --out)")
    ap.add_argument("--names-only", action="store_true",
                    help="only the tables with names and texts (ROM of another state of the game, see en_names_check.py)")
    a = ap.parse_args()
    work = a.work or os.path.join(os.path.dirname(os.path.abspath(a.out)), "probe")
    dumper = Dumper(a.repo, a.lang, a.elf, a.gba, work)
    d = dumper.dump_names() if a.names_only else dumper.dump()
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, sort_keys=True, indent=None, separators=(",", ":"))
    m = d["meta"]
    if a.names_only:
        print("%s: names of %s; skipped: %s" % (a.out, ", ".join("%d %s" % (len(d[k]), k) for k in sorted(d)
                                                                 if k not in ("meta", "constants", "names")),
                                              m["skipped"] or "nothing"))
        return
    print("%s: %d species, %d moves, %d abilities, %d items, %d trainers, %d wild headers, %d maps; "
          "%d tables identical in ELF and ROM image"
          % (a.out, len(d["species"]), len(d["moves"]), len(d["abilities"]), len(d["items"]),
             len(d["trainers"]), len(d["wild"]), len(d["maps"]), m["tables_checked_against_elf"]))
    if m["notes"]:
        print("%d notes in meta.notes, e.g.: %s" % (len(m["notes"]), m["notes"][0]))


if __name__ == "__main__":
    main()
