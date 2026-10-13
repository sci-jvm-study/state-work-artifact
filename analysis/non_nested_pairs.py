"""Ranking quality on pairs of states that are not ancestor and descendant (post hoc). A scheduler or a progress display compares
states on the frontier, which are mostly not nested, while Spearman's rho over a whole tree also counts nested pairs, where capping and the depth
rule are right by construction (the later state has no more work). For each program, over all pairs of non-end states (a, b) that are not in an
ancestor-descendant relation and whose work values differ, this prints the share of pairs the estimator orders correctly among pairs it orders
(ties in the estimate dropped): gamma = (C - D) / (C + D), averaged over the program groups (macro, >= 5 states). Estimators: the live count
(creation order), -depth, M5 Random Forest raw and capped (leave-one-program-group-out predictions of the M5 features).
Also run on nested pairs only, and with the zero-work childless states left out.
Usage: python non_nested_pairs.py > ../results/66_non_nested_pairs.txt"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, macro_average, MIN_ROWS_FOR_GROUP_RHO  
from fit_hybrid_model import M5_FEATURES, make_rf_factory

HERE = os.path.dirname(os.path.abspath(__file__))
df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
nl = df[df.isEndStateAtEntry == False].copy()  
kids = set(zip(df.program, df.parentId))
nl["haskid"] = [(p, s) in kids for p, s in zip(nl.program, nl.stateId)]
# M5 Random Forest, leave-one-program-group-out: each row is predicted by a model trained on every other program group
nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
nl["stage0"] = np.nan
for g in sorted(nl["program_group"].unique()):
    tr, te = nl[nl["program_group"] != g], nl[nl["program_group"] == g]
    m = rf()
    m.fit(tr[M5_FEATURES].values, tr["logWork"].values)
    nl.loc[te.index, "stage0"] = m.predict(te[M5_FEATURES].values)
assert nl.stage0.notna().all()
cap = {}
for p, g in nl.groupby("program"):
    for sid, par, pred in zip(g.stateId, g.parentId, g.stage0):
        cap[(p, sid)] = min(pred, cap.get((p, par), np.inf))
nl["capped"] = [cap[(p, s)] for p, s in zip(nl.program, nl.stateId)]
nl["live_count"] = nl.stateId.astype(float)
nl["neg_depth"] = -nl.depth.astype(float)
EST = {"live count": "live_count", "-depth": "neg_depth", "M5-RF raw": "stage0", "M5-RF capped": "capped"}


def tallies(sub, col, want_nested):
    """concordant, discordant counts over pairs of this program (nested or not)"""
    sid = sub.stateId.values
    idx = {s: i for i, s in enumerate(sid)}
    n = len(sid)
    anc = np.zeros((n, n), dtype=bool)  # anc[i, j]: i is an ancestor of j
    par = sub.parentId.values
    for j in range(n):
        p = par[j]
        while p in idx:
            anc[idx[p], j] = True
            p = par[idx[p]]
    nested = anc | anc.T
    w = sub.actualSubtreeWork.values.astype(float)
    x = sub[col].values.astype(float)
    dw = np.sign(w[:, None] - w[None, :])
    dx = np.sign(x[:, None] - x[None, :])
    mask = np.triu(np.ones((n, n), dtype=bool), 1) & (nested if want_nested else ~nested) & (dw != 0) & (dx != 0)
    c = int(((dw * dx > 0) & mask).sum())
    d = int(((dw * dx < 0) & mask).sum())
    return c, d


def run(data, want_nested):
    res = {k: {} for k in EST}
    for (grp, prog), sub in data.groupby(["program_group", "program"]):
        for k, col in EST.items():
            c, d = tallies(sub, col, want_nested)
            a = res[k].setdefault(grp, [0, 0, 0])
            a[0] += c; a[1] += d; a[2] += len(sub)
    out = {}
    for k in EST:
        pg = {g: (c - d) / (c + d) for g, (c, d, n) in res[k].items() if n >= MIN_ROWS_FOR_GROUP_RHO and c + d > 0}
        out[k] = (macro_average(pg), len(pg))
    return out


for label, data in (("all non-end states", nl), ("zero-work childless states left out", nl[nl.haskid])):
    print(f"=== {label} ===")
    nn = run(data, False)
    ne = run(data, True)
    print(f"{'estimator':16s}{'non-nested pairs':>20}{'nested pairs':>16}")
    for k in EST:
        print(f"{k:16s}{nn[k][0]:>+14.3f} ({nn[k][1]:>2d}){ne[k][0]:>+11.3f} ({ne[k][1]:>2d})")
    print()
