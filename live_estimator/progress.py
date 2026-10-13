"""Stage 2 (live_progress_stage2_predeclared.md): progress bars.

Usage: python progress.py run     # nine held-out programs, StateWorkListener + LiveProgressListener in one JVM each
       python progress.py h1      # offline reconstruction against the live-logged values (H1)
       python progress.py h2      # accuracy of the bars on the nine programs (H2)
"""
import os
import shutil
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from jpf_run import MODEL, NAMES, PROGRAMS, run_jpf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "runs", "progress")
CHECKPOINTS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def run():
    os.makedirs(OUT, exist_ok=True)
    for prog in NAMES:
        for f in ("state_work_dataset.csv", "live_progress.csv"):
            p = os.path.join(PROGRAMS, f)
            if os.path.exists(p):
                os.remove(p)
        s, wall, tail = run_jpf(prog, ["gov.nasa.jpf.symbc.StateWorkListener", "gov.nasa.jpf.symbc.LiveProgressListener"],
                                {"liveprog.model": MODEL, "liveprog.logfile": "live_progress.csv"},
                                jvm_flags=["-Dstatework.quiet=true"])
        if not os.path.exists(os.path.join(PROGRAMS, "live_progress.csv")):
            print("FAILED", prog, tail)
            continue
        shutil.move(os.path.join(PROGRAMS, "state_work_dataset.csv"), os.path.join(OUT, prog + "_work.csv"))
        shutil.move(os.path.join(PROGRAMS, "live_progress.csv"), os.path.join(OUT, prog + "_prog.csv"))
        print("ok", prog, flush=True)


# ---------------------------------------------------------------- offline implementation of the bars (from a recorded tree)
def bars_offline(work, pred_cap_log, pred_raw_log, oracle=False):
    """work: StateWorkListener rows sorted by stateId (all states). pred_*_log: dict stateId -> log-space prediction for non-end
    states. Returns a DataFrame with one row per state: builtin, jpfbar, Rcap, Rraw (NaN at end states), Rorc (oracle, if asked)."""
    n_ = work["choiceGeneratorTotal"].values
    p_ = work["choiceGeneratorProcessed"].values
    end = work["isEndStateAtEntry"].values
    sid = work["stateId"].values
    par = dict(zip(work["stateId"], work["parentId"]))
    truew = dict(zip(work["stateId"], work["actualSubtreeWork"]))
    idx = {s: i for i, s in enumerate(sid)}

    def chain(s):  # open stack root..s, as state ids
        c = []
        while s != -1:
            c.append(s)
            s = par[s]
        return c[::-1]

    out = []
    jpfbar = 0.0
    for i, s in enumerate(sid):
        ch = chain(s)
        # built-in: chain without the root
        delta, percent = 1.0, 0.0
        for a in ch[1:]:
            n, p = n_[idx[a]], p_[idx[a]]
            if n in (-1, 0):
                continue
            delta /= n
            percent += delta * (0 if p == -1 else max(0, p - 1))
        builtin = 1.0 if len(ch) == 1 else percent
        # JPFBar weight of this path including the root level, as in fit_jpfbar_baseline.leaf_path_weight
        w = 1.0
        for a in ch:
            n = n_[idx[a]]
            if n not in (-1, 0):
                w /= n
        rec = {"stateId": s, "builtin": builtin, "jpfbar": jpfbar}
        if end[i]:
            jpfbar += w
            rec.update(Rcap=np.nan, Rraw=np.nan, Rorc=np.nan)
        else:
            def R(wf):
                tot = wf(ch[-1])
                for a in ch:
                    n, p = n_[idx[a]], p_[idx[a]]
                    u = max(0, n - p) if (n not in (-1, 0) and p >= 0) else 0
                    tot += u * wf(a)
                return tot
            rec["Rcap"] = R(lambda a: np.expm1(pred_cap_log[a]))
            rec["Rraw"] = R(lambda a: np.expm1(pred_raw_log[a]))
            rec["Rorc"] = R(lambda a: float(truew[a]))
        out.append(rec)
    return pd.DataFrame(out)


def model_bars(work, B):
    """Turn the remaining-work estimates into bars, with the end-state rule (subtract executed work since the last prediction)."""
    D = (work["entryInstructionCount"].values - work["entryInstructionCount"].values[0]).astype(float)  # since root entry
    res = {}
    for name in ("Rcap", "Rraw", "Rorc"):
        R = B[name].values.copy()
        bar = np.zeros(len(D))
        last_R, last_D = None, None
        for i in range(len(D)):
            if not np.isnan(R[i]):
                last_R, last_D = R[i], D[i]
                cur = R[i]
            else:
                cur = max(0.0, last_R - (D[i] - last_D)) if last_R is not None else 0.0
            bar[i] = D[i] / (D[i] + cur) if D[i] + cur > 0 else 0.0
        res[name] = np.clip(bar, 0, 1)
    return res


def errors(tau, est, D, D_total):
    """time-weighted MAE (percentage points), event-weighted MAE, max error, error at checkpoints."""
    e = np.abs(est - tau)
    nxt = np.append(D[1:], D_total)
    w = (nxt - D) / D_total
    tw = 100 * float(np.sum(e * w))
    ev = 100 * float(np.mean(e))
    cps = []
    for c in CHECKPOINTS:
        j = np.argmax(tau >= c) if (tau >= c).any() else len(tau) - 1
        cps.append(100 * float(e[j]))
    return tw, ev, 100 * float(e.max()), cps


