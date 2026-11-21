"""Read C data tables of the game through the C preprocessor.

(The preprocessor call itself lives in tu.py.)
Enums(text)        -> every enum constant of the preprocessed text
find_init(text, n) -> source of the initializer of `<type> n[] = {...}`
parse_init(src)    -> nested Python structure (dict for designated/positional)
CEval(enums).eval(expr) -> int/float/str of a C constant expression
"""
import re

# ---------------------------------------------------------------- tokenizer
TOK = re.compile(r"""
  (?P<ws>\s+)
 |(?P<str>"(?:[^"\\]|\\.)*")
 |(?P<chr>'(?:[^'\\]|\\.)*')
 |(?P<num>(?:0[xX][0-9a-fA-F]+|\d+\.\d*(?:[eE][-+]?\d+)?|\.\d+|\d+)[uUlLfF]*)
 |(?P<id>[A-Za-z_]\w*)
 |(?P<op><<=|>>=|<<|>>|<=|>=|==|!=|&&|\|\||->|\.\.\.|[-+*/%()<>!~&|^?:,.\[\]{}=;])
""", re.X)


def tokenize(s):
    pos, out = 0, []
    while pos < len(s):
        m = TOK.match(s, pos)
        if not m:
            raise ValueError("bad char %r at %d" % (s[pos:pos + 20], pos))
        pos = m.end()
        if m.lastgroup != "ws":
            out.append(m.group())
    return out


class Enums(dict):
    def __init__(self, text, ev=None):
        super().__init__()
        self.by_enum = {}   # enum tag -> [member names] in order
        ev = ev or CEval(self)
        for m in re.finditer(r"\benum\b\s*(?:__attribute__\s*\(\(\w+\)\)\s*)?(\w*)\s*(?::\s*\w+\s*)?\{([^{}]*)\}", text):
            members = self.by_enum.setdefault(m.group(1), []) if m.group(1) else []
            nxt = 0
            for entry in split_top(m.group(2)):
                entry = entry.strip()
                if not entry:
                    continue
                name, _, expr = entry.partition("=")
                name = name.strip()
                if expr.strip():
                    try:
                        v = ev.eval(expr)
                    except Exception:
                        v = None
                    nxt = v if isinstance(v, int) and not isinstance(v, Sym) else nxt
                self[name] = nxt
                members.append(name)
                nxt += 1


def split_top(s):
    depth, cur, out = 0, [], []
    for ch in s:
        if ch in "({[":
            depth += 1
        elif ch in ")}]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def find_init(text, name):
    m = re.search(r"\b%s\s*\[[^\]]*\](?:\s*\[[^\]]*\])*\s*=\s*\{" % re.escape(name), text)
    if not m:
        m = re.search(r"\b%s\s*=\s*\{" % re.escape(name), text)
    if not m:
        return None
    return find_init_at(text, m.end() - 1)


def find_init_at(text, i):
    """Brace block starting at text[i] == '{' (strings respected)."""
    depth = 0
    in_str = False
    j = i
    while j < len(text):
        c = text[j]
        if in_str:
            if c == "\\":
                j += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
        j += 1
    return None


# ---------------------------------------------------------------- initializer
class Init:
    """Parsed brace initializer: .items = [(designator or None, value)]
    value is Init or a token list (expression)."""

    def __init__(self, items):
        self.items = items

    def get(self, key, default=None):
        for k, v in self.items:
            if k == key:
                return v
        return default

    def positional(self):
        return [v for k, v in self.items]


