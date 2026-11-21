"""Type chart (data/typechart): the game's effectiveness table as a matrix and
per type, plus which types count as physical or special when the move split
is switched off in the challenge settings.

Sources: gTypeEffectivenessTable and gTypesInfo (gamedata.typeinfo); the
setting's name and choices are read from the challenge menu's own texts.
"""
from common import html as H
from gamedata import text, tu, typeinfo

PATH = "data/typechart"

STRINGS = {
    "de": {
        "lead": "Jede Zeile ist der Typ der Attacke, jede Spalte der Typ des getroffenen Pokémon. "
                "Hat das Ziel zwei Typen, werden beide Werte multipliziert.",
        "keywords": "typen effektivität schwächen resistenzen immunität sehr effektiv",
        "sec_matrix": "Tabelle",
        "corner": "Angriff ↓ · Ziel →",
        "cell": "{atk} gegen {dfn}: {mult}",
        "leg_2": "sehr effektiv",
        "leg_05": "nicht sehr effektiv",
        "leg_0": "keine Wirkung",
        "leg_1": "normal",
        "sec_types": "Typ für Typ",
        "types_intro": "Für jeden Typ: wogegen seine Attacken stark oder schwach sind und welche Attacken "
                       "ein Pokémon dieses Typs fürchten muss.",
        "attacking": "Attacken dieses Typs",
        "defending": "Als Ziel",
        "sec_split": "Physisch oder speziell nach Typ",
        "split_intro": "Die Einstellung „{option}“ (Reiter „{tab}“ der Herausforderungen) legt fest, woher eine "
                       "Attacke ihre Kategorie bekommt.",
        "split_off": "Mit „{off}“ richtet sich die Kategorie nach dem Typ der Attacke; Status-Attacken bleiben "
                     "Status-Attacken.",
    },
    "en": {
        "lead": "Each row is the type of the move, each column the type of the Pokémon that is hit. "
                "If the target has two types, both values are multiplied.",
        "keywords": "types effectiveness weaknesses resistances immunity super effective",
        "sec_matrix": "Chart",
        "corner": "Attack ↓ · Target →",
        "cell": "{atk} against {dfn}: {mult}",
        "leg_2": "super effective",
        "leg_05": "not very effective",
        "leg_0": "no effect",
        "leg_1": "normal",
        "sec_types": "Type by type",
        "types_intro": "For every type: what its moves are strong or weak against, and which moves a "
                       "Pokémon of that type has to fear.",
        "attacking": "Moves of this type",
        "defending": "As the target",
        "sec_split": "Physical or special by type",
        "split_intro": "The setting “{option}” (tab “{tab}” of the challenges) decides where a move gets "
                       "its category from.",
        "split_off": "With “{off}” the category follows the type of the move; status moves stay status moves.",
    },
}

CELL = {2.0: ("x2", "2"), 0.5: ("x05", "½"), 0.0: ("x0", "0"), 1.0: ("", "")}


def register(ctx):
    ctx.add_page(PATH, keywords=ctx.t("keywords"))


def _split_option(lang):
    """(name, tab, choice names, descriptions) of the move-split setting, or None."""
    try:
        t = tu.load("src/challenge_menu.c", lang=lang)
        item = t.table("sTabItems_Mode")[t.need("ITEM_MODE_SPLIT")]
        tab = t.table("sTabs")[t.need("TAB_MODE")]
        name = text.clean(t.text_field(item, "name"))
        descs = [text.clean(t.text_value(x)) for x in t.init(str(t.field(item, "descriptions"))).positional()]
        choices = [text.clean(t.text_value(x)) for x in t.init(str(t.field(item, "choiceNames"))).positional()]
        tab_name = text.clean(t.text_value(tab.positional()[0]))
    except Exception:
        return None
    if not (name and tab_name and choices and len(choices) == len(descs)):
        return None
    return name, tab_name, choices, descs


def _label(ty):
    return ('<span class="tc-t t-%s"><span class="tc-abbr" aria-hidden="true">%s</span>'
            '<span class="tc-full">%s</span></span>' % (ty.slug, H.esc(ty.name[:3]), H.esc(ty.name)))


