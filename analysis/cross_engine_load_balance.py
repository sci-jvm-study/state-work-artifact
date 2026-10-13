"""Load-balance replay (load_balance_replay.py, load_balance_probe_cost.py) on JPF's, COASTAL's and GDart's trees for the same programs.

Same decision, cut rule (shallowest level with >= 4K non-leaf states, K in {4, 8}), longest-weight-first assignment and outcome
(largest true worker work / balanced work) as load_balance_replay.py. Weights: count; Random Forest predictions (M3, dynamic
features, on all three engines; M5, static + dynamic, where static features exist) fitted leave-one-program-group-out on these
programs only; Knuth 30 probes with the probing cost not charged and charged (spread perfectly over the K workers); hindsight
subtree size; true work. Work units as in cross_engine_cost_and_cap.py. Each engine is replayed on all of its programs whose
tree has JPF's node count, with JPF on the same programs.

Usage: python cross_engine_load_balance.py"""
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross_engine_replication as cer  
from models_m1_to_m5 import rank_biserial  
from cross_engine_cost_and_cap import cap, exact_programs, M3, M5  
from load_balance_replay import lpt_makespan, N_PROBES, SEED  

KS = [4, 8]
UNITS_PER_WORKER = 4


def replay(df, models):
    preds = {}
    for name, feats in models:
        nl = cap(df, feats)
        preds[name] = {(p, s): max(v, 0.0) for p, s, v in zip(nl["program"], nl["stateId"], nl["raw"])}
    rows = []
    for prog, d in df.groupby("program"):
        g = d["program_group"].iloc[0]
        d = d.sort_values(["depth", "stateId"])
        by = {r.stateId: r for r in d.itertuples()}
        kids = defaultdict(list)
        for r in d.itertuples():
            kids[r.parentId].append(r.stateId)
        level, size = {}, {i: 1 for i in by}
        for i in by:
            level[i] = level[by[i].parentId] + 1 if by[i].parentId in level else 0
        for i in reversed(list(by)):
            if by[i].parentId in size:
                size[by[i].parentId] += size[i]
        excl = {i: max(0.0, by[i].actualSubtreeWork - sum(by[c].actualSubtreeWork for c in kids.get(i, []))) for i in by}
        by_level = defaultdict(list)
        for i, r in by.items():
            if not r.isEndStateAtEntry:
                by_level[level[i]].append(i)

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
            lvl = next((l for l in sorted(by_level) if len(by_level[l]) >= UNITS_PER_WORKER * K), None)
            if lvl is None:
                continue
            units = sorted(by_level[lvl])
            W = np.array([by[u].actualSubtreeWork for u in units], dtype=float)
            if W.sum() == 0:
                continue
            ideal = W.sum() / K
            rng = np.random.default_rng(SEED)
            est, pc = [], 0.0
            for u in units:
                vals = [probe(u, rng) for _ in range(N_PROBES)]
                est.append(np.mean([v[0] for v in vals]))
                pc += sum(v[1] for v in vals)
            res = {"count": lpt_makespan(np.ones(len(units)), W, K) / ideal}
            for name in preds:
                res[name + " RF"] = lpt_makespan(np.array([preds[name][(prog, u)] for u in units]), W, K) / ideal
            kn = lpt_makespan(np.array(est), W, K) / ideal
            res["Knuth 30, not charged"] = kn
            res["Knuth 30, charged (spread over K)"] = kn + pc / K / ideal
            res["hindsight size"] = lpt_makespan(np.array([size[u] for u in units], dtype=float), W, K) / ideal
            res["true work"] = lpt_makespan(W, W, K) / ideal
            for n, v in res.items():
                rows.append({"K": K, "group": g, "program": prog, "sched": n, "v": v})
    return pd.DataFrame(rows)


def report(label, df, models):
    print("=" * 100)
    print(label)
    r = replay(df, models)
    for K in KS:
        rk = r[r["K"] == K]
        piv = rk.groupby(["sched", "group"])["v"].mean().reset_index().pivot(index="group", columns="sched", values="v")
        print(f"K = {K}: {rk['program'].nunique()} configurations in {len(piv)} program groups have a level with >= {UNITS_PER_WORKER * K} non-leaf states")
        print(f"{'weights':<38}{'macro run time / ideal':>24}{'vs count: better / worse':>28}   p, rank-biserial r")
        for n in [c for c in rk["sched"].drop_duplicates()]:
            d = piv[n] - piv["count"]
            if n == "count":
                print(f"{n:<38}{piv[n].mean():>24.3f}")
                continue
            p = wilcoxon(d).pvalue if (d != 0).any() else float("nan")
            print(f"{n:<38}{piv[n].mean():>24.3f}{f'{(d < 0).sum()} / {(d > 0).sum()}':>28}   p = {p:.3g}, r = {rank_biserial(piv[n], piv['count']):+.2f}")
        print()


if __name__ == "__main__":
    # Each engine on all of its programs whose tree has JPF's node count (the replay needs large trees, which the three-engine
    # intersection of cross_engine_cost_and_cap.py drops), with JPF on the same programs.
    programs = exact_programs("data_coastal2")
    print(f"{len(programs)} programs with JPF's node count on COASTAL (depth-first)\n")
    report("JPF, on the COASTAL programs", cer.load(cer.JPF_DIR, programs), [("M3", M3), ("M5", M5)])
    report("COASTAL (depth-first)", cer.load(os.path.join(cer.ROOT, "engines", "data", "data_coastal2"), programs, coastal=True),
           [("M3", M3), ("M5", M5)])
    programs = exact_programs("data_gdart")
    print(f"{len(programs)} programs with JPF's node count on GDart\n")
    report("JPF, on the GDart programs", cer.load(cer.JPF_DIR, programs), [("M3", M3), ("M5", M5)])
    gd = cer.add_jpf_log_columns(cer.load(os.path.join(cer.ROOT, "engines", "data", "data_gdart"), programs))
    gd["threadCount"] = 1
    gd["actualSubtreeWork"] = gd["actualFullRunWork"]
    report("GDart (work = full run; M3 only)", gd, [("M3", M3)])
