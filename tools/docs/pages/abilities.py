"""Abilities (data/abilities): the list and one page per ability.

Reference implementation of a "list + one page per entity" module:
register() announces the index page and every ability page, render() writes
them. Source: gAbilitiesInfo and the species' ability slots (gamedata.abilities).
"""
from common import html as H
from common import search
from gamedata import abilities

INDEX = "data/abilities/index"

STRINGS = {
    "de": {
        "lead": "Alle {n} Fähigkeiten des Spiels mit ihrer Beschreibung. Jede Fähigkeit hat eine eigene Seite "
                "mit den Pokémon, die sie haben können.",
        "placeholder": "Fähigkeit oder Wirkung suchen …",
        "facet_use": "Vorkommen",
        "use_yes": "Bei Pokémon im Spiel",
        "use_no": "Ohne Pokémon",
        "count": "{n} Pokémon",
        "eyebrow": "Fähigkeit",
        "sec_regular": "Pokémon mit dieser Fähigkeit",
        "sec_hidden": "Als versteckte Fähigkeit",
        "regular_intro": "Diese Pokémon haben die Fähigkeit als eine ihrer regulären Fähigkeiten.",
        "hidden_intro": "Bei diesen Pokémon ist sie die versteckte Fähigkeit.",
        "nobody": "Kein Pokémon im Spiel hat diese Fähigkeit.",
        "sec_effect": "Wirkung",
        "all": "Alle Fähigkeiten",
    },
    "en": {
        "lead": "All {n} abilities in the game with their descriptions. Every ability has its own page "
                "listing the Pokémon that can have it.",
        "placeholder": "Search ability or effect …",
        "facet_use": "In use",
        "use_yes": "Pokémon in the game have it",
        "use_no": "No Pokémon",
        "count": "{n} Pokémon",
        "eyebrow": "Ability",
        "sec_regular": "Pokémon with this ability",
        "sec_hidden": "As a Hidden Ability",
        "regular_intro": "These Pokémon have it as one of their regular abilities.",
        "hidden_intro": "For these Pokémon it is the Hidden Ability.",
        "nobody": "No Pokémon in the game has this ability.",
        "sec_effect": "Effect",
        "all": "All abilities",
    },
}


def _sorted(lang):
    return sorted(abilities.all_abilities(lang).values(), key=lambda a: (search.fold(a.name), a.id))


def register(ctx):
    ctx.add_page(INDEX)
    for a in _sorted(ctx.lang):
        ctx.add_entity("ability", a.const, a.name, sub=a.description)


def _holders(ctx, a):
    h = abilities.holders(a.id, ctx.lang)
    return h["regular"], h["hidden"]


def _tiles(ctx, sps):
    return H.ent_grid([H.species_tile(ctx, sp, number=sp.natdex or None) for sp in sps])


def render(ctx):
    t = ctx.t
    alls = _sorted(ctx.lang)

    # ---- the list
    ctx.begin(INDEX)
    items = []
    for a in alls:
        reg, hid = _holders(ctx, a)
        n = len({sp.id for sp in reg + hid})
        data = H.filter_attrs([a.name, a.description], use="yes" if n else "no")
        items.append(H.ent(ctx.url_for("ability", a.const), a.name, note=a.description,
                           aside=H.chip(t("count", n=n), "muted") if n else None, data=data))
    bar = H.filter_bar(ctx, "abilities", placeholder=t("placeholder"), facets=[
        {"key": "use", "label": t("facet_use"), "options": [("yes", t("use_yes")), ("no", t("use_no"))]}])
    groups = H.letter_groups([(a.name, x) for a, x in zip(alls, items)],
                             lambda xs: H.ent_grid(xs, cls="ents-wide"), "abilities")
    ctx.end(bar + groups,
            lead=H.esc(t("lead", n=ctx.num(len(alls)))))

    # ---- one page per ability
    for i, a in enumerate(alls):
        ctx.begin("ability", a.const)
        reg, hid = _holders(ctx, a)
        body = []
        if reg:
            body.append(H.section(t("sec_regular"), _tiles(ctx, reg), id="pokemon",
                                  intro=H.esc(t("regular_intro"))))
        if hid:
            body.append(H.section(t("sec_hidden"), _tiles(ctx, hid), id="hidden",
                                  intro=H.esc(t("hidden_intro"))))
        if not reg and not hid:
            body.append(H.callout(ctx, "note", H.p(t("nobody"))))
        n = len({sp.id for sp in reg + hid})
        ctx.end("".join(body), eyebrow=t("eyebrow"), lead=H.esc(a.description),
                chips=H.chip(t("count", n=n), "jade") if n else None,
                prev=("ability", alls[i - 1].const) if i else None,
                next=("ability", alls[i + 1].const) if i + 1 < len(alls) else None)
