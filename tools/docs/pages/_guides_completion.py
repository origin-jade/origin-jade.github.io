"""Completing the Pokédex (guides/completion): what the game counts as complete and what
it gives for it.

Sources (gamedata.hand_completion): Trainer Card stars = GetHnSTrainerStars
(src/trainer_card.c); diplomas = the scripts that show a diploma with their dex check
(text decided in src/diploma.c); Pokédex rewards = Prof. Oak's lab script and Prof. Birch's
lab script; Oak's aides = the Kanto scripts with their required counts. The species a dex
check needs are computed by ports of HasAllKantoMons, HasAllJohotoMons, HasAllHoennMons and
HasAllMons (src/pokedex.c), pinned by fingerprints (hand_completion.check_mirror).
"""
from common import html as H
from gamedata import hand_completion as HC
from gamedata import hand_facts as F
from gamedata import maps, trainers
from pages import _game_util as U

PATH = "guides/completion"
CHECK_KIND = {"HasAllKantoMons": "kanto", "HasAllJohotoMons": "johto", "HasAllHoennMons": "hoenn",
              "HasAllMons": "national"}
STAR_FLAGS = {"FLAG_IS_JOHTO_CHAMPION": "co_star_johto", "FLAG_IS_KANTO_CHAMPION": "co_star_kanto",
              "FLAG_IS_HOENN_CHAMPION": "co_star_hoenn"}

S = {
    "de": {
        "co_lead": "Was das Spiel als „vollständig“ zählt und was du dafür bekommst. Gezählt werden immer "
                   "gefangene Pokémon, nicht nur gesehene.",
        "co_sec_rewards": "Belohnungen für den Pokédex",
        "co_rewards_intro": "Jede Region hat ihre eigene Liste. Wer eine Liste vollständig gefangen hat, holt "
                            "sich die Belohnung persönlich ab.",
        "co_col_dex": "Pokédex",
        "co_col_need": "Nötig",
        "co_col_who": "Abholen bei",
        "co_col_reward": "Belohnung",
        "co_n_caught": "{n} gefangen",
        "co_oak": "Professor Eich, {where}",
        "co_birch": "Professor Birk, {where} (nach dem Hoenn-Titel)",
        "co_birch_reward": "einer der Hoenn-Starter {species} (Lv. {lv})",
        "co_dex_kanto": "Kanto",
        "co_dex_johto": "Johto",
        "co_dex_hoenn": "Hoenn",
        "co_dex_national": "National",
        "co_sec_diploma": "Diplome",
        "co_diploma_intro": "Ein Diplom ist die Urkunde für einen vollständigen Pokédex. Hast du alle {n} Pokémon "
                            "des Nationalen Pokédex gefangen, zeigt jedes Diplom den Nationalen Pokédex.",
        "co_col_diploma": "Diplom",
        "co_col_where": "Wo",
        "co_diploma_region": "{region}-Diplom",
        "co_diploma_where": "dem Spieldesigner in {where} zeigen",
        "co_sec_aides": "Professor Eichs Assistenten",
        "co_aides_intro": "In Kanto warten Assistenten von Professor Eich. Sie belohnen dich, wenn du genug "
                          "verschiedene Pokémon gefangen hast.",
        "co_col_place": "Ort",
        "co_aides_note": "Gezählt wird der Kanto-Pokédex; spielst du mit zufällig vertauschten Pokémon-Arten, "
                         "zählt der Nationale. Hast du den {expshare} schon, bekommst du stattdessen: {small}.",
        "co_sec_stars": "Sterne auf dem Trainerpass",
        "co_stars_intro": "Jeder erfüllte Punkt gibt einen Stern, die Reihenfolge ist egal. Mit allen {n} "
                          "Sternen begrüßt dich die Schwester im Pokémon-Center anders.",
        "co_star_johto": "Champ von Johto werden",
        "co_star_kanto": "Champ von Kanto werden",
        "co_star_hoenn": "Champ von Hoenn werden",
        "co_star_trainer": "{name} besiegen ({where})",
        "co_sec_lists": "Welche Pokémon zählen",
        "co_lists_intro": "Diese Arten musst du für die jeweilige Liste gefangen haben.",
        "co_list_sum": "{label}: {n} Pokémon",
        "co_not_counted": "Zählen nicht mit: {names}.",
        "co_national_all": "Der Nationale Pokédex braucht alle {n} Arten des Spiels außer den hier genannten.",
        "co_reason_hoenn": "gehört zu Hoenn",
        "co_reason_mythical": "mysteriöses Pokémon",
        "co_reason_not_required": "nicht nötig",
    },
    "en": {
        "co_lead": "What the game counts as “complete” and what you get for it. Only caught Pokémon count, "
                   "not Pokémon you have merely seen.",
        "co_sec_rewards": "Rewards for the Pokédex",
        "co_rewards_intro": "Every region has its own list. Once you have caught a whole list, collect the "
                            "reward in person.",
        "co_col_dex": "Pokédex",
        "co_col_need": "Needed",
        "co_col_who": "Collect from",
        "co_col_reward": "Reward",
        "co_n_caught": "{n} caught",
        "co_oak": "Professor Oak, {where}",
        "co_birch": "Professor Birch, {where} (after the Hoenn title)",
        "co_birch_reward": "one of the Hoenn starters {species} (Lv. {lv})",
        "co_dex_kanto": "Kanto",
        "co_dex_johto": "Johto",
        "co_dex_hoenn": "Hoenn",
        "co_dex_national": "National",
        "co_sec_diploma": "Diplomas",
        "co_diploma_intro": "A diploma is the certificate for a complete Pokédex. Once you have caught all {n} "
                            "Pokémon of the National Pokédex, every diploma shows the National Pokédex.",
        "co_col_diploma": "Diploma",
        "co_col_where": "Where",
        "co_diploma_region": "{region} diploma",
        "co_diploma_where": "show it to the game designer in {where}",
        "co_sec_aides": "Professor Oak's aides",
        "co_aides_intro": "Aides of Professor Oak wait in Kanto. They reward you once you have caught enough "
                          "different Pokémon.",
        "co_col_place": "Place",
        "co_aides_note": "The Kanto Pokédex is counted; if you play with randomly swapped species, the National "
                         "one counts. If you already have the {expshare}, you get the {small} instead.",
        "co_sec_stars": "Stars on the Trainer Card",
        "co_stars_intro": "Each completed goal gives one star, in any order. With all {n} stars the nurse at "
                          "the Pokémon Center greets you differently.",
        "co_star_johto": "Become Champion of Johto",
        "co_star_kanto": "Become Champion of Kanto",
        "co_star_hoenn": "Become Champion of Hoenn",
        "co_star_trainer": "Defeat {name} ({where})",
        "co_sec_lists": "Which Pokémon count",
        "co_lists_intro": "You need to have caught these species for each list.",
        "co_list_sum": "{label}: {n} Pokémon",
        "co_not_counted": "Not counted: {names}.",
        "co_national_all": "The National Pokédex needs all {n} species of the game except the ones named here.",
        "co_reason_hoenn": "belongs to Hoenn",
        "co_reason_mythical": "Mythical Pokémon",
        "co_reason_not_required": "not needed",
    },
}


