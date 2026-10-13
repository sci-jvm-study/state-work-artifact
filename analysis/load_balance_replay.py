"""Downstream decision check: splitting the search among K parallel workers by per-state work estimates (replay on recorded trees).

The decision. Parallel symbolic execution partitions the open subtrees of a search among K workers; the run ends when the slowest
worker ends. A partitioner that counts treats every open state as the same amount of work; one that estimates work weights each
state by its predicted subtree work. This script replays that decision on the recorded trees of every configuration.

Set-up (fixed before looking at any result). Cut: the shallowest level of the tree (states at equal distance from the root) with
at least 4K non-leaf states; the non-leaf states at that level are the units to be assigned (leaves have no further work and are
recognised as leaves when entered). A configuration with no such level is not used. Assignment: longest-processing-time-first
(units sorted by decreasing weight, each given to the worker with the smallest weight sum so far), weights below. Outcome: the
makespan, the largest TRUE subtree work (instructions) among the workers, divided by the perfectly balanced value (sum of the
units' work / K); 1.0 is perfect and larger is worse. The work before the cut is common to all partitioners and not counted;
communication and re-execution costs are not modelled.

Weights: count (every unit 1; what counting assumes); random (random weights, mean of 20 seeds); M5 linear and M5 RF (predicted
subtree work of the unit from the leave-one-program-group-out models on static features and depth; known when the state is
entered); Knuth (mean of 30 random-descent estimates of the subtree size; the probing cost is NOT charged here, unlike in the
paper's cost analysis); hindsight size (true number of states in the subtree, needs the finished exploration); oracle (true
subtree work, a bound that this assignment rule can reach).
Configurations are averaged within their program group, then over groups (macro); paired tests are Wilcoxon signed-rank on the
group values, two-sided.

Usage: python load_balance_replay.py [units per worker = 4]"""
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.linear_model import LinearRegression

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import load_all, rank_biserial  
from fit_hybrid_model import M5_FEATURES, make_rf_factory  
KS = [4, 8]
UNITS_PER_WORKER = int(sys.argv[1]) if len(sys.argv) > 1 else 4  # primary setting 4 (fixed in advance); 2 and 8 are sensitivity checks
N_RANDOM = 20
N_PROBES = 30
SEED = 42


def loo_predictions(nl, factory):
    pred = pd.Series(index=nl.index, dtype=float)
    for g in nl["program_group"].unique():
        tr, te = nl[nl["program_group"] != g], nl[nl["program_group"] == g]
        m = factory()
        m.fit(tr[M5_FEATURES].values, tr["logWork"].values)
        pred.loc[te.index] = m.predict(te[M5_FEATURES].values)
    return pred


def lpt_makespan(weights, true_work, K):
    """Assign units by longest-weight-first to the least-loaded worker (loaded by weight); return the true makespan."""
    order = np.argsort(-np.asarray(weights, dtype=float), kind="stable")
    load_w = np.zeros(K)
    load_t = np.zeros(K)
    for i in order:
        k = int(np.argmin(load_w))
        load_w[k] += weights[i]
        load_t[k] += true_work[i]
    return load_t.max()


