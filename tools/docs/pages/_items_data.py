"""Where every item comes from, per item (language neutral).

Built from the same data the location pages show (pages._world_data.items_of), so an
item page and the pages of its places always agree.

    places()        -> {item id: [Place]} in travel order
    Place           loc (location key), map_id, kind "ball" | "hidden" | "gift" | "bought" |
                    "berry" | "shop", qty (per find), count (how often on that map),
                    price ((currency, amount) for "bought", int for "shop"), badges (Johto
                    badges a shop needs, or None), underfoot, not_ball
    held()          -> {item id: ([Species] always, [Species] common, [Species] rare)}
    held_chances()  -> ((common %, rare %), (common %, rare %) with a boosting lead)
    pickup()        -> {item id: [10 percentages]} (gamedata.dex_pickup)
    smash()         -> {item id: percent per smashed rock}
    trainer_items() -> item ids held by a trainer's Pokémon or used by a trainer
    listed_ids()    -> ids of the items that get a page
"""
import functools
import re

from gamedata import dex_pickup, items as IT, locations as LOC, repo_path, species as SP, trainers
from gamedata import trainers_items as TI

from pages import _world_data as D


class Place:
    def __init__(self, **kw):
        self.qty, self.count, self.price, self.badges = 1, 1, None, None
        self.underfoot = self.not_ball = False
        self.__dict__.update(kw)


@functools.lru_cache(maxsize=None)
def places():
    out = {}

    def add(iid, **kw):
        out.setdefault(iid, []).append(Place(**kw))
    for loc in LOC.all_locations():
        d = D.items_of(loc.key)
        for mid, s, n in d.found:
            add(s.item, loc=loc.key, map_id=mid, kind=s.kind, qty=s.amount or 1, count=n,
                underfoot=s.kind == "hidden" and s.detail == "underfoot",
                not_ball=s.kind == "ball" and s.detail == "object")
        for mid, s, _n in d.gifts:
            add(s.item, loc=loc.key, map_id=mid, kind="gift", qty=s.amount or 1)
        for mid, s, price in d.bought:
            add(s.item, loc=loc.key, map_id=mid, kind="bought", qty=s.amount or 1, price=price)
        for iid, n in d.berries:
            add(iid, loc=loc.key, map_id=None, kind="berry", count=n)
        for mid, srcs in d.shops:
            for s in srcs:
                add(s.item, loc=loc.key, map_id=mid, kind="shop", price=s.price, badges=s.detail or None)
    return out


@functools.lru_cache(maxsize=None)
def held():
    out = {}
    for sp in sorted(SP.all_species("de").values(), key=lambda s: (s.natdex or 9999, s.id)):
        if sp.held_common and sp.held_common == sp.held_rare:
            out.setdefault(sp.held_common, ([], [], []))[0].append(sp.const)
            continue
        for slot, it in ((1, sp.held_common), (2, sp.held_rare)):
            if it:
                out.setdefault(it, ([], [], []))[slot].append(sp.const)
    return out


@functools.lru_cache(maxsize=None)
def held_chances():
    """SetWildMonHeldItem (src/pokemon.c): no item below chanceNoItem, the common item below
    chanceNotRare, else the rare one; the first number of each pair applies when the lead
    Pokémon boosts held items."""
    src = open(repo_path("src", "pokemon.c"), encoding="utf-8").read()
    body = src[src.index("void SetWildMonHeldItem(void)"):]
    a = re.search(r"chanceNoItem\s*=\s*itemHeldBoost\s*\?\s*(\d+)\s*:\s*(\d+)", body)
    b = re.search(r"chanceNotRare\s*=\s*itemHeldBoost\s*\?\s*(\d+)\s*:\s*(\d+)", body)
    no_b, no_n, nr_b, nr_n = int(a.group(1)), int(a.group(2)), int(b.group(1)), int(b.group(2))
    return (nr_n - no_n, 100 - nr_n), (nr_b - no_b, 100 - nr_b)


@functools.lru_cache(maxsize=None)
def pickup():
    return {iid: pct for iid, pct in dex_pickup.pickup_table()}


@functools.lru_cache(maxsize=None)
def smash():
    out = {}
    for iid, lst in TI.sources().items():
        for s in lst:
            if s.kind == "random" and "Smash" in s.detail[1]:
                out[iid] = s.detail[0]
    return out


@functools.lru_cache(maxsize=None)
def trainer_items():
    out = set()
    for tr in trainers.all_trainers().values():
        out.update(x for x in (tr.items or ()) if x)
        out.update(m.item for m in tr.mons if m.item)
    return frozenset(out)


@functools.lru_cache(maxsize=None)
def listed_ids():
    alls = IT.all_items("de")
    ids = set(places()) | set(held()) | set(pickup()) | set(smash()) | trainer_items()
    ids |= {i for i, it in alls.items() if it.tm}
    return frozenset(i for i in ids if i in alls)
