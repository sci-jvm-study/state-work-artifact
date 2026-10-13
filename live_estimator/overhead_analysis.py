"""H2 of live_estimator_stage1_predeclared.md, computed from results/timing_raw.csv and results/cap_microbench.txt.

Usage: python overhead_analysis.py"""
import os
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(HERE, "..", "heldout", "data")
sys.path.insert(0, os.path.join(HERE, "..", "analysis"))

raw = pd.read_csv(os.path.join(HERE, "results", "timing_raw.csv"))
cap_ns = float(np.mean([float(l.split("=")[1]) for l in open(os.path.join(HERE, "results", "cap_microbench.txt")) if "=" in l]))

med = raw.groupby(["program", "condition"])[["searchNs", "featNs", "predCapNs", "nonleaf", "states"]].median().reset_index()
piv = med.pivot(index="program", columns="condition", values="searchNs") / 1e6  # ms
rows = []
for prog, g in raw.groupby("program"):
    m = med[med.program == prog].set_index("condition")
    nl = m.loc["rfcap-timed", "nonleaf"]
    rows.append({
        "program": prog.replace("Ho", "", 1), "states": int(m.loc["none", "states"]), "nonleaf": int(nl),
        "S0_ms": piv.loc[prog, "none"], "features_ms": piv.loc[prog, "features"], "rf_ms": piv.loc[prog, "rf"],
        "rfcap_ms": piv.loc[prog, "rfcap"],
        "feat_us_per_state": m.loc["rfcap-timed", "featNs"] / nl / 1e3,
        "predcap_us_per_state": m.loc["rfcap-timed", "predCapNs"] / nl / 1e3,
        "predcap_ms": m.loc["rfcap-timed", "predCapNs"] / 1e6,
        "predcap_share_pct": 100 * m.loc["rfcap-timed", "predCapNs"] / m.loc["none", "searchNs"],
        "feat_share_pct": 100 * m.loc["rfcap-timed", "featNs"] / m.loc["none", "searchNs"],
    })
R = pd.DataFrame(rows)
pd.set_option("display.width", 250, "display.max_columns", 30)
print(R.round(3).to_string(index=False))

S0 = R["S0_ms"].sum()
E = R["predcap_ms"].sum()
nl_total = R["nonleaf"].sum()
pred_ns_per_state = E * 1e6 / nl_total
h2a = E / S0
h2b = cap_ns / pred_ns_per_state
print(f"\nsum of S0 over programs: {S0:.1f} ms; sum of median prediction+capping time: {E:.2f} ms")
print(f"H2(a) prediction+capping share of search time: {100 * h2a:.2f}%  (bar: <= 5%) -> {'holds' if h2a <= 0.05 else 'FAILS'}")
print(f"prediction+capping per non-leaf state: {pred_ns_per_state / 1e3:.2f} us; capping alone (microbenchmark): {cap_ns:.2f} ns")
print(f"H2(b) capping / prediction per state: {100 * h2b:.3f}%  (bar: <= 1%) -> {'holds' if h2b <= 0.01 else 'FAILS'}")
print(f"feature extraction share of search time (no bar): {100 * R['feat_ms'].sum() / S0 if 'feat_ms' in R else 100 * (R['feat_us_per_state'] * R['nonleaf'] / 1e3).sum() / S0:.2f}%")

print("\nDescriptive: end-to-end search time relative to condition none (median over 15 runs per program; noise-limited)")
for c in ("features", "rf", "rfcap"):
    rel = 100 * (R[f"{c}_ms" if c != "features" else "features_ms"] / R["S0_ms"] - 1)
    print(f"  {c:9s} per program % : {', '.join(f'{v:+.1f}' for v in rel)};  sum-weighted {100 * (R[c + '_ms' if c != 'features' else 'features_ms'].sum() / S0 - 1):+.2f}%")

# spread of search time within a condition, to show how much of the end-to-end difference is noise
cv = raw[raw.condition == "none"].groupby("program")["searchNs"].agg(lambda s: (s.quantile(0.75) - s.quantile(0.25)) / s.median())
print(f"\nIQR/median of S0 across the 15 runs, per program: {', '.join(f'{100 * v:.1f}%' for v in cv)}")

# counterfactual probing cost on the same programs: 30 random descents from every non-leaf state, in instructions
from fit_knuth_online_cost_analysis import own_step_cost_map
rng = np.random.default_rng(42)
print("\nCounterfactual 30-probe Knuth cost over the same programs (instructions): total over non-leaf states / whole-search work")
tot_probe, tot_search = 0.0, 0.0
for prog in sorted(raw.program.unique()):
    d = pd.read_csv(os.path.join(ARCHIVE, prog + ".csv")).sort_values("stateId").reset_index(drop=True)
    by_id, children, own_cost = own_step_cost_map(d)
    root_work = float(d["actualSubtreeWork"].iloc[0])
    cost = 0.0
    for sid, row in by_id.items():
        if row["isEndStateAtEntry"]:
            continue
        for _ in range(30):
            cur, c = sid, own_cost[sid]
            while children.get(cur):
                kids = children[cur]
                cur = kids[rng.integers(0, len(kids))]
                c += own_cost[cur]
            cost += c
    tot_probe += cost
    tot_search += root_work
    print(f"  {prog.replace('Ho', '', 1):52s} {cost / root_work:7.1f}x")
print(f"  all nine programs: {tot_probe / tot_search:.1f}x the search's own work, against {100 * h2a:.2f}% (wall-clock) for prediction+capping")

print("\nMachine:", platform.platform(), "|", platform.processor())
try:
    print(subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                         capture_output=True, text=True, timeout=30).stdout.strip())
except Exception as e:
    print("cpu name unavailable:", e)
R.to_csv(os.path.join(HERE, "results", "h2_overhead_per_program.csv"), index=False)
