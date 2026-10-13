"""Random Forest hyperparameter selection by nested cross-validation.

For each eligible group (the outer test fold), max_features is selected by an inner LOPO loop over the other eligible groups only. The best
value then fits a model on those groups, and the model scores the outer group, which the selection never saw.

Only max_features is nested (MAX_FEATURES_CANDIDATES: 'sqrt', 1.0, 'log2'). n_estimators=200, max_depth=None and min_samples_leaf=1 are fixed.

Usage:
    python fit_nested_cv_rf_tuning.py"""

import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import ( 
    load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci,
)
from fit_hybrid_model import attach_group_c_predictions, eligible_groups, M5_FEATURES, make_rf_factory

MAX_FEATURES_CANDIDATES = ["sqrt", 1.0, "log2"]


def fit_and_score(train, test, features, model_factory):
    X_train, y_train = train[features].values, train["logWork"].values
    X_test, y_test = test[features].values, test["logWork"].values
    model = model_factory()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    if len(set(y_test)) < 2 or len(set(y_pred)) < 2:
        return None
    r, _ = spearmanr(y_test, y_pred)
    return None if np.isnan(r) else float(r)


def inner_lopo_score(train_groups_df, inner_groups, features, max_features_val):
    """Inner LOPO across the OUTER TRAINING pool only -- scores one
    candidate max_features value, never touching the true outer test fold."""
    factory = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1,
                               max_features=max_features_val)
    rhos = []
    for inner_held_out in inner_groups:
        inner_train = train_groups_df[train_groups_df["program_group"] != inner_held_out]
        inner_test = train_groups_df[train_groups_df["program_group"] == inner_held_out]
        if len(inner_test) < MIN_ROWS_FOR_GROUP_RHO or len(inner_train) < 3:
            continue
        r = fit_and_score(inner_train, inner_test, features, factory)
        if r is not None:
            rhos.append(r)
    return float(np.mean(rhos)) if rhos else float("-inf")


def main():
    df = load_all()
    non_leaf = df[df["isEndStateAtEntry"] == False].copy() 
    non_leaf["logWork"] = np.log1p(non_leaf["actualSubtreeWork"])
    non_leaf, _ = attach_group_c_predictions(non_leaf)
    scored = non_leaf.dropna(subset=["groupC_pred"]).copy()
    elig = eligible_groups(scored)
    M6_FEATURES = M5_FEATURES + ["groupC_pred"]
    # training pool = the eligible groups' rows (the rule of fit_hybrid_model.py)
    scored = scored[scored["program_group"].isin(elig)].copy()

    print(f"Nested CV over {len(elig)} Group-C-eligible outer folds, inner LOPO selecting "
          f"max_features in {MAX_FEATURES_CANDIDATES}\n")

    outer_per_group_rho = {}
    chosen_per_fold = {}

    for outer_held_out in elig:
        outer_train = scored[scored["program_group"] != outer_held_out]
        outer_test = scored[scored["program_group"] == outer_held_out]
        if len(outer_test) < MIN_ROWS_FOR_GROUP_RHO or len(outer_train) < 3:
            continue

        inner_groups = [g for g in elig if g != outer_held_out]
        inner_scores = {}
        for candidate in MAX_FEATURES_CANDIDATES:
            inner_scores[candidate] = inner_lopo_score(outer_train, inner_groups, M6_FEATURES, candidate)
        best_candidate = max(inner_scores, key=inner_scores.get)
        chosen_per_fold[outer_held_out] = best_candidate

        final_factory = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1,
                                         max_features=best_candidate)
        r = fit_and_score(outer_train, outer_test, M6_FEATURES, final_factory)
        if r is not None:
            outer_per_group_rho[outer_held_out] = r

        print(f"  outer={outer_held_out:<26} inner-selected max_features={best_candidate!s:<6} "
              f"outer test rho={r if r is not None else float('nan'):.3f}  "
              f"(inner scores: {', '.join(f'{k}={v:.3f}' for k, v in inner_scores.items())})")

    macro = macro_average(outer_per_group_rho)
    ci = bootstrap_macro_ci(outer_per_group_rho)
    print(f"\n=== NESTED CV RESULT (leakage-free hyperparameter selection) ===")
    print(f"Macro rho = {macro:.3f} [{ci[0]:.3f},{ci[1]:.3f}]  groups={len(outer_per_group_rho)}")

    from collections import Counter
    print(f"\nHyperparameter chosen per outer fold: {dict(Counter(chosen_per_fold.values()))}")
    print("(The value of each outer fold is selected without using the data of that fold.)")

    sqrt_rho = {}
    for g in elig:
        r = fit_and_score(scored[scored["program_group"] != g], scored[scored["program_group"] == g], M6_FEATURES,
                          make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt"))
        if r is not None:
            sqrt_rho[g] = r
    print(f"\nFor comparison, the same LOPO protocol with one global max_features='sqrt' (the configuration used elsewhere): "
          f"macro rho = {macro_average(sqrt_rho):.3f}  groups={len(sqrt_rho)}")


if __name__ == "__main__":
    main()
