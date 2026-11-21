"""Data layer of the player documentation.

Every page reads the game through these loaders, never through its own
parser, so all pages agree on names, numbers and levels. The loaders read
the repository the same way the build does: the C preprocessor with the
Makefile flags (see tu.py), the .party files, the map JSONs and the graphics.

Two builds, two languages: the German build (default) and the English build
(make GAME_LANG=ENGLISH, i.e. -DLANG_ENGLISH). Every loader that returns text
takes lang="de" | "en" and returns exactly what that build shows; lang=None
means the language of the process:

    gamedata.set_lang("en")      # or the environment variable OJ_DOCS_LANG=en
    gamedata.lang()              -> "en"

Results are cached per language, so both can be used in one process. The two
builds differ in text only (tu.nontext_diff, trainers_scriptdb.nontext_diff;
checked by selftest.py), so numbers, levels, tables and availability are the
same objects' values in both languages.

Modules (all results are cached per process):
    tu          preprocessed translation units, constants, INCBIN paths, named strings
    text        game text -> plain site text (line breaks, placeholders; German and English rules)
    typeinfo    types, type chart, type icons
    species     gSpeciesInfo, learnsets, evolutions, dex orders
    moves       gMovesInfo, TM/HM list, tutor moves
    abilities   gAbilitiesInfo
    natures     gNaturesInfo
    items       gItemsInfo, bag pockets, item icons
    maps        map ids -> display name, region, remap region
    levels      Python mirror of src/level_scaling.c (fixed levels, rematch band)
    trainers    .party files, trainer classes, battle sites, effective teams
    trainers_scriptdb  event scripts with resolved #if/.if, script texts per language
    encounters  wild_encounters.json with the game's table choice and levels
    dex_texts   labels of the in-game Pokédex (egg groups, growth rates, catch classes)
    graphics    palette-correct PNG export (Pillow)
"""
import os

REPO = os.environ.get("OJ_REPO") or os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

LANGS = ("de", "en")


def repo_path(*parts):
    return os.path.join(REPO, *parts)


def lang(l=None):
    """Resolve a language argument (None -> the process language)."""
    from . import tu
    return tu.lang(l)


def set_lang(l):
    """Set the process language (what lang=None means in every loader); returns the previous one."""
    from . import tu
    return tu.set_lang(l)
