"""Level & EXP system (game/levels): fixed levels per region, how experience is
weighted, the Exp. Share, the level cap of the challenge menu, obedience and the
reference levels of rematches.

Sources: gamedata.levels (the level and experience rules of the game), the level
spans of all wild Pokémon and trainers (gamedata.encounters, gamedata.trainers),
gamedata.game_rules (level cap and obedience tables), the experience code of the
battle engine (pinned below).
"""
from common import html as H
from gamedata import encounters as E
from gamedata import game_rules as G
from gamedata import hand_facts as F
from gamedata import hand_completion as HC
from gamedata import levels
from gamedata import maps
from gamedata import trainers as T
from pages import _game_util as U
from pages import _game_shared as X

PATH = "game/levels"

S = {
    "de": {
        "lv_keywords": "level erfahrung ep exp levelcap level-limit gehorsam ep-teiler skalierung",
        "lv_lead": "In Origin Jade spielst du drei Regionen hintereinander mit demselben Team. Damit das aufgeht, "
                   "haben alle Gegner feste Level, die von Region zu Region weiter steigen, und die Erfahrung wird "
                   "je Region anders gewichtet.",
        "lv_sec_fixed": "Feste Level",
        "lv_fixed_1": "Jedes wilde Pokémon und jedes Trainer-Pokémon hat ein festes Level. Nichts richtet sich nach "
                      "deinem Team: Wer viel trainiert, hat es leichter, wer durchrennt, hat es schwerer.",
        "lv_fixed_2": "Kanto ist der Anfang und reicht bis zur Liga. Johto schließt dort an, Hoenn setzt noch einmal "
                      "darauf auf – die höchsten Level einer Region triffst du jeweils erst spät oder nach ihrem "
                      "Titel. Auf dem Weg von Kanto nach Johto ({entry}) sind die Level etwas niedriger als im "
                      "übrigen Johto.",
        "lv_fixed_3": "Geschenkte Pokémon, feste Begegnungen und wandernde Pokémon haben eigene, von Hand gesetzte "
                      "Level; sie stehen bei den jeweiligen Pokémon und Orten.",
        "lv_col_region": "Region", "lv_col_wild": "Wilde Pokémon", "lv_col_trainers": "Trainer",
        "lv_entry_row": "Weg nach Johto",
        "lv_table_note": "Die Tabelle nennt das niedrigste und das höchste Level, das im Spiel vorkommt; Rückkämpfe sind "
                         "nicht mitgezählt.",
        "lv_evolved": "Weil die Level in Johto und Hoenn höher sind als in den Originalen, treten Trainer-Pokémon dort "
                      "meist schon entwickelt an. Die Trainerseiten zeigen die Teams so, wie du sie triffst.",
        "lv_sec_exp": "Erfahrung",
        "lv_exp_intro": "Die Erfahrung richtet sich danach, in welcher Region der Kampf stattfindet. So wächst dein "
                        "Team mit der Reise mit, statt den Gegnern davonzulaufen.",
        "lv_col_where": "Kampf in …", "lv_col_factor": "Erfahrung",
        "lv_exp_kanto_low": "Kanto, dein Pokémon ist höchstens {lv}",
        "lv_exp_kanto": "Kanto, dein Pokémon ist darüber",
        "lv_exp_johto": "Johto",
        "lv_exp_hoenn": "Hoenn und alle Orte außerhalb der drei Regionen",
        "lv_soft_title": "Abstand zum Gegner",
        "lv_soft_above": "Ist dein Pokémon mehr als {n} Level über dem besiegten oder gefangenen Pokémon, bekommt es "
                         "nur {pct} des Werts aus der Tabelle.",
        "lv_soft_below": "Ist es mehr als {n} Level darunter, bekommt es die volle Erfahrung ({pct}) – in Kanto erst "
                         "ab dem dritten Orden.",
        "lv_more_title": "Was sonst noch zählt",
        "lv_more_base": "Grundlage ist wie in den neueren Spielen die Basis-Erfahrung des Gegners mal sein Level: "
                        "Stärkere Gegner geben einem schwächeren Pokémon mehr, schwächere Gegner weniger.",
        "lv_more_trainer": "Trainerkämpfe geben das {mult}-Fache.",
        "lv_more_catch": "Auch das Fangen eines Pokémon gibt Erfahrung.",
        "lv_more_traded": "Getauschte Pokémon bekommen das {mult}-Fache.",
        "lv_more_egg": "Das {egg} und der {charm} geben jeweils das {mult}-Fache. Den {charm} bekommst du von "
                       "Prof. Eich für den vollständigen Kanto-Pokédex.",
        "lv_more_mult": "Die Herausforderung „{opt}“ multipliziert am Ende alles: {choices}.",
        "lv_more_max": "Auf {lv} gibt es keine Erfahrung mehr, Fleiß-Punkte aber weiterhin.",
        "lv_sec_share": "EP-Teiler",
        "lv_share_1": "Der {share} liegt von Anfang an im Beutel und ist eingeschaltet. Benutze ihn im Beutel, um ihn "
                      "aus- oder wieder einzuschalten.",
        "lv_share_2": "Ist er an, wird die Erfahrung geteilt, nicht vermehrt: Die eine Hälfte teilen sich die "
                      "Pokémon, die gekämpft haben, die andere Hälfte wird gleichmäßig auf alle kampffähigen "
                      "Pokémon im Team verteilt – die Kämpfer eingeschlossen.",
        "lv_share_3": "Ist er aus, bekommen nur die Pokémon Erfahrung, die im Kampf waren. Wer ein einzelnes Pokémon "
                      "schnell hochziehen will, schaltet ihn aus.",
        "lv_sec_caps": "Level-Limit",
        "lv_caps_1": "Das Level-Limit ist freiwillig: Du schaltest es im Menü „Herausforderungen“ unter „{opt}“ ein "
                     "({choices}). Ohne diese Herausforderung gibt es kein Limit.",
        "lv_caps_2": "Das Limit richtet sich nach deinen Kanto-Orden. Am Limit bekommt ein Pokémon keine Erfahrung "
                     "mehr, ein {candy} wirkt nicht, und auch in der Pension steigt es nicht darüber.",
        "lv_col_progress": "Fortschritt",
        "lv_caps_badges_0": "Kein Orden", "lv_caps_badges_1": "1 Orden", "lv_caps_badges_n": "{n} Orden",
        "lv_caps_title1": "Nach dem Titel in Kanto",
        "lv_caps_title2": "Nach dem Titel in Johto",
        "lv_caps_none": "kein Limit",
        "lv_caps_note": "In Johto bleibt das Limit also durchgehend bei {lv}; in Hoenn gibt es keins mehr.",
        "lv_sec_obey": "Gehorsam",
        "lv_obey_1": "Selbst gefangene, geschlüpfte und geschenkte Pokémon gehorchen immer, egal wie hoch ihr Level "
                     "ist. Nur Pokémon mit einem anderen Originaltrainer – also getauschte, auch die aus Tauschen im "
                     "Spiel – können Befehle verweigern, wenn ihr Level über der Grenze liegt.",
        "lv_obey_2": "Bis zum Titel in Kanto zählen die Kanto-Orden, danach die Johto-Orden. Nach dem Titel in Johto "
                     "gehorcht jedes Pokémon.",
        "lv_col_badges": "Anzahl",
        "lv_col_obey_kanto": "Kanto-Orden",
        "lv_col_obey_johto": "Johto-Orden",
        "lv_sec_rematch": "Level bei Rückkämpfen",
        "lv_rematch_1": "Rückkämpfe sind die einzige Ausnahme von den festen Leveln: Sie wachsen mit deinem "
                        "Fortschritt. Das Spiel schaut dabei nicht auf dein Team, sondern auf deine Orden und Titel "
                        "und nimmt dafür ein Richtlevel an.",
        "lv_rematch_2": "Bei Rückkämpfen per {phone} liegt das stärkste Pokémon des Gegners {plow} bis {phigh} Level "
                        "unter dem Richtlevel. Die acht Arenaleiter von Kanto kannst du nach dem Kanto-Titel in ihrer "
                        "Arena erneut herausfordern; ihr stärkstes Pokémon liegt {llow} bis {lhigh} Level darüber. Die "
                        "übrigen Pokémon eines Teams behalten ihren Abstand zum stärksten.",
        "lv_rematch_more": "Alle Rückkampf-Teams stehen unter {link}.",
        "lv_col_ref_kanto": "Kanto", "lv_col_ref_johto": "Johto", "lv_col_ref_hoenn": "Hoenn",
        "lv_ref_caption": "Welches Richtlevel gilt, zeigt die Tabelle: Bis zum Kanto-Titel zählen die Kanto-Orden, "
                          "danach die Johto-Orden und nach dem Johto-Titel die Hoenn-Orden.",
        "lv_ref_final": "Nach dem Titel in Hoenn ist das Richtlevel {lv}.",
    },
    "en": {
        "lv_keywords": "level experience exp level cap obedience exp share scaling",
        "lv_lead": "In Origin Jade you play three regions in a row with the same team. To make that work, every "
                   "opponent has a fixed level that keeps rising from region to region, and experience is weighted "
                   "differently in each region.",
        "lv_sec_fixed": "Fixed levels",
        "lv_fixed_1": "Every wild Pokémon and every Trainer's Pokémon has a fixed level. Nothing depends on your "
                      "team: train a lot and it gets easier, rush through and it gets harder.",
        "lv_fixed_2": "Kanto is the start and runs up to the League. Johto picks up from there and Hoenn goes higher "
                      "still – you meet a region's highest levels late or after its title. On the way from Kanto to "
                      "Johto ({entry}) the levels are a little lower than in the rest of Johto.",
        "lv_fixed_3": "Gift Pokémon, static encounters and roaming Pokémon have their own hand-set levels; you find "
                      "them on the pages of those Pokémon and places.",
        "lv_col_region": "Region", "lv_col_wild": "Wild Pokémon", "lv_col_trainers": "Trainers",
        "lv_entry_row": "Way to Johto",
        "lv_table_note": "The table gives the lowest and the highest level found in the game; rematches are not "
                         "counted.",
        "lv_evolved": "Because the levels in Johto and Hoenn are higher than in the originals, Trainers' Pokémon "
                      "there usually show up evolved. The Trainer pages list the teams as you meet them.",
        "lv_sec_exp": "Experience",
        "lv_exp_intro": "Experience depends on the region the battle takes place in. That way your team grows with "
                        "the journey instead of running away from the opposition.",
        "lv_col_where": "Battle in …", "lv_col_factor": "Experience",
        "lv_exp_kanto_low": "Kanto, your Pokémon is at most {lv}",
        "lv_exp_kanto": "Kanto, your Pokémon is above that",
        "lv_exp_johto": "Johto",
        "lv_exp_hoenn": "Hoenn and every place outside the three regions",
        "lv_soft_title": "Distance to the opponent",
        "lv_soft_above": "If your Pokémon is more than {n} levels above the defeated or caught Pokémon, it only gets "
                         "{pct} of the value in the table.",
        "lv_soft_below": "If it is more than {n} levels below, it gets full experience ({pct}) – in Kanto only from "
                         "the third Badge on.",
        "lv_more_title": "What else counts",
        "lv_more_base": "As in the newer games, the basis is the opponent's base experience times its level: stronger "
                        "opponents give a weaker Pokémon more, weaker opponents less.",
        "lv_more_trainer": "Trainer battles give {mult} times as much.",
        "lv_more_catch": "Catching a Pokémon gives experience too.",
        "lv_more_traded": "Traded Pokémon get {mult} times as much.",
        "lv_more_egg": "The {egg} and the {charm} each give {mult} times as much. Prof. Oak gives you the {charm} for "
                       "completing the Kanto Pokédex.",
        "lv_more_mult": "The challenge “{opt}” multiplies everything at the end: {choices}.",
        "lv_more_max": "At {lv} there is no more experience, but effort values are still earned.",
        "lv_sec_share": "Exp. Share",
        "lv_share_1": "The {share} is in your Bag from the start and switched on. Use it in the Bag to turn it off "
                      "or on again.",
        "lv_share_2": "While it is on, experience is shared, not multiplied: one half is split among the Pokémon "
                      "that fought, the other half is spread evenly over every Pokémon in the party that can battle "
                      "– the fighters included.",
        "lv_share_3": "While it is off, only the Pokémon that took part get experience. Turn it off if you want to "
                      "raise a single Pokémon quickly.",
        "lv_sec_caps": "Level cap",
        "lv_caps_1": "The level cap is optional: you switch it on in the challenge menu under “{opt}” ({choices}). "
                     "Without that challenge there is no cap.",
        "lv_caps_2": "The cap follows your Kanto Badges. At the cap a Pokémon gains no more experience, a {candy} "
                     "has no effect, and it does not grow past it at the Day Care either.",
        "lv_col_progress": "Progress",
        "lv_caps_badges_0": "No Badge", "lv_caps_badges_1": "1 Badge", "lv_caps_badges_n": "{n} Badges",
        "lv_caps_title1": "After the title in Kanto",
        "lv_caps_title2": "After the title in Johto",
        "lv_caps_none": "no cap",
        "lv_caps_note": "So the cap stays at {lv} all through Johto, and there is none in Hoenn.",
        "lv_sec_obey": "Obedience",
        "lv_obey_1": "Pokémon you caught, hatched or were given always obey, whatever their level. Only Pokémon with "
                     "a different original Trainer – traded ones, including those from in-game trades – can refuse "
                     "orders when their level is above the limit.",
        "lv_obey_2": "Up to the title in Kanto the Kanto Badges count, after it the Johto Badges. After the title in "
                     "Johto every Pokémon obeys.",
        "lv_col_badges": "Number",
        "lv_col_obey_kanto": "Kanto Badges",
        "lv_col_obey_johto": "Johto Badges",
        "lv_sec_rematch": "Levels in rematches",
        "lv_rematch_1": "Rematches are the one exception to fixed levels: they grow with your progress. The game "
                        "does not look at your team for that but at your Badges and titles, and assumes a reference "
                        "level for them.",
        "lv_rematch_2": "In rematches by {phone} the opponent's strongest Pokémon is {plow} to {phigh} levels below "
                        "the reference level. The eight Kanto Gym Leaders can be challenged again in their Gyms after "
                        "the Kanto title; their strongest Pokémon is {llow} to {lhigh} levels above it. The other "
                        "Pokémon of a team keep their distance to the strongest.",
        "lv_rematch_more": "All rematch teams are listed under {link}.",
        "lv_col_ref_kanto": "Kanto", "lv_col_ref_johto": "Johto", "lv_col_ref_hoenn": "Hoenn",
        "lv_ref_caption": "The table shows which reference level applies: up to the Kanto title the Kanto Badges "
                          "count, then the Johto Badges, and after the Johto title the Hoenn Badges.",
        "lv_ref_final": "After the title in Hoenn the reference level is {lv}.",
    },
}