def _regional_check(check):
    """HasAllRegionalMons is HasAllJohotoMons in this game."""
    if check == "HasAllRegionalMons":
        F.require("src/pokedex.c",
                  r"bool16 HasAllRegionalMons\(void\)\n\{\n    if \(IS_HNS\)\n        return HasAllJohotoMons\(\);")
        return "HasAllJohotoMons"
    return check


def _skipped(ctx, kind):
    skip = [(sp, r) for sp, r in HC.dex_skipped(kind, ctx.lang) if r != "later"]
    if not skip:
        return ""
    names = ", ".join("%s (%s)" % (U.species(ctx, sp), U.e(ctx.t("co_reason_" + r))) for sp, r in skip)
    return U.p(ctx, "co_not_counted", names=names)


def render(ctx):
    t = ctx.t
    lang = ctx.lang
    HC.check_mirror()
    ctx.begin(PATH)
    out = []
    dex = lambda kind: t("co_dex_" + kind)
    need = {k: len(HC.dex_required(k, lang)) for k in ("kanto", "johto", "hoenn", "national")}

    # ---- rewards
    rows = []
    oak = U.place(ctx, "PalletTown_ProfessorOaksLab_Frlg")
    for check, const, _flag in HC.oak_rewards():
        kind = CHECK_KIND[check]
        rows.append([H.esc(dex(kind)), H.esc(t("co_n_caught", n=need[kind])), U.fmt(ctx, "co_oak", where=oak),
                     U.item(ctx, const, icon=True)])
    check, consts, lv = HC.birch_johto_starter()
    kind = CHECK_KIND[check]
    rows.append([H.esc(dex(kind)), H.esc(t("co_n_caught", n=need[kind])),
                 U.fmt(ctx, "co_birch", where=U.place(ctx, "LittlerootTown_ProfessorBirchsLab")),
                 U.fmt(ctx, "co_birch_reward", species=U.join(ctx, [U.species(ctx, c) for c in consts], "or"),
                       lv=lv)])
    out.append(H.section(t("co_sec_rewards"), H.table(
        [(t("co_col_dex"), "main"), t("co_col_need"), t("co_col_who"), t("co_col_reward")], rows),
        id="rewards", intro=H.esc(t("co_rewards_intro"))))

    # ---- diplomas
    F.require("src/diploma.c", r"if \(HasAllMons\(\)\)\s*\{[^}]*gText_DexNational")
    rows = []
    for d in HC.diplomas():
        kind = CHECK_KIND.get(_regional_check(d.check))
        if kind is None:
            raise ValueError("%s: unknown dex check %s" % (d.script, d.check))
        rows.append([H.esc(t("co_diploma_region", region=dex(kind))), H.esc(t("co_n_caught", n=need[kind])),
                     U.fmt(ctx, "co_diploma_where", where=U.place(ctx, d.map_dir))])
    out.append(H.section(t("co_sec_diploma"), H.table(
        [(t("co_col_diploma"), "main"), t("co_col_need"), t("co_col_where")], rows), id="diplomas",
        intro=H.esc(t("co_diploma_intro", n=need["national"]))))

    # ---- aides
    rows = []
    for a in sorted(HC.aides(), key=lambda a: a.required):
        if a.var4 != 2:
            raise ValueError("%s: aide count mode %d not described" % (a.map_dir, a.var4))
        rows.append([U.place(ctx, a.map_dir), H.esc(t("co_n_caught", n=a.required)),
                     U.item(ctx, a.items[0], icon=True)])
    F.require("data/maps/Route15_WestEntrance_2F_Frlg/scripts.inc",
              r"checkitem ITEM_EXP_SHARE\n\tgoto_if_eq VAR_RESULT, TRUE, Route15_WestEntrance_2F_EventScript_GiveSmallExpShare")
    F.require("src/birch_pc.c", r"gSpecialVar_0x8004 == 2 && !IsSpeciesRandomizerOn\(\)")
    note = H.callout(ctx, "note", U.p(ctx, "co_aides_note", expshare=U.item(ctx, "ITEM_EXP_SHARE"),
                                      small=U.item(ctx, "ITEM_EXP_SHARE_SMALL")))
    out.append(H.section(t("co_sec_aides"), H.table(
        [(t("co_col_place"), "main"), t("co_col_need"), t("co_col_reward")], rows) + note, id="aides",
        intro=H.esc(t("co_aides_intro"))))

    # ---- stars
    stars = HC.stars()
    F.require("data/scripts/pkmn_center_nurse.inc",
              r"specialvar VAR_RESULT, CountPlayerTrainerStars\n\tgoto_if_eq VAR_RESULT, %d, EventScript_PkmnCenterNurse_GoldCard"
              % len(stars))
    lis = []
    for st in stars:
        if st.kind == "flag":
            lis.append(H.esc(t(STAR_FLAGS[st.const])))
        else:
            where = []
            for b in trainers.battles(st.const):
                if b.map_id:
                    x = U.place(ctx, b.map_id)
                    if x not in where:
                        where.append(x)
            lis.append(U.fmt(ctx, "co_star_trainer", name=U.trainer(ctx, st.const), where=", ".join(where)))
    out.append(H.section(t("co_sec_stars"), H.ul(lis), id="stars",
                         intro=H.esc(t("co_stars_intro", n=len(stars)))))

    # ---- which species count
    folds = []
    for kind in ("kanto", "johto", "hoenn"):
        sps = HC.dex_required(kind, lang)
        body = _skipped(ctx, kind) + "<p>%s</p>" % ", ".join(U.species(ctx, sp) for sp in sps)
        folds.append(H.details(t("co_list_sum", label=dex(kind), n=len(sps)), H.prose(body)))
    national = H.prose(U.p(ctx, "co_national_all", n=need["national"]) + _skipped(ctx, "national"))
    folds.append(H.details(t("co_list_sum", label=dex("national"), n=need["national"]), national))
    out.append(H.section(t("co_sec_lists"), "".join(folds), id="lists", intro=H.esc(t("co_lists_intro"))))
    ctx.end("".join(out), lead=H.esc(t("co_lead")))
