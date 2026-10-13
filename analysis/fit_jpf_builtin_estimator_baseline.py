"""JPF's built-in progress estimator (gov.nasa.jpf.listener.StateCountEstimator in jpf-core), adapted to score one state.

The listener estimates the total number of states from the branching factor along the current path:

    delta = 1.0; percent = 0.0
    for each transition i from the root to the current point:
        delta   /= number of choices of its ChoiceGenerator
        percent += delta * (processed choices of that ChoiceGenerator - 1)
    if the path is empty: percent = 1.0
    expectedTotalStates = currentStateCount / percent

Adaptation: for a non-leaf state s, percent(s) is computed along the root-to-s path of s from the logged choiceGeneratorTotal and
choiceGeneratorProcessed of its ancestors. The prediction is expectedTotalStates(s) - stateId(s), the number of states that the whole search
still has left when s is created. It is compared with the work below s, so the global scope of the estimator and the local scope of the target
differ. States with percent(s) <= 0 are left out of the scoring.

Usage:
    python fit_jpf_builtin_estimator_baseline.py"""

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


def state_count_estimator_predictions(df):
    """One program's full tree (leaves included, needed for stateId ->
    ancestor-chain walks). Returns (actuals, predicted, state_ids) for every
    non-leaf state with a well-defined (percent > 0) prediction."""
    row_by_id = {int(row["stateId"]): row for _, row in df.iterrows()}

    def percent_iterative(state_id):
        """percent(s), computed by walking s's own root-to-s ancestor chain,
        exactly mirroring StateCountEstimator.log()'s loop (one CG-weighted
        term per ancestor level, accumulated as a running sum)."""
        chain = []
        cur = state_id
        while True:
            row = row_by_id[cur]
            pid = int(row["parentId"])
            if pid == -1 or pid not in row_by_id:
                break
            chain.append(row)
            cur = pid
        chain.reverse()  # root-to-s order

        delta = 1.0
        percent = 0.0
        for row in chain:
            t_i = row["choiceGeneratorTotal"]
            if t_i in (-1, 0):
                continue
            delta /= t_i
            processed_i = row["choiceGeneratorProcessed"]
            proc = 0 if processed_i in (-1,) else max(0, processed_i - 1)
            percent += delta * proc
        if not chain:
            percent = 1.0
        return percent

    actuals, predicted, state_ids = [], [], []
    for state_id, row in row_by_id.items():
        if row["isEndStateAtEntry"]:
            continue
        percent = percent_iterative(state_id)
        if percent <= 0:
            continue
        expected_total = state_id / percent
        predicted_remaining = expected_total - state_id
        actuals.append(row["actualSubtreeWork"])
        predicted.append(predicted_remaining)
        state_ids.append(state_id)
    return actuals, predicted, state_ids


def main():
    df = load_all()

    all_actuals, all_preds, all_groups = [], [], []
    excluded_undefined = 0
    total_non_leaf = 0
    for program, prog_df in df.groupby("program"):
        actuals, predicted, _ = state_count_estimator_predictions(prog_df)
        group = prog_df["program_group"].iloc[0]
        n_non_leaf = (~prog_df["isEndStateAtEntry"]).sum()
        total_non_leaf += n_non_leaf
        excluded_undefined += n_non_leaf - len(actuals)
        all_actuals.extend(actuals)
        all_preds.extend(predicted)
        all_groups.extend([group] * len(actuals))

    scored = pd.DataFrame({"program_group": all_groups, "actual": all_actuals, "pred": all_preds})
    print(f"Non-leaf states: {total_non_leaf} total, {len(scored)} with a well-defined prediction "
          f"({excluded_undefined} excluded: percent(s) <= 0, undefined by the source formula itself).\n")

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

    print("JPF's built-in StateCountEstimator, adapted per-state (predicted_remaining_work(s) = "
          "expectedTotalStates(s) - stateId(s)):")
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
