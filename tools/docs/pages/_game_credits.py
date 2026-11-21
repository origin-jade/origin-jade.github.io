"""Credits (game/credits): the projects Origin Jade is built on and the people the
game and the repository credit.

Sources (gamedata.hand_credits): the project chain of README.md "## Credits", the
credits roll of the game (names exactly as the game shows them), the contributors
table and the resource list of CREDITS.md (names and roles only).
"""
from common import html as H
from gamedata import hand_credits as K
from gamedata import hand_facts as F
from pages import _game_util as U

PATH = "game/credits"

S = {
    "de": {
        "cr_keywords": "credits danksagung mitwirkende team heart soul expansion abspann",
        "cr_lead": "Wer Pokémon Origin Jade macht und auf welchen Projekten es aufbaut.",
        "cr_sec_team": "Origin Jade",
        "cr_team_intro": "Pokémon Origin Jade ist ein Projekt von:",
        "cr_sec_chain": "Worauf Origin Jade aufbaut",
        "cr_chain_hns_t": "Pokémon Heart & Soul",
        "cr_chain_hns": "Version {ver} vom HnS-Team – die direkte Grundlage von Origin Jade. Johto stammt von dort.",
        "cr_chain_modern_t": "Modern Emerald",
        "cr_chain_modern": "Von resetes12 – die Basis, auf der Heart & Soul zuerst aufgebaut wurde.",
        "cr_chain_rhh_t": "pokeemerald-expansion",
        "cr_chain_rhh": "Von RHH (Rom Hacking Hideout), Version {ver} mit späteren Änderungen und ausgewählten "
                        "Korrekturen bis {fix}.",
        "cr_chain_pret_t": "pokeemerald",
        "cr_chain_pret": "Von pret – die Grundlage, auf der alle diese Projekte aufbauen.",
        "cr_chain_ask": "Wer Origin Jade weiterverwendet, nennt bitte Origin Jade und behält die ganze Kette bei: "
                        "Pokémon Heart & Soul, Modern Emerald, pokeemerald-expansion von RHH mit Versionsnummer und "
                        "pokeemerald.",
        "cr_sec_roll": "Abspann des Spiels",
        "cr_roll_intro": "Die Namen aus dem Abspann, in der Reihenfolge und Schreibweise des Spiels.",
        "cr_sec_contrib": "Mitwirkende der Grundlage",
        "cr_contrib_intro": "Die {n} Mitwirkenden, die die Projektunterlagen für pokeemerald-expansion aufführen, "
                            "mit ihren Beiträgen.",
        "cr_col_name": "Name", "cr_col_roles": "Beiträge",
        "cr_sec_res": "Weitere Quellen",
        "cr_res_mega": "Überwelt-Sprites der Mega-Entwicklungen",
        "cr_res_other": "Grafiken, Daten und Vorarbeiten",
        "cr_role_code": "Code", "cr_role_maintenance": "Pflege", "cr_role_design": "Design",
        "cr_role_doc": "Dokumentation", "cr_role_data": "Daten", "cr_role_bugs": "Fehlerberichte",
        "cr_role_infra": "Infrastruktur", "cr_role_pm": "Projektleitung", "cr_role_promo": "Öffentlichkeitsarbeit",
        "cr_role_research": "Recherche", "cr_role_review": "Reviews", "cr_role_tests": "Tests",
        "cr_role_tutorials": "Anleitungen", "cr_role_usertest": "Spieltests",
    },
    "en": {
        "cr_keywords": "credits thanks contributors team heart soul expansion",
        "cr_lead": "Who makes Pokémon Origin Jade and which projects it is built on.",
        "cr_sec_team": "Origin Jade",
        "cr_team_intro": "Pokémon Origin Jade is a project by:",
        "cr_sec_chain": "What Origin Jade is built on",
        "cr_chain_hns_t": "Pokémon Heart & Soul",
        "cr_chain_hns": "Version {ver} by the HnS team – the direct base of Origin Jade. Johto comes from it.",
        "cr_chain_modern_t": "Modern Emerald",
        "cr_chain_modern": "By resetes12 – the base Heart & Soul was first built on.",
        "cr_chain_rhh_t": "pokeemerald-expansion",
        "cr_chain_rhh": "By RHH (Rom Hacking Hideout), version {ver} with later changes and selected fixes up "
                        "to {fix}.",
        "cr_chain_pret_t": "pokeemerald",
        "cr_chain_pret": "By pret – the foundation all of these projects build on.",
        "cr_chain_ask": "If you build on Origin Jade, please credit Origin Jade and keep the whole chain: Pokémon "
                        "Heart & Soul, Modern Emerald, RHH's pokeemerald-expansion with its version number, and "
                        "pokeemerald.",
        "cr_sec_roll": "The game's credits",
        "cr_roll_intro": "The names from the credits roll, in the game's order and spelling.",
        "cr_sec_contrib": "Contributors to the base",
        "cr_contrib_intro": "The {n} contributors the project papers list for pokeemerald-expansion, with what "
                            "they contributed.",
        "cr_col_name": "Name", "cr_col_roles": "Contributions",
        "cr_sec_res": "Further sources",
        "cr_res_mega": "Overworld sprites of the Mega Evolutions",
        "cr_res_other": "Graphics, data and groundwork",
        "cr_role_code": "Code", "cr_role_maintenance": "Maintenance", "cr_role_design": "Design",
        "cr_role_doc": "Documentation", "cr_role_data": "Data", "cr_role_bugs": "Bug reports",
        "cr_role_infra": "Infrastructure", "cr_role_pm": "Project management", "cr_role_promo": "Promotion",
        "cr_role_research": "Research", "cr_role_review": "Reviews", "cr_role_tests": "Tests",
        "cr_role_tutorials": "Tutorials", "cr_role_usertest": "Playtesting",
    },
}

