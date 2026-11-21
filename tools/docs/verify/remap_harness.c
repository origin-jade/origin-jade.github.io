// Host harness for remap_check.py: runs the game's own level rules on the PC.
//
// Compiled natively (gcc) with the project's headers and build defines. The
// rules themselves are not written here:
//   * src/level_scaling.c is included as a whole (below),
//   * remap_extracted.inc holds functions cut verbatim out of src/battle_setup.c,
//     src/wild_encounter.c, src/rtc.c, src/pokemon.c and src/difficulty.c by remap_check.py,
//   * remap_tables.h holds the tables of the compiled game (from the ROM dump):
//     trainers with their parties, battle partners, the rematch table,
//     evolutions and the wild encounter headers.
// What is written here: the game state the rules read (current map, progress
// flags, badge counts, time of day, the trainer battle parameters), stubs for
// engine functions outside the rules, and a driver that calls the rules the
// way src/battle_main.c (CreateNPCTrainerPartyWithId), src/battle_partner.c
// (FillPartnerParty) and src/wild_encounter.c (TryGenerateWildMon) do.
//
// Protocol: one command per input line, one result line per command that
// prints (see main()).
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "global.h"
#undef ARM_FUNC
#define ARM_FUNC
#include "battle.h"
#include "battle_pike.h"
#include "battle_pyramid.h"
#include "battle_setup.h"
#include "data.h"
#include "debug.h"
#include "difficulty.h"
#include "event_data.h"
#include "overworld.h"
#include "pokemon.h"
#include "rtc.h"
#include "wild_encounter.h"
#include "constants/battle_partner.h"
#include "constants/battle_pyramid.h"
#include "constants/battle_setup.h"
#include "constants/flags.h"
#include "constants/maps.h"
#include "constants/rematches.h"
#include "constants/vars.h"
#include "constants/wild_encounter.h"

// ---------------------------------------------------------------- game state
struct MapHeader gMapHeader;
static struct SaveBlock1 sSaveBlock1;
struct SaveBlock1 *gSaveBlock1Ptr = &sSaveBlock1;
TrainerBattleParameter gTrainerBattleParameter;
bool8 gIsDebugBattle = FALSE;

static bool8 hChampion[3];     // Kanto, Johto, Hoenn title
static u32 hBadges[3];         // badges per region
static bool8 hLeaderFlag;      // FLAG_TEMP_KANTO_LEADER_REMATCH (set by the gym scripts)
static enum TimeOfDay hTime;

static void Unexpected(const char *what, long v)
{
    fprintf(stderr, "remap_harness: %s(%ld) is not provided by the harness\n", what, v);
    exit(3);
}

// ---------------------------------------------------------------- stubs
bool8 FlagGet(u16 id)
{
    switch (id)
    {
    case FLAG_IS_KANTO_CHAMPION: return hChampion[0];
    case FLAG_IS_JOHTO_CHAMPION: return hChampion[1];
    case FLAG_IS_HOENN_CHAMPION: return hChampion[2];
    case FLAG_TEMP_KANTO_LEADER_REMATCH: return hLeaderFlag;
    case FLAG_BADGE03_GET: return hBadges[0] >= 3;
    }
    Unexpected("FlagGet", id);
    return FALSE;
}

u8 FlagSet(u16 id) { return 0; }

u16 VarGet(u16 id)
{
    if (id == VAR_ALTERING_CAVE_WILD_SET)
        return 0;
    Unexpected("VarGet", id);
    return 0;
}

u32 GetKantoBadgeCount(void) { return hBadges[0]; }
u32 GetJohtoBadgeCount(void) { return hBadges[1]; }
u32 GetHoennBadgeCount(void) { return hBadges[2]; }
enum TimeOfDay GetTimeOfDay(void) { return hTime; }
bool8 InBattlePike(void) { return FALSE; }
u8 CurrentBattlePyramidLocation(void) { return PYRAMID_LOCATION_NONE; }
const struct Trainer *GetDebugAiTrainer(void) { return NULL; }
enum DifficultyLevel GetCurrentDifficultyLevel(void) { return DIFFICULTY_NORMAL; }
// An assertf of the game's code firing (an id outside its table, a species that is
// not in this build): a development build shows a crash screen there, a release
// build goes on with the recovery value. The harness goes on like a release build
// and appends " !<message>" to the result line of the command.
static char hAssert[200];
void AssertfCrashScreen(const void *return0, const char *fmt, ...)
{
    va_list ap;
    char *p;

    va_start(ap, fmt);
    vsnprintf(hAssert, sizeof(hAssert), fmt, ap);
    va_end(ap);
    for (p = hAssert; *p; p++)
        if (*p == ' ' || *p == '\n') *p = '_';
}
static void EndLine(void)
{
    if (hAssert[0])
        printf(" !%s", hAssert);
    hAssert[0] = 0;
    printf("\n");
}
enum DifficultyLevel GetBattlePartnerDifficultyLevel(u16 partnerId) { return DIFFICULTY_NORMAL; }

