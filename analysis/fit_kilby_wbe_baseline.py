"""Weighted Backtrack Estimator (WBE) of Kilby, Slaney, Thiebaux and Walsh, "Estimating Search Tree Size", AAAI 2006, adapted to score one state.

During chronological backtracking, WBE estimates the number of nodes N as

    N = [sum over d in D of prob(d) * (2^(d+1) - 1)] / [sum over d in D of prob(d)],   prob(d) = 2^-d

where D is the multiset of the lengths of the branches visited so far. Like JPF's StateCountEstimator it is a live estimate for the whole tree.

Adaptation: for a non-leaf state s, D_s holds the depths of all leaves visited strictly before s (smaller stateId), so nothing from the future
of s is used. The d of the formula is depth - 1, because the depth column of the data is 1 at the root. The prediction is N(s) - stateId(s)
and is compared with the work below s, so the global scope of the estimate and the local scope of the target differ. A state is left unscored
while D_s is empty.

Usage:
    python fit_kilby_wbe_baseline.py"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import (  
    load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci,
)


def wbe_predictions(df):
    """One program's full tree (leaves included). Returns (actuals,
    predicted, state_ids) for every non-leaf state with at least one
    chronologically-prior leaf observed (WBE undefined before that)."""
    df_sorted = df.sort_values("stateId")

    leaf_depths_so_far = []  # multiset D, grows as we scan in stateId order
    weighted_num = 0.0       # running sum(d): prob(d) * (2^(d+1) - 1)
    weighted_den = 0.0       # running sum(d): prob(d)

    actuals, predicted, state_ids = [], [], []
    for _, row in df_sorted.iterrows():
        state_id = int(row["stateId"])
        if row["isEndStateAtEntry"]:
            d = int(row["depth"]) - 1  # paper's 0-indexed-from-root convention
            if d < 0:
                d = 0
            prob_d = 2.0 ** (-d)
            weighted_num += prob_d * (2.0 ** (d + 1) - 1)
            weighted_den += prob_d
            continue

        if weighted_den == 0:
            continue  # WBE undefined before any leaf has been seen

        n_estimate = weighted_num / weighted_den
        predicted_remaining = n_estimate - state_id
        actuals.append(row["actualSubtreeWork"])
        predicted.append(predicted_remaining)
        state_ids.append(state_id)

    return actuals, predicted, state_ids


def main():
    df = load_all()

    all_actuals, all_preds, all_groups = [], [], []
    total_non_leaf = 0
    for program, prog_df in df.groupby("program"):
        actuals, predicted, _ = wbe_predictions(prog_df)
        group = prog_df["program_group"].iloc[0]
        total_non_leaf += (~prog_df["isEndStateAtEntry"]).sum()
        all_actuals.extend(actuals)
        all_preds.extend(predicted)
        all_groups.extend([group] * len(actuals))

    scored = pd.DataFrame({"program_group": all_groups, "actual": all_actuals, "pred": all_preds})
    excluded = total_non_leaf - len(scored)
    print(f"Non-leaf states: {total_non_leaf} total, {len(scored)} scored "
          f"({excluded} excluded: no prior leaf seen yet, WBE undefined by the source formula itself).\n")

    per_group_rho = {}
    for g, sub in scored.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
            continue
        if sub["actual"].nunique() < 2 or sub["pred"].nunique() < 2:
            continue
        rho, _ = spearmanr(sub["actual"], sub["pred"])
        if not np.isnan(rho):
            per_group_rho[g] = rho

    pooled_rho, _ = spearmanr(scored["actual"], scored["pred"])
    macro_rho = macro_average(per_group_rho)
    ci_lo, ci_hi = bootstrap_macro_ci(per_group_rho)

    print("Kilby WBE, adapted per-state (predicted_remaining_work(s) = N_estimate(s) - stateId(s), "
          "N_estimate from leaves seen strictly before s):")
    print(f"  Pooled rho = {pooled_rho:.3f}   Macro rho = {macro_rho:.3f} [{ci_lo:.3f},{ci_hi:.3f}]  "
          f"groups={len(per_group_rho)}")

    print("\n=== Per-program-group rho, blank = < 5 rows ===")
    for g in sorted(scored["program_group"].unique()):
        sub = scored[scored["program_group"] == g]
        if g in per_group_rho:
            print(f"{g:<26} n={len(sub):<6} rho={per_group_rho[g]:.3f}")
        else:
            print(f"{g:<26} n={len(sub):<6} rho=--")



if __name__ == "__main__":
    main()
