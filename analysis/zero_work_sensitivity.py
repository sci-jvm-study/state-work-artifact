"""Sensitivity check (post hoc, not predeclared): do the main P55 macro-rho numbers change if the 4,054 zero-work childless states
(results/61) are left out of the scoring? Groups are rescored on the remaining rows (same rules: >= 5 rows, non-constant values).
Estimators: the live count (state-creation order), the depth rule rule, and M5 Random Forest raw and capped, using its own
leave-one-program-out predictions (RF, max_features sqrt). Capping follows the parent chain.
Usage: python zero_work_sensitivity.py > ../results/62_zero_work_sensitivity.txt"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, macro_average, MIN_ROWS_FOR_GROUP_RHO  

HERE = os.path.dirname(os.path.abspath(__file__))
df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
nl = df[df.isEndStateAtEntry == False].copy() 
haskid = set(zip(df.program, df.parentId))
nl["haskid"] = [(p, s) in haskid for p, s in zip(nl.program, nl.stateId)]
from fit_hybrid_model import M5_FEATURES, make_rf_factory  
from models_m1_to_m5 import run_lopo  
nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
all_groups = sorted(nl.program_group.unique())
res = run_lopo(nl, all_groups, M5_FEATURES, model_factory=make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt"))
order = np.concatenate([nl[nl.program_group == g].index.values for g in all_groups if len(nl[nl.program_group != g]) >= 3 and (nl.program_group == g).any()])
assert len(order) == len(res["preds"])
nl.loc[order, "stage0"] = res["preds"]
assert nl.stage0.notna().all()

# capped prediction: min(own, parent's capped), parents are processed first (lower stateId)
cap = {}
for p, g in nl.sort_values(["program", "stateId"]).groupby("program"):
    for sid, par, pred in zip(g.stateId, g.parentId, g.stage0):
        cap[(p, sid)] = min(pred, cap.get((p, par), np.inf))
nl["capped"] = [cap[(p, s)] for p, s in zip(nl.program, nl.stateId)]

methods = {"live count (creation order)": nl.stateId, "-depth": -nl.depth, "M5-RF raw": nl.stage0, "M5-RF capped": nl.capped}


def macro(d, col):
    out = {}
    for g, s in d.groupby("program_group"):
        if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s.actualSubtreeWork.nunique() > 1 and s[col].nunique() > 1:
            out[g] = spearmanr(s.actualSubtreeWork, s[col])[0]
    return macro_average(out), len(out)


for name, col in methods.items():
    nl["_m"] = col.values
    a, na = macro(nl, "_m")
    b, nb = macro(nl[nl.haskid], "_m")
    print(f"{name:30s} all rows: {a:+.3f} ({na} groups)   without zero-work childless rows: {b:+.3f} ({nb} groups)")