// ---------------------------------------------------------------- the game's tables and rules
#include "remap_tables.h"
#include "src/level_scaling.c"
#include "remap_extracted.inc"

// ---------------------------------------------------------------- driver
static void SetMap(int group, int num, int mapsec)
{
    gSaveBlock1Ptr->location.mapGroup = group;
    gSaveBlock1Ptr->location.mapNum = num;
    gMapHeader.regionMapSectionId = mapsec;
}

// src/battle_main.c CreateNPCTrainerPartyWithId: the first monsCount Pokemon, the
// party maximum over them, then level and species per Pokemon.
static void TrainerTeam(u16 trainerId, int mode, int monsCount)
{
    const struct Trainer *trainer = GetTrainerStructFromId(trainerId);
    u8 scalingPartyMaxLvl = 0;
    int i;

    memset(&gTrainerBattleParameter, 0, sizeof(gTrainerBattleParameter));
    TRAINER_BATTLE_PARAM.mode = mode;
    TRAINER_BATTLE_PARAM.opponentA = trainerId;
    if (monsCount > trainer->partySize)
        monsCount = trainer->partySize;
    for (i = 0; i < monsCount; i++)
    {
        if (trainer->party[i].lvl > scalingPartyMaxLvl)
            scalingPartyMaxLvl = trainer->party[i].lvl;
    }
    printf("T %d %d %d", IsNormalPhoneRematchBattle(trainerId) ? 1 : 0,
           IsKantoLeaderRematchBattle(trainerId) ? 1 : 0, monsCount);
    for (i = 0; i < monsCount; i++)
    {
        u8 scaledLvl = ScaleTrainerMonLevel(trainer, trainerId, trainer->party[i].lvl, scalingPartyMaxLvl);
        u16 species = ScaleTrainerMonSpecies(trainer->party[i].species, scaledLvl, trainerId, i);
        printf(" %d %d", scaledLvl, species);
    }
    EndLine();
}

// src/battle_partner.c FillPartnerParty: the first 3 Pokemon of the partner.
static void PartnerTeam(int partner, u16 opponent)
{
    u16 trainerId = TRAINER_PARTNER(partner);
    const struct Trainer *p = &gBattlePartners[DIFFICULTY_NORMAL][trainerId - TRAINER_PARTNER(PARTNER_NONE)];
    u8 partyMaxLevel = 0;
    int i, n = 0;

    memset(&gTrainerBattleParameter, 0, sizeof(gTrainerBattleParameter));
    TRAINER_BATTLE_PARAM.mode = TRAINER_BATTLE_SINGLE;
    TRAINER_BATTLE_PARAM.opponentA = opponent;
    for (i = 0; i < 3 && i < p->partySize; i++)
    {
        if (p->party[i].lvl > partyMaxLevel)
            partyMaxLevel = p->party[i].lvl;
        n++;
    }
    printf("Q %d", n);
    for (i = 0; i < 3 && i < p->partySize; i++)
    {
        u8 lvl = ScalePartnerMonLevel(p->party[i].lvl, partyMaxLevel);
        u16 species = ScaleTrainerMonSpecies(p->party[i].species, lvl, trainerId, i);
        printf(" %d %d", lvl, species);
    }
    EndLine();
}

// src/wild_encounter.c: header of the map, table of the time of day, and for every slot
// the levels ScaleWildMonLevel gives over the slot's level range (ChooseWildMonLevel
// picks any level from the lower to the higher of minLevel/maxLevel).
static void WildArea(const char *name, u32 headerId, enum WildPokemonArea area, int count)
{
    enum TimeOfDay tod = GetTimeOfDayForEncounters(headerId, area);
    const struct WildEncounterTypes *t = &gWildMonHeaders[headerId].encounterTypes[tod];
    const struct WildPokemonInfo *info = area == WILD_AREA_LAND ? t->landMonsInfo
                                       : area == WILD_AREA_WATER ? t->waterMonsInfo
                                       : area == WILD_AREA_ROCKS ? t->rockSmashMonsInfo
                                       : t->fishingMonsInfo;
    int i;

    if (info == NULL)
    {
        printf(" %s %d -", name, tod);
        return;
    }
    printf(" %s %d %d", name, tod, info->encounterRate);
    for (i = 0; i < count; i++)
    {
        int a = info->wildPokemon[i].minLevel, b = info->wildPokemon[i].maxLevel, l, lo = 255, hi = 0;
        if (a > b) { int x = a; a = b; b = x; }
        for (l = a; l <= b; l++)
        {
            int s = ScaleWildMonLevel(l);
            if (s < lo) lo = s;
            if (s > hi) hi = s;
        }
        printf(" %d:%d:%d:%d:%d", info->wildPokemon[i].species, a, b, lo, hi);
    }
}

