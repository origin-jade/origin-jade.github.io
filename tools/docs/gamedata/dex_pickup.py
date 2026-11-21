"""Pickup (Mitnahme) and Honey Gather (Honigmaul) after a battle, as Cmd_pickup
in src/battle_script_commands.c does it (outside the Battle Pyramid and Pike):

  * Pickup: a party Pokémon with the ability and no held item finds an item with
    chance 1/10 (Random() % 10 == 0); the item is chosen from sPickupTable by the
    column (level - 1) / 10 (capped at 9) with the column's percentages.
  * Honey Gather: no held item, chance (column + 1) * 5 % for ITEM_HONEY.

    dex_pickup.pickup_table() -> [(item_id, [10 percentages])]
    dex_pickup.PICKUP_CHANCE  -> 10 (percent)
    dex_pickup.honey_chances() -> [5, 10, ..., 50]   (per level column)
    dex_pickup.columns()       -> [(1, 10), (11, 20), ..., (91, 100)]
"""
import functools

from . import tu as TU

SRC = "src/battle_script_commands.c"
PICKUP_CHANCE = 10          # (Random() % 10) == 0


@functools.lru_cache(maxsize=None)
def pickup_table():
    t = TU.load(SRC)
    out = []
    for _, v in sorted(t.table("sPickupTable").items()):
        item, pct = t.value(v)
        out.append((item, list(pct)))
    for item, pct in out:
        if len(pct) != 10:
            raise TU.DataError("%s: sPickupTable row with %d columns" % (SRC, len(pct)))
    return out


def columns():
    return [(i * 10 + 1, i * 10 + 10) for i in range(10)]


def honey_chances():
    return [(i + 1) * 5 for i in range(10)]
