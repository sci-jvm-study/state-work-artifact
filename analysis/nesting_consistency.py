"""Nesting-consistency post-processing of M5 Random Forest predictions (see nesting_consistency_predeclared.md, written before this script was run).

Usage: python nesting_consistency.py"""
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci  
from fit_hybrid_model import M5_FEATURES, make_rf_factory  
from load_balance_replay import loo_predictions  


def adjust(d, pred):
    """d: rows of one configuration sorted by stateId; pred: dict stateId -> W^ (work units) for non-leaf states.
    Returns dicts for variants A and B."""
    entry = dict(zip(d["stateId"], d["entryInstructionCount"]))
    par = dict(zip(d["stateId"], d["parentId"]))
    A, B = {}, {}
    for s in sorted(pred):
        p = par[s]
        if p in A:
            A[s] = min(pred[s], A[p])
            B[s] = min(pred[s], max(B[p] - (entry[s] - entry[p]), 1.0))
        else:
            A[s] = B[s] = pred[s]
    return A, B


def main():
    df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
    nl = df[df["isEndStateAtEntry"] == False].copy()  
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    nl["p_rf"] = np.expm1(loo_predictions(nl, rf))
    rows = []
    viol = defaultdict(lambda: np.zeros(3))  # group -> (pred anc < desc, equal, anc > desc) over nested pairs
    for prog, d in df.groupby("program"):
        g = d["program_group"].iloc[0]
        d = d.reset_index(drop=True)
        sub = nl.loc[nl["program"] == prog]
        pred = dict(zip(sub["stateId"], sub["p_rf"]))
        A, B = adjust(d, pred)
        par = dict(zip(d["stateId"], d["parentId"]))
        for s in pred:  # nested pairs: every non-leaf ancestor of s
            a = par[s]
            while a in par:
                if a in pred:
                    viol[g] += np.array([pred[a] < pred[s], pred[a] == pred[s], pred[a] > pred[s]], dtype=float)
                a = par[a]
        for s in pred:
            rows.append((g, s, float(d.loc[d.stateId == s, "actualSubtreeWork"].iloc[0]), pred[s], A[s], B[s]))
    R = pd.DataFrame(rows, columns=["g", "s", "actual", "raw", "A", "B"])
    groups = [g for g, s in nl.groupby("program_group") if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s["actualSubtreeWork"].nunique() > 1]
    print(f"scoreable groups: {len(groups)}\n")
    vs = np.array([viol[g] / viol[g].sum() for g in groups if viol[g].sum() > 0])
    print(f"Raw M5-RF on nested pairs (macro over {len(vs)} groups with nested pairs): ancestor predicted LOWER than descendant {vs[:, 0].mean():.3f}, equal {vs[:, 1].mean():.3f}, higher {vs[:, 2].mean():.3f}\n")
    res = {}
    for name in ("raw", "A", "B"):
        per = {}
        for g in groups:
            s = R[R.g == g]
            if s[name].nunique() > 1 and s["actual"].nunique() > 1:
                per[g] = spearmanr(s["actual"], s[name])[0]
        res[name] = per
    print(f"{'variant':<28}{'groups':>7}{'macro rho':>11}   95% CI")
    for name, label in (("raw", "raw M5 RF"), ("A", "A: cap by ancestor estimate"), ("B", "B: cap by remaining estimate")):
        lo, hi = bootstrap_macro_ci(res[name])
        print(f"{label:<28}{len(res[name]):>7}{macro_average(res[name]):>+11.3f}   [{lo:+.3f}, {hi:+.3f}]")
    lost = [g for g in groups if g in res["raw"] and g not in res["A"]]
    print(f"\nGroups scoreable for raw but not for A (capped predictions constant or too few distinct values): {lost}\n")
    ok = {}
    for name in ("A", "B"):
        common = [g for g in groups if g in res["raw"] and g in res[name]]
        diff = np.array([res[name][g] - res["raw"][g] for g in common])
        gain = macro_average({g: res[name][g] for g in common}) - macro_average({g: res["raw"][g] for g in common})
        worse = int((diff < -0.05).sum())
        better = int((diff > 0.05).sum())
        ok[name] = gain >= 0.03 and worse <= 5
        raw_c = macro_average({g: res["raw"][g] for g in common})
        print(f"{name}: macro rho on these {len(common)} groups, raw {raw_c:+.3f} -> {name} {raw_c + gain:+.3f}")
        print(f"{name}: macro gain over raw {gain:+.3f} on {len(common)} groups; better by > 0.05 in {better}, worse by > 0.05 in {worse} -> "
              f"{'ADOPT for further study' if ok[name] else 'NOT ADOPTED'}")
    size = nl.groupby("program_group").size()
    print("\nBy tree size, POST HOC (bands as in nesting_decomposition.py, not predeclared): macro rho raw -> A on the groups A can score")
    for lo_, hi_ in [(0, 15), (15, 60), (60, 300), (300, 10 ** 6)]:
        gs = [g for g in groups if lo_ <= size[g] < hi_ and g in res["A"] and g in res["raw"]]
        if gs:
            print(f"  non-leaf states in [{lo_}, {hi_ if hi_ < 10 ** 6 else 'inf'}): {len(gs)} groups, raw {np.mean([res['raw'][g] for g in gs]):+.3f} -> A {np.mean([res['A'][g] for g in gs]):+.3f}")
    if ok["A"]:
        heldout(nl, rf)


def heldout(nl, rf):
    import glob
    print("\nHELD-OUT (variant A only, frozen M5 RF fitted on all 66 main groups, run once):")
    m = rf().fit(nl[M5_FEATURES].values, nl["logWork"].values)
    raw, adj = {}, {}
    for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "heldout", "data", "*.csv"))):
        name = os.path.splitext(os.path.basename(f))[0]
        d = pd.read_csv(f).sort_values("stateId").reset_index(drop=True)
        n_l = d[d["isEndStateAtEntry"] == False]
        pred = dict(zip(n_l["stateId"], np.expm1(m.predict(n_l[M5_FEATURES].values))))
        A, _ = adjust(d, pred)
        act = dict(zip(n_l["stateId"], n_l["actualSubtreeWork"]))
        ids = list(pred)
        for label, dd in (("raw", pred), ("A", A)):
            x = [act[i] for i in ids]
            y = [dd[i] for i in ids]
            r = spearmanr(x, y)[0] if len(set(y)) > 1 and len(set(x)) > 1 else np.nan
            (raw if label == "raw" else adj)[name] = r
    for k in raw:
        print(f"  {k[2:38]:<36} raw {raw[k]:+.3f}  A {adj[k]:+.3f}  difference {adj[k] - raw[k]:+.3f}")
    rr = {k: v for k, v in raw.items() if not np.isnan(v) and not np.isnan(adj[k])}
    print(f"  macro over {len(rr)} programs: raw {np.mean(list(rr.values())):+.3f}, A {np.mean([adj[k] for k in rr]):+.3f}")


if __name__ == "__main__":
    main()