static void Wild(int time)
{
    u16 headerId;

    hTime = time;
    headerId = GetCurrentMapWildMonHeaderId();
    if (headerId == HEADER_NONE)
    {
        printf("W none\n");
        return;
    }
    printf("W %d", headerId);
    WildArea("land", headerId, WILD_AREA_LAND, LAND_WILD_COUNT);
    WildArea("water", headerId, WILD_AREA_WATER, WATER_WILD_COUNT);
    WildArea("rock_smash", headerId, WILD_AREA_ROCKS, ROCK_WILD_COUNT);
    WildArea("fishing", headerId, WILD_AREA_FISHING, FISH_WILD_COUNT);
    EndLine();
}

// Every level 1..MAX_LEVEL through the level functions on the current map.
static void AllLevels(int trainerClass)
{
    struct Trainer fake = {0};
    int l;

    fake.trainerClass = trainerClass;
    memset(&gTrainerBattleParameter, 0, sizeof(gTrainerBattleParameter));
    TRAINER_BATTLE_PARAM.mode = TRAINER_BATTLE_SINGLE;
    printf("A %d", (int)GetRemapRegion());
    for (l = 1; l <= MAX_LEVEL; l++)
        printf(" %d,%d,%d,%d", ScaleTrainerMonLevel(&fake, TRAINER_NONE, l, l), ScaleWildMonLevel(l),
               ScalePartnerMonLevel(l, l), ScaleStaticMonLevel(l));
    EndLine();
}

static void ExpTable(void)
{
    int r, o;

    printf("X");
    for (r = 1; r <= MAX_LEVEL; r++)
        for (o = 1; o <= MAX_LEVEL; o++)
            printf(" %u", (unsigned)GetRemapExpPercent(r, o));
    EndLine();
}

int main(void)
{
    char line[256];
    int a, b, c, d, e, f;

    while (fgets(line, sizeof(line), stdin))
    {
        switch (line[0])
        {
        case 'M': // M group num mapsec
            if (sscanf(line + 1, "%d %d %d", &a, &b, &c) != 3) Unexpected("M", 0);
            SetMap(a, b, c);
            break;
        case 'P': // P kantoTitle johtoTitle hoennTitle kantoBadges johtoBadges hoennBadges
            if (sscanf(line + 1, "%d %d %d %d %d %d", &a, &b, &c, &d, &e, &f) != 6) Unexpected("P", 0);
            hChampion[0] = a; hChampion[1] = b; hChampion[2] = c;
            hBadges[0] = d; hBadges[1] = e; hBadges[2] = f;
            break;
        case 'S': // progress step and its player level
            a = GetRematchProgressStep();
            printf("S %d %d\n", a, sRematchBandPlayerLevels[a]);
            break;
        case 'T': // T trainerId mode(0 single, 1 rematch, 2 rematch double) leaderFlag monsCount
            if (sscanf(line + 1, "%d %d %d %d", &a, &b, &c, &d) != 4) Unexpected("T", 0);
            hLeaderFlag = c;
            TrainerTeam(a, b == 1 ? TRAINER_BATTLE_REMATCH : b == 2 ? TRAINER_BATTLE_REMATCH_DOUBLE : TRAINER_BATTLE_SINGLE, d);
            hLeaderFlag = FALSE;
            break;
        case 'Q': // Q partner opponentTrainerId
            if (sscanf(line + 1, "%d %d", &a, &b) != 2) Unexpected("Q", 0);
            PartnerTeam(a, b);
            break;
        case 'W': // W timeOfDay
            if (sscanf(line + 1, "%d", &a) != 1) Unexpected("W", 0);
            Wild(a);
            break;
        case 'A': // A trainerClass
            if (sscanf(line + 1, "%d", &a) != 1) Unexpected("A", 0);
            AllLevels(a);
            break;
        case 'X':
            ExpTable();
            break;
        case 'H': // TrainerEvoHash trainerId partyIndex step
            if (sscanf(line + 1, "%d %d %d", &a, &b, &c) != 3) Unexpected("H", 0);
            printf("H %u\n", (unsigned)TrainerEvoHash(a, b, c));
            break;
        case '\n':
            break;
        default:
            Unexpected("command", line[0]);
        }
    }
    return 0;
}
