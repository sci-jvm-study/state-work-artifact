"""Writes the per-group macro rho of the raw, online-capped and offline-projected predictions of nesting_offline.py to a CSV, for the figures. It
computes the same numbers as nesting_offline.py, whose report is results/47.

Usage: python nesting_offline_groups_csv.py"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO  
from fit_hybrid_model import make_rf_factory  
from load_balance_replay import loo_predictions  
from nesting_consistency import adjust as online_adjust  
from nesting_offline import isotonic_tree_project  

df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
nl = df[df["isEndStateAtEntry"] == False].copy()
nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
nl["p_rf"] = np.expm1(loo_predictions(nl, rf))
rows = []
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
    for s in pred:
        rows.append((g, s, float(d.loc[d.stateId == s, "actualSubtreeWork"].iloc[0]), pred[s], A[s], Q[s]))
R = pd.DataFrame(rows, columns=["g", "s", "actual", "raw", "online", "offline"])
groups = [g for g, s in nl.groupby("program_group") if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s["actualSubtreeWork"].nunique() > 1]

out = []
nonleaf_by_group = nl.groupby("program_group").size()
for g in groups:
    s = R[R.g == g]
    row = {"group": g, "nonleaf": int(nonleaf_by_group[g])}
    for name in ("raw", "online", "offline"):
        if s[name].nunique() > 1 and s["actual"].nunique() > 1:
            row[name] = spearmanr(s["actual"], s[name])[0]
        else:
            row[name] = np.nan
    out.append(row)

out_df = pd.DataFrame(out)
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "47_nesting_offline_groups.csv")
out_df.to_csv(out_path, index=False)
print(f"wrote {len(out_df)} rows to {out_path}")
