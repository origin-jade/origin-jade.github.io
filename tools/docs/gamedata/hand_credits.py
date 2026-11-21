"""Credits as the game and the repository state them.

    hand_credits.roll()        -> [(heading, [names])] in roll order: the in-game credits of
                                  this build (src/data/credits_hns.h, sCreditsEntryPointerTable;
                                  title entries form the heading, "A: B" for two title lines,
                                  pages with the same heading are merged)
    hand_credits.chain()       -> [(project, author, url, note)] README.md "## Credits" list
    hand_credits.contributors() -> [(name, [role titles])] CREDITS.md all-contributors table
                                  (names and emoji-key titles only; avatars and links are not used)
    hand_credits.resources()   -> [(section, [(name, url)])] CREDITS.md "Other Credits"/"Resources"

credits_hns.h has no #if branches; the roll is plain English text in the ROM too.
"""
import functools
import html
import re

from . import tu as TU
from . import hand_facts as F

CREDITS_H = "src/data/credits_hns.h"


@functools.lru_cache(maxsize=None)
def roll():
    src = F.raw(CREDITS_H)
    F.require("src/credits_hns.c", r'#include "data/credits_hns.h"')
    texts = dict((k, v) for k, v in re.findall(r'static const u8 (sCreditsText_\w+)\[\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\);', src))
    entries = {}
    for name, title, tsym in re.findall(r"static const struct CreditsEntry (sCreditsEntry_\w+)\s*=\s*\{\s*\d+\s*,\s*(TRUE|FALSE)\s*,\s*(sCreditsText_\w+)\s*\};", src):
        if tsym not in texts:
            raise TU.DataError("%s: %s uses unknown text %s" % (CREDITS_H, name, tsym))
        entries[name] = (title == "TRUE", F.clean(texts[tsym]))
    table = src[src.index("sCreditsEntryPointerTable[PAGE_COUNT][ENTRIES_PER_PAGE] ="):]
    table = table[:table.index("\n};")]
    order, groups = [], {}
    for page, body in re.findall(r"\[(PAGE_\w+)\]\s*=\s*\{(.*?)\}", table, re.S):
        heads, names = [], []
        for ref in re.findall(r"&(sCreditsEntry_\w+)|\b(_)\b", body):
            sym = ref[0]
            if not sym or sym == "sCreditsEntry_EmptyString":
                continue
            if sym not in entries:
                raise TU.DataError("%s: %s unknown" % (CREDITS_H, sym))
            is_title, txt = entries[sym]
            if not txt:
                continue
            (heads if is_title else names).append(txt)
        if not names:
            continue                      # title page ("POKéMON HEART & SOUL", "Credits")
        head = ": ".join(heads) if heads else ""
        if head not in groups:
            groups[head] = []
            order.append(head)
        for n in names:
            if n not in groups[head]:
                groups[head].append(n)
    return [(h, groups[h]) for h in order]


@functools.lru_cache(maxsize=None)
def chain():
    src = F.raw("README.md")
    sec = src[src.index("# Credits"):]
    sec = sec[sec.index("Origin Jade stands on a chain of projects"):]
    out = []
    for proj, author, url, rest in re.findall(
            r"^- \*\*(.+?)\*\*(?: \(([^)]*)\))?[^\[]*?\[[^\]]*\]\(([^)]+)\)[,.]?(.*?)(?=^- |\n\n)", sec, re.M | re.S):
        out.append((proj, author, url, " ".join(rest.split())))
    if len(out) < 4:
        raise TU.DataError("README.md credits list changed shape")
    return out


@functools.lru_cache(maxsize=None)
def contributors():
    src = F.raw("CREDITS.md")
    table = src[src.index("<table>"):src.index("</tbody>")]
    out = []
    for cell in re.findall(r"<td[^>]*>(.*?)</td>", table, re.S):
        name = re.search(r"<b>(.*?)</b>", cell)
        if not name:
            continue
        roles = re.findall(r'title="([^"]+)"', cell)
        out.append((html.unescape(name.group(1)), roles))
    return out


@functools.lru_cache(maxsize=None)
def resources():
    src = F.raw("CREDITS.md")
    sec = src[src.index("## Other Credits"):]
    out, cur = [], None
    for line in sec.splitlines():
        h = re.match(r"^#{2,3} (.+?):?\s*$", line)
        if h:
            if h.group(1) != "Other Credits":
                cur = (h.group(1), [])
                out.append(cur)
            continue
        li = re.match(r"^- (.*)$", line)
        if li and cur is not None:
            m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", li.group(1))
            if m:
                prefix = li.group(1)[:m.start()].strip()
                cur[1].append(((prefix + " " + m.group(1)).strip(), m.group(2)))
    return out
