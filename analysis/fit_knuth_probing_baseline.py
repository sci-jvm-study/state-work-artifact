"""Knuth's random probing, "Estimating the Efficiency of Backtrack Programs", Mathematics of Computation 29(129), 1975, pp. 121-136, adapted to score one state.

From a node, follow one path to a leaf and choose a child uniformly at random at every step. With n_0, n_1, ..., n_l the numbers of
children seen along the path, the estimate of the number of nodes in the subtree is

    C = n_0 + n_0*n_1 + n_0*n_1*n_2 + ... + n_0*n_1*...*n_l

Adaptation: the full tree of every program is already recorded, so a probe is simulated as a random walk over the recorded parent-child
structure and needs no new JPF run. A single probe has a high variance, so N_PROBES probes are averaged per state (fixed seed).

Usage:
    python fit_knuth_probing_baseline.py"""

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

N_PROBES = 30
SEED = 42


def knuth_probe_predictions(prog_df, rng):
    """One program's full tree (leaves included -- needed to know true
    children counts and where descent must stop). Returns
    (actuals, predicted, state_ids) for every NON-LEAF state, predicted =
    average of N_PROBES independent random-descent estimates."""
    children = defaultdict(list)
    row_by_id = {}
    for _, row in prog_df.iterrows():
        sid = int(row["stateId"])
        row_by_id[sid] = row
        pid = int(row["parentId"])
        if pid != -1:
            children[pid].append(sid)

    def one_probe(start_id):
        current = start_id
        cumulative = 0.0
        running_product = 1.0
        while True:
            kids = children.get(current, [])
            n = len(kids)
            if n == 0:
                break
            running_product *= n
            cumulative += running_product
            current = kids[rng.integers(0, n)]
        return cumulative

    actuals, predicted, state_ids = [], [], []
    non_leaf_ids = [sid for sid, row in row_by_id.items() if not row["isEndStateAtEntry"]]
    for sid in non_leaf_ids:
        estimates = [one_probe(sid) for _ in range(N_PROBES)]
        pred = float(np.mean(estimates))
        actuals.append(row_by_id[sid]["actualSubtreeWork"])
        predicted.append(pred)
        state_ids.append(sid)
    return actuals, predicted, state_ids


def main():
    df = load_all()
    rng = np.random.default_rng(SEED)

    all_actuals, all_preds, all_groups = [], [], []
    for program, prog_df in df.groupby("program"):
        actuals, predicted, _ = knuth_probe_predictions(prog_df, rng)
        group = prog_df["program_group"].iloc[0]
        all_actuals.extend(actuals)
        all_preds.extend(predicted)
        all_groups.extend([group] * len(actuals))

    scored = pd.DataFrame({"program_group": all_groups, "actual": all_actuals, "pred": all_preds})
    print(f"Non-leaf states scored: {len(scored)} across {scored['program_group'].nunique()} "
          f"program groups. ({N_PROBES} random probes per state, seed={SEED})\n")

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

    print("Knuth (1975) random-probing estimator (mean of N_PROBES random root-to-leaf "
          "descents, simulated over the already-recorded exhaustive tree):")
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
