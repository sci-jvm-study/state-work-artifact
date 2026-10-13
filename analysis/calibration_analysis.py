"""Magnitude accuracy (calibration) of the estimators that predict work in work units, next to their rank accuracy.

Rank agreement (Spearman rho) does not say whether predicted values have the right scale. For Group C (sibling mean),
M5, M6 (linear and random forest) and the gated M6-RF/M5-RF combination, this script reports, per program group and then
as a macro average over groups (the group is the unit, as elsewhere):
  * median absolute error of log10(1 + work), i.e. the typical multiplicative error factor 10^error;
  * median signed error (bias: > 0 over-predicts);
  * share of states predicted within a factor of 2 and within a factor of 10 of the true work.
Reference: a constant guess, the median log work of the training groups (leave-one-group-out), which carries no
information about the state. Knuth probing and JPF's built-in estimator are not included: their outputs are in state
counts, not work units, so a magnitude error against work is not defined for them.
The models use the same leave-one-program-group-out training as fit_all_baselines_fair_comparison.py (M6 trained on the
other eligible groups' rows only; M5-RF fallback for ineligible groups).

Usage: python calibration_analysis.py"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, run_lopo
from fit_hybrid_model import attach_group_c_predictions, eligible_groups, M5_FEATURES, make_rf_factory


def per_group_stats(groups_of_row, actual_log, pred_log):
    """dict group -> (median |err| in log10, median signed err in log10, within 2x, within 10x, rho)."""
    d = pd.DataFrame({"g": groups_of_row, "a": actual_log, "p": pred_log})
    out = {}
    for g, s in d.groupby("g"):
        if len(s) < MIN_ROWS_FOR_GROUP_RHO:
            continue
        e = (s["p"] - s["a"]) / np.log(10)  # natural-log difference -> log10
        rho = spearmanr(s["a"], s["p"])[0] if s["a"].nunique() > 1 and s["p"].nunique() > 1 else np.nan
        out[g] = (e.abs().median(), e.median(), (e.abs() <= np.log10(2)).mean(), (e.abs() <= 1).mean(), rho)
    return out


def summarize(name, stats, groups=None):
    stats = {g: v for g, v in stats.items() if groups is None or g in groups}
    arr = np.array(list(stats.values()), dtype=float)
    rho = arr[:, 4]
    print(f"{name:<30}{len(stats):>7}{np.nanmedian(arr[:, 0]):>15.2f}{10 ** np.nanmean(arr[:, 0]):>10.1f}x"
          f"{np.nanmean(arr[:, 1]):>+10.2f}{100 * arr[:, 2].mean():>9.0f}%{100 * arr[:, 3].mean():>8.0f}%{(np.nanmean(rho) if np.isfinite(rho).any() else float("nan")):>+9.2f}")


def main():
    df = load_all()
    nl = df[df["isEndStateAtEntry"] == False].copy()
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    nl, _ = attach_group_c_predictions(nl)
    scored = nl.dropna(subset=["groupC_pred"]).copy()
    elig = eligible_groups(scored)
    all_groups = sorted(nl["program_group"].unique())
    inelig = [g for g in all_groups if g not in elig]
    m6 = M5_FEATURES + ["groupC_pred"]
    rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    sc_el = scored[scored["program_group"].isin(elig)]

    results = {}
    # Group C: prediction in work units
    gc = scored[scored["program_group"].isin(elig)]
    results["Group C (sibling mean)"] = per_group_stats(gc["program_group"].values, gc["logWork"].values,
                                                        np.log1p(gc["groupC_pred"].values))
    for name, res in [("M5 linear", run_lopo(nl, all_groups, M5_FEATURES)),
                      ("M5 random forest", run_lopo(nl, all_groups, M5_FEATURES, model_factory=rf)),
                      ("M6 linear", run_lopo(sc_el, elig, m6)),
                      ("M6 random forest", run_lopo(sc_el, elig, m6, model_factory=rf))]:
        results[name] = per_group_stats(res["groups_of_row"], res["actuals"], res["preds"])
    # gated: M6-RF on eligible groups, M5-RF elsewhere
    m6rf = run_lopo(sc_el, elig, m6, model_factory=rf)
    m5rf_all = run_lopo(nl, all_groups, M5_FEATURES, model_factory=rf)
    g_rows, g_a, g_p = list(m6rf["groups_of_row"]), list(m6rf["actuals"]), list(m6rf["preds"])
    for g, a, p in zip(m5rf_all["groups_of_row"], m5rf_all["actuals"], m5rf_all["preds"]):
        if g in inelig:
            g_rows.append(g); g_a.append(a); g_p.append(p)
    results["Gated M6-RF + M5-RF"] = per_group_stats(g_rows, g_a, g_p)

    # constant reference, leave-one-group-out median of training log work
    const_rows, const_a, const_p = [], [], []
    for g in all_groups:
        train = nl[nl["program_group"] != g]["logWork"]
        test = nl[nl["program_group"] == g]
        const_rows += [g] * len(test); const_a += list(test["logWork"]); const_p += [train.median()] * len(test)
    const = per_group_stats(const_rows, const_a, const_p)

    print(f"Non-leaf states: {len(nl)}; groups {len(all_groups)}; eligible for Group C / M6: {len(elig)}\n")
    for label, groups in [(f"{len(elig)} eligible groups (population of Group C and M6)", set(elig)),
                          ("all groups each model can score", None)]:
        print("=" * 110)
        print(label)
        print(f"{'estimator':<30}{'groups':>7}{'median |err|':>15}{'mean factor':>10}{'bias':>10}{'within 2x':>10}{'within 10x':>9}{'rho':>9}")
        print(f"{'(rho column = mean of group rhos)':<30}")
        summarize("constant (training median)", const, groups)
        for name, st in results.items():
            summarize(name, st, groups)
    print("\nmedian |err|: median over groups of the group's median absolute error in log10 units (0.30 = a factor of 2);")
    print("mean factor: 10^(mean over groups of that median absolute error); bias: mean over groups of the median signed log10 error.")


if __name__ == "__main__":
    main()
