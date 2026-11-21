"""Settings & game modes (game/settings): the options menu and the challenge menu,
entry by entry, with the texts of the game.

Sources: gamedata.hand_menus (names, choices and descriptions of both menus),
gamedata.game_rules (which choice a new game starts with, what can still be changed
later, the recommended rules), the scripts and the intro that open the menus.
"""
from common import html as H
from gamedata import game_rules as G
from gamedata import hand_facts as F
from gamedata import hand_menus as M
from pages import _game_util as U
from pages import _game_shared as X

PATH = "game/settings"

# tab constant -> (section id, key of the intro text or None)
CHALLENGE_TABS = (
    ("TAB_MODE", "rules", "set_intro_rules"),
    ("TAB_FEATURES", "general", "set_intro_general"),
    ("TAB_RANDOMIZER", "randomizer", "set_intro_randomizer"),
    ("TAB_NUZLOCKE", "nuzlocke", "set_intro_nuzlocke"),
    ("TAB_DIFFICULTY", "difficulty", "set_intro_difficulty"),
    ("TAB_CHALLENGES", "challenges", "set_intro_challenges"),
)

S = {
    "de": {
        "set_keywords": "optionen herausforderungen nuzlocke zufallsmodus randomizer levelcap schwierigkeit uhr",
        "set_lead": "Origin Jade hat zwei Menüs für Einstellungen: die Optionen für Komfort, Kampf und Ton und die "
                    "Herausforderungen für die Spielregeln – vom Attackenpool über Nuzlocke und Zufallsmodus bis zum "
                    "Level-Limit. Hier steht jeder Eintrag mit dem Text aus dem Spiel.",
        "set_sec_where": "Wo stelle ich was ein?",
        "set_where_options": "Die {b_options} öffnest du jederzeit über das Startmenü. Sie haben {n} Seiten; alles "
                             "dort lässt sich beliebig oft ändern.",
        "set_where_challenges": "Die {b_challenges} erscheinen bei einem neuen Spiel, nachdem du Junge oder Mädchen "
                                "gewählt hast, noch vor der Namenswahl. Mit L und R blätterst du durch die {n} Seiten, "
                                "nach der letzten Seite bestätigst du die Auswahl. Später erreichst du dasselbe Menü "
                                "an jedem PC unter {pc}.",
        "set_where_lock": "Nach dem Spielstart lassen sich viele Regeln nur noch lockern: Bei Einträgen mit dem Hinweis "
                          "„{down}“ kommst du nur noch zu einer Auswahl, die in der Liste weiter oben steht – also "
                          "zurück in Richtung der ersten Auswahl, nicht mehr weiter nach unten. Überlege dir diese "
                          "Regeln deshalb vor dem Start.",
        "set_options": "Optionen",
        "set_challenges": "Herausforderungen",
        "set_default": "Standard",
        "set_recommended": "Empfohlen",
        "set_lock_free": "Jederzeit änderbar",
        "set_lock_down": "Später nur lockern",
        "set_lock_full": "Nur beim Spielstart",
        "set_sec_options": "Optionen",
        "set_options_intro": "Komfort, Kampf und Ton. Diese Einstellungen ändern nichts an den Spielregeln.",
        "set_sec_challenge": "Herausforderungen: {tab}",
        "set_intro_rules": "Die Grundregeln des Spiels. Mit „{recommended}“ gelten die markierten Einstellungen und "
                           "die übrigen Einträge dieser Seite sind gesperrt; erst mit „{custom}“ lassen sie sich "
                           "einzeln umstellen. Alles hier ist auch später frei änderbar.",
        "set_intro_general": "Uhr, Shiny-Chance und kleinere Extras. Das Uhr-Tempo lässt sich nur mit der "
                             "simulierten Uhr einstellen. Meldet die echte Uhr beim Start eines neuen Spiels einen "
                             "Fehler, ist die simulierte Uhr schon vorgewählt.",
        "set_intro_randomizer": "Der Zufallsmodus würfelt aus, was du einzeln einschaltest; die Einträge darunter "
                                "sind nur wählbar, wenn der Zufallsmodus an ist. Alle Angaben dieser Seiten zeigen "
                                "das Spiel ohne Zufallsmodus.",
        "set_intro_nuzlocke": "Die Nuzlocke-Regeln beginnen, sobald du von Prof. Eich den Pokédex bekommst, und "
                              "enden mit dem ersten Titel in Hoenn. Auf der Stufe „{easy}“ sind die Zusatzregeln "
                              "fest; erst ab „{normal}“ lassen sie sich einzeln einstellen.",
        "set_intro_difficulty": "Stellschrauben für leichtere oder härtere Kämpfe. Wie das Level-Limit genau "
                                "rechnet, steht unter {levels}.",
        "set_intro_challenges": "Sonderregeln für ganz eigene Durchläufe. „{thief}“ gibt es nur zusammen mit "
                                "„{mirror}“. Wählst du bei „{onetype}“ den Typ Fee, wird der Fee-Typ automatisch "
                                "eingeschaltet.",
        "set_one_type": "{n} Auswahlmöglichkeiten: jeder der {types} Typen, {random} (das Spiel lost einen Typ aus) "
                        "und {off}",
        "set_hm_title": "Feldattacken trotz Sonderregeln",
        "set_hm": "Mit Nuzlocke, Teamlimit, Spiegel-Modus, einem festen Typ oder einem Zufallsmodus für Starter, "
                  "wilde oder feste Pokémon, Attacken oder Entwicklungen darf das erste Pokémon im Team jede "
                  "Feldattacke einsetzen, auch wenn es sie eigentlich nicht lernen kann. So bleibst du nirgends "
                  "stecken.",
    },
    "en": {
        "set_keywords": "options challenges nuzlocke randomizer level cap difficulty clock",
        "set_lead": "Origin Jade has two menus for settings: the options for comfort, battles and sound, and the "
                    "challenges for the rules of the game – from the movepool to Nuzlocke, the randomizer and the "
                    "level cap. Every entry is listed here with the text the game shows.",
        "set_sec_where": "Where do I set what?",
        "set_where_options": "You can open the {b_options} from the start menu at any time. They have {n} pages, "
                             "and everything there can be changed as often as you like.",
        "set_where_challenges": "The {b_challenges} come up in a new game after you have chosen boy or girl, before "
                                "you enter your name. L and R turn the {n} pages; after the last page you confirm "
                                "your choices. Later the same menu is on every PC under {pc}.",
        "set_where_lock": "Once the game has started, many rules can only be relaxed: entries marked “{down}” only "
                          "let you move to a choice further up their list – back towards the first choice, never "
                          "further down. So think about those rules before you start.",
        "set_options": "options",
        "set_challenges": "challenges",
        "set_default": "Default",
        "set_recommended": "Recommended",
        "set_lock_free": "Change any time",
        "set_lock_down": "Can only be relaxed later",
        "set_lock_full": "Only at the start",
        "set_sec_options": "Options",
        "set_options_intro": "Comfort, battles and sound. None of these settings change the rules of the game.",
        "set_sec_challenge": "Challenges: {tab}",
        "set_intro_rules": "The basic rules of the game. With “{recommended}” the marked settings apply and the "
                           "other entries of this page are locked; “{custom}” lets you change them one by one. "
                           "Everything here can also be changed freely later.",
        "set_intro_general": "Clock, shiny odds and small extras. The clock speed can only be set with the simulated "
                             "clock. If the real clock reports an error when a new game starts, the simulated clock "
                             "is already selected.",
        "set_intro_randomizer": "The randomizer shuffles whatever you switch on; the entries below it can only be "
                                "chosen while the randomizer is on. Everything on these pages describes the game "
                                "without the randomizer.",
        "set_intro_nuzlocke": "The Nuzlocke rules start as soon as Prof. Oak gives you the Pokédex and end with the "
                              "first title in Hoenn. On “{easy}” the extra rules are fixed; from “{normal}” on you "
                              "can set them one by one.",
        "set_intro_difficulty": "Switches for easier or harder battles. How exactly the level cap works is "
                                "explained under {levels}.",
        "set_intro_challenges": "Special rules for runs of your own making. “{thief}” only exists together with "
                                "“{mirror}”. If you pick the Fairy type for “{onetype}”, the Fairy type is switched "
                                "on automatically.",
        "set_one_type": "{n} choices: each of the {types} types, {random} (the game draws a type) and {off}",
        "set_hm_title": "Field moves despite special rules",
        "set_hm": "With Nuzlocke, a party limit, Mirror Mode, a single type, or a randomizer for starters, wild or "
                  "static Pokémon, moves or evolutions, the first Pokémon in your party may use any field move even "
                  "if it could not normally learn it. That way you never get stuck.",
    },
}


