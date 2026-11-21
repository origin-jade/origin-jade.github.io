"""Struct layouts and constant values straight from the project's compiler.

Nothing about a struct is typed by hand here. A small C file that includes the
game's own headers is compiled with the build's flags (Makefile CPPFLAGS and
CFLAGS, plus the language flag); for every requested field it holds

  * a probe object  `const struct T p = { .field = { -1 } };`   - the set bits in
    the object file give byte offset, bit offset and width (works the same for
    plain members, bit-fields, enums, pointers and the first element of arrays),
  * `sizeof` of the member for array members (spec name ends in "[]"),
  * a tiny function `x.field = -1; return x.field < 0;` whose folded result
    (movs r0, #0/#1) tells whether the member is signed.

Constants (enumerators and object-like macros with the wanted prefixes) are
evaluated by the compiler into one `const long long` array.

    lay, consts, dropped, enum_names = cprobe.build(...)   (enum_names: the names that are enumerators)
    lay["SpeciesInfo"]["size"]                      -> 268
    lay["SpeciesInfo"]["fields"]["baseHP"]          -> dict(bit=0, bits=8, signed=False, size=None)
    consts["SPECIES_BULBASAUR"]                     -> 1
"""
import os
import re
import subprocess

from romlib import Elf

CC = os.environ.get("OJ_ARM_CC", "arm-none-eabi-gcc")
# Makefile: CPPFLAGS and the layout-relevant part of CFLAGS
CPPFLAGS = ["-iquote", "include", "-Wno-trigraphs", "-DMODERN=1", "-DTESTING=0", "-DPOKEMON_HNS", "-std=gnu17"]
CFLAGS = ["-mthumb", "-mthumb-interwork", "-O2", "-mabi=apcs-gnu", "-mtune=arm7tdmi", "-march=armv4t", "-w"]
LANG_FLAGS = {"de": [], "en": ["-DLANG_ENGLISH"]}

_BODY_OK = re.compile(r"^[\w\s()+\-*/<>|&~^?:!=.%]+$")


def _run(args, cwd, stdin=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, input=stdin)


def enumerators(text):
    """Names of all enumerators in preprocessed C text, in order."""
    out = []
    for m in re.finditer(r"\benum\b(?:\s*__attribute__\s*\(\((?:[^()]|\([^()]*\))*\)\))?\s*(?:\w+\s*)?"
                         r"(?::\s*\w+\s*)?\{([^{}]*)\}", text):
        depth, cur = 0, []
        parts = []
        for ch in m.group(1):
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        parts.append("".join(cur))
        for p in parts:
            mm = re.match(r"\s*([A-Za-z_]\w*)", p)
            if mm:
                out.append(mm.group(1))
    return out


def object_macros(dm_text):
    """{name: body} of object-like #defines from `cpp -dM` output."""
    out = {}
    for line in dm_text.splitlines():
        m = re.match(r"#define ([A-Za-z_]\w*) (.*)$", line)     # a '(' right after the name = function-like
        if m and m.group(2).strip():
            out[m.group(1)] = m.group(2).strip()
    return out


