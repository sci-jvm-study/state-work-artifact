"""heldout_eval.py on the held-out programs whose COASTAL and GDart trees have exactly the node count of the JPF tree (4 of the 9; the other 5 are
not covered by the engines, so a comparison with models fitted on JPF tree structure would not be fair). Data: ../heldout/data (JPF),
../heldout/data_coastal and ../heldout/data_gdart.

choiceGeneratorTotal and choiceGeneratorProcessed (M3) are synthesized from the sibling structure, as cross_engine_replication.add_jpf_log_columns
does for the main corpus. The static features (M5 and M6, COASTAL only) use the port of the static lookahead of jpf-symbc
(engines/static_features.py) over the pcInstrChain of the node, evaluated against the COASTAL binaries in ../heldout/coastal_bin/<Program>/bin.
GDart has no static features, so only dynamic features are used there.

Usage: python heldout_eval_other_engines.py <jpf|coastal|gdart>"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINES = os.path.join(HERE, "..", "engines")
sys.path.insert(0, HERE)
sys.path.insert(0, ENGINES)
from prune import mark_pruned  
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci, FEATURE_GROUPS  
from fit_hybrid_model import attach_group_c_predictions, eligible_groups, make_rf_factory  
from fit_jpf_builtin_estimator_baseline import state_count_estimator_predictions 
from fit_jpfbar_baseline import jpfbar_predictions  
from fit_knuth_probing_baseline import knuth_probe_predictions 
from fit_kilby_wbe_baseline import wbe_predictions  
from fit_group_c_baseline import recursive_estimator_predictions_with_ids  
from floor_by_cost_measure import subtree_sizes  

M5_FEATURES = FEATURE_GROUPS["M5_static_plus_dynamic"]
M3_FEATURES = FEATURE_GROUPS["M3_dynamic_only"]

ENGINE = sys.argv[1] if len(sys.argv) > 1 else "coastal"
HELD = os.path.join(HERE, "..", "heldout", "data" if ENGINE == "jpf" else f"data_{ENGINE}")
RUNS_HELDOUT = os.path.join(HERE, "..", "heldout", "coastal_bin")
MATCHING = ["HoAllKadaneKadaneSum", "HoAllShellSortShell",
            "HoNumIndexIntervalsCompressDuplicates", "HoNumSortingSortIndicesInsertionSort"]


def add_jpf_log_columns(df):
    df = df.copy()
    df["depth"] = df["depth"] + 1
    tot, proc = {}, {}
    kids = {}
    for r in df.sort_values("stateId").itertuples():
        kids.setdefault(int(r.parentId), []).append(int(r.stateId))
    for parent, ks in kids.items():
        for rank, sid in enumerate(ks, start=1):
            tot[sid] = 1 if parent == -1 else len(ks)
            proc[sid] = rank
    df["choiceGeneratorTotal"] = [tot[int(s)] for s in df["stateId"]]
    df["choiceGeneratorProcessed"] = [proc[int(s)] for s in df["stateId"]]
    return df


STATIC_COLS = ["remainingBytecodesInMethod", "reachableBranchCount", "reachableLoopBackEdgeCount",
               "reachableVirtualCallCount", "reachableAllocSiteCount", "reachableAthrowCount"]


def add_static_columns(df, prog):
    from static_features import ProgramStatics
    ps = ProgramStatics(os.path.join(RUNS_HELDOUT, prog, "bin"), prog)
    df = df.copy()
    vals = {c: [] for c in STATIC_COLS}
    for pc in df["pcInstrChain"]:
        for c, v in zip(STATIC_COLS, ps.features(int(pc), back_if=False)):
            vals[c].append(v)
    for c in STATIC_COLS:
        df[c] = vals[c]
    df["threadCount"] = 1
    return df


def rho(a, p):
    a, p = np.asarray(a, float), np.asarray(p, float)
    if len(a) < MIN_ROWS_FOR_GROUP_RHO or len(set(a)) < 2 or len(set(p)) < 2:
        return np.nan
    r = spearmanr(a, p)[0]
    return r if not np.isnan(r) else np.nan


def main():
    # sorted explicitly: Random Forest bootstrap sampling depends on row order (see heldout_eval.py)
    main_df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
    nl = main_df[main_df["isEndStateAtEntry"] == False].copy()  
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    nl, _ = attach_group_c_predictions(nl)
    elig = eligible_groups(nl.dropna(subset=["groupC_pred"]))
    m6_train = nl[nl["program_group"].isin(elig)].dropna(subset=["groupC_pred"])
    rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    M6F = M5_FEATURES + ["groupC_pred"]
    m3models = {"M3 linear": (LinearRegression().fit(nl[M3_FEATURES].values, nl["logWork"].values), M3_FEATURES),
                "M3 RF": (rf().fit(nl[M3_FEATURES].values, nl["logWork"].values), M3_FEATURES)}
    m5models = {}
    if ENGINE in ("jpf", "coastal"):
        m5models = {"M5 linear": (LinearRegression().fit(nl[M5_FEATURES].values, nl["logWork"].values), M5_FEATURES),
                     "M5 RF": (rf().fit(nl[M5_FEATURES].values, nl["logWork"].values), M5_FEATURES),
                     "M6 linear": (LinearRegression().fit(m6_train[M6F].values, m6_train["logWork"].values), M6F),
                     "M6 RF": (rf().fit(m6_train[M6F].values, m6_train["logWork"].values), M6F)}
    models = {**m3models, **m5models}

    rng = np.random.default_rng(42)
    rows = []
    for prog in MATCHING:
        f = os.path.join(HELD, prog + ".csv")
        if not os.path.exists(f):
            print(f"{prog}: no {ENGINE} tree, skipped")
            continue
        d = pd.read_csv(f)
        if ENGINE != "jpf":
            d = add_jpf_log_columns(d)
        if ENGINE == "coastal":
            d = add_static_columns(d, prog)
        elif ENGINE == "gdart":
            d["threadCount"] = 1
        d["program"], d["program_group"] = prog, prog
        d = d.sort_values("stateId").reset_index(drop=True)
        d = mark_pruned(d)
        n_l = d[d["isEndStateAtEntry"] == False].copy()  
        n_l["logWork"] = np.log1p(n_l["actualSubtreeWork"])
        n_l["hind"] = pd.Series(subtree_sizes(d), index=d.index)[n_l.index].values
        r = {"program": prog.replace("Ho", "", 1), "states": len(d), "nonleaf": len(n_l)}
        r["floor"] = rho(n_l["actualSubtreeWork"], n_l["stateId"])
        r["hindsight"] = rho(n_l["actualSubtreeWork"], n_l["hind"])
        for label, fn in [("JPF built-in", state_count_estimator_predictions), ("JPFBar", jpfbar_predictions), ("Kilby WBE", wbe_predictions)]:
            a, p, _ = fn(d)
            r[label] = rho(a, p)
        a, p, _ = knuth_probe_predictions(d, rng)
        r["Knuth 30"] = rho(a, p)
        a, p, ids = recursive_estimator_predictions_with_ids(n_l)
        r["Group C"] = rho(a, p)
        n_l, _ = attach_group_c_predictions(n_l)
        for label, (m, feats) in models.items():
            sub = n_l if not label.startswith("M6") else n_l.dropna(subset=["groupC_pred"])
            if len(sub) == 0:
                r[label] = np.nan
                continue
            pred = m.predict(sub[feats].values)
            r[label] = rho(sub["logWork"], pred)
        rows.append(r)
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    show = ["program", "states", "nonleaf", "floor", "hindsight", "JPF built-in", "JPFBar", "Kilby WBE", "Group C", "Knuth 30"] + list(models)
    print(f"ENGINE = {ENGINE}, {len(R)} programs (exact node-count match with JPF on both COASTAL and GDart)\n")
    print(R[show].round(2).to_string(index=False))
    print("\nMacro rho over these programs (group-bootstrap 95% interval; n is tiny, informal only):")
    for m in show[3:]:
        v = {g: x for g, x in zip(R["program"], R[m]) if not np.isnan(x)}
        if v:
            lo, hi = bootstrap_macro_ci(v)
            print(f"  {m:<14} groups={len(v):<3} macro rho = {macro_average(v):+.3f}  [{lo:+.3f}, {hi:+.3f}]")


if __name__ == "__main__":
    main()
