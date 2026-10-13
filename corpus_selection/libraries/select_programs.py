"""Selects, from the JPF runs of the generated drivers (run_candidates.py -> tries.csv, kept/), the programs added to the corpus:
  1. scoreable: the kept run has at least 5 non-leaf states (the paper's scoreability floor);
  2. one program per source class: among the methods of one class that pass, the one with the most non-leaf states;
  3. no near-duplicates: a program whose code (comments and whitespace removed, class renamed) has similarity >= 0.85 with a program
     already in the corpus, or with an already selected one of larger tree, is dropped.
Prints the decision for every driver and writes selected.csv. A program whose recorded tree is isomorphic (ignoring sibling order) to the tree of a
selected program is dropped as well; those decisions are recorded in selection_thealgorithms.txt.

Usage: python select_programs.py <generated dir> <corpus benchmarks dir> [<corpus benchmarks dir> ...]"""
import csv
import difflib
import os
import re
import sys

import pandas as pd

G = sys.argv[1]
CORP = sys.argv[2:]
t = pd.read_csv(os.path.join(G, "tries.csv"))
best = t[t.outcome == "ok"].sort_values(["program", "k"]).groupby("program").tail(1).set_index("program")


def code(path):
    s = open(path, encoding="utf-8", errors="replace").read()
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"//[^\n]*", "", s)
    s = re.sub(r"\bpublic\s+class\s+\w+", "class X", s)
    s = re.sub(r"\bclass\s+\w+", "class X", s)
    return re.sub(r"\s+", " ", s)


def src_class(p):
    return re.search(r"Derived from [^:]+: (\S+), method", open(os.path.join(G, p + ".java"), encoding="utf-8").read()).group(1)


corpus = {}
for d in CORP:
    for f in os.listdir(d):
        if f.endswith(".java"):
            corpus[f] = code(os.path.join(d, f))
rows = []
cand = []
for p in sorted(os.listdir(G)):
    if not p.endswith(".java"):
        continue
    n = p[:-5]
    if n not in best.index:
        rows.append((n, "-", "no kept run (" + ",".join(sorted(set(t[t.program == n].outcome))) + ")"))
        continue
    b = best.loc[n]
    if b.nonleaf < 5:
        rows.append((n, b.nonleaf, "below floor (%d non-leaf states)" % b.nonleaf))
        continue
    cand.append((n, int(b.k), int(b.states), int(b.nonleaf), src_class(n)))
bycls = {}
for c in sorted(cand, key=lambda x: -x[3]):
    bycls.setdefault(c[4], []).append(c)
sel = []
for cls, lst in bycls.items():
    for extra in lst[1:]:
        rows.append((extra[0], extra[3], "same source class as " + lst[0][0]))
    sel.append(lst[0])
final = []
for c in sorted(sel, key=lambda x: -x[3]):
    cc = code(os.path.join(G, c[0] + ".java"))
    dup = None
    for f, x in corpus.items():
        if difflib.SequenceMatcher(None, cc, x, autojunk=False).ratio() >= 0.85:
            dup = "corpus " + f
    for o in final:
        if difflib.SequenceMatcher(None, cc, code(os.path.join(G, o[0] + ".java")), autojunk=False).ratio() >= 0.85:
            dup = "selected " + o[0]
    if dup:
        rows.append((c[0], c[3], "near-duplicate of " + dup))
    else:
        final.append(c)
        rows.append((c[0], c[3], "SELECTED k=%d states=%d" % (c[1], c[2])))
for r in sorted(rows, key=lambda x: str(x[2])):
    print(f"{r[0]:<66}{r[2]}")
print(len(final), "selected")
with open(os.path.join(G, "selected.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["program", "k", "states", "nonleaf", "source"])
    w.writerows(final)