CHAIN = (("Pokémon Heart & Soul", "hns"), ("Modern Emerald", "modern"), ("pokeemerald-expansion", "rhh"),
         ("pokeemerald", "pret"))
ROLES = {"Code": "code", "Maintenance": "maintenance", "Design": "design", "Documentation": "doc", "Data": "data",
         "Bug reports": "bugs", "Infrastructure (Hosting, Build-Tools, etc)": "infra", "Project Management": "pm",
         "Promotion": "promo", "Research": "research", "Reviewed Pull Requests": "review", "Tests": "tests",
         "Tutorials": "tutorials", "User Testing": "usertest"}
RESOURCES = {"Mega Evolution Overworld Sprite Credits": "cr_res_mega", "Resources": "cr_res_other"}


def _names(names):
    return "<p>%s</p>" % " · ".join(H.esc(n) for n in names)


# the people behind Origin Jade, as they want to be named
TEAM = ("xMyDayyy", "PekingEnte3")


def render(ctx):
    t = ctx.t
    ctx.begin(PATH)
    body = [H.section(t("cr_sec_team"), H.ul([H.esc(n) for n in TEAM]), id="team", intro=H.esc(t("cr_team_intro")))]

    # ---- the chain of projects (README)
    chain = K.chain()
    if [c[0] for c in chain] != [c[0] for c in CHAIN]:
        raise F.TU.DataError("README credits chain changed: %r" % [c[0] for c in chain])
    hns = F.require("README.md", r"\*\*Pokémon Heart & Soul\*\* \(pokemonHnS-expansion\) (\d+\.\d+\.\d+) by the HnS team").group(1)
    rhh = F.require("README.md", r"version (\d+\.\d+\.\d+) with later unreleased changes\s*"
                                 r"\(`include/constants/expansion\.h`\) and selected fixes up to (\d+\.\d+\.\d+)")
    F.require("README.md", r"\*\*Modern Emerald\*\* by resetes12")
    F.require("README.md", r"\*\*pokeemerald-expansion\*\* by RHH \(Rom Hacking Hideout\)")
    F.require("README.md", r"\*\*pokeemerald\*\* by pret")
    F.require("README.md", r"Johto comes from Pokémon Heart & Soul")
    F.require("README.md", r"If you use it, credit Origin\s+Jade and keep the full chain")
    fmt = {"hns": {"ver": H.esc(hns)}, "rhh": {"ver": H.esc(rhh.group(1)), "fix": H.esc(rhh.group(2))}}
    cards = [H.card("<p>%s</p>" % U.fmt(ctx, "cr_chain_" + key, **fmt.get(key, {})), title=t("cr_chain_%s_t" % key))
             for _name, key in CHAIN]
    body.append(H.section(t("cr_sec_chain"), H.grid(cards, "m") + H.callout(ctx, "note", U.p(ctx, "cr_chain_ask")),
                          id="projects"))
    # The credits roll and the contributors file of the game still describe the base project;
    # they are shown again once the game has its own (render_base below).
    ctx.end("".join(body), lead=H.esc(t("cr_lead")), description=t("cr_lead"))


def render_base(ctx, body):
    t = ctx.t

    # ---- the credits roll of the game
    roll = [(head, names) for head, names in K.roll() if names]
    cards = [H.card(_names(names), title=head) if head else H.card(_names(names)) for head, names in roll]
    body.append(H.section(t("cr_sec_roll"), H.grid(cards, "l"), id="roll", intro=H.esc(t("cr_roll_intro"))))

    # ---- contributors file
    contrib = K.contributors()
    rows = []
    for name, roles in contrib:
        unknown = [r for r in roles if r not in ROLES]
        if unknown:
            raise F.TU.DataError("CREDITS.md: role %r has no translation" % unknown[0])
        rows.append([H.esc(name), H.esc(", ".join(t("cr_role_" + ROLES[r]) for r in roles)) if roles else None])
    table = H.table([(t("cr_col_name"), "main"), t("cr_col_roles")], rows)
    body.append(H.section(t("cr_sec_contrib"), table, id="contributors",
                          intro=H.esc(t("cr_contrib_intro", n=len(contrib)))))

    # ---- other sources
    subs = []
    for sec, entries in K.resources():
        if sec not in RESOURCES:
            raise F.TU.DataError("CREDITS.md: section %r is new" % sec)
        subs.append(H.card(H.ul([H.esc(name) for name, _url in entries]), title=t(RESOURCES[sec])))
    body.append(H.section(t("cr_sec_res"), H.grid(subs, "l"), id="sources"))

    ctx.end("".join(body), lead=H.esc(t("cr_lead")), description=t("cr_lead"))
