"""Spread of subtree work between non-leaf states at the same depth of the same program configuration, for engine work
(actualSubtreeWork) and solver-call count (actualSolverCalls). Only states with a positive value are compared. For every
(program, depth) pair with at least two such states the ratio largest / smallest is computed; the script prints the number of
pairs, the share of pairs with a ratio above 10, the median and 90th percentile of the ratios, and the maximum with its program.
Backs the introduction's statement about states at the same depth.

Usage: python work_ratio_check.py"""
import numpy as np

from models_m1_to_m5 import load_all

df = load_all()
nl = df[df["isEndStateAtEntry"] == False] 
for col, label in (("actualSubtreeWork", "engine work"), ("actualSolverCalls", "solver calls")):
    ratios, where = [], []
    for (prog, depth), s in nl.groupby(["program", "depth"]):
        v = s[col][s[col] > 0]
        if len(v) > 1:
            ratios.append(v.max() / v.min())
            where.append((prog, int(depth)))
    r = np.array(ratios)
    i = int(r.argmax())
    print(f"{label}: {len(r)} (program, depth) pairs with >= 2 states; ratio > 10 in {(r > 10).sum()} ({100 * (r > 10).mean():.1f}%); "
          f"median {np.median(r):.2f}x, 90th percentile {np.percentile(r, 90):.1f}x, maximum {r[i]:.1f}x ({where[i][0]}, depth {where[i][1]})")
