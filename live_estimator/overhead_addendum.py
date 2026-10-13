"""Derived quantities behind the overhead paragraph of Section 5.6 (no new runs): fixed part of the search time, per-program shares, the cost of one prediction in the
live runs and in the isolated loop, and the extrapolation to longer searches. Reads results/timing_raw.csv, results/h2_overhead_per_program.csv and
results/forest_bench.txt. Prints to stdout; redirect to results/h2_overhead_addendum.txt.
Usage: python overhead_addendum.py > results/h2_overhead_addendum.txt"""
import os
import re

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
raw = pd.read_csv(os.path.join(R, "timing_raw.csv"))
per = pd.read_csv(os.path.join(R, "h2_overhead_per_program.csv"))
med0 = raw[raw.condition == "none"].groupby("program")[["searchNs", "states", "nonleaf"]].median()
x = med0["states"].values
y = med0["searchNs"].values / 1e6
res = stats.linregress(x, y)
tcrit = stats.t.ppf(0.975, len(x) - 2)
print(f"1. Fixed part of the search time. Least squares over the nine programs, median search time in condition `none` against number of states:")
print(f"   S0 (ms) = {res.intercept:.0f} + {res.slope:.3f} * states   (R^2 = {res.rvalue ** 2:.3f}, slope standard error {res.stderr:.4f}, "
      f"95% interval {res.slope - tcrit * res.stderr:.3f} to {res.slope + tcrit * res.stderr:.3f} ms/state)")
print()
print("2. Per-program share of search time (percent of S0), prediction+capping / features / sum:")
per["sum_share"] = per["predcap_share_pct"] + per["feat_share_pct"]
print("   " + "; ".join(f"{r.program} {r.predcap_share_pct:.2f} / {r.feat_share_pct:.2f} / {r.sum_share:.2f}" for r in per.itertuples()))
tot_pred = per["predcap_ms"].sum()
tot_s0 = per["S0_ms"].sum()
print(f"   Predeclared H2(a) is on the sum over programs ({100 * tot_pred / tot_s0:.2f}% against a bar of 5%).")
print(f"   Sum of prediction+capping and features: {per.sum_share.sum() and 100 * (tot_pred + (per['feat_share_pct'] * per['S0_ms'] / 100).sum()) / tot_s0:.1f}% "
      f"({per.sum_share.min():.1f}% to {per.sum_share.max():.1f}% for single programs).")
print()
bench = open(os.path.join(R, "forest_bench.txt")).read()
us = [float(v) for v in re.findall(r"rep \d+: ([\d.]+) us", bench)]
print(f"3. Prediction cost per state: {per.predcap_us_per_state.min():.0f} us (largest program) to {per.predcap_us_per_state.max():.0f} us (smallest) inside the short JPF runs; "
      f"about {np.median(us):.0f} us per prediction in an isolated loop over 2378 real feature rows after JIT warm-up (ForestBench, reps {min(us):.1f} to {max(us):.1f} us).")
print()
print("Extrapolation (not a measurement of longer searches):")
big = per.loc[per.program == "NumSortingSort"].iloc[0]
frac = big.nonleaf / big.states
for label, slope in (("slope " + f"{res.slope:.3f}", res.slope), ("lower end " + f"{res.slope - tcrit * res.stderr:.3f}", res.slope - tcrit * res.stderr),
                     ("upper end " + f"{res.slope + tcrit * res.stderr:.3f}", res.slope + tcrit * res.stderr)):
    as_measured = big.predcap_us_per_state * frac / (slope * 1000) * 100
    warm = np.median(us) * frac / (slope * 1000) * 100
    feats = big.feat_us_per_state * frac / (slope * 1000) * 100
    print(f"  {label} ms/state: prediction+capping as measured {as_measured:.1f}% | at {np.median(us):.1f} us (warm loop) {warm:.1f}% | features as measured {feats:.1f}%")
