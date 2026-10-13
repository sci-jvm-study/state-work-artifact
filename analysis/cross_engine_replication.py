"""
Cross-engine replication: does the paper's core picture hold on a second, architecturally different
Java symbolic-execution engine (COASTAL, concolic, own bytecode instrumentation, Z3 via SMT-LIB), on the SAME programs?

Reuses the paper's own pipeline pieces so nothing is re-implemented differently between engines:
  load_all / program_group_of / macro_average / bootstrap_macro_ci / MIN_ROWS_FOR_GROUP_RHO  (models_m1_to_m5)
  recursive_estimator_predictions_with_ids                                              (fit_group_c_baseline, Group C)
  knuth_probe_predictions                                                               (fit_knuth_probing_baseline)
Only models_m1_to_m5.DATA_DIR is redirected to point at each engine's tree CSVs.

For every method the target is actualSubtreeWork: JPF = counter delta between state entry and backtrack (as in the
paper); COASTAL = sum over runs through the node of the instructions executed from the node's deciding branch to the
end of the run (engines/build_trees.py). Methods (all use only information available in the paper's protocol):
  floor      live visitation-order rank (stateId) vs work        [RQ1]
  hindsight  subtree node count N(s) vs work (not deployable)     [RQ1 hindsight check]
  groupC     mean work of already-explored siblings               [history]
  knuth30    Knuth 1975 random probing, 30 probes, seed 42        [probing, offline replay]
Aggregation identical to the paper: per-program-group Spearman rho over non-leaf rows, groups with >= 5 rows and
non-constant actual/predicted, macro mean, group-bootstrap 95% CI.

Usage: python cross_engine_replication.py [--work suffix|full] [--subset all|exact]
"""
import argparse
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
import models_m1_to_m5 as fp  
from models_m1_to_m5 import MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci  
from fit_group_c_baseline import recursive_estimator_predictions_with_ids 
import fit_knuth_probing_baseline as kb  
import fit_jpf_builtin_estimator_baseline as bi  
import fit_jpfbar_baseline as jb  
import fit_kilby_wbe_baseline as kw 

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
JPF_DIR = os.path.join(ROOT, "data")
COASTAL_DIR = os.path.join(ROOT, "engines", "data", "data_coastal")
STATUS_CSV = os.path.join(ROOT, "engines", "run_status.csv")


def add_jpf_log_columns(df):
    """Derive JPF's per-state log columns from a COASTAL tree (see module docstring)."""
    df = df.copy()
    df["depth"] = df["depth"] + 1
    tot, proc = {}, {}
    for program, pdf in df.groupby("program"):
        kids = {}
        for r in pdf.sort_values("stateId").itertuples():
            kids.setdefault(int(r.parentId), []).append(int(r.stateId))
        for parent, ks in kids.items():
            for rank, sid in enumerate(ks, start=1):
                tot[(program, sid)] = 1 if parent == -1 else len(ks)
                proc[(program, sid)] = rank
    keys = list(zip(df["program"], df["stateId"].astype(int)))
    df["choiceGeneratorTotal"] = [tot[k] for k in keys]
    df["choiceGeneratorProcessed"] = [proc[k] for k in keys]
    return df


STATIC_COLS = ["remainingBytecodesInMethod", "reachableBranchCount", "reachableLoopBackEdgeCount",
               "reachableVirtualCallCount", "reachableAllocSiteCount", "reachableAthrowCount"]


def add_static_columns(df, back_if=False):
    """Six static lookahead features for COASTAL nodes from the node's program counter (engines/static_features.py,
    a port of jpf-symbc's StaticLookahead validated in engines/validate_static.py); -1 for leaves. threadCount = 1."""
    sys.path.insert(0, os.path.join(ROOT, "engines"))
    from static_features import ProgramStatics
    df = df.copy()
    cache, vals = {}, {c: [] for c in STATIC_COLS}
    for prog, pc in zip(df["program"], df["pcInstrChain"]):
        if prog not in cache:
            cache[prog] = ProgramStatics(os.path.join(ROOT, "engines", "runs", prog, "bin"), prog)
        for c, v in zip(STATIC_COLS, cache[prog].features(int(pc), back_if=back_if)):
            vals[c].append(v)
    for c in STATIC_COLS:
        df[c] = vals[c]
    df["threadCount"] = 1
    return df


def load(data_dir, programs, coastal=False):
    fp.DATA_DIR = data_dir
    df = fp.load_all()
    df = df[df["program"].isin(programs)].copy()
    if not coastal:
        return df
    df = add_jpf_log_columns(df)
    return add_static_columns(df) if "pcInstrChain" in df.columns else df


def subtree_sizes(prog_df):
    """N(s): number of nodes in the subtree rooted at each state, deepest-first accumulation."""
    size = {int(s): 1 for s in prog_df["stateId"]}
    parent = {int(r.stateId): int(r.parentId) for r in prog_df.itertuples()}
    for sid in sorted(size, key=lambda s: -int(prog_df.loc[prog_df.stateId == s, "depth"].iloc[0])):
        p = parent[sid]
        if p in size:
            size[p] += size[sid]
    return size


