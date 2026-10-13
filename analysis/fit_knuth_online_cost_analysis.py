"""Live cost of Knuth probing. The macro rho of fit_knuth_probing_baseline.py simulates the probes on the fully explored tree, which is free. In a live
search every probe must be explored, so this script computes what it would cost, from the data that is already recorded.

For each non-leaf state s and each of its random descents (the same walks as in fit_knuth_probing_baseline.py), the cost is the sum of the
own step cost of every node on the path from s to the leaf. The own step cost of a node n is actualSubtreeWork(n) minus the sum of
actualSubtreeWork over the children of n. The unit is the unit of actualSubtreeWork.

Three questions:
  A. What share of the full work below s do the probes cost (median, mean, quartiles)?
  B. How do accuracy and cost change with 1, 5, 10 and 30 probes?
  C. For how many states would exploring the subtree fully have been cheaper than probing it?

Usage:
    python fit_knuth_online_cost_analysis.py"""

import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import (
    load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci,
)

PROBE_COUNTS = [1, 5, 10, 30]
SEED = 42


def own_step_cost_map(prog_df):
    """actualSubtreeWork(n) minus the sum of actualSubtreeWork over n's own
    children -- n's own standalone step cost, excluding descendants. This is
    what a live single-path descent through n (without exploring n's OTHER
    children) would actually cost at n itself."""
    by_id = {int(r["stateId"]): r for _, r in prog_df.iterrows()}
    children = defaultdict(list)
    for _, r in prog_df.iterrows():
        pid = int(r["parentId"])
        if pid != -1:
            children[pid].append(int(r["stateId"]))
    own_cost = {}
    for sid, row in by_id.items():
        child_work_sum = sum(by_id[c]["actualSubtreeWork"] for c in children.get(sid, []))
        own_cost[sid] = max(0, row["actualSubtreeWork"] - child_work_sum)
    return by_id, children, own_cost


