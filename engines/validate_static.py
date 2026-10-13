"""Validates the COASTAL static-feature port against jpf-symbc's own logged static features, WITHOUT assuming the two
engines number or order states identically (they do not: for equal node counts the trees can still differ in sibling
order, so an id-by-id comparison would mix up leaves and internal states).

For each program whose COASTAL tree has JPF's node count, compare the MULTISET of six-feature vectors
(remainingBytecodesInMethod, reachableBranchCount, reachableLoopBackEdgeCount, reachableVirtualCallCount,
reachableAllocSiteCount, reachableAthrowCount) over non-leaf states: JPF's logged values against the port evaluated at
COASTAL's program counters. Variants: which PC represents a state, and whether conditional back-jumps count as back-edges.

Usage: python validate_static.py [tree_dir_name]   (default data_coastal2)"""
import os
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from static_features import ProgramStatics

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TREES = sys.argv[1] if len(sys.argv) > 1 else "data_coastal2"
FE = ["remainingBytecodesInMethod", "reachableBranchCount", "reachableLoopBackEdgeCount",
      "reachableVirtualCallCount", "reachableAllocSiteCount", "reachableAthrowCount"]

results = {}
n_prog = 0
for cat in ["synthetic", "real-world", "sv-comp"]:
    d = os.path.join(ROOT, "engines", "data", TREES, cat)
    for f in sorted(os.listdir(d)):
        prog = f[:-4]
        coa = pd.read_csv(os.path.join(d, f))
        jpf = pd.read_csv(os.path.join(ROOT, "data", cat, f))
        if len(coa) != len(jpf):
            continue
        n_prog += 1
        ps = ProgramStatics(os.path.join(ROOT, "engines", "runs", prog, "bin"), prog)
        a = Counter(tuple(int(x) for x in r) for r in jpf[jpf["isEndStateAtEntry"] == False][FE].values)
        for pc_col in ("pcInstrChain", "pcInstrNext"):
            for back_if in (False, True):
                b = Counter(ps.features(int(getattr(r, pc_col)), back_if=back_if)
                            for r in coa.itertuples() if not r.isEndStateAtEntry)
                key = (pc_col, back_if)
                res = results.setdefault(key, {"programs": 0, "identical": 0, "states": 0, "matched": 0})
                res["programs"] += 1
                res["identical"] += int(a == b)
                res["states"] += sum(a.values())
                res["matched"] += sum((a & b).values())

print(f"{n_prog} programs whose COASTAL tree has JPF's node count\n")
for (pc, bi), r in results.items():
    print(f"pc={pc:<13} back_if={str(bi):<5} identical multisets: {r['identical']}/{r['programs']} programs; "
          f"non-leaf states matched {r['matched']}/{r['states']} = {r['matched'] / r['states']:.4f}")
