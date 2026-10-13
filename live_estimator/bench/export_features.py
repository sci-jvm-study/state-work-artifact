"""Writes the M5 feature rows of the nine held-out programs (non-leaf states, no header) that ForestBench.java reads.

Usage: python export_features.py            # writes features.csv next to this file
       javac ForestBench.java
       java ForestBench ../model/m5_rf.bin features.csv      # model/ is made by ../export_rf.py"""
import glob
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURES = ["remainingBytecodesInMethod", "reachableBranchCount", "reachableLoopBackEdgeCount", "reachableVirtualCallCount",
            "reachableAllocSiteCount", "reachableAthrowCount", "choiceGeneratorTotal", "choiceGeneratorProcessed",
            "pathConditionSize", "threadCount"]

rows = []
for f in sorted(glob.glob(os.path.join(HERE, "..", "..", "heldout", "data", "*.csv"))):
    d = pd.read_csv(f)
    rows.append(d[~d.isEndStateAtEntry][FEATURES])
X = pd.concat(rows)
X.to_csv(os.path.join(HERE, "features.csv"), index=False, header=False)
print(len(X), "feature rows")
