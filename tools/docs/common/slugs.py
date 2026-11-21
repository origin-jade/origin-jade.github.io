"""URL slugs and page paths - the one place that defines them.

A slug is derived from the game's constant, never from a display name, so it
is the same in every language:

    slug("SPECIES_BULBASAUR")   -> "bulbasaur"
    slug("SPECIES_HO_OH")       -> "ho-oh"
    slug("MOVE_TACKLE")         -> "tackle"
    slug("MAPSEC_ROUTE_1")      -> "route-1"
    slug("MAP_ROUTE1_FRLG")     -> "route1-frlg"

    entity_path("species", "SPECIES_BULBASAUR") -> "pokedex/bulbasaur"
    entity_path("move", "MOVE_TACKLE")          -> "data/moves/tackle"

A page path is the URL below the language folder without ".html"
("data/abilities/overgrow" -> de/data/abilities/overgrow.html).
"""
import re

# kind -> constant prefixes that are cut off
PREFIXES = {
    "species": ("SPECIES_",),
    "move": ("MOVE_",),
    "ability": ("ABILITY_",),
    "item": ("ITEM_",),
    "location": ("MAPSEC_", "MAP_"),
    "trainer": ("TRAINER_",),
    "type": ("TYPE_",),
}
_ALL_PREFIXES = tuple(p for ps in PREFIXES.values() for p in ps)

# kind -> folder of its entity pages (below the language folder)
ENTITY_DIRS = {
    "species": "pokedex",
    "move": "data/moves",
    "ability": "data/abilities",
    "item": "data/items",
    "location": "world",
    "trainer": "battles/trainers",
}

# The registry kinds, in the order the search groups them.
KINDS = ("species", "move", "ability", "item", "location", "trainer", "page")

# The seven sections of the site (fixed information architecture): id -> folder.
SECTIONS = ("home", "game", "pokedex", "world", "battles", "data", "guides")

_PATH_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*(?:/[a-z0-9]+(?:[-_][a-z0-9]+)*)*$")


def const_of(obj):
    """Constant name of a loader object (its .const) or the string itself."""
    c = getattr(obj, "const", None)
    if c is None:
        c = getattr(obj, "id", obj)
    if not isinstance(c, str):
        raise TypeError("need a constant name or an object with .const, got %r" % (obj,))
    return c


def slug(const, kind=None):
    """Slug of a game constant: prefix cut, lower case, "_" -> "-"."""
    c = const_of(const)
    prefixes = PREFIXES.get(kind, _ALL_PREFIXES) if kind else _ALL_PREFIXES
    for p in prefixes:
        if c.startswith(p):
            c = c[len(p):]
            break
    s = re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")
    if not s:
        raise ValueError("empty slug for %r" % (const,))
    return s


def entity_path(kind, const):
    """Page path of an entity page: "<folder>/<slug>"."""
    if kind not in ENTITY_DIRS:
        raise KeyError("no entity folder for kind %r" % kind)
    return "%s/%s" % (ENTITY_DIRS[kind], slug(const, kind))


def check_path(path):
    """Raise ValueError unless path is a valid page path (lower case, a-z 0-9 - _ /)."""
    if not isinstance(path, str) or not _PATH_RE.match(path):
        raise ValueError("invalid page path %r (lower case a-z, 0-9, '-', '_' and '/')" % (path,))
    return path


def anchor(text):
    """id for a heading or anchor: "a-z0-9-" only (umlauts folded)."""
    import unicodedata
    s = unicodedata.normalize("NFD", str(text).lower().replace("ß", "ss"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "x"
