"""Load-balance replay with the probing cost of Knuth weights charged (extension of load_balance_replay.py, same units, cut rule and seeds).

The 30 probes of every unit are counted as work: a probe's counterfactual live cost is the sum of the exclusive work c(v) = W(v) - sum of the
children's W over the nodes it visits (the definition of RQ4). Two ways of charging the total probing work P of all units of a configuration:
  * parallel: the probes are spread perfectly over the K workers, so the run takes P / K + makespan (an optimistic charge for probing);
  * serial: the probes run before the split on one worker, so the run takes P + makespan.
Reported as (charged run time) / (perfectly balanced work sum(W) / K), so 1.0 is a run with no imbalance and no probing.
Count and M5 weights need no probes and cost nothing here (their features are computed when a state is created).

Usage: python load_balance_probe_cost.py [units per worker = 4] [probes per unit = 30]"""
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.linear_model import LinearRegression

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, rank_biserial  
from fit_hybrid_model import M5_FEATURES, make_rf_factory 
from load_balance_replay import loo_predictions, lpt_makespan, N_PROBES, SEED  

KS = [4, 8]
UNITS_PER_WORKER = int(sys.argv[1]) if len(sys.argv) > 1 else 4
N_PROBES = int(sys.argv[2]) if len(sys.argv) > 2 else N_PROBES  # probes per unit; 30 is the setting of the paper


def main():
    df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
    nl = df[df["isEndStateAtEntry"] == False].copy()  
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    nl["p_rf"] = np.expm1(loo_predictions(nl, rf)).clip(lower=0)
    rows = []
    for prog, d in df.groupby("program"):
        g = d["program_group"].iloc[0]
        by = {r.stateId: r for r in d.itertuples()}
        kids = defaultdict(list)
        for r in d.itertuples():
            kids[r.parentId].append(r.stateId)
        roots = [i for i, r in by.items() if r.parentId not in by]
        level = {roots[0]: 0}
        for i in sorted(by):
            if i != roots[0]:
                level[i] = level[by[i].parentId] + 1
        excl = {i: by[i].actualSubtreeWork - sum(by[c].actualSubtreeWork for c in kids.get(i, [])) for i in by}
        sub = nl.loc[nl["program"] == prog]
        p_rf = dict(zip(sub["stateId"], sub["p_rf"]))
        size = {i: 1 for i in by}
        for i in sorted(by, reverse=True):
            if i != roots[0]:
                size[by[i].parentId] += size[i]
        nonleaf_by_level = defaultdict(list)
        for i, r in by.items():
            if not r.isEndStateAtEntry:
                nonleaf_by_level[level[i]].append(i)

        def probe(s, rng):
            cur, cum, prod, cost = s, 0.0, 1.0, 0.0
            while True:
                cost += excl[cur]
                if not kids.get(cur):
                    break
                prod *= len(kids[cur])
                cum += prod
                cur = kids[cur][rng.integers(0, len(kids[cur]))]
            return cum, cost

        for K in KS:
            lvl = next((l for l in sorted(nonleaf_by_level) if len(nonleaf_by_level[l]) >= UNITS_PER_WORKER * K), None)
            if lvl is None:
                continue
            units = sorted(nonleaf_by_level[lvl])
            W = np.array([by[u].actualSubtreeWork for u in units], dtype=float)
            if W.sum() == 0:
                continue
            ideal = W.sum() / K
            rng = np.random.default_rng(SEED)  # the same draws as load_balance_replay.py
            est, pc = [], 0.0
            for u in units:
                vals = [probe(u, rng) for _ in range(N_PROBES)]
                est.append(np.mean([v[0] for v in vals]))
                pc += sum(v[1] for v in vals)
            est = np.array(est)
            base = {"count": lpt_makespan(np.ones(len(units)), W, K) / ideal,
                    "M5 RF": lpt_makespan(np.array([p_rf[u] for u in units]), W, K) / ideal,
                    "oracle": lpt_makespan(W, W, K) / ideal}
            kn = lpt_makespan(est, W, K) / ideal
            base["Knuth, probing not charged"] = kn
            base["Knuth, probing spread over K workers"] = kn + pc / K / ideal
            base["Knuth, probing serial"] = kn + pc / ideal
            for k, v in base.items():
                rows.append({"K": K, "group": g, "program": prog, "sched": k, "cost": v, "probe_work_over_unit_work": pc / W.sum()})
    r = pd.DataFrame(rows)
    order = ["count", "M5 RF", "Knuth, probing not charged", "Knuth, probing spread over K workers", "Knuth, probing serial", "oracle"]
    for K in KS:
        rk = r[r["K"] == K]
        piv = rk.groupby(["sched", "group"])["cost"].mean().reset_index().pivot(index="group", columns="sched", values="cost")
        pw = rk.drop_duplicates("program").groupby("group")["probe_work_over_unit_work"].mean()
        print("=" * 96)
        print(f"K = {K}: {rk['program'].nunique()} configurations, {len(piv)} groups; probing work / total unit work: median {pw.median():.2f}x, mean {pw.mean():.2f}x")
        print(f"{'weights':<40}{'macro run time / ideal':>24}{'groups better than count':>28}")
        for n in order:
            d = piv[n] - piv["count"]
            better = f"{(d < 0).sum()} / worse {(d > 0).sum()}" if n != "count" else ""
            p = wilcoxon(d).pvalue if n != "count" and (d != 0).any() else float("nan")
            r_rb = rank_biserial(piv[n], piv["count"]) if n != "count" else float("nan")
            extra = (f"  p = {p:.3g}, rank-biserial r = {r_rb:+.2f}") if n != "count" else ""
            print(f"{n:<40}{piv[n].mean():>24.3f}{better:>22}{extra}")


if __name__ == "__main__":
    main()
