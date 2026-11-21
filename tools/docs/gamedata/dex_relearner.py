"""Where the move relearner and the move deleter are: the active maps whose
own script file calls `special TeachMoveRelearnerMove` (src/move_relearner.c)
or `special MoveDeleterChooseMoveToForget` (src/party_menu.c).

Shared scripts in data/scripts/ are not counted: Common_EventScript_MoveRelearner
(data/scripts/move_relearner.inc) is only reached from the debug menu (src/debug.c).

    dex_relearner.places("relearner") -> ["Ebenholz City", ...]  (in-game map section names)
    dex_relearner.places("deleter")
    dex_relearner.place_maps("relearner") -> [map id, ...]  (one per place, same order)
places() takes lang="de"|"en" (None = the process language).
"""
import functools
import os
import re

from . import repo_path
from . import maps

SPECIALS = {
    "relearner": re.compile(r"^\s*special\s+TeachMoveRelearnerMove\b", re.M),
    "deleter": re.compile(r"^\s*special\s+MoveDeleterChooseMoveToForget\b", re.M),
}


@functools.lru_cache(maxsize=None)
def _scan():
    """{kind: [map id]} - the first map of every place (map section name) with the special."""
    out = {k: [] for k in SPECIALS}
    seen = {k: set() for k in SPECIALS}
    for m in sorted(maps.all_maps(lang="de").values(), key=lambda m: (m.group_index, m.map_num)):
        p = repo_path("data", "maps", m.dir, "scripts.inc")
        if not os.path.exists(p) or maps.locked_mapsec(m.mapsec):
            continue
        src = open(p, encoding="utf-8").read()
        for k, pat in SPECIALS.items():
            if pat.search(src) and m.display not in seen[k]:
                seen[k].add(m.display)
                out[k].append(m.id)
    return out


def place_maps(kind):
    return list(_scan()[kind])


def places(kind, lang=None):
    return [maps.by_id(mid, lang).display for mid in _scan()[kind]]