def parse_init(src):
    toks = tokenize(src)
    pos = [0]

    def parse_brace():
        assert toks[pos[0]] == "{"
        pos[0] += 1
        items = []
        while toks[pos[0]] != "}":
            key = None
            if toks[pos[0]] == ".":
                key = toks[pos[0] + 1]
                pos[0] += 2
                while toks[pos[0]] == ".":  # .a.b = x (rare)
                    key += "." + toks[pos[0] + 1]; pos[0] += 2
                assert toks[pos[0]] == "=", toks[pos[0]:pos[0] + 5]
                pos[0] += 1
            elif toks[pos[0]] == "[":
                j = pos[0] + 1
                depth = 1
                while depth:
                    if toks[j] == "[":
                        depth += 1
                    elif toks[j] == "]":
                        depth -= 1
                    j += 1
                key = tuple(toks[pos[0] + 1:j - 1])
                pos[0] = j
                while toks[pos[0]] == "[":  # [a][b] = (gTrainers)
                    j = pos[0] + 1
                    while toks[j] != "]":
                        j += 1
                    key = key + ("][",) + tuple(toks[pos[0] + 1:j]); pos[0] = j + 1
                assert toks[pos[0]] == "=", toks[pos[0]:pos[0] + 5]
                pos[0] += 1
            items.append((key, parse_value()))
            if toks[pos[0]] == ",":
                pos[0] += 1
        pos[0] += 1
        return Init(items)

    def parse_value():
        if toks[pos[0]] == "{":
            return parse_brace()
        # ((type[]) { ... }) -> compound literal in parentheses
        if toks[pos[0]] == "(" and toks[pos[0] + 1] == "(" and toks[pos[0] + 2] in ("const", "struct"):
            pos[0] += 1
            v = parse_value()
            assert toks[pos[0]] == ")"
            pos[0] += 1
            return v
        # compound literal: (type[]) { ... }
        if toks[pos[0]] == "(" :
            j = pos[0]
            depth = 0
            while True:
                if toks[j] == "(":
                    depth += 1
                elif toks[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j + 1 < len(toks) and toks[j + 1] == "{" and toks[pos[0] + 1] in ("const", "struct", "u8", "u16", "s8", "u32", "s16", "s32"):
                pos[0] = j + 1
                return parse_brace()
        out = []
        depth = 0
        while True:
            t = toks[pos[0]]
            if depth == 0 and t in (",", "}"):
                return out
            if t in "([{":
                depth += 1
            elif t in ")]}":
                depth -= 1
            out.append(t)
            pos[0] += 1

    return parse_brace()


# ---------------------------------------------------------------- evaluator
CAST_TYPES = {"uq4_12_t", "u64", "s64", "size_t", "u8", "u16", "u32", "s8", "s16", "s32", "int", "unsigned", "bool8", "bool32", "char", "float", "double", "long"}


class CEval:
    def __init__(self, enums=None):
        self.enums = enums if enums is not None else {}

    def eval(self, expr):
        toks = tokenize(expr) if isinstance(expr, str) else list(expr)
        self.t, self.p = toks, 0
        v = self.ternary()
        return v

    # string literals ( _("..") / COMPOUND_STRING("..") / plain )
    def text(self, toks):
        parts = [t for t in toks if t.startswith('"')]
        if not parts:
            return None
        s = "".join(p[1:-1] for p in parts)
        return _unescape(s)

    def peek(self):
        return self.t[self.p] if self.p < len(self.t) else None

    def take(self, x=None):
        t = self.peek()
        if x is not None and t != x:
            raise ValueError("expected %s got %s in %s" % (x, t, " ".join(self.t)))
        self.p += 1
        return t

    def ternary(self):
        c = self.binop(0)
        if self.peek() == "?":
            self.take()
            a = self.ternary()
            self.take(":")
            b = self.ternary()
            return a if c else b
        return c

    PREC = [["||"], ["&&"], ["|"], ["^"], ["&"], ["==", "!="], ["<", ">", "<=", ">="],
            ["<<", ">>"], ["+", "-"], ["*", "/", "%"]]

    def binop(self, lvl):
        if lvl == len(self.PREC):
            return self.unary()
        a = self.binop(lvl + 1)
        while self.peek() in self.PREC[lvl]:
            op = self.take()
            b = self.binop(lvl + 1)
            a = self.apply(op, a, b)
        return a

    @staticmethod
    def apply(op, a, b):
        if op == "||": return int(bool(a) or bool(b))
        if op == "&&": return int(bool(a) and bool(b))
        if op == "|": return a | b
        if op == "^": return a ^ b
        if op == "&": return a & b
        if op == "==": return int(a == b)
        if op == "!=": return int(a != b)
        if op == "<": return int(a < b)
        if op == ">": return int(a > b)
        if op == "<=": return int(a <= b)
        if op == ">=": return int(a >= b)
        if op == "<<": return a << b
        if op == ">>": return a >> b
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/":
            if isinstance(a, float) or isinstance(b, float):
                return a / b
            q = abs(a) // abs(b)
            return q if (a >= 0) == (b >= 0) else -q
        if op == "%":
            return a - b * CEval.apply("/", a, b)
        raise ValueError(op)

    def unary(self):
        t = self.peek()
        if t == "-":
            self.take(); return -self.unary()
        if t == "+":
            self.take(); return self.unary()
        if t == "!":
            self.take(); return int(not self.unary())
        if t == "~":
            self.take(); return ~self.unary()
        if t == "(":
            # cast?
            if self.p + 1 < len(self.t) and (self.t[self.p + 1] in CAST_TYPES or self.t[self.p + 1] in ("const", "struct")):
                j = self.p + 1
                while self.t[j] != ")":
                    j += 1
                typ = [x for x in self.t[self.p + 1:j] if x not in ("const", "struct")][0]
                if "[" in self.t[self.p + 1:j] or "*" in self.t[self.p + 1:j]:
                    self.p = j + 1
                    return self.unary()
                self.p = j + 1
                v = self.unary()
                if typ in ("float", "double"):
                    return float(v)
                return int(v)
            self.take("(")
            v = self.ternary()
            self.take(")")
            return v
        return self.primary()

    def primary(self):
        t = self.take()
        if t is None:
            raise ValueError("empty")
        if t[0].isdigit() or t[0] == ".":
            s = t.rstrip("uUlLfF") if not t.lower().startswith("0x") else t.rstrip("uUlL")
            if "." in s or ("e" in s.lower() and not s.lower().startswith("0x")):
                return float(s)
            if len(s) > 1 and s[0] == "0" and s.isdigit():
                return int(s, 8)            # C octal literal (00475 = 317)
            return int(s, 0)
        if t.startswith("'"):
            return ord(_unescape(t[1:-1]))
        if t.startswith('"'):
            s = t[1:-1]
            while self.peek() and self.peek().startswith('"'):
                s += self.take()[1:-1]
            return _unescape(s)
        if t in ("_", "COMPOUND_STRING") and self.peek() == "(":
            self.take("(")
            v = self.ternary()
            self.take(")")
            return v
        if t == "sizeof":
            raise ValueError("sizeof")
        if t in self.enums:
            return self.enums[t]
        if t in ("TRUE",):
            return 1
        if t in ("FALSE", "NULL"):
            return 0
        # symbol (pointer to data): keep the name
        return Sym(t)


class Sym(str):
    pass


def _unescape(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            out.append({"n": "\n", "l": "\\l", "p": "\\p", "t": "\t", '"': '"', "\\": "\\", "0": "\0"}.get(n, "\\" + n))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)
