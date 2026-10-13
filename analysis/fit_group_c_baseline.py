"""Group C, the sibling mean: the recursive sibling-average estimator of Kilby et al. (AAAI 2006), over the full corpus.

"The unexplored part of the search tree will be similar to the part we have so far explored." For the i-th child (i >= 2) of a parent, the
prediction is the mean actual work of the already seen children of that parent. The first child of a parent has no earlier sibling and stays
unscored.

Group C is not a fitted model: it has no training phase and no LOPO folds, and parentId is meaningful only inside the run of one program.
The script therefore works on each program file separately and then aggregates the scored predictions to the same pooled and macro Spearman rho
as models_m1_to_m5.py, whose program groups it reuses.

Usage:
    python fit_group_c_baseline.py"""

import glob
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from models_m1_to_m5 import (
    DATA_DIR, program_group_of, MIN_ROWS_FOR_GROUP_RHO,
    macro_average, bootstrap_macro_ci,
)


def recursive_estimator_predictions(df, target_column="actualSubtreeWork"):
    """The estimator on the DataFrame of one program (never pooled across programs, because parentId
    is meaningful only within a single JPF run)."""
    actuals, predicted, _ = recursive_estimator_predictions_with_ids(df, target_column)
    return actuals, predicted


def recursive_estimator_predictions_with_ids(df, target_column="actualSubtreeWork"):
    """Same as recursive_estimator_predictions, but also returns each
    prediction's stateId -- needed to merge Group C's prediction back onto
    the main dataframe as a FEATURE (for the hybrid M6 model), not just to
    score it standalone. First-child-per-parent states are absent from the
    returned stateId list (Group C has no prediction for them), exactly as
    the standalone version silently skips them."""
    by_parent = defaultdict(list)
    for _, row in df.iterrows():
        by_parent[row["parentId"]].append(row)

    actuals, predicted, state_ids = [], [], []
    for parent_id, children in by_parent.items():
        children.sort(key=lambda r: int(r["stateId"]))
        seen_work = []
        for child in children:
            actual = child[target_column]
            if seen_work:
                pred = sum(seen_work) / len(seen_work)
                actuals.append(actual)
                predicted.append(pred)
                state_ids.append(child["stateId"])
            seen_work.append(actual)
    return actuals, predicted, state_ids


def main():
    rows = []
    for path in glob.glob(os.path.join(DATA_DIR, "*", "*.csv")):
        program = os.path.splitext(os.path.basename(path))[0]
        df = pd.read_csv(path)
        df["program"] = program
        df["program_group"] = program_group_of(program)
        rows.append(df)
    from prune import mark_pruned
    full = mark_pruned(pd.concat(rows, ignore_index=True))
    print(f"Loaded {len(full)} total state rows across {full['program'].nunique()} programs.")

    # Match models_m1_to_m5.py's own scope exactly: leaves are
    # trivially actualSubtreeWork==0 and not an interesting prediction
    # target there, so exclude them here too for a fair, same-population
    # comparison against M1-M5's numbers.
    full = full[full["isEndStateAtEntry"] == False].copy() 
    print(f"Non-leaf (internal) states: {len(full)}")

    all_actuals, all_predicted, groups_of_row = [], [], []
    per_group_rho = {}

    for program, prog_df in full.groupby("program"):
        actuals, predicted = recursive_estimator_predictions(prog_df)
        if not actuals:
            continue
        group = program_group_of(program)
        all_actuals.extend(actuals)
        all_predicted.extend(predicted)
        groups_of_row.extend([group] * len(actuals))

    # Aggregate per-group (a program_group may span multiple archived
    # configs, e.g. InsertionSort + InsertionSort5 + InsertionSort6 -- pool
    # their individually-computed sibling predictions before scoring rho,
    # same spirit as models_m1_to_m5.py's per-group rho).
    by_group_actual = defaultdict(list)
    by_group_pred = defaultdict(list)
    for g, a, p in zip(groups_of_row, all_actuals, all_predicted):
        by_group_actual[g].append(a)
        by_group_pred[g].append(p)

    for g in by_group_actual:
        ya, yp = by_group_actual[g], by_group_pred[g]
        if len(ya) >= MIN_ROWS_FOR_GROUP_RHO and len(set(ya)) >= 2 and len(set(yp)) >= 2:
            rho, _ = spearmanr(ya, yp)
            if not np.isnan(rho):
                per_group_rho[g] = rho

    pooled_rho = (spearmanr(all_actuals, all_predicted)[0]
                  if len(set(all_actuals)) >= 2 and len(set(all_predicted)) >= 2 else float("nan"))
    macro_rho = macro_average(per_group_rho)
    ci_lo, ci_hi = bootstrap_macro_ci(per_group_rho)

    print(f"\nGroup C (Kilby recursive sibling-average) baseline, scored on "
          f"{len(all_actuals)} scoreable non-first-child states:")
    print(f"{'Pooled rho':>11} {'Macro rho':>10} {'Macro 95% CI':>16} {'groups':>7}")
    print(f"{pooled_rho:>11.3f} {macro_rho:>10.3f} [{ci_lo:>6.3f},{ci_hi:>6.3f}] "
          f"{len(per_group_rho):>7}")

    print("\n=== Per-program-group Spearman rho (Group C), "
          f"blank = < {MIN_ROWS_FOR_GROUP_RHO} scoreable states ===")
    for g in sorted(by_group_actual):
        v = per_group_rho.get(g)
        n = len(by_group_actual[g])
        print(f"{g:<22} n={n:<6} rho={'%.2f' % v if v is not None else '--'}")

    print("\n[Note] Group C has no training phase and is NOT subject to LOPO leakage concerns --")
    print("it only ever uses a state's own siblings within the SAME program's SAME run. This makes")
    print("it a legitimately different kind of baseline from M1-M5 (which use LOPO precisely because")
    print("they DO learn from other programs) -- compare cautiously, not as a strict apples-to-apples")
    print("cross-validation -- see fit_all_baselines_fair_comparison.py for the fair, same-population")
    print("comparison against M1-M6 that accounts for this difference.")


if __name__ == "__main__":
    main()
