"""All shared UI strings of the site, German and English, and the number formats.

    UI["key"] = (german, english)          one place, both languages side by side
    i18n.ui("de", "search")                -> "Suche"
    i18n.num("de", 1234.5)                 -> "1.234,5"      i18n.num("en", 1234.5) -> "1,234.5"
    i18n.pct("de", 12.5)                   -> "12,5 %"       i18n.pct("en", 12.5)   -> "12.5%"
    i18n.money("de", 3000)                 -> "3.000 ₽"      i18n.money("en", 3000) -> "₽3,000"

Page modules keep their own texts in STRINGS = {"de": {...}, "en": {...}};
check_strings() makes the build fail when a key exists in one language only.
Names of Pokémon, moves, items, abilities, places and types never come from
here: they are read from the game data of the respective language build.
"""
from site_config import LANGS

LANG_INDEX = {"de": 0, "en": 1}
HTML_LANG = {"de": "de", "en": "en"}
LANG_NAMES = {"de": "Deutsch", "en": "English"}

UI = {
    # ---------------------------------------------------------------- site
    "site_name": ("Pokémon Origin Jade", "Pokémon Origin Jade"),
    "site_short": ("Origin Jade", "Origin Jade"),
    "site_tagline": ("Spieler-Doku", "Player's guide"),
    "title_sep": (" · ", " · "),
    "skip": ("Zum Inhalt springen", "Skip to content"),
    "menu": ("Menü", "Menu"),
    "menu_close": ("Menü schließen", "Close menu"),
    "nav_label": ("Seiten", "Pages"),
    "crumbs_label": ("Pfad", "Breadcrumb"),
    "outline_label": ("Auf dieser Seite", "On this page"),
    "top": ("Nach oben", "Back to top"),
    "prev": ("Zurück", "Previous"),
    "next": ("Weiter", "Next"),
    "prevnext_label": ("Benachbarte Seiten", "Adjacent pages"),
    "lang_label": ("Sprache", "Language"),
    "lang_switch_to": ("Auf {name} lesen", "Read in {name}"),
    "theme_toggle": ("Hell/Dunkel umschalten", "Switch between light and dark"),
    "footer_note": ("Alle Angaben stammen aus den Daten des Spiels. Level und Prozentwerte sind genau die Werte, "
                    "die das Spiel verwendet.",
                    "Everything here is read from the game's data. Levels and percentages are exactly the values "
                    "the game uses."),
    "footer_fan": ("Inoffizielles Fanprojekt. Pokémon und alle zugehörigen Namen sind Marken ihrer jeweiligen "
                   "Inhaber.",
                   "Unofficial fan project. Pokémon and all related names are trademarks of their respective "
                   "owners."),
    "community": ("Community", "Community"),
    "root_title": ("Pokémon Origin Jade", "Pokémon Origin Jade"),
    # ---------------------------------------------------------------- sections
    "sec_home": ("Start", "Home"),
    "sec_game": ("Spiel", "Game"),
    "sec_pokedex": ("Pokédex", "Pokédex"),
    "sec_world": ("Welt", "World"),
    "sec_battles": ("Kämpfe", "Battles"),
    "sec_data": ("Datenbank", "Database"),
    "sec_guides": ("Guides", "Guides"),
    "overview": ("Übersicht", "Overview"),
    # ---------------------------------------------------------------- search
    "search": ("Suche", "Search"),
    "search_open": ("Suche öffnen", "Open search"),
    "search_placeholder": ("Pokémon, Attacken, Items, Orte …", "Pokémon, moves, items, places …"),
    "search_hint": ("Tippe, um alles zu durchsuchen.", "Type to search everything."),
    "search_none": ("Nichts gefunden für „{q}“.", "Nothing found for “{q}”."),
    "search_loading": ("Suchindex wird geladen …", "Loading the search index …"),
    "search_failed": ("Der Suchindex konnte nicht geladen werden.", "The search index could not be loaded."),
    "search_results": ("Suchergebnisse", "Search results"),
    "search_count": ("{n} Treffer", "{n} results"),
    "search_more": ("+ {n} weitere – Suche verfeinern", "+ {n} more – refine your search"),
    "search_keys_move": ("wählen", "select"),
    "search_keys_open": ("öffnen", "open"),
    "search_keys_close": ("schließen", "close"),
    "close": ("Schließen", "Close"),
    "kind_species": ("Pokémon", "Pokémon"),
    "kind_move": ("Attacken", "Moves"),
    "kind_ability": ("Fähigkeiten", "Abilities"),
    "kind_item": ("Items", "Items"),
    "kind_location": ("Orte", "Places"),
    "kind_trainer": ("Trainer", "Trainers"),
    "kind_page": ("Seiten", "Pages"),
    # ---------------------------------------------------------------- filter bar
    "filter": ("Filter", "Filter"),
    "filter_text": ("Liste durchsuchen", "Search this list"),
    "filter_placeholder": ("Filtern …", "Filter …"),
    "filter_all": ("Alle", "All"),
    "filter_count": ("{shown} von {total}", "{shown} of {total}"),
    "filter_none": ("Kein Eintrag passt zu diesem Filter.", "Nothing matches this filter."),
    "filter_reset": ("Zurücksetzen", "Reset"),
    "filter_type": ("Typ", "Type"),
    "filter_region": ("Region", "Region"),
    "filter_category": ("Kategorie", "Category"),
    # ---------------------------------------------------------------- shared labels
    "level": ("Lv.", "Lv."),
    "level_n": ("Lv. {n}", "Lv. {n}"),
    "level_range": ("Lv. {lo}–{hi}", "Lv. {lo}–{hi}"),
    "none": ("—", "—"),
    "yes": ("Ja", "Yes"),
    "no": ("Nein", "No"),
    "name": ("Name", "Name"),
    "type": ("Typ", "Type"),
    "types": ("Typen", "Types"),
    "category": ("Kategorie", "Category"),
    "power": ("Stärke", "Power"),
    "accuracy": ("Genauigkeit", "Accuracy"),
    "pp": ("AP", "PP"),
    "move": ("Attacke", "Move"),
    "moves": ("Attacken", "Moves"),
    "ability": ("Fähigkeit", "Ability"),
    "abilities": ("Fähigkeiten", "Abilities"),
    "hidden_ability": ("Versteckte Fähigkeit", "Hidden Ability"),
    "hidden_short": ("versteckt", "hidden"),
    "item": ("Item", "Item"),
    "items": ("Items", "Items"),
    "held_item": ("Getragenes Item", "Held item"),
    "price": ("Preis", "Price"),
    "location": ("Ort", "Location"),
    "region": ("Region", "Region"),
    "pokemon": ("Pokémon", "Pokémon"),
    "trainer": ("Trainer", "Trainer"),
    "team": ("Team", "Team"),
    "reward": ("Preisgeld", "Prize money"),
    "nature": ("Wesen", "Nature"),
    "method": ("Methode", "Method"),
    "time": ("Tageszeit", "Time of day"),
    "rate": ("Chance", "Rate"),
    "levels": ("Level", "Levels"),
    "note": ("Hinweis", "Note"),
    "tip": ("Tipp", "Tip"),
    "warning": ("Achtung", "Warning"),
    "shiny": ("Schillernd", "Shiny"),
    "normal_form": ("Normal", "Regular"),
    "sprite_alt": ("{name}", "{name}"),
    "sprite_shiny_alt": ("{name} (schillernd)", "{name} (shiny)"),
    "total": ("Summe", "Total"),
    "base_stats": ("Basiswerte", "Base stats"),
    "double_battle": ("Doppelkampf", "Double battle"),
    "first_battle": ("Erster Kampf", "First battle"),
    "fold_all": ("Alles einklappen", "Collapse all"),
    "unfold_all": ("Alles ausklappen", "Expand all"),
    "hidden_item": ("versteckt", "hidden"),
    "never_misses": ("—", "—"),
    "no_damage": ("—", "—"),
    "evo_from": ("entwickelt sich aus", "evolves from"),
    "evo_chain_label": ("Entwicklungsreihe", "Evolution line"),
    "any_time": ("Jederzeit", "Any time"),
    # damage categories (site labels; the ids are language neutral)
    "cat_physical": ("Physisch", "Physical"),
    "cat_special": ("Speziell", "Special"),
    "cat_status": ("Status", "Status"),
    # times of day (enum TimeOfDay)
    "time_morning": ("Morgens", "Morning"),
    "time_day": ("Tagsüber", "Day"),
    "col_day_night": ("Tag/Nacht", "Day/night"),
    "time_evening": ("Abends", "Evening"),
    "time_night": ("Nachts", "Night"),
    # encounter methods
    "enc_land": ("Hohes Gras", "Tall grass"),
    "enc_cave": ("Höhle", "Cave"),
    "enc_water": ("Surfen", "Surfing"),
    "enc_rock_smash": ("Zertrümmerer", "Rock Smash"),
    "enc_old_rod": ("Angel", "Old Rod"),
    "enc_good_rod": ("Profiangel", "Good Rod"),
    "enc_super_rod": ("Superangel", "Super Rod"),
    # regions
    "region_kanto": ("Kanto", "Kanto"),
    "region_johto": ("Johto", "Johto"),
    "region_hoenn": ("Hoenn", "Hoenn"),
    # learnset column / tab labels
    "learn_level": ("Level", "Level-up"),
    "learn_tm": ("TM/VM", "TM/HM"),
    "learn_tutor": ("Attacken-Lehrer", "Move tutor"),
    "learn_egg": ("Ei-Attacken", "Egg moves"),
    "learn_evo": ("Entw.", "Evo."),
    "learn_none": ("Keine Attacken auf diesem Weg.", "No moves this way."),
    # stats (fallback; the page shows the game's own stat names where the build has them)
    "stat_hp": ("KP", "HP"),
    "stat_atk": ("Angriff", "Attack"),
    "stat_def": ("Vert.", "Defense"),
    "stat_spa": ("Sp. Ang.", "Sp. Atk"),
    "stat_spd": ("Sp. Ver.", "Sp. Def"),
    "stat_spe": ("Init.", "Speed"),
    # dev
    "dev_stub": ("Diese Seite ist noch nicht gebaut.", "This page has not been built yet."),
}

