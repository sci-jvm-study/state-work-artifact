"""Outcome of every COASTAL attempt of the depth-first runs (runs/ and runs2/, <Program>): a program completed if it wrote coastal_runs.csv,
otherwise the first failure line of its log is reported. Backs the paper's counts of z3 configurations attempted, crashed on COASTAL
limitations and completed, and how the completed ones split into trees with JPF's node count, single-path trees and trees of another size
(run_status_data_coastal2.csv).

Usage: python audit_coastal_attempts.py"""
import os
import re
from collections import Counter

import pandas as pd

ENG = os.path.dirname(os.path.abspath(__file__))
runs = os.path.join(ENG, "runs")
runs2 = os.path.join(ENG, "runs2")
progs = sorted({p for r in (runs, runs2) for p in os.listdir(r) if os.path.isdir(os.path.join(r, p))})
failed = Counter()
n_ok = 0
for p in progs:
    src = [r for r in (runs, runs2) if os.path.isdir(os.path.join(r, p))]
    if any(os.path.exists(os.path.join(r, p, "coastal_runs.csv")) for r in src):
        n_ok += 1
        continue
    log = open(os.path.join(src[0], p, "out.txt"), encoding="utf-8", errors="replace").read()
    m = re.search(r"UNIMPLEMENTED INSTRUCTION: <\d+> (\w+)", log) or re.search(r"(java\.lang\.\w+(?:Error|Exception))", log)
    reason = ("unimplemented instruction " + m.group(1)) if m and m.group(0).startswith("UNIMPL") else (m.group(1) if m else "no failure line")
    failed[reason] += 1
    print(f"failed: {p:<30} {reason}")
print(f"\nattempted {len(progs)}, completed {n_ok}, failed {sum(failed.values())}: {dict(failed)}")
st = pd.read_csv(os.path.join(ENG, "run_status_data_coastal2.csv"))
exact = st[st.nodes == st.jpf_states]
other = st[st.nodes != st.jpf_states]
print(f"completed programs: {len(st)}; tree with exactly JPF's node count: {len(exact)}; single-path tree: {(other.nodes == 1).sum()}; "
      f"other size: {(other.nodes != 1).sum()}")
