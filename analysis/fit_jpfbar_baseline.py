"""JPFBar: Wang, K. et al., "A Progress Bar for the JPF Search Using Program Executions", JPF Workshop 2018 (ESEC/FSE 2018), adapted to score one
state.

JPFBar is a live, cumulative tracker of the share of the search that is done. For a complete execution path p = <c_1, ..., c_k> (a sequence of
non-deterministic choices, c_i one choice out of t_i, ending at an end state), weight(p) = 1 / (t_1 * t_2 * ... * t_k). The weight of the root is
1, so the weights of all paths sum to 1, and the weight is divided evenly among the children of a state. Progress = sum of weight(p) over the
completed paths so far, a value in [0, 1]. A choice with t_i = -1 (no choice generator) contributes no term.

Adaptation (as for the JPF built-in estimator and the Kilby WBE): for a non-leaf state s, progress_so_far(s) is the sum of weight(leaf) over every
leaf (isEndStateAtEntry == True) visited strictly before s in stateId order, which is what a live JPFBar listener would have reported when s was
created. The prediction is predicted_remaining_work(s) = stateId(s) / progress_so_far(s) - stateId(s), compared with the work below s, so the
global scope of the estimate and the local scope of the target differ.

Usage:
    python fit_jpfbar_baseline.py"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import ( 
    load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci,
)


def leaf_path_weight(row_by_id, leaf_id):
    """weight(p) for the complete path from root to this leaf: 1 / prod(t_i)
    over every ancestor step (t_i = -1 contributes no term)."""
    weight = 1.0
    cur = leaf_id
    while True:
        row = row_by_id[cur]
        t_i = row["choiceGeneratorTotal"]
        if t_i not in (-1, 0):
            weight /= t_i
        pid = int(row["parentId"])
        if pid == -1 or pid not in row_by_id:
            break
        cur = pid
    return weight


def jpfbar_predictions(df):
    """One program's full tree. Returns (actuals, predicted, state_ids) for
    every non-leaf state with at least one chronologically-prior completed
    path (JPFBar's progress is 0, undefined for extrapolation, before that)."""
    row_by_id = {int(row["stateId"]): row for _, row in df.iterrows()}
    df_sorted = df.sort_values("stateId")

    progress_so_far = 0.0
    actuals, predicted, state_ids = [], [], []
    for _, row in df_sorted.iterrows():
        state_id = int(row["stateId"])
        if row["isEndStateAtEntry"]:
            progress_so_far += leaf_path_weight(row_by_id, state_id)
            continue

        if progress_so_far <= 0:
            continue  # no completed path yet -- JPFBar's progress is 0

        expected_total = state_id / progress_so_far
        predicted_remaining = expected_total - state_id
        actuals.append(row["actualSubtreeWork"])
        predicted.append(predicted_remaining)
        state_ids.append(state_id)

    return actuals, predicted, state_ids


def main():
    df = load_all()

    all_actuals, all_preds, all_groups = [], [], []
    total_non_leaf = 0
    for program, prog_df in df.groupby("program"):
        actuals, predicted, _ = jpfbar_predictions(prog_df)
        group = prog_df["program_group"].iloc[0]
        total_non_leaf += (~prog_df["isEndStateAtEntry"]).sum()
        all_actuals.extend(actuals)
        all_preds.extend(predicted)
        all_groups.extend([group] * len(actuals))

    scored = pd.DataFrame({"program_group": all_groups, "actual": all_actuals, "pred": all_preds})
    excluded = total_non_leaf - len(scored)
    print(f"Non-leaf states: {total_non_leaf} total, {len(scored)} scored "
          f"({excluded} excluded: no completed path seen yet, JPFBar progress undefined for "
          f"extrapolation).\n")

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

    print("JPFBar, adapted per-state (predicted_remaining_work(s) = "
          "(stateId(s)/progress_so_far(s)) - stateId(s), progress from completed paths seen "
          "strictly before s):")
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