def build(repo, lang, work, structs, const_wanted, includes, extra_source="", exprs=None):
    """Compile the probe file. structs: {struct name: [field, ...]} (field may be
    nested "a.b", array members end in "[]"). const_wanted(name) -> bool.
    exprs: {key: C constant expression} evaluated by the compiler as well
    (sizeof of a type or of an extern table's element); they come back in the
    constants dict under "=key"."""
    os.makedirs(work, exist_ok=True)
    flags = CPPFLAGS + LANG_FLAGS[lang]
    prelude = "".join('#include "%s"\n' % h for h in includes) + extra_source + "\n"
    pre = _run([CC, "-E", "-P", *flags, "-x", "c", "-"], repo, prelude)
    if pre.returncode:
        raise RuntimeError("cpp failed:\n" + pre.stderr[:4000])
    dm = _run([CC, "-E", "-dM", *flags, "-x", "c", "-"], repo, prelude)
    names, seen = [], set()
    expr_keys = list(exprs or {})
    enum_names = set()
    for n in enumerators(pre.stdout):
        if n not in seen and const_wanted(n):
            seen.add(n)
            names.append(n)
            enum_names.add(n)
    for n, body in object_macros(dm.stdout).items():
        if n not in seen and const_wanted(n) and _BODY_OK.match(body) and not n.startswith("__"):
            seen.add(n)
            names.append(n)

    lay_lines, field_list = [], []
    sizes = []
    for sname, fields in structs.items():
        sizes.append(sname)
        for i, f in enumerate(fields):
            is_array = f.endswith("[]")
            fname = f[:-2] if is_array else f
            sym = "oj_p_%s_%d" % (sname, i)
            lay_lines.append("const struct %s %s = { .%s = { -1 } };" % (sname, sym, fname))
            if is_array:
                lay_lines.append("const unsigned oj_z_%s_%d = sizeof(((struct %s *)0)->%s);" % (sname, i, sname, fname))
            else:
                lay_lines.append("int oj_s_%s_%d(void) { struct %s x = {0}; x.%s = -1; return x.%s < 0; }"
                                 % (sname, i, sname, fname, fname))
            field_list.append((sname, i, fname, is_array))
    lay_src = "\n".join(lay_lines) + "\nconst unsigned oj_sizeof[] = { %s };\n" % ", ".join(
        "sizeof(struct %s)" % s for s in sizes)

    src_path = os.path.join(work, "probe_%s.c" % lang)
    obj_path = os.path.join(work, "probe_%s.o" % lang)
    dropped = []
    for _ in range(12):
        head = prelude + lay_src + "const long long oj_consts[] = {\n"
        first = head.count("\n") + 1
        body = "".join("(long long)(%s),\n" % n for n in names)
        body += "".join("(long long)(%s),\n" % exprs[k] for k in expr_keys)
        with open(src_path, "w") as fh:
            fh.write(head + body + "0 };\n")
        r = _run([CC, "-c", *flags, *CFLAGS, "-fmax-errors=0", src_path, "-o", obj_path], repo)
        if r.returncode == 0:
            break
        bad = set()
        for m in re.finditer(r"probe_%s\.c:(\d+):\d+: (?:error|note: in expansion)" % lang, r.stderr):
            ln = int(m.group(1))
            if first <= ln < first + len(names):
                bad.add(ln - first)
        if not bad:
            raise RuntimeError("probe does not compile:\n" + r.stderr[:6000])
        dropped += [names[i] for i in sorted(bad)]
        names = [n for i, n in enumerate(names) if i not in bad]
    else:
        raise RuntimeError("probe does not compile after pruning")

    obj = Elf(obj_path)
    import struct as S
    raw = obj.symbol_bytes("oj_consts")
    vals = S.unpack("<%dq" % (len(raw) // 8), raw)
    consts = dict(zip(names, vals))
    for k, v in zip(expr_keys, vals[len(names):]):
        consts["=" + k] = v
    raw = obj.symbol_bytes("oj_sizeof")
    szs = S.unpack("<%dI" % (len(raw) // 4), raw)
    layout = {s: dict(size=z, fields={}) for s, z in zip(sizes, szs)}
    for sname, i, fname, is_array in field_list:
        b = obj.symbol_bytes("oj_p_%s_%d" % (sname, i))
        if len(b) != layout[sname]["size"]:
            raise RuntimeError("probe size of %s.%s" % (sname, fname))
        v = int.from_bytes(b, "little")
        if v == 0:
            raise RuntimeError("probe of %s.%s is empty" % (sname, fname))
        bit = (v & -v).bit_length() - 1
        w = v >> bit
        bits = w.bit_length()
        if w != (1 << bits) - 1:
            raise RuntimeError("probe of %s.%s is not one run of bits" % (sname, fname))
        fld = dict(bit=bit, bits=bits, signed=False, size=None)
        if is_array:
            fld["size"] = S.unpack("<I", obj.symbol_bytes("oj_z_%s_%d" % (sname, i)))[0]
        else:
            code = obj.symbol_bytes("oj_s_%s_%d" % (sname, i))[:2]
            if code == b"\x01\x20":
                fld["signed"] = True
            elif code != b"\x00\x20":
                raise RuntimeError("cannot tell the signedness of %s.%s (%s)" % (sname, fname, code.hex()))
        layout[sname]["fields"][fname] = fld
    return layout, consts, dropped, enum_names & set(consts)


class Struct:
    """Reads members of one struct instance from bytes with a probed layout."""

    def __init__(self, layout, name):
        self.name = name
        self.size = layout[name]["size"]
        self.fields = layout[name]["fields"]

    def get(self, buf, off, field):
        f = self.fields[field]
        nbytes = (f["bit"] % 8 + f["bits"] + 7) // 8
        start = off + f["bit"] // 8
        v = int.from_bytes(buf[start:start + nbytes], "little") >> (f["bit"] % 8)
        v &= (1 << f["bits"]) - 1
        if f["signed"] and v >> (f["bits"] - 1):
            v -= 1 << f["bits"]
        return v

    def array(self, buf, off, field):
        """All elements of an array member (element width from the probe)."""
        f = self.fields[field]
        if f["bit"] % 8 or f["bits"] % 8 or f["size"] is None:
            raise ValueError("%s.%s is not an array member" % (self.name, field))
        w = f["bits"] // 8
        start = off + f["bit"] // 8
        return [int.from_bytes(buf[start + i * w:start + (i + 1) * w], "little") for i in range(f["size"] // w)]

    def raw(self, buf, off, field):
        f = self.fields[field]
        start = off + f["bit"] // 8
        return bytes(buf[start:start + f["size"]])
