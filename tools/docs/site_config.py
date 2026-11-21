"""Settings of the documentation site that are not game data.

Edit this file to change the shown version or to add community links.
"""

# Shown in the footer and on the start page (both languages).
VERSION = {"de": "Version 0.9.1 (Beta)", "en": "Version 0.9.1 (Beta)"}

# Language a visitor gets when neither a stored choice nor the browser
# language decides (root index.html).
DEFAULT_LANG = "de"
LANGS = ("de", "en")

# Community links. An empty URL means the link is not shown anywhere.
# Each entry: key, label (de, en), URL.
COMMUNITY_LINKS = (
    ("discord", ("Discord", "Discord"), ""),
    ("github", ("GitHub", "GitHub"), ""),
    ("hackdex", ("Hackdex", "Hackdex"), ""),
)

# Box icon used as the site mark in the top bar and as browser tab icon
# (a species constant; the sprite comes from the game's graphics).
MASCOT = "SPECIES_RAYQUAZA"

# English texts. The repository holds both languages, so the English site reads the
# English names and texts from this tree. A different source tree can still be given
# with the environment variable OJ_DOCS_EN_SRC (or build_site.py --en-src), e.g. to
# preview a translation branch; paths listed here are tried first to last.
EN_TEXT_SOURCE = ()

# How English names are written. The English game writes names in capitals
# (BULBASAUR, POUND, LITTLEROOT TOWN):
#   "title"  natural capitalisation (Bulbasaur, Pound, Littleroot Town) - default
#   "game"   exactly as the game shows them
# Only names are converted, never descriptions or dialogue. OJ_DOCS_EN_NAME_STYLE
# (or build_site.py --en-name-style) overrides this.
EN_NAME_STYLE = "title"

# True: every page asks search engines not to list it (for a preview before the release).
# Set to False for the public release.
NOINDEX = True