# The fixed pages of the site (information architecture): path -> (section,
# sidebar order, title de, title en[, sidebar label de, sidebar label en]).
# A module claims a page with ctx.add_page(path); title, section and sidebar
# position then come from here. Entity pages (one per Pokémon, move, ...) are
# not listed; they hang below their index page.
SITEMAP = {
    "index": ("home", 0, "Start", "Home"),
    "game/features": ("game", 10, "Neuerungen", "What's new"),
    "game/start": ("game", 20, "Erste Schritte & FAQ", "Getting started & FAQ"),
    "game/settings": ("game", 30, "Einstellungen & Spielmodi", "Settings & game modes"),
    "game/levels": ("game", 40, "Level- & EP-System", "Level & EXP system"),
    "game/changelog": ("game", 50, "Updates", "Updates"),
    "game/credits": ("game", 60, "Credits", "Credits"),
    "pokedex/index": ("pokedex", 10, "Pokédex", "Pokédex", "Alle Pokémon", "All Pokémon"),
    "world/index": ("world", 10, "Welt", "World", "Übersicht", "Overview"),
    "world/kanto": ("world", 20, "Kanto", "Kanto"),
    "world/johto": ("world", 30, "Johto", "Johto"),
    "world/hoenn": ("world", 40, "Hoenn", "Hoenn"),
    "battles/index": ("battles", 10, "Kämpfe", "Battles", "Übersicht", "Overview"),
    "battles/kanto": ("battles", 20, "Arenen & Liga: Kanto", "Gyms & League: Kanto"),
    "battles/johto": ("battles", 30, "Arenen & Liga: Johto", "Gyms & League: Johto"),
    "battles/hoenn": ("battles", 40, "Arenen & Liga: Hoenn", "Gyms & League: Hoenn"),
    "battles/rivals": ("battles", 50, "Rivalen & Schurken-Teams", "Rivals & villain teams"),
    "battles/rematches": ("battles", 60, "Rückkämpfe per PokéCom", "Pokégear rematches"),
    "battles/trainers": ("battles", 70, "Alle Trainer", "All trainers"),
    "data/moves/index": ("data", 10, "Attacken", "Moves"),
    "data/abilities/index": ("data", 20, "Fähigkeiten", "Abilities"),
    "data/items/index": ("data", 30, "Items", "Items"),
    "data/tms": ("data", 40, "TMs & VMs", "TMs & HMs"),
    "data/berries": ("data", 50, "Beeren", "Berries"),
    "data/typechart": ("data", 60, "Typen-Tabelle", "Type chart"),
    "guides/breeding": ("guides", 10, "Zucht", "Breeding"),
    "guides/shiny": ("guides", 20, "Schillernde Pokémon", "Shiny Pokémon"),
    "guides/legendaries": ("guides", 30, "Legendäre Pokémon", "Legendary Pokémon"),
    "guides/gifts": ("guides", 40, "Geschenke & Tausch", "Gifts & in-game trades"),
    "guides/pokeblocks": ("guides", 50, "Pokériegel", "Pokéblocks"),
    "guides/completion": ("guides", 60, "Pokédex vervollständigen", "Completing the Pokédex"),
    "guides/keyitems": ("guides", 70, "Schlüssel-Items", "Key items"),
}

