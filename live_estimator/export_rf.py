"""Fit the frozen M5 Random Forest of heldout_eval.py and export it for the Java listener.

Binary layout (big-endian): magic 0x4D355246, nFeatures, nTrees; then per tree nNodes followed by the arrays
left[int32], right[int32], feature[int32], threshold[float64], value[float64] (scikit-learn tree_ arrays, leaves have left = -1).

Usage: python export_rf.py"""
import os
import sys

import joblib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.join(HERE, "..", "analysis")
sys.path.insert(0, ANALYSIS)
from models_m1_to_m5 import load_all  
from fit_hybrid_model import M5_FEATURES, make_rf_factory  

OUT = os.path.join(HERE, "model")
os.makedirs(OUT, exist_ok=True)

df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
nl = df[df["isEndStateAtEntry"] == False].copy()  
nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
print(f"fitting on {len(nl)} non-leaf rows, {nl['program_group'].nunique()} groups, features {M5_FEATURES}")

rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")()
rf.fit(nl[M5_FEATURES].values, nl["logWork"].values)
joblib.dump(rf, os.path.join(OUT, "m5_rf.joblib"))

with open(os.path.join(OUT, "m5_rf.bin"), "wb") as f:
    f.write(np.array([0x4D355246, len(M5_FEATURES), len(rf.estimators_)], dtype=">i4").tobytes())
    total_nodes, max_depth = 0, 0
    for est in rf.estimators_:
        t = est.tree_
        f.write(np.array([t.node_count], dtype=">i4").tobytes())
        f.write(t.children_left.astype(">i4").tobytes())
        f.write(t.children_right.astype(">i4").tobytes())
        f.write(t.feature.astype(">i4").tobytes())
        f.write(t.threshold.astype(">f8").tobytes())
        f.write(t.value[:, 0, 0].astype(">f8").tobytes())
        total_nodes += t.node_count
        max_depth = max(max_depth, t.max_depth)
with open(os.path.join(OUT, "m5_rf_features.txt"), "w") as f:
    f.write("\n".join(M5_FEATURES) + "\n")
print(f"exported {len(rf.estimators_)} trees, {total_nodes} nodes, max tree depth {max_depth}, "
      f"{os.path.getsize(os.path.join(OUT, 'm5_rf.bin')) / 1e6:.1f} MB")