PHONE = {"de": "PokéCom", "en": "Pokégear"}


def _span(ctx, spans, key):
    v = spans.get(key)
    return H.esc(ctx.level_range(v[0], v[1])) if v else None


def _badges(ctx, n):
    t = ctx.t
    return t("lv_caps_badges_0") if n == 0 else t("lv_caps_badges_1") if n == 1 else t("lv_caps_badges_n", n=n)


def _fixed(ctx):
    t = ctx.t
    levels.check_mirror()
    wild, tr = E.level_span(), T.level_span()
    rows = []
    for region in ("Kanto", "Johto", "Hoenn"):
        if region == "Johto":
            rows.append([H.esc(t("lv_entry_row")), _span(ctx, wild, ("Johto", True)), _span(ctx, tr, ("Johto", True))])
        rows.append([U.region_chip(ctx, region), _span(ctx, wild, (region, False)), _span(ctx, tr, (region, False))])
    entry = U.join(ctx, [U.mapsec(ctx, s) for s in levels.JOHTO_ENTRY_MAPSECS])
    for region in ("JOHTO", "HOENN"):
        r = levels._rules(region)
        if not (r["enabled"] and r["evolve"]):
            raise F.TU.DataError("trainer evolution rule changed: review the level page")
    table = H.table([(t("lv_col_region"), "main"), (t("lv_col_wild"), "num"), (t("lv_col_trainers"), "num")], rows,
                    stack=False)
    return (U.prose(ctx, "lv_fixed_1") + H.prose(U.p(ctx, "lv_fixed_2", entry=entry)) + table
            + U.prose(ctx, "lv_table_note", "lv_fixed_3", "lv_evolved"))


