"""Does the negative state-count-floor result depend on which cost measure defines "work"?

For each cost measure recorded per state (bytecode instructions, allocations, GC cycles, solver calls, solver time,
wall-clock time), reports over the non-leaf states of every program group with at least MIN_ROWS_FOR_GROUP_RHO rows and
a non-constant target:
  * macro Spearman rho of the visitation-order rank (stateId, the live count) with the measure;
  * macro Spearman rho of the hindsight subtree size (states in the subtree) with the measure;
  * number of groups scored.
Groups where a measure is constant (e.g. no allocation in any subtree) are not scored for that measure.
Wall-clock is unavailable for one group collected before that instrumentation existed (rows with all zeros are dropped).

Usage: python floor_by_cost_measure.py"""
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci

MEASURES = [("actualSubtreeWork", "bytecode instructions"), ("actualAllocWork", "allocations"), ("actualGcWork", "GC cycles"),
            ("actualSolverCalls", "solver calls"), ("actualSolverNanos", "solver time"), ("actualWallClockNanos", "wall-clock time")]


def subtree_sizes(sub):
    """States in the subtree of each state (itself included), from stateId/parentId, for one program's rows."""
    ids = set(sub["stateId"])
    size = {i: 1 for i in ids}
    parent = dict(zip(sub["stateId"], sub["parentId"]))
    for i in sorted(ids, reverse=True):  # children have larger ids than parents
        p = parent[i]
        if p in size:
            size[p] += size[i]
    return sub["stateId"].map(size).values


def main():
    df = load_all()
    df = df.sort_values(["program", "stateId"])
    # hindsight size over ALL rows (leaves included) of each configuration, then restrict to non-leaf rows
    df["hind"] = 0
    for prog, idx in df.groupby("program").groups.items():
        df.loc[idx, "hind"] = subtree_sizes(df.loc[idx])
    nl = df[df["isEndStateAtEntry"] == False].copy() 
    print(f"Non-leaf states: {len(nl)} across {nl['program_group'].nunique()} program groups.\n")
    print(f"{'measure':<24}{'groups':>7}   {'live count (stateId)':<28}{'hindsight subtree size'}")
    for col, name in MEASURES:
        d = nl.copy()
        if col == "actualWallClockNanos":
            ok = d.groupby("program")[col].transform("max") > 0
            d = d[ok]
        live, hind = {}, {}
        for g, sub in d.groupby("program_group"):
            if len(sub) < MIN_ROWS_FOR_GROUP_RHO or sub[col].nunique() < 2:
                continue
            r1 = spearmanr(sub["stateId"], sub[col])[0]
            r2 = spearmanr(sub["hind"], sub[col])[0]
            if not np.isnan(r1):
                live[g] = r1
            if not np.isnan(r2):
                hind[g] = r2
        l_lo, l_hi = bootstrap_macro_ci(live)
        h_lo, h_hi = bootstrap_macro_ci(hind)
        print(f"{name:<24}{len(live):>7}   {macro_average(live):+.3f} [{l_lo:+.3f},{l_hi:+.3f}]".ljust(59)
              + f"{macro_average(hind):+.3f} [{h_lo:+.3f},{h_hi:+.3f}]")


if __name__ == "__main__":
    main()
