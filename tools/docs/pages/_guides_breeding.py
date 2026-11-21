"""Breeding (guides/breeding): what is special about breeding in this game.

Only the points that differ from the main-series rules a player knows: the Day Cares, the
Oval Charm, the party slot, baby Pokémon without incense and the Odd Egg. They are read
from src/daycare.c and its settings (gamedata.hand_breeding); the code path a sentence
relies on is pinned with hand_facts.require, so a changed rule stops the build instead of
leaving a wrong sentence. The lead says that everything else follows the recent games;
the settings behind that sentence are checked in render().
"""
from common import html as H
from gamedata import hand_breeding as B
from gamedata import hand_facts as F
from pages import _game_util as U

PATH = "guides/breeding"

S = {
    "de": {
        "br_lead": "Was bei der Zucht in Origin Jade besonders ist. Alles Übrige – Vererbung von Wesen, Werten, "
                   "Fähigkeit, Ball und Ei-Attacken – funktioniert wie in den neueren Pokémon-Spielen.",
        "br_sec_special": "Besonderheiten",
        "br_daycare": "Pensionen",
        "br_daycare_text": "Es gibt eine Pension pro Region: {places}. Jede Pension hat ihre eigenen zwei Plätze.",
        "br_oval": "Ovalpin",
        "br_oval_text": "Den {oval} bekommst du mit dem ersten Ei aus einer Pension. Er erhöht die Chance auf "
                        "weitere Eier.",
        "br_space": "Platz im Team",
        "br_space_text": "Das Ei kommt nur ins Team, wenn dort ein Platz frei ist – das gilt auch, wenn du mit "
                         "einem kleineren Team spielst.",
        "br_incense": "Baby-Pokémon",
        "br_incense_text": "Baby-Pokémon schlüpfen ohne Rauch-Item: Kein Elternteil muss dafür etwas tragen.",
        "br_sec_odd": "Seltsames Ei",
        "br_odd_text": "Der Sohn des Pensionspaares in der Pension auf {where} gibt dir einmal ein Seltsames Ei, "
                       "wenn du seine Frage mit den richtigen vier Wörtern beantwortest. Die Bücher in der "
                       "Pension geben Hinweise. Welche Antwort du gibst, bestimmt das Pokémon im Ei. Das Ei ist "
                       "mit {shiny} % Chance schillernd.",
        "br_col_mon": "Pokémon",
        "br_col_words": "Antwort (vier Wörter)",
    },
    "en": {
        "br_lead": "What is special about breeding in Origin Jade. Everything else – how nature, IVs, ability, "
                   "ball and egg moves are passed on – works as in the recent Pokémon games.",
        "br_sec_special": "What is special",
        "br_daycare": "Day Cares",
        "br_daycare_text": "There is one Day Care per region: {places}. Each Day Care has its own two slots.",
        "br_oval": "Oval Charm",
        "br_oval_text": "You receive the {oval} together with your first egg from a Day Care. It raises the "
                        "chance of further eggs.",
        "br_space": "Room in the party",
        "br_space_text": "You only get the egg if there is a free slot in your party – this also applies when "
                         "you play with a smaller party.",
        "br_incense": "Baby Pokémon",
        "br_incense_text": "Baby Pokémon hatch without an incense: no parent has to hold anything for it.",
        "br_sec_odd": "Odd Egg",
        "br_odd_text": "The son of the Day-Care couple at the Day Care on {where} gives you an Odd Egg once if you "
                       "answer his question with the right four words. The books in the Day Care give hints. "
                       "Your answer decides which Pokémon is in the egg. The egg has a {shiny}% chance to be "
                       "shiny.",
        "br_col_mon": "Pokémon",
        "br_col_words": "Answer (four words)",
    },
}

GEN = lambda n: n - 1       # value of the GEN_n constant


def _rule(ctx, title_key, body, **fmt):
    title = ctx.t(title_key).format(**fmt) if fmt else ctx.t(title_key)
    return H.sub(title, body)


def _need(name, gen, pattern=None):
    """The page states the rule of this setting at `gen` or later; anything else stops the build."""
    if B.cfg(name) < GEN(gen):
        raise ValueError("breeding guide: %s is below Gen %d, the text no longer fits" % (name, gen))
    if pattern:
        F.require("src/daycare.c", pattern)


def render(ctx):
    lang = ctx.lang
    ctx.begin(PATH)
    oval = U.item(ctx, "ITEM_OVAL_CHARM")

    # the lead: inheritance follows the recent games
    _need("P_NATURE_INHERITANCE", 5, r"if \(P_NATURE_INHERITANCE > GEN_4\)\n\s*return slot;")
    _need("P_ABILITY_INHERITANCE", 6)
    _need("P_BALL_INHERITING", 7)
    _need("P_MOTHER_EGG_MOVE_INHERITANCE", 6)
    _need("P_TM_INHERITANCE", 6)
    _need("P_EGG_MOVE_TRANSFER", 9)
    _need("P_NIDORAN_M_DITTO_BREED", 5)

    places = U.join(ctx, ["%s (%s)" % (U.place(ctx, m), U.e(U.region_name(ctx, m.region))) for m in B.daycares(lang)])
    for d in ("data/scripts/day_care.inc", "data/maps/Route5_Frlg/scripts.inc",
              "data/maps/Route34_DayCare_hns/scripts.inc"):
        F.require(d, r"call_if_unset FLAG_RECEIVED_OVAL_CHARM, DayCare_EventScript_GiveOvalCharm")
    if not all(w > p for _c, p, w in B.compat()):
        raise ValueError("breeding guide: the Oval Charm no longer raises the egg chance")
    F.require("src/daycare.c",
              r"if \(GetMonData\(&gPlayerParty\[GetMaxPartySize\(\) - 1\], MON_DATA_SPECIES\) != SPECIES_NONE\)\n\s*return;")
    _need("P_INCENSE_BREEDING", 9, r"if \(P_INCENSE_BREEDING < GEN_9\)\n\s*AlterEggSpeciesWithIncenseItem")
    special = [_rule(ctx, "br_daycare", U.p(ctx, "br_daycare_text", places=places)),
               _rule(ctx, "br_oval", U.p(ctx, "br_oval_text", oval=oval)),
               _rule(ctx, "br_space", U.p(ctx, "br_space_text")),
               _rule(ctx, "br_incense", U.p(ctx, "br_incense_text"))]
    out = [H.section(ctx.t("br_sec_special"), "".join(special), id="special")]

    odd = B.odd_egg(lang)
    rows = [[U.species(ctx, s, icon=True), H.esc(" · ".join(w))] for s, w in odd.rows]
    out.append(H.section(ctx.t("br_sec_odd"),
                         U.p(ctx, "br_odd_text", where=U.place(ctx, odd.map_dir), shiny=odd.shiny_percent)
                         + H.table([(ctx.t("br_col_mon"), "main"), ctx.t("br_col_words")], rows), id="odd-egg"))
    ctx.end("".join(out), lead=H.esc(ctx.t("br_lead")))