def main():
    df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
    nl = df[df["isEndStateAtEntry"] == False].copy()
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    nl["p_lin"] = np.expm1(loo_predictions(nl, LinearRegression)).clip(lower=0)
    nl["p_rf"] = np.expm1(loo_predictions(nl, rf)).clip(lower=0)

    names = ["count", "random", "M5 linear", "M5 RF", "Knuth 30", "hindsight size", "oracle"]
    rows = []
    used = defaultdict(int)
    for prog, d in df.groupby("program"):
        g = d["program_group"].iloc[0]
        by = {r.stateId: r for r in d.itertuples()}
        kids = defaultdict(list)
        for r in d.itertuples():
            kids[r.parentId].append(r.stateId)
        roots = [i for i, r in by.items() if r.parentId not in by]
        assert len(roots) == 1
        level = {roots[0]: 0}
        for i in sorted(by):  # parents have smaller ids than children
            if i != roots[0]:
                level[i] = level[by[i].parentId] + 1
        size = {i: 1 for i in by}
        for i in sorted(by, reverse=True):
            if i != roots[0]:
                size[by[i].parentId] += size[i]
        sub = nl.loc[nl["program"] == prog]
        p_lin, p_rf = dict(zip(sub["stateId"], sub["p_lin"])), dict(zip(sub["stateId"], sub["p_rf"]))
        nonleaf_by_level = defaultdict(list)
        for i, r in by.items():
            if not r.isEndStateAtEntry:
                nonleaf_by_level[level[i]].append(i)

        def probe(s, rng):
            cur, cum, prod = s, 0.0, 1.0
            while kids.get(cur):
                prod *= len(kids[cur])
                cum += prod
                cur = kids[cur][rng.integers(0, len(kids[cur]))]
            return cum

        for K in KS:
            lvl = next((l for l in sorted(nonleaf_by_level) if len(nonleaf_by_level[l]) >= UNITS_PER_WORKER * K), None)
            if lvl is None:
                continue
            units = sorted(nonleaf_by_level[lvl])
            W = np.array([by[u].actualSubtreeWork for u in units], dtype=float)
            if W.sum() == 0:
                continue
            ideal = W.sum() / K
            rng = np.random.default_rng(SEED)
            wts = {"count": np.ones(len(units)),
                   "M5 linear": np.array([p_lin[u] for u in units]), "M5 RF": np.array([p_rf[u] for u in units]),
                   "Knuth 30": np.array([np.mean([probe(u, rng) for _ in range(N_PROBES)]) for u in units]),
                   "hindsight size": np.array([size[u] for u in units], dtype=float), "oracle": W}
            res = {n: lpt_makespan(w, W, K) / ideal for n, w in wts.items()}
            res["random"] = np.mean([lpt_makespan(np.random.default_rng(s).random(len(units)), W, K) / ideal for s in range(N_RANDOM)])
            for n in names:
                rows.append({"K": K, "group": g, "program": prog, "sched": n, "imbalance": res[n], "units": len(units)})
            used[K] += 1
    r = pd.DataFrame(rows)
    for K in KS:
        rk = r[r["K"] == K]
        grp = rk.groupby(["sched", "group"])["imbalance"].mean().reset_index()
        piv = grp.pivot(index="group", columns="sched", values="imbalance")
        print("=" * 100)
        print(f"K = {K} workers: {used[K]} configurations in {len(piv)} program groups have a level with >= {UNITS_PER_WORKER * K} non-leaf states "
              f"(median {rk.drop_duplicates('program')['units'].median():.0f} units)")
        print(f"{'weights':<16}{'macro imbalance':>17}{'median over groups':>20}{'share of groups <= 1.25':>25}")
        for n in names:
            v = piv[n]
            print(f"{n:<16}{v.mean():>17.3f}{v.median():>20.3f}{100 * (v <= 1.25).mean():>24.0f}%")
        print("\nPaired comparison (imbalance, lower is better; difference = first minus second), groups better/worse for the first:")
        for a, b in [("M5 RF", "count"), ("M5 linear", "count"), ("Knuth 30", "count"), ("hindsight size", "count"),
                     ("random", "count"), ("M5 RF", "M5 linear"), ("oracle", "M5 RF")]:
            diff = piv[a] - piv[b]
            p = wilcoxon(diff).pvalue if (diff != 0).any() else float("nan")
            r_rb = rank_biserial(piv[a], piv[b])  # standard sign: positive r means a (first-named) tends to be HIGHER-valued than b (here, imbalance, so positive = a worse)
            print(f"  {a:<15} vs {b:<10} mean difference {diff.mean():+.3f}, better {(diff < 0).sum()} / worse {(diff > 0).sum()}, p = {p:.3g}, rank-biserial r = {r_rb:+.2f}")
    print("\n(imbalance = largest true worker load / perfectly balanced load; 1.000 is perfect)")


if __name__ == "__main__":
    main()
