"""Sensitivity check, history-based models (post hoc): the same question as zero_work_sensitivity.py, for Group C, M6 Random Forest,
the imputed M6 and the gated M6-RF/M5-RF combination. The models are fit exactly as in fit_m6_imputation_comparison.py (all rows, same protocol);
only the scoring changes: each group is rescored on the rows that have a recorded child (the 4,054 childless zero-work rows left out).
With DROP_ZERO_WORK=1 the rows are instead left out of everything: training, Group C's sibling means and scoring (a second analysis; the rows of
the two analyses are then the same, so the two columns printed are equal).
Usage: python zero_work_sensitivity_history.py > ../results/63_zero_work_sensitivity_history.txt
       DROP_ZERO_WORK=1 python zero_work_sensitivity_history.py > ../results/63b_zero_work_dropped_history.txt"""
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, run_lopo, macro_average, MIN_ROWS_FOR_GROUP_RHO  
from fit_hybrid_model import attach_group_c_predictions, eligible_groups, M5_FEATURES, M6_FEATURES, make_rf_factory  

df = load_all()
nl = df[df["isEndStateAtEntry"] == False].copy()  
nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
has_child = set(zip(df.program, df.parentId))
nl["haskid"] = [(p, s) in has_child for p, s in zip(nl.program, nl.stateId)]
DROP = os.environ.get("DROP_ZERO_WORK") == "1"  # 1: leave the rows out of training, Group C and scoring alike (second analysis)
if DROP:
    nl = nl[nl.haskid].copy()
nl, _ = attach_group_c_predictions(nl)
rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
all_groups = sorted(nl.program_group.unique())


def attach(res, data, groups, col):
    """put the LOPO predictions back on the rows (run_lopo visits groups in the given order, rows in data order)"""
    out = []
    for g in groups:
        sub = data[data.program_group == g]
        if len(data[data.program_group != g]) >= 3 and len(sub):
            out.append(sub.index.to_series())
    idx = np.concatenate([s.values for s in out])
    assert len(idx) == len(res["preds"])
    data.loc[idx, col] = res["preds"]


def macro(data, col, groups=None):
    out = {}
    for g, s in data.groupby("program_group"):
        if groups is not None and g not in groups:
            continue
        s = s.dropna(subset=[col])
        if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s.logWork.nunique() > 1 and s[col].nunique() > 1:
            out[g] = spearmanr(s.logWork, s[col])[0]
    return out


scored = nl.dropna(subset=["groupC_pred"]).copy()
elig = eligible_groups(scored)
scored_elig = scored[scored.program_group.isin(elig)].copy()
r = run_lopo(scored_elig, elig, M6_FEATURES, model_factory=rf)
attach(r, scored_elig, elig, "m6rf")

imp = nl.copy()
imp["groupC_pred"] = imp["groupC_pred"].fillna(nl["groupC_pred"].median())
r = run_lopo(imp, all_groups, M6_FEATURES, model_factory=rf)
attach(r, nl, all_groups, "m6imp")
r = run_lopo(nl, all_groups, M5_FEATURES, model_factory=rf)
attach(r, nl, all_groups, "m5rf")
# gated: M6-RF prediction on eligible groups, M5-RF elsewhere (per group, so ranks are within one group)
nl["m6rf"] = scored_elig["m6rf"]
nl["gated"] = np.where(nl.program_group.isin(elig), nl["m6rf"], nl["m5rf"])

for name, col, groups in [(f"Group C (P{len(elig)})", "groupC_pred", elig), (f"M6 Random Forest (P{len(elig)})", "m6rf", elig),
                          ("M6 RF, imputed history (P55)", "m6imp", None), ("M5 Random Forest (P55)", "m5rf", None),
                          ("Gated M6-RF / M5-RF (P55)", "gated", None)]:
    a = macro(nl, col, groups)
    b = macro(nl[nl.haskid], col, groups)
    print(f"{name:32s} all rows: {macro_average(a):+.3f} ({len(a)} groups)   without zero-work childless rows: {macro_average(b):+.3f} ({len(b)} groups)")