def _exp(ctx):
    t = ctx.t
    C = levels.C
    bs = "src/battle_script_commands.c"
    # the experience code the text describes
    F.require(bs, r"GetRemapExpPercent\(expGetterLvl, gBattleMons\[faintedBattler\]\.level\)\) / 100;")
    F.require(bs, r"if \(B_TRAINER_EXP_MULTIPLIER <= GEN_7 && gBattleTypeFlags & BATTLE_TYPE_TRAINER\)\s*"
                  r"calculatedExp = \(calculatedExp \* 150\) / 100;")
    F.require(bs, r"if \(IsTradedMon\(&gPlayerParty\[expGetterMonId\]\)\)\s*\*expAmount = \(\*expAmount \* 150\) / 100;")
    F.require(bs, r"if \(holdEffect == HOLD_EFFECT_LUCKY_EGG\)\s*\*expAmount = \(\*expAmount \* 150\) / 100;")
    F.require(bs, r"if \(CheckBagHasItem\(ITEM_EXP_CHARM, 1\)\)[^\n]*\n\s*\*expAmount = \(\*expAmount \* 150\) / 100;")
    F.require(bs, r"value \*= sExperienceScalingFactors\[\(faintedLevel \* 2\) \+ 10\];")
    F.require(bs, r"if \(expMult == OPTIONS_EXP_MULTIPLIER_0X\)\s*\*expAmount = 0;")
    if not (F.C("B_TRAINER_EXP_MULTIPLIER") <= F.C("GEN_7") and F.C("B_SCALED_EXP") == F.C("GEN_5")
            and F.C("B_EXP_CATCH") >= F.C("GEN_6") and F.C("B_UNEVOLVED_EXP_MULTIPLIER") < F.C("GEN_6")
            and not F.C("B_AFFECTION_MECHANICS") and F.C("B_MAX_LEVEL_EV_GAINS") >= F.C("GEN_5")):
        raise F.TU.DataError("experience settings changed: review the level page")
    if not any(check == "HasAllKantoMons" and const == "ITEM_EXP_CHARM" for check, const, _ in HC.oak_rewards()):
        raise F.TU.DataError("the Exp. Charm is no longer the Kanto Pokédex reward: review the level page")
    lucky = U.item_obj(ctx, "ITEM_LUCKY_EGG")
    if lucky is None:
        raise F.TU.DataError("Lucky Egg changed: review the level page")

    rows = [
        [H.esc(t("lv_exp_kanto_low", lv=ctx.level(C("REMAP_EXP_KANTO_LOW_UNTIL")))),
         H.esc(ctx.pct(C("REMAP_EXP_KANTO_LOW_PERCENT")))],
        [H.esc(t("lv_exp_kanto")), H.esc(ctx.pct(C("REMAP_EXP_KANTO_PERCENT")))],
        [H.esc(t("lv_exp_johto")), H.esc(ctx.pct(C("REMAP_EXP_JOHTO_PERCENT")))],
        [H.esc(t("lv_exp_hoenn")), H.esc(ctx.pct(C("REMAP_EXP_HOENN_PERCENT")))],
    ]
    table = H.table([(t("lv_col_where"), "main"), (t("lv_col_factor"), "num")], rows)
    soft = H.ul([
        U.fmt(ctx, "lv_soft_above", n=C("REMAP_EXP_SOFT_ABOVE"), pct=H.esc(ctx.pct(C("REMAP_EXP_SOFT_ABOVE_PERCENT")))),
        U.fmt(ctx, "lv_soft_below", n=C("REMAP_EXP_SOFT_BELOW"), pct=H.esc(ctx.pct(100))),
    ])
    mult = X.challenge(ctx, "TAB_DIFFICULTY", "ITEM_DIFFICULTY_EXP_MULTIPLIER")
    m15 = H.esc(ctx.num(1.5))
    more = H.ul([
        U.fmt(ctx, "lv_more_base"),
        U.fmt(ctx, "lv_more_trainer", mult=m15),
        U.fmt(ctx, "lv_more_catch"),
        U.fmt(ctx, "lv_more_traded", mult=m15),
        U.fmt(ctx, "lv_more_egg", egg=U.item(ctx, lucky), charm=U.item(ctx, "ITEM_EXP_CHARM"), mult=m15),
        U.fmt(ctx, "lv_more_mult", opt=H.esc(mult.name), choices=X.choices_line(ctx, mult)),
        U.fmt(ctx, "lv_more_max", lv=H.esc(ctx.level(C("MAX_LEVEL")))),
    ])
    return (U.prose(ctx, "lv_exp_intro") + table + H.sub(t("lv_soft_title"), soft, id="exp-distance")
            + H.sub(t("lv_more_title"), more, id="exp-more"))


