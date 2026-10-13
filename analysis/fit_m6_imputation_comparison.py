"""Two ways to extend M6-RF beyond the program groups in which its history feature (groupC_pred) is defined:

  1. imputing a neutral value (the corpus median) for the missing feature, so that M6-RF is the single model everywhere (this script);
  2. a separately trained fallback model for the groups without history (the gated model of fit_hybrid_model.py).

Both are scored on the same population, the one that the gated model reaches.

Usage:
    python fit_m6_imputation_comparison.py"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import load_all, bootstrap_macro_ci, run_lopo, macro_average
from fit_hybrid_model import attach_group_c_predictions, eligible_groups, M5_FEATURES, M6_FEATURES, make_rf_factory


def main():
    df = load_all()
    non_leaf = df[df["isEndStateAtEntry"] == False].copy()
    non_leaf["logWork"] = np.log1p(non_leaf["actualSubtreeWork"])
    non_leaf, _ = attach_group_c_predictions(non_leaf)

    all_groups = sorted(non_leaf["program_group"].unique())
    # max_features="sqrt": the nested-CV-corrected tuned config used throughout
    # (see fit_nested_cv_rf_tuning.py) -- kept consistent with every other RF result reported.
    tuned_rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")

    scored = non_leaf.dropna(subset=["groupC_pred"]).copy()
    elig = eligible_groups(scored)
    # M6 is trained on the other eligible groups' rows only (the rule of fit_hybrid_model.py), so every M6 number in this package uses one training pool.
    scored_elig = scored[scored["program_group"].isin(elig)]
    m6rf_true = run_lopo(scored_elig, elig, M6_FEATURES, model_factory=tuned_rf)
    print(f"M6-RF standalone (native, history feature actually defined): "
          f"macro={m6rf_true['macro_rho']:.3f}  groups={m6rf_true['n_groups_in_macro']}")

    median_pred = non_leaf["groupC_pred"].median()
    imputed = non_leaf.copy()
    imputed["groupC_pred"] = imputed["groupC_pred"].fillna(median_pred)
    print(f"Imputing missing groupC_pred with the corpus-wide median ({median_pred:.3f}) -- "
          f"a neutral 'no information' filler, not a leak (computed from logWork's own overall "
          f"scale only, never from any test row's actual target).")

    m6rf_imputed = run_lopo(imputed, all_groups, M6_FEATURES, model_factory=tuned_rf)
    ci_imputed = bootstrap_macro_ci(m6rf_imputed["per_group_rho"])
    print(f"M6-RF + imputed history (extended to full scoreable population): "
          f"macro={m6rf_imputed['macro_rho']:.3f}  [{ci_imputed[0]:.3f},{ci_imputed[1]:.3f}]  "
          f"groups={m6rf_imputed['n_groups_in_macro']}")

    same_pop = sorted(m6rf_imputed["per_group_rho"].keys())
    m5rf_same_pop = run_lopo(non_leaf, same_pop, M5_FEATURES, model_factory=tuned_rf)
    print(f"M5-RF alone, same population (no history at all): "
          f"macro={m5rf_same_pop['macro_rho']:.3f}  groups={m5rf_same_pop['n_groups_in_macro']}")

    gated = dict(m6rf_true["per_group_rho"])
    for g, v in m5rf_same_pop["per_group_rho"].items():
        if g not in gated:
            gated[g] = v
    ci_gated = bootstrap_macro_ci(gated)
    print(f"Gated M6-RF+M5-RF (M6-RF on the eligible groups, M5-RF elsewhere) on this same population: "
          f"macro={macro_average(gated):.3f}  [{ci_gated[0]:.3f},{ci_gated[1]:.3f}]  groups={len(gated)}")


if __name__ == "__main__":
    main()
