"""
Construct validation: correlate W against measured per-subtree wall-clock on a fixed idle machine.

W(s), as used throughout the modeling, is `actualSubtreeWork` --> a COUNT (bytecodes
executed), not a timed quantity. This script checks whether that count-based proxy actually tracks
REAL measured wall-clock time, using the `actualWallClockNanos` column: System.nanoTime() captured
at a state's push (stateAdvanced) and pop (stateBacktracked/searchFinished), same snapshot/delta
pattern as every other counter in StateWorkListener (see ../instrumentation/README.md).

CONFOUND: the listener's per-event console logging (a line per ADVANCED/BACKTRACKED/PROCESSED event)
happens inside every still-open ancestor frame's timed window, so console I/O cost would inflate
actualWallClockNanos roughly in proportion to subtree size -- correlating actualWallClockNanos with
actualSubtreeWork tautologically via shared print-count, not real computation time. The corpus is
collected with a `-Dstatework.quiet=true` flag (StateWorkListener.java) that suppresses per-event
printing; this does not affect any counter (verified: every counter is bit-for-bit identical between
quiet and non-quiet runs of the same program).

Usage:
    python fit_construct_validation.py
"""

import os
import sys
import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import load_all, macro_average, bootstrap_macro_ci  


def rho_report(non_leaf, x_col, y_col, program_groups, min_rows=5):
    per_group_rho = {}
    for g in program_groups:
        sub = non_leaf[non_leaf["program_group"] == g]
        if len(sub) < min_rows:
            continue
        if sub[x_col].nunique() < 2 or sub[y_col].nunique() < 2:
            continue
        rho, _ = spearmanr(sub[x_col], sub[y_col])
        if not np.isnan(rho):
            per_group_rho[g] = rho
    pooled_rho, _ = spearmanr(non_leaf[x_col], non_leaf[y_col])
    macro_rho = macro_average(per_group_rho)
    ci_lo, ci_hi = bootstrap_macro_ci(per_group_rho)
    return pooled_rho, macro_rho, (ci_lo, ci_hi), len(per_group_rho)


def main():
    df = load_all()

    has_wallclock = "actualWallClockNanos" in df.columns
    if not has_wallclock:
        raise SystemExit("No actualWallClockNanos column -- re-run the corpus with the "
                          "wall-clock instrumentation first (see ../instrumentation/README.md).")

    missing_mask = df["actualWallClockNanos"].isna()
    excluded = sorted(df.loc[missing_mask, "program"].unique())
    if excluded:
        print(f"Excluding {len(excluded)} program(s) without wall-clock data: {excluded}")
    df = df[~missing_mask].copy()

    non_leaf = df[df["isEndStateAtEntry"] == False].copy()  
    program_groups = sorted(non_leaf["program_group"].unique())
    print(f"Non-leaf states with wall-clock data: {len(non_leaf)} across "
          f"{len(program_groups)} program groups.\n")

    print("=== Does the count-based W_engine proxy (actualSubtreeWork) track REAL measured "
          "wall-clock time? ===\n")

    pooled, macro, ci, n_groups = rho_report(
        non_leaf, "actualSubtreeWork", "actualWallClockNanos", program_groups)
    print(f"actualSubtreeWork vs actualWallClockNanos:")
    print(f"  pooled rho = {pooled:.3f}   macro rho = {macro:.3f} [{ci[0]:.3f},{ci[1]:.3f}]  "
          f"groups={n_groups}")

    pooled_s, macro_s, ci_s, n_s = rho_report(
        non_leaf, "actualSolverNanos", "actualWallClockNanos", program_groups)
    print(f"\nactualSolverNanos vs actualWallClockNanos (does solver time alone track real time?):")
    print(f"  pooled rho = {pooled_s:.3f}   macro rho = {macro_s:.3f} [{ci_s[0]:.3f},{ci_s[1]:.3f}]  "
          f"groups={n_s}")

    # Does the engine count combined with the solver time track the wall-clock time better than either alone? The two have different
    # units (a count and nanoseconds), so the ranks are added; Spearman rho depends on ranks only.
    non_leaf["engine_plus_solver_rank_proxy"] = (
        non_leaf["actualSubtreeWork"].rank() + non_leaf["actualSolverNanos"].rank())
    pooled_c, macro_c, ci_c, n_c = rho_report(
        non_leaf, "engine_plus_solver_rank_proxy", "actualWallClockNanos", program_groups)
    print(f"\nrank(actualSubtreeWork) + rank(actualSolverNanos) vs actualWallClockNanos "
          f"(does combining help?):")
    print(f"  pooled rho = {pooled_c:.3f}   macro rho = {macro_c:.3f} [{ci_c[0]:.3f},{ci_c[1]:.3f}]  "
          f"groups={n_c}")

    print("\n=== Per-program-group rho (actualSubtreeWork vs actualWallClockNanos), "
          "blank = < 5 rows ===")
    for g in program_groups:
        sub = non_leaf[non_leaf["program_group"] == g]
        if len(sub) < 5 or sub["actualSubtreeWork"].nunique() < 2:
            print(f"{g:<26} n={len(sub):<6} rho=--")
            continue
        rho, _ = spearmanr(sub["actualSubtreeWork"], sub["actualWallClockNanos"])
        print(f"{g:<26} n={len(sub):<6} rho={rho:.3f}" if not np.isnan(rho)
              else f"{g:<26} n={len(sub):<6} rho=--")

    print("\n[Note] Single-machine measurement on a machine that was not a dedicated benchmarking rig.")


if __name__ == "__main__":
    main()