def _card(ctx, item, rule=None, mark_key="set_default", extra=None):
    t = ctx.t
    lines = []
    if item.dynamic:
        lines.append(extra or "")
        for d in dict.fromkeys(item.descs):
            lines.append(H.esc(d))
        body = "".join("<p>%s</p>" % x for x in lines if x)
    elif len(item.choices) > 2 and len({c.desc for c in item.choices}) == 1 and item.choices[0].desc:
        # one text for every choice: say it once
        names = []
        for i, c in enumerate(item.choices):
            mark = " " + H.chip(t(mark_key), "jade") if rule is not None and i == rule.default else ""
            names.append(U.b(H.esc(c.name)) + mark)
        body = "<p>%s</p><p>%s</p>" % (H.esc(item.choices[0].desc), " / ".join(names))
    else:
        for i, c in enumerate(item.choices):
            mark = " " + H.chip(t(mark_key), "jade") if rule is not None and i == rule.default else ""
            lines.append("%s%s%s" % (U.b(H.esc(c.name)), mark,
                                     " – " + H.esc(c.desc) if c.desc else ""))
        body = H.ul(lines)
    if rule is not None and rule.lock != "free":
        body += "<p>%s</p>" % H.chip(t("set_lock_" + rule.lock), "warn" if rule.lock == "down" else "muted")
    return H.card(body, title=item.name)