def predictions(df):
    """Per-row predictions for the four methods, on non-leaf rows, computed program by program."""
    rows = []
    rng = np.random.default_rng(kb.SEED)
    for program, pdf in df.groupby("program"):
        group = pdf["program_group"].iloc[0]
        sizes = subtree_sizes(pdf)
        actual_by_id = {int(r.stateId): float(r.actualSubtreeWork) for r in pdf.itertuples()}
        _, gc_pred, gc_ids = recursive_estimator_predictions_with_ids(pdf)
        gc = {int(i): float(p) for i, p in zip(gc_ids, gc_pred)}
        k_actual, k_pred, k_ids = kb.knuth_probe_predictions(pdf, rng)
        kn = {int(i): float(p) for i, p in zip(k_ids, k_pred)}
        _, bp, bids = bi.state_count_estimator_predictions(pdf)
        bi_d = {int(i): float(p) for i, p in zip(bids, bp)}
        _, jp, jids = jb.jpfbar_predictions(pdf)
        jb_d = {int(i): float(p) for i, p in zip(jids, jp)}
        _, wp, wids = kw.wbe_predictions(pdf)
        kw_d = {int(i): float(p) for i, p in zip(wids, wp)}
        for r in pdf[pdf["isEndStateAtEntry"] == False].itertuples():
            sid = int(r.stateId)
            rows.append({
                "program": program, "program_group": group, "stateId": sid, "actual": actual_by_id[sid],
                "floor": float(sid), "hindsight": float(sizes[sid]),
                "groupC": gc.get(sid, np.nan), "knuth30": kn.get(sid, np.nan),
                "jpfbuiltin": bi_d.get(sid, np.nan), "jpfbar": jb_d.get(sid, np.nan), "kilby": kw_d.get(sid, np.nan),
            })
    return pd.DataFrame(rows)


def group_rhos(pred, method):
    per = {}
    sub_all = pred.dropna(subset=[method])
    for g, sub in sub_all.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO or sub["actual"].nunique() < 2 or sub[method].nunique() < 2:
            continue
        r, _ = spearmanr(sub["actual"], sub[method])
        if not np.isnan(r):
            per[g] = r
    return per


def report(label, pred, methods):
    out = {}
    print(f"--- {label}: {pred['program'].nunique()} programs, {pred['program_group'].nunique()} groups, "
          f"{len(pred)} non-leaf rows")
    for m in methods:
        per = group_rhos(pred, m)
        macro = macro_average(per)
        lo, hi = bootstrap_macro_ci(per)
        print(f"   {m:<10} macro rho = {macro:6.3f}  [{lo:7.3f},{hi:7.3f}]  scoreable groups = {len(per)}")
        out[m] = per
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="suffix", choices=["suffix", "full"])
    ap.add_argument("--subset", default="all", choices=["all", "exact"])
    ap.add_argument("--coastal", default="data_coastal", help="data_coastal | data_coastal_BF | data_coastal_RAND")
    a = ap.parse_args()
    ENGINE = "GDart" if "gdart" in a.coastal else "COASTAL"
    COASTAL_DIR = os.path.join(ROOT, "engines", "data", a.coastal)
    STATUS_CSV = os.path.join(ROOT, "engines", "run_status_" + a.coastal + ".csv")

    st = pd.read_csv(STATUS_CSV)
    clean = st[st["status"] == "clean"]
    print(f"{ENGINE} runs: {len(st)} programs; clean = {len(clean)}; excluded = {len(st) - len(clean)}")
    for r in st[st["status"] != "clean"].itertuples():
        print(f"   excluded {r.program}: {r.status}")
    if a.subset == "exact":
        clean = clean[clean["nodes"] == clean["jpf_states"]]
    programs = set(clean["program"])
    print(f"analysis set ({a.subset} tree-size agreement): {len(programs)} programs\n")

    jpf = load(JPF_DIR, programs)
    coa = load(COASTAL_DIR, programs, coastal=True)
    if a.work == "full":
        coa = coa.copy()
        coa["actualSubtreeWork"] = coa["actualFullRunWork"]

    methods = ["floor", "hindsight", "jpfbuiltin", "jpfbar", "kilby", "groupC", "knuth30"]
    pj = predictions(jpf)
    pc = predictions(coa)
    rj = report("JPF (same programs)", pj, methods)
    rc = report(f"{ENGINE} (work = {a.work})", pc, methods)

    print("\nSame-group comparison (macro over the groups scoreable in BOTH engines, identical group set):")
    print(f"   {'method':<10}{'n_groups':>9}{'JPF macro [CI]':>24}{ENGINE + ' macro [CI]':>24}{'paired Wilcoxon p':>19}")
    from scipy.stats import wilcoxon
    for m in methods:
        shared = sorted(set(rj[m]) & set(rc[m]))
        if not shared:
            continue
        aj = {g: rj[m][g] for g in shared}
        ac = {g: rc[m][g] for g in shared}
        lj, hj = bootstrap_macro_ci(aj)
        lc, hc = bootstrap_macro_ci(ac)
        d = np.array([aj[g] - ac[g] for g in shared])
        pw = wilcoxon(d).pvalue if np.any(d != 0) and len(d) >= 5 else float("nan")
        print(f"   {m:<10}{len(shared):>9}{macro_average(aj):>10.3f} [{lj:5.2f},{hj:5.2f}]"
              f"{macro_average(ac):>10.3f} [{lc:5.2f},{hc:5.2f}]{pw:>19.3f}")

    print("\nPer-group agreement between engines (Spearman of per-group rho over shared scoreable groups):")
    for m in methods:
        shared = sorted(set(rj[m]) & set(rc[m]))
        if len(shared) >= 4:
            r, _ = spearmanr([rj[m][g] for g in shared], [rc[m][g] for g in shared])
            print(f"   {m:<10} n_shared_groups = {len(shared):>2}   rho(JPF_rho, {ENGINE}_rho) = {r:5.2f}")
