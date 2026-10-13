"""Larger trees: the parameter-free estimators on the programs of the large set (PREDECLARATION.md), reported per program.

Uses the code of the main analysis (../analysis) and the kept runs of the sweep (kept/, or --kept). A program belongs to the large set if its
kept run has at least 5,000 states.

Usage: python eval_large.py [--kept kept] > results_large.txt
"""
import argparse
import os
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "analysis"))
import models_m1_to_m5 as fp
from fit_group_c_baseline import recursive_estimator_predictions_with_ids
from fit_knuth_probing_baseline import knuth_probe_predictions
from fit_knuth_online_cost_analysis import own_step_cost_map
from fit_node_count_baseline import compute_node_counts

MIN_STATES = 5000
ap = argparse.ArgumentParser()
ap.add_argument("--kept", default=os.path.join(HERE, "kept"))
args = ap.parse_args()

tmp = tempfile.mkdtemp()
chosen = []
for f in sorted(os.listdir(args.kept)):
    if not f.endswith(".csv"):
        continue
    name = f[:-4]
    n = sum(1 for _ in open(os.path.join(args.kept, f), encoding="utf-8")) - 1
    if n >= MIN_STATES:
        fam = "synthetic"
        for cat in ("real-world", "sv-comp", "synthetic"):
            if os.path.exists(os.path.join(HERE, "..", "data", cat, name + ".csv")):
                fam = cat
        os.makedirs(os.path.join(tmp, fam), exist_ok=True)
        shutil.copyfile(os.path.join(args.kept, f), os.path.join(tmp, fam, f))
        chosen.append(name)
fp.DATA_DIR = tmp
df = fp.load_all()
shutil.rmtree(tmp, ignore_errors=True)
print(f"large set: {len(chosen)} programs with at least {MIN_STATES} states: {chosen}\n")

df = compute_node_counts(df)
rho = lambda a, b: float(spearmanr(a, b)[0])
rng = np.random.default_rng(42)
for name in chosen:
    sub = df[df.program == name].reset_index(drop=True)
    nl = sub[sub.isEndStateAtEntry == False]
    w = nl.actualSubtreeWork.values.astype(float)
    print(f"=== {name}: {len(sub)} states, {len(nl)} non-leaf states, max depth {int(sub.depth.max())}")
    print(f"  live count (state id)            rho = {rho(nl.stateId, w):+.3f}")
    print(f"  final subtree size N(s)          rho = {rho(nl.nodeCount, w):+.3f}")
    print(f"  depth rule (-depth, post hoc)    rho = {rho(-nl.depth, w):+.3f}")
    a, p, _ = recursive_estimator_predictions_with_ids(nl)
    print(f"  sibling mean (Group C)           rho = {rho(a, p):+.3f}  on {len(a)} states")
    a, p, _ = knuth_probe_predictions(sub, rng)
    print(f"  Knuth probing, 30 probes         rho = {rho(a, p):+.3f}")
    by_id, children, own_cost = own_step_cost_map(sub)
    ratios = []
    for sid in nl.stateId:
        actual = by_id[sid]["actualSubtreeWork"]
        if actual <= 0:
            continue
        tot = 0.0
        for _ in range(30):
            cur, cost = int(sid), own_cost[int(sid)]
            while True:
                kids = children.get(cur, [])
                if not kids:
                    break
                cur = kids[rng.integers(0, len(kids))]
                cost += own_cost[cur]
            tot += cost
        ratios.append(tot / actual)
    r = np.array(ratios)
    print(f"  30-probe cost / work of the state: median {np.median(r):.2f}x, share of states where probing costs more than exploring "
          f"{100 * np.mean(r > 1):.1f}%  ({len(r)} states with work > 0)\n")
