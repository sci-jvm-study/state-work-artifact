"""Final subtree size N(s) against the work W(s) of a state.

N(s) is the number of states in the subtree of s, with s and the leaves included. It is computed from the stateId and parentId columns and
scored like every other baseline: Spearman rho per program group, macro mean over the groups with at least 5 non-leaf rows, and a bootstrap
CI over groups. The live count of the paper is the creation rank stateId, which is a different quantity and is scored by other scripts.

Method: every program tree is processed on its own, because parentId is local to one run. Each state starts with count 1. States are visited
from the deepest level upward, and each one adds its count to its parent (iterative, because some trees have more than 1,400 states). A
parentId that is not a stateId of the same program is not propagated further. This happens at the top, because the JPF root is not logged as a
row and its children carry parentId=0.

Usage:
    python fit_node_count_baseline.py"""

import os
import sys
import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import (
    load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci,
)


def compute_node_counts(df):
    """Adds a 'nodeCount' column: N(s), the total state count (self +
    all descendants) of the subtree rooted at s, computed per-program."""
    df = df.copy()
    node_count = np.empty(len(df), dtype=np.int64)
    for program, sub in df.groupby("program"):
        idx = sub.index.to_numpy()
        state_ids = sub["stateId"].to_numpy()
        parent_ids = sub["parentId"].to_numpy()
        depths = sub["depth"].to_numpy()

        # Verify the depth(parent) = depth(child) - 1 assumption this method
        # depends on, rather than silently trusting it.
        parent_depth = dict(zip(state_ids, depths))
        for sid, pid, d in zip(state_ids, parent_ids, depths):
            if pid in parent_depth and parent_depth[pid] != d - 1:
                raise AssertionError(
                    f"{program}: state {sid} has depth {d} but parent {pid} "
                    f"has depth {parent_depth[pid]} (expected {d - 1}) -- "
                    "the deepest-first accumulation order is unsafe here."
                )

        order = np.argsort(-depths, kind="stable")
        size = dict(zip(state_ids, np.ones(len(state_ids), dtype=np.int64)))
        for pos in order:
            sid = state_ids[pos]
            pid = parent_ids[pos]
            if pid in size:
                size[pid] += size[sid]

        local_counts = np.array([size[sid] for sid in state_ids], dtype=np.int64)
        node_count[idx] = local_counts

    df["nodeCount"] = node_count
    return df


def main():
    df = load_all()
    df = compute_node_counts(df)
    non_leaf = df[df["isEndStateAtEntry"] == False].copy()
    print(f"Non-leaf states: {len(non_leaf)} across {non_leaf['program_group'].nunique()} program groups.\n")

    # Sanity spot-check: a leaf's own subtree must have nodeCount == 1.
    leaves = df[df["isEndStateAtEntry"] == True]
    bad_leaves = (leaves["nodeCount"] != 1).sum()
    print(f"Sanity check: {bad_leaves} of {len(leaves)} leaf states have nodeCount != 1 "
          f"(expected 0).\n")

    per_group_rho = {}
    for g, sub in non_leaf.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
            continue
        if sub["nodeCount"].nunique() < 2 or sub["actualSubtreeWork"].nunique() < 2:
            continue
        rho, _ = spearmanr(sub["nodeCount"], sub["actualSubtreeWork"])
        if not np.isnan(rho):
            per_group_rho[g] = rho

    pooled_rho, _ = spearmanr(non_leaf["nodeCount"], non_leaf["actualSubtreeWork"])
    macro_rho = macro_average(per_group_rho)
    ci_lo, ci_hi = bootstrap_macro_ci(per_group_rho)

    print("True N(s) (subtree node count, from stateId/parentId) vs W_engine(s) (actualSubtreeWork):")
    print(f"  Pooled rho = {pooled_rho:.3f}   Macro rho = {macro_rho:.3f} [{ci_lo:.3f},{ci_hi:.3f}]  "
          f"groups={len(per_group_rho)}")

    # Compare directly against the already-reported visitation-order-rank result,
    # computed identically, so the two numbers are apples-to-apples.
    rank_per_group_rho = {}
    for g, sub in non_leaf.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
            continue
        if sub["stateId"].nunique() < 2 or sub["actualSubtreeWork"].nunique() < 2:
            continue
        rho, _ = spearmanr(sub["stateId"], sub["actualSubtreeWork"])
        if not np.isnan(rho):
            rank_per_group_rho[g] = rho
    rank_pooled_rho, _ = spearmanr(non_leaf["stateId"], non_leaf["actualSubtreeWork"])
    rank_macro_rho = macro_average(rank_per_group_rho)
    rank_ci_lo, rank_ci_hi = bootstrap_macro_ci(rank_per_group_rho)

    print("\nFor comparison, visitation-order rank (stateId(s)) vs W_engine(s), same population:")
    print(f"  Pooled rho = {rank_pooled_rho:.3f}   Macro rho = {rank_macro_rho:.3f} "
          f"[{rank_ci_lo:.3f},{rank_ci_hi:.3f}]  groups={len(rank_per_group_rho)}")

    print("\n=== Per-program-group rho for N(s), blank = < 5 rows ===")
    for g in sorted(non_leaf["program_group"].unique()):
        sub = non_leaf[non_leaf["program_group"] == g]
        if g in per_group_rho:
            print(f"{g:<26} n={len(sub):<6} rho={per_group_rho[g]:.3f}")
        else:
            print(f"{g:<26} n={len(sub):<6} rho=--")



if __name__ == "__main__":
    main()
