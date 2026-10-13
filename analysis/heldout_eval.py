"""Held-out corpus (../heldout/, pre-registered in ../heldout/PREREGISTRATION.md): the frozen estimators and models on programs that were not
used for selection rules, fitting or tuning.

Models are fitted once on ALL non-leaf rows of the 66 program groups of the main corpus (M5 linear and random forest with the settings of
fit_hybrid_model.make_rf_factory: 200 trees, max_features sqrt, seed 42; M6 on the rows of history-eligible groups only) and applied to the
held-out programs; nothing is refitted or tuned on held-out data. Baselines have no parameters (Knuth: 30 probes, seed 42, programs in
sorted order). Each held-out program is its own group. Reports per program and macro over the groups with at least 5 non-leaf states and
non-constant work (group bootstrap interval), the pre-registered hypotheses H1-H4, and the calibration statistics of
calibration_analysis.py.

Usage: python heldout_eval.py"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from prune import mark_pruned  
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci 
from fit_hybrid_model import attach_group_c_predictions, eligible_groups, M5_FEATURES, make_rf_factory  
from fit_jpf_builtin_estimator_baseline import state_count_estimator_predictions  
from fit_jpfbar_baseline import jpfbar_predictions  
from fit_knuth_probing_baseline import knuth_probe_predictions  
from fit_kilby_wbe_baseline import wbe_predictions  
from fit_group_c_baseline import recursive_estimator_predictions_with_ids 
from floor_by_cost_measure import subtree_sizes  
from calibration_analysis import per_group_stats  

HELD = os.path.join(HERE, "..", "heldout", "data")


def rho(a, p):
    a, p = np.asarray(a, float), np.asarray(p, float)
    if len(a) < MIN_ROWS_FOR_GROUP_RHO or len(set(a)) < 2 or len(set(p)) < 2:
        return np.nan
    r = spearmanr(a, p)[0]
    return r if not np.isnan(r) else np.nan


def main():
    # frozen models, fitted on the main corpus
    # Sorted explicitly (not left at glob() order, which is filesystem-dependent) so the Random Forest's
    # bootstrap sampling, which draws by row position, is reproducible across machines.
    main_df = load_all().sort_values(["program", "stateId"]).reset_index(drop=True)
    nl = main_df[main_df["isEndStateAtEntry"] == False].copy()  
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    nl, _ = attach_group_c_predictions(nl)
    elig = eligible_groups(nl.dropna(subset=["groupC_pred"]))
    m6_train = nl[nl["program_group"].isin(elig)].dropna(subset=["groupC_pred"])
    rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    M6F = M5_FEATURES + ["groupC_pred"]
    models = {"M5 linear": (LinearRegression().fit(nl[M5_FEATURES].values, nl["logWork"].values), M5_FEATURES),
              "M5 RF": (rf().fit(nl[M5_FEATURES].values, nl["logWork"].values), M5_FEATURES),
              "M6 linear": (LinearRegression().fit(m6_train[M6F].values, m6_train["logWork"].values), M6F),
              "M6 RF": (rf().fit(m6_train[M6F].values, m6_train["logWork"].values), M6F)}
    const = float(nl["logWork"].median())

    # ---- held-out programs
    files = sorted(glob.glob(os.path.join(HELD, "*.csv")))
    rng = np.random.default_rng(42)
    rows, cal = [], {n: ([], [], []) for n in list(models) + ["Group C", "constant"]}
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        d = pd.read_csv(f)
        d["program"], d["program_group"] = name, name
        d = d.sort_values("stateId").reset_index(drop=True)
        d = mark_pruned(d)
        n_l = d[d["isEndStateAtEntry"] == False].copy()  
        n_l["logWork"] = np.log1p(n_l["actualSubtreeWork"])
        n_l["hind"] = pd.Series(subtree_sizes(d), index=d.index)[n_l.index].values
        r = {"program": name.replace("Ho", "", 1), "states": len(d), "nonleaf": len(n_l), "states_work_distinct": n_l["actualSubtreeWork"].nunique()}
        r["floor"] = rho(n_l["actualSubtreeWork"], n_l["stateId"])
        r["hindsight"] = rho(n_l["actualSubtreeWork"], n_l["hind"])
        for label, fn in [("JPF built-in", state_count_estimator_predictions), ("JPFBar", jpfbar_predictions), ("Kilby WBE", wbe_predictions)]:
            a, p, _ = fn(d)
            r[label] = rho(a, p)
        a, p, _ = knuth_probe_predictions(d, rng)
        r["Knuth 30"] = rho(a, p)
        a, p, ids = recursive_estimator_predictions_with_ids(n_l)
        r["Group C"] = rho(a, p)
        r["GC rows"] = len(a)
        n_l, _ = attach_group_c_predictions(n_l)
        for label, (m, feats) in models.items():
            sub = n_l if label.startswith("M5") else n_l.dropna(subset=["groupC_pred"])
            if len(sub) == 0:
                r[label] = np.nan
                continue
            pred = m.predict(sub[feats].values)
            r[label] = rho(sub["logWork"], pred)
            if len(sub) >= MIN_ROWS_FOR_GROUP_RHO:
                cal[label][0].extend([name] * len(sub)); cal[label][1].extend(sub["logWork"]); cal[label][2].extend(pred)
        sc = n_l.dropna(subset=["groupC_pred"])
        cal["Group C"][0].extend([name] * len(sc)); cal["Group C"][1].extend(sc["logWork"]); cal["Group C"][2].extend(sc["groupC_pred"])
        cal["constant"][0].extend([name] * len(n_l)); cal["constant"][1].extend(n_l["logWork"]); cal["constant"][2].extend([const] * len(n_l))
        rows.append(r)
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    show = ["program", "states", "nonleaf", "floor", "hindsight", "JPF built-in", "JPFBar", "Kilby WBE", "Group C", "Knuth 30", "M5 linear", "M5 RF", "M6 linear", "M6 RF"]
    print(f"held-out programs: {len(R)}; scoreable (>= {MIN_ROWS_FOR_GROUP_RHO} non-leaf states and non-constant work): "
          f"{int(((R.nonleaf >= MIN_ROWS_FOR_GROUP_RHO) & (R.states_work_distinct >= 2)).sum())}")
    print(f"main corpus used for fitting: {nl['program_group'].nunique()} groups, {len(nl)} non-leaf rows; M6 trained on {len(elig)} eligible groups\n")
    print(R[show].round(2).to_string(index=False))
    # Post hoc sensitivity analysis (not pre-registered): 81% of the feature vectors of JaiLowerBoundLowerBound also occur in the training rows
    # of the main corpus, so it is structurally close to a main-corpus program that the code-similarity rule did not catch.
    for label, excl in [("ALL HELD-OUT PROGRAMS (pre-registered set)", set()), ("SENSITIVITY: without JaiLowerBoundLowerBound (post hoc)", {"JaiLowerBoundLowerBound"})]:
        Rs = R[~R["program"].isin(excl)]
        print("\n" + "=" * 100 + "\n" + label + f": {len(Rs)} programs")
        print("Macro rho over the groups where the method is defined (group-bootstrap 95% interval):")
        macro = {}
        for m in show[3:]:
            v = {g: x for g, x in zip(Rs["program"], Rs[m]) if not np.isnan(x)}
            if v:
                lo, hi = bootstrap_macro_ci(v)
                macro[m] = macro_average(v)
                print(f"  {m:<14} groups={len(v):<3} macro rho = {macro[m]:+.3f}  [{lo:+.3f}, {hi:+.3f}]")
        print("Pre-registered hypotheses:")
        print(f"  H1 floor negative:            macro {macro['floor']:+.3f} -> {'holds' if macro['floor'] < 0 else 'FAILS'}")
        print(f"  H2 hindsight >= 0.90:         macro {macro['hindsight']:+.3f} -> {'holds' if macro['hindsight'] >= 0.90 else 'FAILS'}")
        ok3 = all(abs(macro[k]) <= 0.30 for k in ("JPF built-in", "JPFBar"))
        print(f"  H3 JPF built-in, JPFBar within +-0.30 of 0: {macro['JPF built-in']:+.3f}, {macro['JPFBar']:+.3f} -> {'holds' if ok3 else 'FAILS'}")
        print(f"  H4 Group C positive:          macro {macro['Group C']:+.3f} -> {'holds' if macro['Group C'] > 0 else 'FAILS'}")
        print("Calibration (log10 error of 1+work; per group the median absolute error, then mean over groups -> factor; frozen models):")
        print(f"{'estimator':<12}{'groups':>7}{'mean factor':>13}{'bias':>8}{'within 2x':>11}{'within 10x':>12}")
        for name, (g, a, pr) in cal.items():
            g, a, pr = np.array(g), np.array(a), np.array(pr)
            keep = ~np.isin(g, [("Ho" + e) for e in excl])
            st = per_group_stats(g[keep], a[keep], pr[keep])
            if not st:
                continue
            arr = np.array(list(st.values()), float)
            print(f"{name:<12}{len(st):>7}{10 ** np.nanmean(arr[:, 0]):>12.1f}x{np.nanmean(arr[:, 1]):>+8.2f}{100 * arr[:, 2].mean():>10.0f}%{100 * arr[:, 3].mean():>11.0f}%")


if __name__ == "__main__":
    main()
