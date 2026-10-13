"""Sensitivity check, progress and size baselines (post hoc, not predeclared): JPF built-in, JPFBar and Kilby WBE with and without the 4,054
zero-work childless states in the scoring (the predictions themselves are made on the full tree, as in fit_all_baselines_fair_comparison.py).
Usage: python zero_work_sensitivity_baselines.py > ../results/64_zero_work_sensitivity_baselines.txt"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average  
from fit_jpf_builtin_estimator_baseline import state_count_estimator_predictions  
from fit_jpfbar_baseline import jpfbar_predictions  
from fit_kilby_wbe_baseline import wbe_predictions  


def rows_for(df, fn):
    out = []
    for program, prog_df in df.groupby("program"):
        a, p, ids = fn(prog_df)
        g = prog_df["program_group"].iloc[0]
        out.append(pd.DataFrame({"program_group": g, "actual": a, "pred": p}))
    return pd.concat(out, ignore_index=True)


def macro(d):
    pg = {}
    for g, s in d.groupby("program_group"):
        if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s["actual"].nunique() > 1 and s["pred"].nunique() > 1:
            r, _ = spearmanr(s["actual"], s["pred"])
            if not np.isnan(r):
                pg[g] = r
    return macro_average(pg), len(pg)


df = load_all()
for name, fn in [("JPF built-in", state_count_estimator_predictions), ("JPFBar", jpfbar_predictions), ("Kilby WBE", wbe_predictions)]:
    d = rows_for(df, fn)
    a, na = macro(d)
    b, nb = macro(d[d["actual"] > 0])
    print(f"{name:14s} all rows: {a:+.3f} ({na} groups)   without zero-work rows: {b:+.3f} ({nb} groups)")