# Strings site.js needs (injected into assets/site.js at build time).
JS_KEYS = ("search", "search_placeholder", "search_hint", "search_none", "search_loading", "search_failed",
           "search_results", "search_more", "search_keys_move", "search_keys_open", "search_keys_close",
           "close", "menu", "menu_close", "filter_count", "filter_none", "fold_all", "unfold_all",
           "kind_species", "kind_move", "kind_ability", "kind_item", "kind_location", "kind_trainer", "kind_page")


def ui(lang, key, **fmt):
    """Shared UI string. KeyError for an unknown key."""
    try:
        s = UI[key][LANG_INDEX[lang]]
    except KeyError:
        raise KeyError("UI string %r missing (common/i18n.py)" % key) from None
    return s.format(**fmt) if fmt else s


def sitemap_title(lang, path, nav=False):
    """Title (or the shorter sidebar label) of a fixed page, None if path is not in SITEMAP."""
    e = SITEMAP.get(path)
    if e is None:
        return None
    i = LANG_INDEX[lang]
    if nav and len(e) >= 6:
        return e[4 + i]
    return e[2 + i]


def js_strings():
    """{lang: {key: text}} for site.js."""
    return {lang: {k: UI[k][LANG_INDEX[lang]] for k in JS_KEYS} for lang in LANGS}


