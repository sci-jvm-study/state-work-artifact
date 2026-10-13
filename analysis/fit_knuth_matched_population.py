"""Knuth probing on the population of Group C.

The probe-count table of fit_knuth_online_cost_analysis.py scores Knuth probing on its own scoreable population, while Group C is scored on
the largest set that every baseline, Group C included, can score (the Group-C-eligible groups). A comparison of the two needs one population.
This script recomputes the Knuth probe-count accuracy and cost curve restricted to the Group-C-eligible groups. It reuses the probe simulation
and the seed of fit_knuth_online_cost_analysis.py, so only the groups that enter the macro average change.

Usage:
    python fit_knuth_matched_population.py"""

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
from fit_knuth_online_cost_analysis import own_step_cost_map, PROBE_COUNTS, SEED  
from fit_hybrid_model import attach_group_c_predictions, eligible_groups  

def simulate_probes(df, rng):
    """Replicates fit_knuth_online_cost_analysis.py's probe simulation exactly
    (same code path, same seed), returning the per-state scored frame."""
    all_rows = []
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
            max_k = max(PROBE_COUNTS)
            for probe_i in range(max_k):
                current = sid
                cumulative = 0.0
                branch_product = 1.0
                path_cost = 0.0
                while True:
                    kids = children.get(current, [])
                    path_cost += own_cost[current]
                    if not kids:
                        break
                    branch_product *= len(kids)
                    cumulative += branch_product
                    current = kids[rng.integers(0, len(kids))]
                running_est_sum += cumulative
                running_cost_sum += path_cost
                k_done = probe_i + 1
                if k_done in PROBE_COUNTS:
                    estimates_at_k[k_done] = running_est_sum / k_done
                    cost_at_k[k_done] = running_cost_sum
            all_rows.append({
                "program_group": group,
                "actual": actual,
                **{f"pred_k{k}": estimates_at_k[k] for k in PROBE_COUNTS},
                **{f"cost_k{k}": cost_at_k[k] for k in PROBE_COUNTS},
            })
    return pd.DataFrame(all_rows)


def probe_curve(scored, restrict_to=None, label=""):
    print(f"\n=== Knuth accuracy and cost by probe count{label} ===")
    print(f"{'k (probes)':>12}{'Macro rho':>12}{'95% CI':>16}{'groups':>9}{'Median cost %':>16}")
    sub_all = scored if restrict_to is None else scored[scored["program_group"].isin(restrict_to)]
    for k in PROBE_COUNTS:
        per_group_rho = {}
        for g, sub in scored.groupby("program_group"):
            if restrict_to is not None and g not in restrict_to:
                continue
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
        # Cost is computed on the SAME restricted state population, so the
        # accuracy and cost columns of a given row always describe one population.
        cost_pct = np.where(sub_all["actual"] > 0,
                            100.0 * sub_all[f"cost_k{k}"] / sub_all["actual"], np.nan)
        med_cost = pd.Series(cost_pct).dropna().median()
        print(f"{k:>12}{macro:>12.3f}  [{ci[0]:.3f},{ci[1]:.3f}]{len(per_group_rho):>9}{med_cost:>15.1f}%")


def main():
    df = load_all()
    rng = np.random.default_rng(SEED)
    scored = simulate_probes(df, rng)

    # The Group-C-eligible population, computed exactly the way
    # fit_all_baselines_fair_comparison.py computes it.
    non_leaf = df[df["isEndStateAtEntry"] == False].copy()
    non_leaf["logWork"] = np.log1p(non_leaf["actualSubtreeWork"])
    non_leaf, _ = attach_group_c_predictions(non_leaf)
    scored_gc = non_leaf.dropna(subset=["groupC_pred"]).copy()
    elig = eligible_groups(scored_gc)
    print(f"Group-C-eligible population: {len(elig)} groups")

    probe_curve(scored, restrict_to=None,
                label=" -- Knuth's OWN full scoreable population")
    probe_curve(scored, restrict_to=set(elig),
                label=" -- RESTRICTED to the Group-C-eligible population")

    # post hoc: the same curve with the zero-work childless states left out of the scoring
    # (a non-end state has a recorded child exactly when its subtree work is non-zero, results/61)
    nz = scored[scored["actual"] > 0]
    probe_curve(nz, restrict_to=set(elig),
                label=" -- RESTRICTED to the Group-C-eligible population, zero-work states left out of the scoring")

    print("\n[Note] Group C's macro rho is on the Group-C-eligible population, so a Knuth probe count is compared "
          "with it on the restricted row above and not on the larger population of Knuth probing.")


if __name__ == "__main__":
    main()
