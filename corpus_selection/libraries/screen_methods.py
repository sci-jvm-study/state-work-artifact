"""Method-level feasibility screen of open-source Java libraries for this study's protocol. A static method is a candidate if it can
be run symbolically by jpf-symbc's z3/choco integrations as a self-contained unit and has non-trivial control flow:

  P  parameters  only int and int[] (an int[] is filled from symbolic ints by the driver), at most MAX_SYMS symbolic ints in total
  R  return      int, boolean, void or int[]
  T  tooling     no bitwise AND/OR/XOR/shift/complement, no float/double/long/char/String/generics/lambdas/instanceof/synchronized
  C  calls       every call is to a JDK method on the allow-list (Math.abs/min/max/signum, Integer.compare/signum) or to another
                 static method of the same file that passes P, R, T and C itself (a closure the driver copies along)
  K  constants   every ALL_CAPS identifier is a `static final int` of the same file with a literal value (or a JDK constant on the allow-list)
  B  branching   at least MIN_LOC code lines and at least one loop or conditional
  L  license     the library's own license (checked once per library: Apache-2.0 for all three used here)

Exceptions thrown by the method are allowed; the driver catches RuntimeException so the path ends normally.
Writes candidates.csv (one row per static method with the first failing stage) and prints the funnel.

Usage: python screen_methods.py <src dir> <library name> [out.csv]"""
import csv
import os
import re
import sys
from collections import Counter

SRC, LIB = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else "candidates_%s.csv" % LIB
MAX_SYMS, MIN_LOC = 6, 5
ALLOW_CALLS = {"Math.abs", "Math.min", "Math.max", "Math.signum", "Integer.compare", "Integer.signum"}
ALLOW_CONST = {"Integer.MAX_VALUE", "Integer.MIN_VALUE", "INDEX_NOT_FOUND"}
KEYWORDS = {"if", "for", "while", "switch", "return", "catch", "synchronized", "assert", "throw", "new", "do", "else", "try", "case", "int", "boolean", "this", "super"}
BITWISE = re.compile(r"(?<![&|])[&|^](?![&|=])|<<|>>|~\s*[\w(]|[&|^]=")
BAD_TYPES = re.compile(r"\b(float|double|long|char|byte|short|String|Object|Integer\s*\.\s*(?:parseInt|valueOf|toString)|Long|Double|Float|Character|StringBuilder)\b|<[A-Za-z]|->|instanceof|synchronized|\.length\(\)|\.get\(|\.size\(\)")
SIG = re.compile(r"(?:(?:public|protected|private)\s+)?static\s+(?:final\s+)?([\w\[\]<>?,\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w.,\s]+)?\{")


def strip(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"//[^\n]*", "", t)
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', t)


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


def parse_params(p):
    out = []
    for x in [q.strip() for q in p.split(",") if q.strip()]:
        x = re.sub(r"\bfinal\s+", "", x)
        m = re.match(r"(int\s*\[\]|int)\s+(\w+)$", x)
        if not m:
            return None
        out.append((m.group(1).replace(" ", ""), m.group(2)))
    return out


methods = []  # (file, name, ret, params or None, body, raw_params)
consts = {}
for r, _, fs in os.walk(SRC):
    for f in fs:
        if not f.endswith(".java"):
            continue
        path = os.path.join(r, f)
        code = strip(open(path, encoding="utf-8", errors="replace").read())
        consts[path] = set(re.findall(r"static\s+final\s+int\s+([A-Z_][A-Z0-9_]*)\s*=\s*-?\d+\s*;", code))
        for m in SIG.finditer(code):
            e = match_brace(code, m.end() - 1)
            if e < 0:
                continue
            methods.append((path, m.group(2), m.group(1).strip(), parse_params(m.group(3)), code[m.end():e], m.group(3)))

by_file = {}
for mth in methods:
    by_file.setdefault(mth[0], {}).setdefault(mth[1], []).append(mth)


def stages(path, name, ret, params, body, seen=(), top=False):
    """first failing stage letter or '' (passes)"""
    if params is None or sum(1 for p in params if p[0] == "int[]") > 1 or len(params) == 0:
        return "P"
    if sum(1 for p in params if p[0] == "int") + 4 * sum(1 for p in params if p[0] == "int[]") > MAX_SYMS:
        return "P"
    if ret not in ("int", "boolean", "void", "int[]"):
        return "R"
    if BITWISE.search(body) or BAD_TYPES.search(body):
        return "T"
    calls = set(re.findall(r"\b([A-Za-z_][\w]*(?:\s*\.\s*[A-Za-z_]\w*)*)\s*\(", body)) - KEYWORDS
    for c in calls:
        c = re.sub(r"\s+", "", c)
        if c in ALLOW_CALLS:
            continue
        cand = by_file[path].get(c)
        if not cand or (name, ) == (c, ) or c in seen:
            if c == name:
                continue  # direct recursion is fine
            return "C"
        if all(stages(path, c, x[2], x[3], x[4], seen + (name,), False) for x in cand):
            return "C"
    for c in set(re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", body)):
        if c not in consts[path] and c not in ALLOW_CONST:
            return "K"
    loc = sum(1 for l in body.splitlines() if l.strip())
    if top and (loc < MIN_LOC or not re.search(r"\b(if|for|while|switch)\b|\?", body)):
        return "B"
    return ""


rows = []
for path, name, ret, params, body, raw in methods:
    if name in ("main",):
        continue
    st = stages(path, name, ret, params, body, (), True)
    rows.append({"library": LIB, "file": os.path.relpath(path, SRC).replace("\\", "/"), "method": name, "signature": re.sub(r"\s+", " ", raw),
                 "returns": ret, "loc": sum(1 for l in body.splitlines() if l.strip()), "failed_stage": st or "-"})
order = "PRTCKB"
cnt = Counter(r["failed_stage"] for r in rows)
alive = len(rows)
print(f"{LIB}: {len(rows)} static methods")
for s in order:
    alive -= cnt.get(s, 0)
    print(f"  after {s}: {alive}")
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("candidates:", cnt.get("-", 0))