def main():
    df = load_all()
    rng = np.random.default_rng(SEED)

    # A + B: cost as % of own actualSubtreeWork, and accuracy at each
    # probe-count checkpoint.
    all_rows = []  # per-state records: group, actual, pred@k for each k, cost@k for each k
    for program, prog_df in df.groupby("program"):
        by_id, children, own_cost = own_step_cost_map(prog_df)
        non_leaf_ids = [sid for sid, row in by_id.items() if not row["isEndStateAtEntry"]]
        group = prog_df["program_group"].iloc[0]

        for sid in non_leaf_ids:
            row = by_id[sid]
            actual = row["actualSubtreeWork"]
            estimates_at_k = {}
            cost_at_k = {}
            running_est_sum = 0.0
            running_cost_sum = 0.0
            k_index = 0
            max_k = max(PROBE_COUNTS)
            for probe_i in range(max_k):
                current = sid
                cumulative = 0.0
                running_product = 1.0
                path_cost = own_cost[sid]
                while True:
                    kids = children.get(current, [])
                    n = len(kids)
                    if n == 0:
                        break
                    running_product *= n
                    cumulative += running_product
                    current = kids[rng.integers(0, n)]
                    path_cost += own_cost[current]
                running_est_sum += cumulative
                running_cost_sum += path_cost
                k_index += 1
                if k_index in PROBE_COUNTS:
                    estimates_at_k[k_index] = running_est_sum / k_index
                    cost_at_k[k_index] = running_cost_sum

            all_rows.append({
                "program_group": group, "stateId": sid, "actual": actual,
                **{f"pred_k{k}": estimates_at_k[k] for k in PROBE_COUNTS},
                **{f"cost_k{k}": cost_at_k[k] for k in PROBE_COUNTS},
            })

    scored = pd.DataFrame(all_rows)
    print(f"Non-leaf states scored: {len(scored)} across {scored['program_group'].nunique()} groups.\n")

    # A: cost as % of own actualSubtreeWork
    print("=== A. Real cost of 30-probe Knuth estimation, as % of the state's own actualSubtreeWork ===")
    scored["cost_pct_k30"] = np.where(
        scored["actual"] > 0, 100.0 * scored["cost_k30"] / scored["actual"], np.nan)
    valid = scored["cost_pct_k30"].dropna()
    print(f"  Median: {valid.median():.1f}%   Mean: {valid.mean():.1f}%   "
          f"25th/75th percentile: {valid.quantile(0.25):.1f}% / {valid.quantile(0.75):.1f}%")
    print(f"  (i.e. gathering 30 live probes for a state typically costs this fraction of what "
          f"FULLY exploring that state's own subtree would have cost anyway)")

    # B: accuracy vs probe count (cost/accuracy curve)
    print("\n=== B. Accuracy vs. probe count (cost/accuracy tradeoff) ===")
    print(f"{'k (probes)':>12}{'Macro rho':>12}{'95% CI':>16}{'Median cost %':>16}")
    for k in PROBE_COUNTS:
        per_group_rho = {}
        for g, sub in scored.groupby("program_group"):
            if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
                continue
            pred_col = f"pred_k{k}"
            if sub["actual"].nunique() < 2 or sub[pred_col].nunique() < 2:
                continue
            r, _ = spearmanr(sub["actual"], sub[pred_col])
            if not np.isnan(r):
                per_group_rho[g] = r
        macro = macro_average(per_group_rho)
        ci = bootstrap_macro_ci(per_group_rho)
        cost_col = f"cost_k{k}"
        cost_pct = np.where(scored["actual"] > 0, 100.0 * scored[cost_col] / scored["actual"], np.nan)
        med_cost = pd.Series(cost_pct).dropna().median()
        print(f"{k:>12}{macro:>12.3f}  [{ci[0]:.3f},{ci[1]:.3f}]{med_cost:>15.1f}%")

    # C: the share of states whose 30-probe cost exceeds their own actual work (probing costs more than exploring the subtree fully).
    over_100 = (scored["cost_pct_k30"] > 100).mean() * 100
    n_pos = scored["cost_pct_k30"].notna().sum()
    over_100_pos = (scored["cost_pct_k30"].dropna() > 100).mean() * 100
    print(f"\n=== C. Sanity check: does 30-probe estimation ever cost MORE than full exploration? ===")
    print(f"  {over_100:.1f}% of scored states: 30-probe cost EXCEEDS the state's own full "
          f"actualSubtreeWork (i.e. probing would have been a worse deal than just fully exploring).")
    print(f"  {n_pos} of {len(scored)} scored states ({100.0 * n_pos / len(scored):.1f}%) have non-zero actualSubtreeWork (the cost ratio is undefined "
          f"for the rest, and the median above is over these); among them {over_100_pos:.1f}% exceed.")

    # D: work-weighted view: total probe cost against total own work,
    # over the states with non-zero work, and per group
    pos = scored[scored["actual"] > 0]
    print("\n=== D. Work-weighted ratio (30 probes), states with non-zero actualSubtreeWork ===")
    print(f"  All such states pooled: sum of probe cost / sum of own work = {pos['cost_k30'].sum() / pos['actual'].sum():.2f}x")
    per_group = pos.groupby("program_group").apply(lambda d: d["cost_k30"].sum() / d["actual"].sum())
    print(f"  Per group: median {per_group.median():.2f}x, 25th/75th percentile {per_group.quantile(0.25):.2f}x / {per_group.quantile(0.75):.2f}x, "
          f"min {per_group.min():.2f}x, max {per_group.max():.2f}x ({len(per_group)} groups)")
    print(f"  Groups where total probe cost exceeds total own work: {(per_group > 1).sum()} of {len(per_group)}")
    zero = scored[scored["actual"] <= 0]
    print(f"  Non-leaf states with zero own work: {len(zero)} of {len(scored)} ({100.0 * len(zero) / len(scored):.1f}%)")

    # E: accuracy without the zero-work childless states (post hoc)
    print("\n=== E. Knuth accuracy with the zero-work childless states left out of the scoring (P55 groups) ===")
    print(f"{'k (probes)':>12}{'All rows':>12}{'Without zero-work':>20}{'groups':>9}")
    for k in PROBE_COUNTS:
        res = {}
        for label, d in (("all", scored), ("nz", pos)):
            pg = {}
            for g, sub in d.groupby("program_group"):
                if len(sub) >= MIN_ROWS_FOR_GROUP_RHO and sub["actual"].nunique() > 1 and sub[f"pred_k{k}"].nunique() > 1:
                    r, _ = spearmanr(sub["actual"], sub[f"pred_k{k}"])
                    if not np.isnan(r):
                        pg[g] = r
            res[label] = (macro_average(pg), len(pg))
        print(f"{k:>12}{res['all'][0]:>12.3f}{res['nz'][0]:>20.3f}{res['nz'][1]:>9}")

    # F: probing cost against the size of the state's own subtree work (post hoc)
    print("\n=== F. 30-probe cost as a multiple of the state's own subtree work, by size of that work (states with non-zero work) ===")
    bins = [0, 100, 1000, 10000, 100000, np.inf]
    labels = ["<=100", "101-1000", "1001-10000", "10001-100000", ">100000"]
    pos = pos.assign(size_bin=pd.cut(pos["actual"], bins=bins, labels=labels))
    print(f"{'own work (bytecodes)':>22}{'states':>8}{'median x':>10}{'share >1x':>11}{'sum cost / sum work':>22}")
    for lab in labels:
        d = pos[pos["size_bin"] == lab]
        if len(d):
            ratio = d["cost_k30"] / d["actual"]
            print(f"{lab:>22}{len(d):>8}{ratio.median():>10.2f}{100 * (ratio > 1).mean():>10.1f}%{d['cost_k30'].sum() / d['actual'].sum():>22.2f}")



if __name__ == "__main__":
    main()
