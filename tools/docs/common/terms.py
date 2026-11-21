"""Words of the game that the components need (stat names).

    terms.stat_names(ctx) -> {"hp": "KP", "atk": "Angriff", "def": "Vert.", "spa": "Sp. Ang.", ...}

The names are the ones of the status screen (src/strings.c). Where the build
writes them in capitals (the English build: "ATTACK"), the battle message
names of the same stats are used (src/battle_message.c: "Attack"). If a
string cannot be read, the shared UI label is the fallback.
"""
import functools

_SUMMARY = {"hp": "gText_HP3", "atk": "gText_Attack", "def": "gText_Defense",
            "spa": "gText_SpAtk", "spd": "gText_SpDef", "spe": "gText_Speed"}
_BATTLE = {"hp": "sText_HP", "atk": "sText_Attack", "def": "sText_Defense",
           "spa": "sText_SpAttack", "spd": "sText_SpDefense", "spe": "sText_Speed"}


@functools.lru_cache(maxsize=None)
def _stat_names(lang):
    from gamedata import tu, text, namestyle
    out = {}
    for k in _SUMMARY:
        name = None
        try:
            raw = tu.cstring("src/strings.c", _SUMMARY[k], lang)
            written = tu.written_in("src/strings.c", raw, lang)
            name = text.clean(raw, written)
            if name and name.upper() == name and len(name) > 2:
                # in capitals (English): the battle messages write the same stat in mixed
                # case; if they do not either, the site's name style applies (namestyle.py)
                alt_raw = tu.cstring("src/battle_message.c", _BATTLE[k], lang)
                alt = text.clean(alt_raw, tu.written_in("src/battle_message.c", alt_raw, lang))
                name = alt if alt and alt.upper() != alt else namestyle.show(alt or name, written, "label", lang)
        except Exception:
            name = None
        out[k] = name or None
    return out


def stat_names(ctx):
    names = _stat_names(ctx.lang)
    return {k: v or ctx.ui("stat_" + k) for k, v in names.items()}