def _share(ctx):
    bs = "src/battle_script_commands.c"
    F.require("data/scripts/new_game.inc", r"^\tadditem ITEM_EXP_SHARE$")
    F.require("data/scripts/new_game.inc", r"^\tsetflag FLAG_EXP_SHARE_ENABLED$")
    F.require(bs, r"\*exp = SAFE_DIV\(calculatedExp / 2, viaSentIn\);")
    F.require(bs, r"expShareExpValue = calculatedExp / 2 / viaExpShare;")
    F.require(bs, r"if \(holdEffect == HOLD_EFFECT_EXP_SHARE \|\| IsGen6ExpShareEnabled\(\)\)\s*\{\s*"
                  r"expShareBits \|= 1u << i;\s*viaExpShare\+\+;")
    F.require("src/item_use.c", r"gText_ExpShareOff")
    if F.C("B_SPLIT_EXP") >= F.C("GEN_6"):
        raise F.TU.DataError("experience split changed: review the Exp. Share text")
    return (H.prose(U.p(ctx, "lv_share_1", share=U.item(ctx, "ITEM_EXP_SHARE")))
            + U.prose(ctx, "lv_share_2", "lv_share_3"))


def _caps(ctx):
    t = ctx.t
    caps = G.level_caps()
    opt = X.challenge(ctx, "TAB_DIFFICULTY", "ITEM_DIFFICULTY_LEVEL_CAP")
    normal, hard = opt.choices[1].name, opt.choices[2].name
    rows = [[H.esc(_badges(ctx, n)), H.esc(ctx.level(caps["normal"][n])), H.esc(ctx.level(caps["hard"][n]))]
            for n in range(9)]
    after = H.esc(ctx.level(caps["after_first_title"]))
    rows.append([H.esc(t("lv_caps_title1")), after, after])
    rows.append([H.esc(t("lv_caps_title2")), H.esc(t("lv_caps_none")), H.esc(t("lv_caps_none"))])
    table = H.table([(t("lv_col_progress"), "main"), (normal, "num"), (hard, "num")], rows, stack=False)
    intro = (U.p(ctx, "lv_caps_1", opt=H.esc(opt.name), choices=X.choices_line(ctx, opt))
             + U.p(ctx, "lv_caps_2", candy=U.item(ctx, "ITEM_RARE_CANDY")))
    return H.prose(intro) + table + H.prose(U.p(ctx, "lv_caps_note", lv=after))


