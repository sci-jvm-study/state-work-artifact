"""H1 of live_estimator_stage1_predeclared.md: live predictions against the offline replay, on the nine held-out programs.

Usage: python fidelity.py run      # runs StateWorkListener + LiveEstimatorListener together, one JVM per program
       python fidelity.py check    # compares the outputs against the archive and against scikit-learn / nesting_consistency.adjust
"""
import os
import shutil
import sys

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from jpf_run import MODEL, NAMES, PROGRAMS, run_jpf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "runs", "fidelity")
ARCHIVE = os.path.join(HERE, "..", "heldout", "data")
sys.path.insert(0, os.path.join(HERE, "..", "analysis"))

FEATS = ["remainingBytecodesInMethod", "reachableBranchCount", "reachableLoopBackEdgeCount", "reachableVirtualCallCount",
         "reachableAllocSiteCount", "reachableAthrowCount", "choiceGeneratorTotal", "choiceGeneratorProcessed",
         "pathConditionSize", "threadCount"]
TOL = 1e-6


def run():
    os.makedirs(OUT, exist_ok=True)
    for prog in NAMES:
        for f in ("state_work_dataset.csv", "live_predictions.csv"):
            p = os.path.join(PROGRAMS, f)
            if os.path.exists(p):
                os.remove(p)
        s, wall, tail = run_jpf(prog, ["gov.nasa.jpf.symbc.StateWorkListener", "gov.nasa.jpf.symbc.LiveEstimatorListener"],
                                {"liveest.mode": "rfcap", "liveest.model": MODEL, "liveest.log": "true",
                                 "liveest.logfile": "live_predictions.csv"}, jvm_flags=["-Dstatework.quiet=true"])
        if s is None:
            print("FAILED", prog, tail)
            continue
        shutil.move(os.path.join(PROGRAMS, "state_work_dataset.csv"), os.path.join(OUT, prog + "_work.csv"))
        shutil.move(os.path.join(PROGRAMS, "live_predictions.csv"), os.path.join(OUT, prog + "_live.csv"))
        print(f"{prog}: states={s['states']} nonleaf={s['nonleaf']} searchNs={s['searchNs']} wall={wall:.1f}s", flush=True)


def rho(a, p):
    a, p = np.asarray(a, float), np.asarray(p, float)
    if len(a) < 5 or len(set(a)) < 2 or len(set(p)) < 2:
        return np.nan
    return spearmanr(a, p)[0]


def check():
    argv, sys.argv = sys.argv, sys.argv[:1]  # load_balance_replay (imported by nesting_consistency) reads sys.argv[1] at import
    from nesting_consistency import adjust
    sys.argv = argv
    rf = joblib.load(os.path.join(HERE, "model", "m5_rf.joblib"))
    rows, macro_raw, macro_cap, macro_raw_live, macro_cap_live = [], [], [], [], []
    for prog in NAMES:
        work = pd.read_csv(os.path.join(OUT, prog + "_work.csv")).sort_values("stateId").reset_index(drop=True)
        live = pd.read_csv(os.path.join(OUT, prog + "_live.csv")).sort_values("stateId").reset_index(drop=True)
        arch = pd.read_csv(os.path.join(ARCHIVE, prog + ".csv")).sort_values("stateId").reset_index(drop=True)
        r = {"program": prog.replace("Ho", "", 1), "states": len(live)}

        # (a) features and structure: this run's listener vs the same run's StateWorkListener, and vs the archive
        nl_w = work[~work["isEndStateAtEntry"]]
        nl_l = live[live["isEnd"] == False].reset_index(drop=True)  
        same_ids = (len(nl_w) == len(nl_l)) and (nl_w["stateId"].values == nl_l["stateId"].values).all()
        r["ids_equal"] = bool(same_ids)
        r["feat_mismatch_vs_run"] = int((nl_w[FEATS].values != nl_l[FEATS].values).sum()) if same_ids else -1
        r["parent_mismatch_vs_run"] = int((work["parentId"].values != live["parentId"].values).sum())
        a_nl = arch[~arch["isEndStateAtEntry"]].reset_index(drop=True)
        ok_arch = len(a_nl) == len(nl_l) and (a_nl["stateId"].values == nl_l["stateId"].values).all()
        r["feat_mismatch_vs_archive"] = int((a_nl[FEATS].values != nl_l[FEATS].values).sum()) if ok_arch else -1
        r["work_mismatch_vs_archive"] = int((arch["actualSubtreeWork"].values != work["actualSubtreeWork"].values).sum()) \
            if len(arch) == len(work) else -1

        # (b) raw prediction against scikit-learn on the same features
        py_raw = rf.predict(nl_l[FEATS].values.astype(float))
        r["max_abs_raw"] = float(np.max(np.abs(py_raw - nl_l["raw"].values)))

        # (c) capped prediction against nesting_consistency.adjust (variant A, work units) on the recorded tree
        d = work.copy()
        pred = dict(zip(nl_w["stateId"], np.expm1(py_raw)))
        A, _ = adjust(d, pred)
        py_cap = np.log1p(np.array([A[s] for s in nl_w["stateId"]]))
        r["max_abs_cap"] = float(np.max(np.abs(py_cap - nl_l["capped"].values)))

        # (d) rank accuracy, live against measured work of this run. Pruned choices (no recorded child, zero work, see analysis/prune.py) are
        # predicted like every other state during the search but are leaves, so they are not scored.
        has_child = nl_w["stateId"].isin(set(work["parentId"])).values
        act = nl_w["actualSubtreeWork"].values[has_child]
        r["pruned_choices"] = int((~has_child).sum())
        r["rho_raw_live"], r["rho_cap_live"] = rho(act, nl_l["raw"].values[has_child]), rho(act, nl_l["capped"].values[has_child])
        r["rho_raw_py"], r["rho_cap_py"] = rho(act, py_raw[has_child]), rho(act, py_cap[has_child])
        rows.append(r)
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(R.round(6).to_string(index=False))
    print()
    for c in ("rho_raw_live", "rho_cap_live", "rho_raw_py", "rho_cap_py"):
        print(f"macro {c}: {np.nanmean(R[c]):.4f}")
    h1a = (R["ids_equal"].all() and (R["feat_mismatch_vs_run"] == 0).all() and (R["parent_mismatch_vs_run"] == 0).all()
           and (R["feat_mismatch_vs_archive"] == 0).all() and (R["work_mismatch_vs_archive"] == 0).all())
    h1b = (R["max_abs_raw"] <= TOL).all()
    h1c = (R["max_abs_cap"] <= TOL).all()
    h1d = (abs(np.nanmean(R["rho_raw_live"]) - np.nanmean(R["rho_raw_py"])) <= TOL
           and abs(np.nanmean(R["rho_cap_live"]) - np.nanmean(R["rho_cap_py"])) <= TOL)
    print(f"\nH1(a) features/structure/work equal: {h1a}\nH1(b) raw within {TOL}: {h1b}\nH1(c) capped within {TOL}: {h1c}\n"
          f"H1(d) live macro rho equals the scikit-learn macro rho (raw and capped): {h1d}\nH1 holds: {h1a and h1b and h1c and h1d}")
    R.to_csv(os.path.join(HERE, "results", "h1_fidelity.csv"), index=False)


if __name__ == "__main__":
    {"run": run, "check": check}[sys.argv[1]]()