def _matrix(ctx, tys):
    t = ctx.t
    head = ['<th scope="col" class="tc-corner">%s</th>' % H.esc(t("corner"))]
    head += ['<th scope="col">%s</th>' % _label(d) for d in tys]
    rows = []
    for a in tys:
        cells = ['<th scope="row">%s</th>' % _label(a)]
        for d in tys:
            m = typeinfo.effectiveness(a.id, d.id)
            if m not in CELL:
                ctx.todo("type chart: unexpected factor %r (%s against %s)" % (m, a.name, d.name))
                m = 1.0
            cls, shown = CELL[m]
            title = t("cell", atk=a.name, dfn=d.name, mult=ctx.mult(m))
            cells.append('<td%s title="%s">%s</td>' % (' class="%s"' % cls if cls else "", H.esc(title),
                                                       shown or '<span class="sr">1</span>'))
        rows.append("<tr>%s</tr>" % "".join(cells))
    legend = "".join('<li><b class="%s">%s</b>%s</li>' % (c, s, H.esc("%s (%s)" % (t(k), ctx.mult(m))))
                     for m, c, s, k in ((2.0, "x2", "2", "leg_2"), (0.5, "x05", "½", "leg_05"),
                                        (0.0, "x0", "0", "leg_0"), (1.0, "", "", "leg_1")))
    return ('<div class="tc-wrap"><table class="tc"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
            '<ul class="tc-legend">%s</ul></div>' % ("".join(head), "\n".join(rows), legend))


def _groups(ctx, pairs):
    """<dl class="matchups"> from [(multiplier, [types])], strongest first, neutral left out."""
    rows = []
    for m, lst in pairs:
        if m == 1.0 or not lst:
            continue
        cls = "x0" if m == 0 else "xhi" if m > 1 else "xlo"
        rows.append('<div class="mu %s"><dt>%s</dt><dd>%s</dd></div>'
                    % (cls, H.esc(ctx.mult(m)), "".join(H.type_chip(ctx, x) for x in lst)))
    return '<dl class="matchups">%s</dl>' % "".join(rows) if rows else '<p class="muted">%s</p>' % H.esc(ctx.ui("none"))


def _type_cards(ctx, tys):
    cards = []
    for ty in tys:
        atk, dfn = {}, {}
        for o in tys:
            atk.setdefault(typeinfo.effectiveness(ty.id, o.id), []).append(o)
            dfn.setdefault(typeinfo.effectiveness(o.id, ty.id), []).append(o)
        body = ('<p class="tcard-h">%s</p><h4>%s</h4>%s<h4>%s</h4>%s'
                % (H.type_chip(ctx, ty), H.esc(ctx.t("attacking")),
                   _groups(ctx, sorted(atk.items(), reverse=True)), H.esc(ctx.t("defending")),
                   _groups(ctx, sorted(dfn.items(), reverse=True))))
        cards.append(H.card(body, cls="tcard", id="type-" + ty.slug))
    return H.grid(cards, "l")


def _cat_card(ctx, cat, lst):
    return H.card('<p class="tcard-h">%s</p><p class="chips">%s</p>'
                  % (H.cat_chip(ctx, cat), "".join(H.type_chip(ctx, x) for x in lst)), cls="tcard")


def render(ctx):
    t = ctx.t
    tys = typeinfo.battle_types()
    ctx.begin(PATH)
    body = [H.section(t("sec_matrix"), _matrix(ctx, tys), id="chart")]
    body.append(H.section(t("sec_types"), _type_cards(ctx, tys), id="types", intro=H.esc(t("types_intro"))))

    opt = _split_option(ctx.lang)
    if opt is None:
        ctx.todo("type chart: the move-split setting of the challenge menu could not be read; section left out")
    else:
        name, tab, choices, descs = opt
        inner = [H.prose(H.p(t("split_intro", option=name, tab=tab)))]
        inner.append(H.kv([(c, H.esc(d)) for c, d in zip(choices, descs)]))
        inner.append(H.prose(H.p(t("split_off", off=choices[0]))))
        phys = [x for x in tys if x.damage_category == 0]
        spec = [x for x in tys if x.damage_category == 1]
        inner.append(H.grid([_cat_card(ctx, "physical", phys), _cat_card(ctx, "special", spec)], "l"))
        body.append(H.section(t("sec_split"), "".join(inner), id="split"))
    ctx.end("".join(body), lead=H.esc(t("lead")), wide=True)
