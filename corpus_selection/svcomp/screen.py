"""Static feasibility screen of the SV-COMP Java benchmark tasks (sv-benchmarks, directory java/) for this study's protocol.

A task is a .yml file naming its source directories and, per property, an expected verdict. For every task the sources are read and
the following mechanical criteria are applied one after the other (each stage keeps only what passed all earlier stages):

  D  domain     the task comes from a source folder holding general-purpose software or tool regression tests (domain models and security suites are excluded, see DOMAIN_EXCLUDED).
  I  inputs     every symbolic input is read with Verifier.nondetInt() (jpf-symbc's symbolic ints; no other nondet type used).
  T  tooling    no bitwise AND/OR/XOR/shift/complement operators (neither z3 nor choco integration of jpf-symbc supports them
                symbolically), no String/float/double/long/char arithmetic, no threads/IO/reflection.
  V  verdict    every expected verdict of the task is true: exhaustive exploration completes only if no property violation stops
                the search (jpf-symbc terminates at the first violation).
  U  unique     one task per distinct program source (several .yml files can share a program).

Usage: python screen.py <path to sv-benchmarks/java> [out.csv]"""
import csv
import os
import re
import sys
from collections import Counter

ROOT = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "screen.csv"

DOMAIN_EXCLUDED = {"MinePump": "pump-controller model", "rtems-lock-model": "RTOS model",
                   "securibench": "web-security suite", "juliet-java": "CWE vulnerability suite"}
NONDET = re.compile(r"Verifier\s*\.\s*nondet(\w+)\s*\(")
BITWISE = re.compile(r"(?<![&|])[&|^](?![&|=])|<<|>>|~\s*[\w(]|[&|^]=")
TOOL_BAD = [
    ("String", re.compile(r"\bString\b(?!\s*\[\]\s*args)")),
    ("float/double", re.compile(r"\b(float|double|Float|Double)\b")),
    ("long", re.compile(r"\blong\b|\bLong\b")),
    ("char", re.compile(r"\bchar\b|\bCharacter\b")),
    ("threads", re.compile(r"\bThread\b|java\.util\.concurrent|synchronized|Runnable")),
    ("io/reflection", re.compile(r"java\.io|java\.nio|System\.in|Class\.forName|java\.lang\.reflect|System\.getProperty")),
]


def strip_comments(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"//[^\n]*", "", t)


def parse_yml(path):
    txt = open(path, encoding="utf-8").read()
    files = re.findall(r"^\s*-\s+(\S+/?)\s*$", txt.split("properties:")[0], flags=re.M)
    verdicts = re.findall(r"expected_verdict:\s*(true|false)", txt)
    return [f.strip("'\"") for f in files if f.strip("'\"")], verdicts


def sources(task_dir, files):
    out = []
    for f in files:
        p = os.path.normpath(os.path.join(task_dir, f))
        if os.path.basename(p) == "common":
            continue
        if os.path.isdir(p):
            for r, _, fs in os.walk(p):
                out += [os.path.join(r, x) for x in fs if x.endswith(".java")]
        elif p.endswith(".java") and os.path.exists(p):
            out.append(p)
    return sorted(out)


rows = []
for r, _, fs in os.walk(ROOT):
    for f in fs:
        if not f.endswith(".yml"):
            continue
        path = os.path.join(r, f)
        folder = os.path.relpath(path, ROOT).replace("\\", "/").split("/")[0]
        files, verdicts = parse_yml(path)
        srcs = sources(r, files)
        code = "\n".join(strip_comments(open(s, encoding="utf-8", errors="replace").read()) for s in srcs)
        nd = Counter(NONDET.findall(code))
        bad = [n for n, rx in TOOL_BAD if rx.search(code)]
        rows.append({
            "task": os.path.relpath(path, ROOT).replace("\\", "/"), "folder": folder, "sources": ";".join(os.path.relpath(s, ROOT).replace("\\", "/") for s in srcs),
            "loc": sum(1 for l in code.splitlines() if l.strip()), "nondets": ",".join(f"{k}:{v}" for k, v in sorted(nd.items())),
            "bitwise": bool(BITWISE.search(code)), "tool_bad": ",".join(bad), "verdicts": ",".join(verdicts),
        })

funnel = []
cur = rows
funnel.append(("all Java tasks", len(cur)))
stage = {}
for r in cur:
    r["D"] = r["folder"] not in DOMAIN_EXCLUDED
cur = [r for r in cur if r["D"]]; funnel.append(("D domain: general-purpose software / tool regression tests", len(cur)))
for r in cur:
    r["I"] = bool(r["nondets"]) and set(k.split(":")[0] for k in r["nondets"].split(",")) <= {"Int"}
cur = [r for r in cur if r["I"]]; funnel.append(("I inputs: only Verifier.nondetInt()", len(cur)))
for r in cur:
    r["T"] = (not r["bitwise"]) and not r["tool_bad"]
cur = [r for r in cur if r["T"]]; funnel.append(("T tooling: no bitwise ops, String/float/double/long/char, threads, IO", len(cur)))
for r in cur:
    r["V"] = bool(r["verdicts"]) and all(v == "true" for v in r["verdicts"].split(","))
cur = [r for r in cur if r["V"]]; funnel.append(("V verdict: all expected verdicts true", len(cur)))
seen, uniq = set(), []
for r in cur:
    if r["sources"] not in seen:
        seen.add(r["sources"]); uniq.append(r)
funnel.append(("U unique program sources", len(uniq)))
keep = {r["task"] for r in uniq}
for r in rows:
    r["passed_all"] = r["task"] in keep
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["task", "folder", "sources", "loc", "nondets", "bitwise", "tool_bad", "verdicts", "D", "I", "T", "V", "passed_all"], extrasaction="ignore")
    w.writeheader()
    for r in sorted(rows, key=lambda x: x["task"]):
        w.writerow(r)
print("funnel (cumulative):")
for name, n in funnel:
    print(f"  {n:5d}  {name}")
print("\ntasks per source folder (all -> passed all stages):")
allc, pc = Counter(r["folder"] for r in rows), Counter(r["folder"] for r in uniq)
for k, v in sorted(allc.items(), key=lambda x: -x[1]):
    print(f"  {k:<26}{v:5d} -> {pc.get(k, 0):3d}")
