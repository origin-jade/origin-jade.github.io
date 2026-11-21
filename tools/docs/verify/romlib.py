"""Reading the compiled game: ELF32 files, symbols, ROM bytes, game text.

    elf = Elf(path)                  minimal ELF32 little-endian reader (sections, symbols,
                                     program headers); no external modules
    rom = Rom(elf_path, gba_path)    address -> bytes, checked against both files
    rom.sym("gSpeciesInfo")          -> (address, size)   (arm-none-eabi-nm -S)
    rom.u8/u16/u32/s8/bytes(addr)    little-endian reads at a ROM address (0x08000000 based)
    cm = Charmap(repo/charmap.txt)   cm.decode(bytes) -> game text in the notation of the sources
"""
import re
import struct
import subprocess

ROM_BASE = 0x08000000


class Elf:
    """ELF32 little-endian: section table, symbol table, program headers."""

    def __init__(self, path):
        self.path = path
        self.data = open(path, "rb").read()
        d = self.data
        if d[:4] != b"\x7fELF" or d[4] != 1 or d[5] != 1:
            raise ValueError("%s: not an ELF32 little-endian file" % path)
        (self.e_type, self.e_machine, _v, self.e_entry, self.e_phoff, self.e_shoff, _fl, _eh,
         self.e_phentsize, self.e_phnum, self.e_shentsize, self.e_shnum, self.e_shstrndx) = \
            struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
        self.sections = []
        for i in range(self.e_shnum):
            (name, typ, flags, addr, off, size, link, info, align, entsize) = \
                struct.unpack_from("<IIIIIIIIII", d, self.e_shoff + i * self.e_shentsize)
            self.sections.append(dict(name_off=name, type=typ, flags=flags, addr=addr, offset=off,
                                      size=size, link=link, info=info, entsize=entsize, index=i))
        strtab = self.sections[self.e_shstrndx] if self.e_shnum else None
        for s in self.sections:
            s["name"] = self._str(strtab, s["name_off"])
        self.segments = []
        for i in range(self.e_phnum):
            (typ, off, vaddr, paddr, filesz, memsz, flags, align) = \
                struct.unpack_from("<IIIIIIII", d, self.e_phoff + i * self.e_phentsize)
            self.segments.append(dict(type=typ, offset=off, vaddr=vaddr, paddr=paddr,
                                      filesz=filesz, memsz=memsz, flags=flags))
        self._symbols = None

    def _str(self, strsec, off):
        if strsec is None:
            return ""
        start = strsec["offset"] + off
        end = self.data.index(b"\0", start)
        return self.data[start:end].decode("utf-8", "replace")

    def section(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        return None

    def symbols(self):
        """{name: dict(value, size, shndx, bind, type)} of .symtab (last definition wins)."""
        if self._symbols is None:
            out = {}
            for sec in self.sections:
                if sec["type"] != 2:        # SHT_SYMTAB
                    continue
                strsec = self.sections[sec["link"]]
                for i in range(sec["size"] // 16):
                    name, value, size, info, _other, shndx = struct.unpack_from(
                        "<IIIBBH", self.data, sec["offset"] + i * 16)
                    n = self._str(strsec, name)
                    if n:
                        out[n] = dict(value=value, size=size, shndx=shndx, bind=info >> 4, type=info & 15)
            self._symbols = out
        return self._symbols

    def symbol_bytes(self, name):
        """Bytes of a defined object/function symbol of a relocatable object (.o)."""
        s = self.symbols()[name]
        sec = self.sections[s["shndx"]]
        value = s["value"] & ~1 if s["type"] == 2 else s["value"]   # thumb bit of functions
        if sec["type"] == 8:                 # SHT_NOBITS (.bss): all zero
            return bytes(s["size"])
        start = sec["offset"] + value - (sec["addr"] if self.e_type == 2 else 0)
        return self.data[start:start + s["size"]]

    def file_offset(self, addr):
        """File offset of a loaded address (PT_LOAD segments), None if not in the file."""
        for seg in self.segments:
            if seg["type"] == 1 and seg["vaddr"] <= addr < seg["vaddr"] + seg["filesz"]:
                return seg["offset"] + addr - seg["vaddr"]
        return None


class Rom:
    """The ROM image with the ELF's symbols. Reads come from the .gba; the ELF
    segment that holds the same address must contain the same bytes (checked for
    every symbol table that is read through table_bytes())."""

    def __init__(self, elf_path, gba_path, nm="arm-none-eabi-nm"):
        self.elf = Elf(elf_path)
        self.gba = open(gba_path, "rb").read()
        self.syms = {}
        self.ambiguous = set()      # names that stand for several addresses (static symbols)
        out = subprocess.run([nm, "-S", elf_path], capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            p = line.split()
            if len(p) == 4:
                name, val = p[3], (int(p[0], 16), int(p[1], 16))
            elif len(p) == 3:
                name, val = p[2], (int(p[0], 16), 0)
            else:
                continue
            if name in self.syms and self.syms[name][0] != val[0]:
                self.ambiguous.add(name)
            self.syms.setdefault(name, val)
        self.checked = 0

    def has(self, name):
        return name in self.syms

    def sym(self, name):
        if name not in self.syms:
            raise KeyError("symbol %s is not in %s" % (name, self.elf.path))
        if name in self.ambiguous:
            raise KeyError("symbol %s exists several times in %s" % (name, self.elf.path))
        return self.syms[name]

    def in_rom(self, addr):
        return ROM_BASE <= addr < ROM_BASE + len(self.gba)

    def bytes(self, addr, n):
        if not (self.in_rom(addr) and self.in_rom(addr + n - 1)):
            raise ValueError("address 0x%08X (+%d) is outside the ROM" % (addr, n))
        o = addr - ROM_BASE
        return self.gba[o:o + n]

    def table_bytes(self, name):
        """All bytes of a symbol; ELF and .gba must agree."""
        addr, size = self.sym(name)
        b = self.bytes(addr, size)
        fo = self.elf.file_offset(addr)
        if fo is None or self.elf.data[fo:fo + size] != b:
            raise ValueError("%s: ELF and ROM image differ at 0x%08X" % (name, addr))
        self.checked += 1
        return b

    def u8(self, a):
        return self.bytes(a, 1)[0]

    def u16(self, a):
        return struct.unpack("<H", self.bytes(a, 2))[0]

    def u32(self, a):
        return struct.unpack("<I", self.bytes(a, 4))[0]

    def cstr(self, addr, limit=4000):
        """Game string bytes at addr up to (not including) the 0xFF terminator."""
        if not addr:
            return None
        o = addr - ROM_BASE
        end = self.gba.find(b"\xff", o, o + limit)
        if end < 0:
            raise ValueError("unterminated string at 0x%08X" % addr)
        return self.gba[o:end]


class Charmap:
    """charmap.txt -> decoder. The first definition of a byte sequence wins
    (Latin block before the Japanese one, '-' before '_', the typographic
    apostrophe before the plain one)."""

    # how the C sources write the control characters
    ESCAPES = {"\\n": "\n", "\\l": "\\l", "\\p": "\\p"}

    def __init__(self, path):
        self.seq = {}        # bytes tuple -> text
        self.char_byte = {}  # single character -> byte
        for line in open(path, encoding="utf-8"):
            line = line.split("@")[0].rstrip() if not line.lstrip().startswith("'@'") else line.rstrip()
            m = re.match(r"^('(?:\\.|[^'\\])+'|\w+)\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+)$", line)
            if not m:
                continue
            key, val = m.group(1), tuple(int(x, 16) for x in m.group(2).split())
            if key.startswith("'"):
                ch = key[1:-1]
                if ch.startswith("\\") and len(ch) == 2:
                    ch = {"\\n": "\n", "\\l": "\\l", "\\p": "\\p", "\\'": "'", "\\\\": "\\"}.get(ch, ch)
                if len(ch) == 1 and len(val) == 1:
                    self.char_byte.setdefault(ch, val[0])
                txt = ch
            else:
                txt = "{%s}" % key
            self.seq.setdefault(val, txt)
        self.maxlen = max(len(k) for k in self.seq)
        self.byte_char = {}
        for k, v in self.seq.items():
            if len(k) == 1:
                self.byte_char[k[0]] = v

    # Sequences of several bytes are text only behind these first bytes: the
    # PKMN / POKEBLOCK ligatures and the control prefixes. The sound and music
    # ids of the charmap (SE_M_MILK_DRINK = E1 00) are arguments of control
    # codes and must not be matched in running text ("m " is E1 00 as well).
    MULTI_FIRST = frozenset((0x53, 0x55, 0xF8, 0xF9, 0xFC, 0xFD))

    def decode(self, data):
        """bytes (without terminator) -> text. Unknown bytes become {XX}."""
        if data is None:
            return None
        out, i, n = [], 0, len(data)
        while i < n:
            top = min(self.maxlen, n - i) if data[i] in self.MULTI_FIRST else 1
            for ln in range(top, 0, -1):
                t = self.seq.get(tuple(data[i:i + ln]))
                if t is not None:
                    out.append(t)
                    i += ln
                    break
            else:
                out.append("{%02X}" % data[i])
                i += 1
        return "".join(out)

    def decode_fixed(self, data):
        """Fixed-size name buffer: text up to the 0xFF terminator. A buffer of
        zero bytes only was never initialised (no terminator either): empty."""
        if not any(data):
            return ""
        end = data.find(b"\xff")
        return self.decode(data if end < 0 else data[:end])

    def canon(self, s):
        """Text as the ROM can hold it: every character replaced by the first
        charmap character with the same byte ("'" -> "’", "_" -> "-"). Characters
        whose byte is first defined as a named glyph ({NBSP}) stay as they are."""
        if s is None:
            return None
        out = []
        for c in s:
            b = self.char_byte.get(c)
            t = self.byte_char.get(b) if b is not None else None
            out.append(t if t is not None and len(t) == 1 else c)
        return "".join(out)