def check():
    """Problems of the shared tables (empty list = fine)."""
    problems = []
    for k, v in UI.items():
        if not (isinstance(v, tuple) and len(v) == len(LANGS) and all(isinstance(x, str) and x for x in v)):
            problems.append("i18n.UI[%r] needs one non-empty text per language %r" % (k, LANGS))
    for p, e in SITEMAP.items():
        if len(e) not in (4, 6) or not all(isinstance(x, str) and x for x in e[2:]):
            problems.append("i18n.SITEMAP[%r] is malformed" % p)
    for k in JS_KEYS:
        if k not in UI:
            problems.append("i18n.JS_KEYS: %r is not in UI" % k)
    return problems


def check_strings(name, strings):
    """Problems of a page module's STRINGS = {"de": {...}, "en": {...}}."""
    problems = []
    if strings is None:
        return problems
    if not isinstance(strings, dict) or set(strings) != set(LANGS):
        return ["%s: STRINGS needs exactly the languages %s" % (name, ", ".join(LANGS))]
    keys = [set(strings[l]) for l in LANGS]
    for i, lang in enumerate(LANGS):
        for other in LANGS[i + 1:]:
            j = LANGS.index(other)
            for k in sorted(keys[i] - keys[j]):
                problems.append("%s: STRINGS key %r exists in %s but not in %s" % (name, k, lang, other))
            for k in sorted(keys[j] - keys[i]):
                problems.append("%s: STRINGS key %r exists in %s but not in %s" % (name, k, other, lang))
    for lang in LANGS:
        for k, v in strings[lang].items():
            if not isinstance(v, str) or not v:
                problems.append("%s: STRINGS[%s][%r] is empty or not text" % (name, lang, k))
    return problems


# ---------------------------------------------------------------------- numbers
def num(lang, x, digits=1):
    """Number in the language's format. ints get thousands separators,
    floats up to `digits` decimals without trailing zeros."""
    if isinstance(x, bool):
        raise TypeError("num() got a bool")
    if isinstance(x, int):
        s = "{:,}".format(x)
    else:
        s = "{:,.{d}f}".format(x, d=digits)
        if "." in s:
            s = s.rstrip("0").rstrip(".")
    if lang == "de":
        s = s.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")
    return s.replace("-", "−")


def pct(lang, x, digits=1):
    """Percentage: de "12,5 %", en "12.5%"."""
    return ("%s %%" if lang == "de" else "%s%%") % num(lang, x, digits)


def money(lang, n):
    """PokéDollar amount: de "3.000 ₽", en "₽3,000"."""
    return ("%s ₽" % num(lang, int(n))) if lang == "de" else ("₽%s" % num(lang, int(n)))


def mult(lang, m):
    """Damage multiplier: ×2, ×½, ×¼, ×0, ×1,5."""
    frac = {0.5: "½", 0.25: "¼", 0.125: "⅛"}
    if m in frac:
        return "×" + frac[m]
    if float(m).is_integer():
        return "×%d" % int(m)
    return "×" + num(lang, float(m), 2)
