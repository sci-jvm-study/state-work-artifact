"""Depth rule (post hoc): the rule "the deeper the state, the less work" with no fitting,
prediction = -depth. Macro Spearman rho over the scoreable program groups, on the populations of the paper: P55 (default scoreable), P29 (history
eligible, the groups Group C and M6 score), and the nine held-out programs (P9). Also prints M1 (depth, fitted by LOPO) for comparison.

Usage: python depth_rule.py"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, run_lopo, macro_average, bootstrap_macro_ci, MIN_ROWS_FOR_GROUP_RHO, FEATURE_GROUPS
from fit_hybrid_model import attach_group_c_predictions, eligible_groups  
from sklearn.linear_model import LinearRegression  


def rho_groups(df, groups):
    out = {}
    for g in groups:
        s = df[df.program_group == g]
        if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s.actualSubtreeWork.nunique() > 1 and s.depth.nunique() > 1:
            out[g] = spearmanr(s.actualSubtreeWork, -s.depth)[0]
    return out


df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
nl = df[df.isEndStateAtEntry == False].copy()  
nl["logWork"] = np.log1p(nl.actualSubtreeWork)
groups = sorted(nl.program_group.unique())

p55 = rho_groups(nl, groups)
nl2, _ = attach_group_c_predictions(nl.copy())
elig = eligible_groups(nl2.dropna(subset=["groupC_pred"]))
p29 = {g: v for g, v in p55.items() if g in elig}
m1 = run_lopo(nl, groups, FEATURE_GROUPS["M1_depth_only"], model_factory=LinearRegression)["per_group_rho"]

held = {}
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "heldout", "data", "*.csv"))):
    d = pd.read_csv(f)
    d = d[~d.isEndStateAtEntry]
    name = os.path.basename(f)[:-4]
    if len(d) >= MIN_ROWS_FOR_GROUP_RHO and d.actualSubtreeWork.nunique() > 1:
        held[name] = spearmanr(d.actualSubtreeWork, -d.depth)[0]

for label, res in (("depth rule, P55", p55), ("depth rule, P29", p29), ("depth rule, P9 (nine held-out programs)", held),
                   ("M1 (depth, fitted by LOPO), P55", m1)):
    lo, hi = bootstrap_macro_ci(res)
    print(f"{label:48s} groups={len(res):3d}  macro rho = {macro_average(res):+.3f}  [{lo:+.3f}, {hi:+.3f}]")
print("\nper group, depth rule, P55: negative in", sum(v < 0 for v in p55.values()), "of", len(p55), "groups")
print("share of groups with rho > 0.5:", round(float(np.mean([v > 0.5 for v in p55.values()])), 2), f"({sum(v > 0.5 for v in p55.values())} of {len(p55)} groups)")

# Random Forest on the four dynamic features (M3-RF), leave-one-program-out, for the same population
from fit_hybrid_model import make_rf_factory  
m3rf = run_lopo(nl, groups, FEATURE_GROUPS["M3_dynamic_only"], model_factory=make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt"))["per_group_rho"]
lo, hi = bootstrap_macro_ci(m3rf)
print(f"{'M3 Random Forest (LOPO), P55':48s} groups={len(m3rf):3d}  macro rho = {macro_average(m3rf):+.3f}  [{lo:+.3f}, {hi:+.3f}]")
