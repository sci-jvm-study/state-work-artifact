"""The three splits side by side for the primary models: within-program (an optimistic bound), leave-one-program-out (LOPO, used by every other
model script in this package) and leave-one-family-out (LOFO, the strictest test, which holds out a whole family of related programs).

The family taxonomy is the FAMILY dict of fit_hybrid_model.py, which covers every program group of the corpus.

  - WITHIN-PROGRAM: random 80/20 split of the states within each program group (no program held out). A model that fails even here cannot
    fit the data at all.
  - LOPO: hold out one program group and train on all others, as in run_lopo(), so these numbers match the other scripts exactly.
  - LOFO: hold out a whole family (all its program groups at once) and train on the remaining families. A family with only one program
    group (e.g. graph_algo = BellmanFord alone) makes LOFO and LOPO identical for that fold.

Usage:
    python fit_generalization_splits.py"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import (  
    load_all, FEATURE_GROUPS, MIN_ROWS_FOR_GROUP_RHO,
    macro_average, bootstrap_macro_ci, run_lopo,
)
from fit_hybrid_model import FAMILY  

WITHIN_PROGRAM_SEED = 42
WITHIN_PROGRAM_TEST_FRAC = 0.2


def run_within_program(non_leaf, program_groups, features, seed=WITHIN_PROGRAM_SEED):
    """Optimistic bound: random state-level 80/20 split WITHIN each program
    group (never across groups) -- fit on 80% of a group's own states,
    score on the held-out 20% of that SAME group. No cross-program
    generalization tested at all; this is a ceiling, not a realistic
    estimate."""
    rng = np.random.default_rng(seed)
    per_group_rho = {}
    all_actuals, all_preds = [], []

    for g in program_groups:
        sub = non_leaf[non_leaf["program_group"] == g]
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO * 2:  # need enough for a train+test split
            continue
        idx = rng.permutation(len(sub))
        n_test = max(1, int(len(sub) * WITHIN_PROGRAM_TEST_FRAC))
        test_idx, train_idx = idx[:n_test], idx[n_test:]
        if len(train_idx) < 3:
            continue
        X_train = sub.iloc[train_idx][features].values
        y_train = sub.iloc[train_idx]["logWork"].values
        X_test = sub.iloc[test_idx][features].values
        y_test = sub.iloc[test_idx]["logWork"].values

        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        all_actuals.extend(y_test)
        all_preds.extend(y_pred)
        if len(y_test) >= 3 and len(set(y_test)) >= 2 and len(set(y_pred)) >= 2:
            r, _ = spearmanr(y_test, y_pred)
            if not np.isnan(r):
                per_group_rho[g] = r

    pooled = (spearmanr(all_actuals, all_preds)[0]
              if len(set(all_actuals)) >= 2 else float("nan"))
    return {"pooled_rho": pooled, "macro_rho": macro_average(per_group_rho),
            "per_group_rho": per_group_rho, "n_groups_in_macro": len(per_group_rho)}


def run_lofo(non_leaf, features, family_of):
    """Leave-one-FAMILY-out: hold out every program group in a family at
    once, train on all other families' rows, test on the held-out family's
    rows. Mirrors run_lopo()'s structure exactly, one level up (family
    instead of program group)."""
    families = sorted(set(family_of.values()))
    non_leaf = non_leaf.copy()
    non_leaf["family"] = non_leaf["program_group"].map(family_of)

    per_group_rho = {}
    all_actuals, all_preds, groups_of_row = [], [], []

    for held_out_family in families:
        train = non_leaf[non_leaf["family"] != held_out_family]
        test = non_leaf[non_leaf["family"] == held_out_family]
        if len(train) < 3 or len(test) == 0:
            continue

        X_train = train[features].values
        y_train = train["logWork"].values
        X_test = test[features].values
        y_test = test["logWork"].values

        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        all_actuals.extend(y_test)
        all_preds.extend(y_pred)
        groups_of_row.extend(test["program_group"].tolist())

        # per-program-group rho within this held-out family (same
        # MIN_ROWS_FOR_GROUP_RHO convention as everywhere else)
        test_with_pred = test.copy()
        test_with_pred["_pred"] = y_pred
        for g, sub in test_with_pred.groupby("program_group"):
            if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
                continue
            if sub["logWork"].nunique() < 2 or sub["_pred"].nunique() < 2:
                continue
            r, _ = spearmanr(sub["logWork"], sub["_pred"])
            if not np.isnan(r):
                per_group_rho[g] = r

    pooled = (spearmanr(all_actuals, all_preds)[0]
              if len(set(all_actuals)) >= 2 else float("nan"))
    return {"pooled_rho": pooled, "macro_rho": macro_average(per_group_rho),
            "per_group_rho": per_group_rho, "n_groups_in_macro": len(per_group_rho)}


def main():
    df = load_all()
    non_leaf = df[df["isEndStateAtEntry"] == False].copy() 
    non_leaf["logWork"] = np.log1p(non_leaf["actualSubtreeWork"])
    program_groups = sorted(non_leaf["program_group"].unique())

    # Coverage check: does FAMILY cover every program group in this corpus?
    missing = [g for g in program_groups if g not in FAMILY]
    if missing:
        print(f"WARNING: {len(missing)} program groups have no family assignment, excluded from "
              f"LOFO: {missing}")
    families = sorted(set(FAMILY.values()))
    family_sizes = {f: sum(1 for g in FAMILY.values() if g == f) for f in families}
    single_program_families = [f for f, n in family_sizes.items() if n == 1]
    print(f"{len(families)} families covering {len(FAMILY)} program groups "
          f"({len(single_program_families)} single-program families, where LOFO==LOPO for that "
          f"family's one fold): {single_program_families}\n")

    print(f"{'Model':<24}{'Within-program':>16}{'LOPO':>10}{'LOFO':>10}{'LOPO->LOFO drop':>18}")
    print("=" * 80)

    for model_name, features in FEATURE_GROUPS.items():
        wp_res = run_within_program(non_leaf, program_groups, features)
        lopo_res = run_lopo(non_leaf, program_groups, features, sample_weighted=False)
        lofo_res = run_lofo(non_leaf, features, FAMILY)

        drop = (lopo_res["macro_rho"] - lofo_res["macro_rho"]
                if not (np.isnan(lopo_res["macro_rho"]) or np.isnan(lofo_res["macro_rho"]))
                else float("nan"))
        print(f"{model_name:<24}{wp_res['macro_rho']:>16.3f}{lopo_res['macro_rho']:>10.3f}"
              f"{lofo_res['macro_rho']:>10.3f}{drop:>18.3f}")

    print("\n=== Per-family LOFO macro rho (M5, the strongest linear model) -- which families "
          "generalize worst? ===")
    lofo_m5 = run_lofo(non_leaf, FEATURE_GROUPS["M5_static_plus_dynamic"], FAMILY)
    per_family = {}
    non_leaf_fam = non_leaf.copy()
    non_leaf_fam["family"] = non_leaf_fam["program_group"].map(FAMILY)
    for family in families:
        groups_in_family = [g for g, f in FAMILY.items() if f == family]
        rhos = [lofo_m5["per_group_rho"][g] for g in groups_in_family if g in lofo_m5["per_group_rho"]]
        if rhos:
            per_family[family] = float(np.mean(rhos))
    for family, rho in sorted(per_family.items(), key=lambda kv: kv[1]):
        n_groups = family_sizes[family]
        print(f"  {family:<24} mean_rho={rho:>7.3f}  ({n_groups} program group(s) in this family)")



if __name__ == "__main__":
    main()
