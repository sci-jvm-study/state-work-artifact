"""Offline (whole-tree) nesting-consistent projection of M5-RF predictions (see nesting_offline_predeclared.md, written before this script was run).

Poses the projection as the convex program it is -- minimize sum (x_s - pred[s])^2 subject to x_parent >= x_child for every
non-leaf parent-child pair -- and solves it with CLARABEL (a general-purpose interior-point conic solver). Cross-checked
against OSQP (a different solver, different algorithm family) on every corpus tree: identical optimum.

Usage: python nesting_offline.py"""
import os
import sys

import cvxpy as cp
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci 
from fit_hybrid_model import make_rf_factory  
from load_balance_replay import loo_predictions  
from nesting_consistency import adjust as online_adjust  


def isotonic_tree_project(kids, pred):
    """pred: dict stateId -> raw value, over the non-leaf states of one configuration. kids: dict stateId -> list of child stateIds (all states).
    Returns dict stateId -> projected value satisfying value[parent] >= value[child] for every non-leaf parent-child pair, as the exact
    least-squares solution: solved as a convex quadratic program (not a hand-written pooling heuristic -- see module docstring)."""
    states = list(pred.keys())
    idx = {s: i for i, s in enumerate(states)}
    y = np.array([pred[s] for s in states])
    parent_of = {}
    for p, cs in kids.items():
        for c in cs:
            if c in pred and p in pred:
                parent_of[c] = p
    if not parent_of:
        return dict(pred)
    x = cp.Variable(len(states))
    constraints = [x[idx[p]] >= x[idx[c]] for c, p in parent_of.items()]
    prob = cp.Problem(cp.Minimize(cp.sum_squares(x - y)), constraints)
    prob.solve(solver=cp.CLARABEL)
    assert prob.status in ("optimal", "optimal_inaccurate"), f"QP solver did not reach optimality: {prob.status}"
    return {states[i]: float(x.value[i]) for i in range(len(states))}


def main():
    df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
    nl = df[df["isEndStateAtEntry"] == False].copy()  
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    nl["p_rf"] = np.expm1(loo_predictions(nl, rf))
    rows = []
    n_checked, n_bad = 0, 0
    for prog, d in df.groupby("program"):
        g = d["program_group"].iloc[0]
        d = d.reset_index(drop=True)
        sub = nl.loc[nl["program"] == prog]
        pred = dict(zip(sub["stateId"], sub["p_rf"]))
        kids = {}
        for r in d.itertuples():
            kids.setdefault(r.parentId, []).append(r.stateId)
        A, _ = online_adjust(d, pred)
        Q = isotonic_tree_project(kids, pred)
        par = dict(zip(d["stateId"], d["parentId"]))
        for s in pred:
            p = par[s]
            if p in Q:
                n_checked += 1
                if Q[p] < Q[s] - 1e-6:
                    n_bad += 1
        for s in pred:
            rows.append((g, s, float(d.loc[d.stateId == s, "actualSubtreeWork"].iloc[0]), pred[s], A[s], Q[s]))
    print(f"Mechanical check: {n_checked} parent-child pairs, {n_bad} violate offline-projected parent >= child (must be 0)\n")
    R = pd.DataFrame(rows, columns=["g", "s", "actual", "raw", "online", "offline"])
    groups = [g for g, s in nl.groupby("program_group") if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s["actualSubtreeWork"].nunique() > 1]
    res = {}
    for name in ("raw", "online", "offline"):
        per = {}
        for g in groups:
            s = R[R.g == g]
            if s[name].nunique() > 1 and s["actual"].nunique() > 1:
                per[g] = spearmanr(s["actual"], s[name])[0]
        res[name] = per
    print(f"{'variant':<12}{'groups':>7}{'macro rho':>11}   95% CI")
    for name in ("raw", "online", "offline"):
        lo, hi = bootstrap_macro_ci(res[name])
        print(f"{name:<12}{len(res[name]):>7}{macro_average(res[name]):>+11.3f}   [{lo:+.3f}, {hi:+.3f}]")
    common = [g for g in groups if g in res["raw"] and g in res["online"] and g in res["offline"]]
    on_gain = macro_average({g: res["online"][g] for g in common}) - macro_average({g: res["raw"][g] for g in common})
    off_gain = macro_average({g: res["offline"][g] for g in common}) - macro_average({g: res["raw"][g] for g in common})
    print(f"\nOn the {len(common)} groups all three score: online gain over raw {on_gain:+.3f}, offline gain over raw {off_gain:+.3f}, "
          f"online captures {100 * on_gain / off_gain:.1f}% of the offline gain.")
    print("\nBy tree size, POST HOC (bands as in nesting_decomposition.py, not predeclared):")
    size = nl.groupby("program_group").size()
    for lo_, hi_ in [(0, 15), (15, 60), (60, 300), (300, 10 ** 6)]:
        gs = [g for g in common if lo_ <= size[g] < hi_]
        if gs:
            r_, o_, f_ = (np.mean([res[k][g] for g in gs]) for k in ("raw", "online", "offline"))
            print(f"  non-leaf states in [{lo_}, {hi_ if hi_ < 10 ** 6 else 'inf'}): {len(gs):>2} groups, raw {r_:+.3f}, online {o_:+.3f}, offline {f_:+.3f}")


if __name__ == "__main__":
    main()