def _obey(ctx):
    t = ctx.t
    ob = G.obedience()
    rows = [[H.esc(str(n)), H.esc(ctx.level(ob["first"][n])), H.esc(ctx.level(ob["second"][n]))] for n in range(9)]
    table = H.table([(t("lv_col_badges"), "main"), (t("lv_col_obey_kanto"), "num"), (t("lv_col_obey_johto"), "num")],
                    rows, stack=False)
    return U.prose(ctx, "lv_obey_1", "lv_obey_2") + table


def _rematch(ctx):
    t = ctx.t
    pl = levels.band_player_levels()
    (plow, phigh), (llow, lhigh) = X.bands()
    # the table rows are the game's progress steps: 0-8 badges per region, then the last title
    steps = levels.band_steps()
    if [s.step for s in steps if s.reachable and not s.title] != list(range(0, 9)) + list(range(10, 19)) + list(range(20, 29)):
        raise F.TU.DataError("rematch progress steps changed: review the level page")
    rows = [[H.esc(str(n)), H.esc(ctx.level(pl[n])), H.esc(ctx.level(pl[10 + n])), H.esc(ctx.level(pl[20 + n]))]
            for n in range(9)]
    table = H.table([(t("lv_col_badges"), "main"), (t("lv_col_ref_kanto"), "num"), (t("lv_col_ref_johto"), "num"),
                     (t("lv_col_ref_hoenn"), "num")], rows, stack=False)
    out = U.prose(ctx, "lv_rematch_1") + H.prose(U.p(ctx, "lv_rematch_2", phone=H.esc(PHONE[ctx.lang]), plow=plow,
                                                     phigh=phigh, llow=llow, lhigh=lhigh))
    out += U.prose(ctx, "lv_ref_caption") + table + H.prose(U.p(ctx, "lv_ref_final", lv=H.esc(ctx.level(pl[29]))))
    if ctx.url("battles/rematches"):
        out += H.prose(U.p(ctx, "lv_rematch_more", link=U.page(ctx, "battles/rematches")))
    return out


def render(ctx):
    t = ctx.t
    ctx.begin(PATH)
    body = [
        H.section(t("lv_sec_fixed"), _fixed(ctx), id="fixed"),
        H.section(t("lv_sec_exp"), _exp(ctx), id="exp"),
        H.section(t("lv_sec_share"), _share(ctx), id="exp-share"),
        H.section(t("lv_sec_caps"), _caps(ctx), id="caps"),
        H.section(t("lv_sec_obey"), _obey(ctx), id="obedience"),
        H.section(t("lv_sec_rematch"), _rematch(ctx), id="rematches"),
    ]
    ctx.end("".join(body), lead=H.esc(t("lv_lead")), description=t("lv_lead"))
