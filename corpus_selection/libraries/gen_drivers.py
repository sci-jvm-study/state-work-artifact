"""Generates one driver program per screened candidate method (screen_methods.py, failed_stage '-'), in this study's convention:

  * the method, the same-file static helper methods it calls (transitively) and the `static final int` constants it uses are copied
    verbatim (comments removed) into a class of its own; nothing else is changed
  * `public static void classify(int ...)` is the symbolic entry point: every int parameter of the method becomes a symbolic int, an
    int[] parameter becomes an array of ARRLEN symbolic ints; the call is wrapped in try/catch RuntimeException so that a thrown
    exception ends the path normally instead of stopping the search
  * the original license and provenance go into the file header

Usage: python gen_drivers.py <candidates.csv> <src dir> <library name> <license header file> <out dir> [exclude.txt]"""
import csv
import os
import re
import sys

CSV, SRC, LIB, LIC, OUT = sys.argv[1:6]
EXCL = set(open(sys.argv[6]).read().split()) if len(sys.argv) > 6 else set()
ARRLEN = 4
os.makedirs(OUT, exist_ok=True)
SIG = re.compile(r"(?:(?:public|protected|private)\s+)?static\s+(?:final\s+)?([\w\[\]<>?,\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w.,\s]+)?\{")
KEYWORDS = {"if", "for", "while", "switch", "return", "catch", "synchronized", "assert", "throw", "new", "do", "else", "try", "case", "int", "boolean", "this", "super"}


def strip_comments(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"(?<!:)//[^\n]*", "", t)


def match_brace(s, i):
    d = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0:
                return j
    return -1


def methods_of(code):
    out = {}
    for m in SIG.finditer(code):
        e = match_brace(code, m.end() - 1)
        if e < 0:
            continue
        out.setdefault(m.group(2), []).append((m.group(1).strip(), m.group(3), code[m.start():e + 1], code[m.end():e]))
    return out


lic = open(LIC, encoding="utf-8").read().rstrip()
made = []
for r in csv.DictReader(open(CSV, encoding="utf-8")):
    if r["failed_stage"] != "-":
        continue
    path = os.path.join(SRC, r["file"])
    code = strip_comments(open(path, encoding="utf-8", errors="replace").read())
    ms = methods_of(code)
    sig_norm = lambda s: re.sub(r"\s+", " ", s).strip()
    top = [x for x in ms.get(r["method"], []) if sig_norm(x[1]) == r["signature"]]
    if not top:
        continue
    ret, raw, text, body = top[0]
    cls_short = os.path.basename(path)[:-5]
    name = "Ta" + cls_short + (r["method"][0].upper() + r["method"][1:] if sum(1 for x in ms if x == r["method"]) >= 1 else "")
    if name in EXCL or cls_short + "." + r["method"] in EXCL:
        continue
    # closure of helpers and constants
    helpers, seen, todo = [], {r["method"]}, [body]
    while todo:
        b = todo.pop()
        for c in set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", b)) - KEYWORDS:
            if c in seen or c not in ms:
                continue
            seen.add(c)
            for x in ms[c]:
                helpers.append(x[2])
                todo.append(x[3])
    alltext = "\n".join([text] + helpers)
    consts = []
    for c in sorted(set(re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", alltext))):
        m = re.search(r"static\s+final\s+int\s+" + c + r"\s*=\s*(-?\d+)\s*;", code)
        if m:
            consts.append(f"    static final int {c} = {m.group(1)};")
    params = []
    args, syms = [], []
    for ptype, pname in [re.match(r"\s*(?:final\s+)?(int\s*\[\]|int)\s+(\w+)", p).groups() for p in raw.split(",") if p.strip()]:
        if ptype.replace(" ", "") == "int":
            syms.append(pname)
            args.append(pname)
        else:
            elems = [f"{pname}{i}" for i in range(ARRLEN)]
            syms += elems
            params.append(f"        int[] {pname}Arr = {{{', '.join(elems)}}};")
            args.append(pname + "Arr")
    header = (f"// Derived from {LIB}: {r['file']}, method {r['method']}({r['signature']}).\n"
              f"{lic}\n"
              f"// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments\n"
              f"// removed) into this class; classify() is the symbolic entry point (int arrays are built from {ARRLEN} symbolic ints and the call\n"
              f"// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.\n")
    src = (header + f"public class {name} {{\n" + ("\n".join(consts) + "\n" if consts else "") +
           "    " + text.replace("\n", "\n    ") + "\n" +
           "".join("    " + h.replace("\n", "\n    ") + "\n" for h in helpers) +
           f"    public static void classify({', '.join('int ' + s for s in syms)}) {{\n" + "\n".join(params) + ("\n" if params else "") +
           f"        try {{\n            {r['method']}({', '.join(args)});\n        }} catch (RuntimeException e) {{\n        }}\n    }}\n" +
           f"    public static void main(String[] args) {{ classify({', '.join(['0'] * len(syms))}); }}\n}}\n")
    open(os.path.join(OUT, name + ".java"), "w", encoding="utf-8", newline="\n").write(src)
    made.append((name, r["file"], r["method"], len(syms)))
for m in made:
    print(*m)
print(len(made), "drivers written to", OUT)