def _options(ctx):
    subs = []
    for tab in M.option_tabs(ctx.lang):
        subs.append(H.sub(tab.name, H.grid([_card(ctx, it) for it in tab.items], "l")))
    return "".join(subs)


def _one_type(ctx):
    types = G.one_type_types()
    # the two names the game draws itself for this entry
    rnd = F.require("src/challenge_menu.c", r'#if GERMAN\s*static const u8 sText_Random\[\] = _\("([^"]+)"\);\s*'
                                            r'static const u8 sText_Off\[\] = _\("([^"]+)"\);\s*#else\s*'
                                            r'static const u8 sText_Random\[\] = _\("([^"]+)"\);\s*'
                                            r'static const u8 sText_Off\[\] = _\("([^"]+)"\);')
    random_name, off_name = (rnd.group(1), rnd.group(2)) if ctx.lang == "de" else \
        (rnd.group(3).capitalize(), rnd.group(4).capitalize())
    text = U.fmt(ctx, "set_one_type", n=len(types) + 2, types=len(types), random=U.b(H.esc(random_name)),
                 off=U.b(H.esc(off_name)) + " " + H.chip(ctx.t("set_default"), "jade"))
    return text + "</p><p>" + H.chips([H.type_chip(ctx, ty) for ty in types])


def render(ctx):
    t = ctx.t
    ctx.begin(PATH)
    rules = G.challenge_rules()
    ch_tabs = M.challenge_tabs(ctx.lang)
    opt_tabs = M.option_tabs(ctx.lang)

    # where the menus are (pinned to the code that opens them)
    F.require("src/oak_speech_hns.c", r"gTasks\[taskId\]\.func = Task_NewGameHnsSpeech_ChooseGender;")
    F.require("src/oak_speech_hns.c", r"static void Task_NewGameHnsSpeech_ChallengeMenu\(u8 taskId\)[\s\S]*?"
                                      r"static void Task_NewGameHnsSpeech_WhatsYourName\(u8 taskId\)")
    F.require("data/scripts/pc.inc", r"EventScript_ChallengeViewer::\s*playse SE_PC_LOGIN\s*callnative Script_OpenChallengeMenu")
    F.require("src/challenge_menu.c", r"if \(JOY_NEW\(L_BUTTON\)\)\s*\{\s*SwitchTab\(taskId, -1\);")
    pc_entry = X.pc_entry(ctx)

    body = []
    where = "".join([
        U.p(ctx, "set_where_options", b_options=U.b(H.esc(t("set_options"))), n=len(opt_tabs)),
        U.p(ctx, "set_where_challenges", b_challenges=U.b(H.esc(t("set_challenges"))), n=len(ch_tabs),
            pc=U.quote(ctx, pc_entry)),
        U.p(ctx, "set_where_lock", down=H.esc(t("set_lock_down"))),
    ])
    body.append(H.section(t("set_sec_where"), H.prose(where), id="where"))

    body.append(H.section(t("set_sec_options"), _options(ctx), id="options", intro=H.esc(t("set_options_intro"))))

    # facts the intro texts rely on
    F.require("src/challenge_menu.c", r"return \*GetSelectionPtr\(TAB_MODE, ITEM_MODE_GAMEMODE\) == 1; // CUSTOM")
    F.require("src/challenge_menu.c", r"case ITEM_FEATURES_RTC_SPEED:\s*// Only with the fake clock\.")
    F.require("src/new_game.c", r"if \(RtcGetErrorStatus\(\) & RTC_ERR_FLAG_MASK\)\s*"
                                r"gSaveblock3\.challengeSettings\.tx_Features_RTCType = 1;")
    F.require("src/challenge_menu.c", r"default:\s*return masterOn;")
    F.require("data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc", r"setflag FLAG_START_NUZLOCKE")
    F.require("data/maps/EverGrandeCity_HallOfFame/scripts.inc", r"setflag FLAG_END_NUZLOCKE")
    F.require("src/challenge_menu.c", r"if \(nuzSel == 1\) // EASY — lock all sub-options except RARE_CANDY")
    F.require("src/challenge_menu.c", r"case ITEM_CHALLENGES_MIRROR_THIEF:\s*"
                                      r"return \*GetSelectionPtr\(TAB_CHALLENGES, ITEM_CHALLENGES_MIRROR\) == 1;")
    F.require("src/challenge_menu.c", r"cs->tx_Mode_Fairy_Types = cs->tx_Challenges_OneTypeChallenge == TYPE_FAIRY;")
    F.require("src/challenge_menu.c",
              r"return \(cs->tx_Challenges_Nuzlocke\s*\|\| cs->tx_Nuzlocke_EasyMode\s*\|\| cs->tx_Challenges_Mirror\s*"
              r"\|\| cs->tx_Random_Moves\s*\|\| cs->tx_Random_Starter\s*\|\| cs->tx_Random_WildPokemon\s*"
              r"\|\| cs->tx_Random_Static\s*\|\| cs->tx_Random_Evolutions\s*\|\| cs->tx_Random_EvolutionMethods\s*"
              r"\|\| cs->tx_Challenges_PartyLimit != 0\s*\|\| IsOneTypeChallengeActive\(\)\);")

    mode = X.challenge(ctx, "TAB_MODE", "ITEM_MODE_GAMEMODE")
    nuz = X.challenge(ctx, "TAB_NUZLOCKE", "ITEM_NUZLOCKE_NUZLOCKE")
    fmt = {
        "recommended": H.esc(mode.choices[0].name), "custom": H.esc(mode.choices[1].name),
        "easy": H.esc(nuz.choices[1].name), "normal": H.esc(nuz.choices[2].name),
        "levels": U.anchor_link(ctx, "game/levels", "caps", ctx.title_of("page", "game/levels") or ""),
        "thief": H.esc(X.challenge(ctx, "TAB_CHALLENGES", "ITEM_CHALLENGES_MIRROR_THIEF").name),
        "mirror": H.esc(X.challenge(ctx, "TAB_CHALLENGES", "ITEM_CHALLENGES_MIRROR").name),
        "onetype": H.esc(X.challenge(ctx, "TAB_CHALLENGES", "ITEM_CHALLENGES_ONE_TYPE").name),
    }
    one_type_pos = G.position("TAB_CHALLENGES", "ITEM_CHALLENGES_ONE_TYPE")
    mode_tab = G.position("TAB_MODE", "ITEM_MODE_GAMEMODE")
    for const, sid, intro_key in CHALLENGE_TABS:
        ti = G.position(const, {"TAB_MODE": "ITEM_MODE_GAMEMODE", "TAB_FEATURES": "ITEM_FEATURES_RTC_TYPE",
                                "TAB_RANDOMIZER": "ITEM_RANDOM_OFF_ON", "TAB_NUZLOCKE": "ITEM_NUZLOCKE_NUZLOCKE",
                                "TAB_DIFFICULTY": "ITEM_DIFFICULTY_PARTY_LIMIT",
                                "TAB_CHALLENGES": "ITEM_CHALLENGES_POKECENTER"}[const])[0]
        tab = ch_tabs[ti]
        cards = []
        for p, it in enumerate(tab.items):
            rule = rules[(ti, p)]
            if (ti, p) == one_type_pos:
                cards.append(_card(ctx, it, rule, extra=_one_type(ctx)))
            elif ti == mode_tab[0] and p != mode_tab[1]:
                cards.append(_card(ctx, it, rule, mark_key="set_recommended"))
            else:
                cards.append(_card(ctx, it, rule))
        intro = U.fmt(ctx, intro_key, **{k: v for k, v in fmt.items() if "{%s}" % k in t(intro_key)})
        sec = H.grid(cards, "l")
        if const == "TAB_CHALLENGES":
            sec += H.callout(ctx, "note", "<p>%s</p>" % H.esc(t("set_hm")), title=t("set_hm_title"))
        body.append(H.section(t("set_sec_challenge", tab=tab.name), sec, id=sid, intro=intro))

    ctx.end("".join(body), lead=H.esc(t("set_lead")), description=t("set_lead"))
