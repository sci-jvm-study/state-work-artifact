"""Post hoc check on the held-out programs (not pre-registered): for how many non-leaf states of a held-out program the feature vector (the M5
static and dynamic features) also occurs among the training rows of the main corpus, and for how many the work equals that of a training row with
the same vector. It also gives the error of the frozen M5 Random Forest on each program, to show where exact predictions come from.

Usage: python heldout_feature_overlap.py"""
import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from prune import mark_pruned  
from models_m1_to_m5 import load_all  
from fit_hybrid_model import M5_FEATURES, make_rf_factory  

main_df = load_all()
nl = main_df[main_df["isEndStateAtEntry"] == False].copy()  
nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")()
rf.fit(nl[M5_FEATURES].values, nl["logWork"].values)
keys_train = list(map(tuple, nl[M5_FEATURES].round(6).values))
train_work = {}
for k, w in zip(keys_train, nl["actualSubtreeWork"]):
    train_work.setdefault(k, set()).add(w)
print(f"{'program':<38}{'n':>6}{'median |err|':>14}{'mean |err|':>12}{'|err|<0.01':>12}{'vector in training':>20}{'and same work':>15}")
for f in sorted(glob.glob(os.path.join(HERE, "..", "heldout", "data", "*.csv"))):
    d = mark_pruned(pd.read_csv(f))
    d = d[d["isEndStateAtEntry"] == False].copy()  
    d["logWork"] = np.log1p(d["actualSubtreeWork"])
    e = np.abs(rf.predict(d[M5_FEATURES].values) - d["logWork"].values) / np.log(10)
    keys = list(map(tuple, d[M5_FEATURES].round(6).values))
    seen = np.mean([k in train_work for k in keys])
    same = np.mean([(k in train_work) and (w in train_work[k]) for k, w in zip(keys, d["actualSubtreeWork"])])
    print(f"{os.path.basename(f)[2:-4][:36]:<38}{len(d):>6}{np.median(e):>14.3f}{e.mean():>12.3f}{np.mean(e < 0.01):>12.3f}{seen:>20.3f}{same:>15.3f}")