def h1():
    rows = []
    for prog in NAMES:
        work = pd.read_csv(os.path.join(OUT, prog + "_work.csv")).sort_values("stateId").reset_index(drop=True)
        live = pd.read_csv(os.path.join(OUT, prog + "_prog.csv")).sort_values("stateId").reset_index(drop=True)
        assert (work["stateId"].values == live["stateId"].values).all()
        assert (work["choiceGeneratorTotal"].values == live["n"].values).all()
        assert (work["choiceGeneratorProcessed"].values == live["p"].values).all()
        root = work[work["parentId"] == -1]
        assert (root["choiceGeneratorTotal"] == 1).all() and (root["choiceGeneratorProcessed"] == 1).all(), \
            "root level is not the trivial single thread choice (n = p = 1), so it would matter whether it is in the chain"
        cap = {int(s): v for s, v in zip(live["stateId"], live["capLog"]) if not np.isnan(v)}
        raw = {int(s): v for s, v in zip(live["stateId"], live["rawLog"]) if not np.isnan(v)}
        B = bars_offline(work, cap, raw)

        def rel(a, b):
            m = ~(np.isnan(a) | np.isnan(b))
            nan_ok = (np.isnan(a) == np.isnan(b)).all()
            d = np.abs(a[m] - b[m]) / np.maximum(np.abs(b[m]), 1e-300)
            return float(d.max()) if m.any() else 0.0, nan_ok
        r = {"program": prog.replace("Ho", "", 1), "states": len(work)}
        for name, col in (("builtin", "builtin"), ("jpfbar", "jpfbar"), ("Rcap", "Rcap"), ("Rraw", "Rraw")):
            r["max_rel_" + name], r["nan_pattern_" + name] = rel(B[name].values.astype(float), live[col].values.astype(float))
        rows.append(r)
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(R.to_string(index=False))
    mx = max(R[c].max() for c in R.columns if c.startswith("max_rel_"))
    nan_ok = all(R[c].all() for c in R.columns if c.startswith("nan_pattern_"))
    print(f"\nlargest relative difference: {mx:.3e}; NaN patterns equal: {nan_ok}")
    print("H1 holds:", mx <= 1e-9 and nan_ok)
    R.to_csv(os.path.join(HERE, "results", "stage2_h1.csv"), index=False)


def h2():
    rows, cps = [], {}
    for prog in NAMES:
        work = pd.read_csv(os.path.join(OUT, prog + "_work.csv")).sort_values("stateId").reset_index(drop=True)
        live = pd.read_csv(os.path.join(OUT, prog + "_prog.csv")).sort_values("stateId").reset_index(drop=True)
        cap = {int(s): v for s, v in zip(live["stateId"], live["capLog"]) if not np.isnan(v)}
        raw = {int(s): v for s, v in zip(live["stateId"], live["rawLog"]) if not np.isnan(v)}
        B = bars_offline(work, cap, raw)
        mb = model_bars(work, B)
        D = (work["entryInstructionCount"].values - work["entryInstructionCount"].values[0]).astype(float)  # since root entry
        D_total = float(work["actualSubtreeWork"].values[0])  # work of the root subtree = the whole search
        tau = D / D_total
        wall = work["entryWallClockNanos"].values.astype(float)
        wall_tau = (wall - wall[0]) / (work["exitWallClockNanos"].max() - wall[0])
        series = {"model_capped": mb["Rcap"], "model_raw": mb["Rraw"], "oracle_sibling": mb["Rorc"],
                  "JPF_builtin": np.clip(B["builtin"].values, 0, 1), "JPFBar": np.clip(B["jpfbar"].values, 0, 1)}
        r = {"program": prog.replace("Ho", "", 1), "states": len(work)}
        for k, est in series.items():
            tw, ev, mx, c = errors(tau, est, D, D_total)
            r["tw_" + k], r["ev_" + k], r["max_" + k] = tw, ev, mx
            cps[(prog, k)] = c
            r["wall_tw_" + k] = 100 * float(np.sum(np.abs(est - wall_tau) * ((np.append(D[1:], D_total) - D) / D_total)))
        rows.append(r)
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    keys = ["model_capped", "model_raw", "oracle_sibling", "JPF_builtin", "JPFBar"]
    print("time-weighted MAE, percentage points (primary)")
    print(R[["program", "states"] + ["tw_" + k for k in keys]].round(2).to_string(index=False))
    print("\nmacro:", {k: round(R["tw_" + k].mean(), 2) for k in keys})
    for base in ("JPF_builtin", "JPFBar"):
        d = R["tw_" + base] - R["tw_model_capped"]
        better = int((d > 0).sum())
        p = wilcoxon(d).pvalue if (d != 0).any() else np.nan
        print(f"capped model vs {base}: macro gain {d.mean():+.2f} points, better in {better}/9, Wilcoxon p = {p:.3g}")
    h2_ok = all((R["tw_model_capped"].mean() < R["tw_" + b].mean()) and ((R["tw_model_capped"] < R["tw_" + b]).sum() >= 7)
                for b in ("JPF_builtin", "JPFBar"))
    print("H2 holds:", h2_ok)
    print("\nevent-weighted MAE:", {k: round(R["ev_" + k].mean(), 2) for k in keys})
    print("max error:", {k: round(R["max_" + k].mean(), 2) for k in keys})
    print("wall-clock target, time-weighted MAE:", {k: round(R["wall_tw_" + k].mean(), 2) for k in keys})
    print("\nerror at checkpoints, mean over programs (points):")
    print(pd.DataFrame({k: np.mean([cps[(p, k)] for p in NAMES], axis=0) for k in keys}, index=[f"{int(c*100)}%" for c in CHECKPOINTS]).round(1))
    R.to_csv(os.path.join(HERE, "results", "stage2_h2.csv"), index=False)


if __name__ == "__main__":
    {"run": run, "h1": h1, "h2": h2}[sys.argv[1]]()
