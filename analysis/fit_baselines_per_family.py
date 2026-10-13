"""Per-family accuracy of the baselines (follows fit_generalization_splits.py).

LOPO and LOFO test whether a fitted model (M1 to M6, which learns coefficients from other programs) generalizes to unseen programs or
families. The six baselines are parameter-free formulas that are applied to each state with only the local data of its own program (sibling
averages, path history, visitation counts, random probes within its own subtree). They use no information from other programs, so LOPO and
LOFO would be identical to no split for them.

What can be asked is whether the accuracy of a baseline varies with the program family. This script aggregates the per-group rho of every
baseline (the machinery of fit_all_baselines_fair_comparison.py) by family (the FAMILY dict of fit_hybrid_model.py), the taxonomy that is also
used for the per-family LOFO breakdown of M1 to M6.

Usage:
    python fit_baselines_per_family.py"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO 
from fit_hybrid_model import FAMILY  
from fit_jpf_builtin_estimator_baseline import state_count_estimator_predictions  
from fit_jpfbar_baseline import jpfbar_predictions  
from fit_knuth_probing_baseline import knuth_probe_predictions  
from fit_kilby_wbe_baseline import wbe_predictions 
from fit_group_c_baseline import recursive_estimator_predictions_with_ids 


def per_group_rho_from(df, predictor_fn, needs_rng=False, rng=None, use_non_leaf_only=False):
    all_a, all_p, all_g = [], [], []
    iterate_df = df
    for program, prog_df in iterate_df.groupby("program"):
        if needs_rng:
            a, p, _ = predictor_fn(prog_df, rng)
        else:
            a, p, _ = predictor_fn(prog_df)
        g = prog_df["program_group"].iloc[0]
        all_a.extend(a); all_p.extend(p); all_g.extend([g] * len(a))
    scored = pd.DataFrame({"program_group": all_g, "actual": all_a, "pred": all_p})
    per_group = {}
    for g, sub in scored.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
            continue
        if sub["actual"].nunique() < 2 or sub["pred"].nunique() < 2:
            continue
        r, _ = spearmanr(sub["actual"], sub["pred"])
        if not np.isnan(r):
            per_group[g] = r
    return per_group


def main():
    df = load_all()
    non_leaf = df[df["isEndStateAtEntry"] == False].copy()  
    rng = np.random.default_rng(42)

    print("Computing per-group rho for all six baselines...\n")

    results = {}
    results["1 JPF built-in"] = per_group_rho_from(df, state_count_estimator_predictions)
    results["2 JPFBar"] = per_group_rho_from(df, jpfbar_predictions)
    results["3 Knuth probing"] = per_group_rho_from(df, knuth_probe_predictions, needs_rng=True, rng=rng)
    results["4 Kilby WBE"] = per_group_rho_from(df, wbe_predictions)

    results["6 State-count floor"] = {}
    for g, sub in non_leaf.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO or sub["stateId"].nunique() < 2:
            continue
        r, _ = spearmanr(sub["stateId"], sub["actualSubtreeWork"])
        if not np.isnan(r):
            results["6 State-count floor"][g] = r

    gc_per_group = {}
    for program, prog_df in non_leaf.groupby("program"):
        a, p, _ = recursive_estimator_predictions_with_ids(prog_df)
        g = prog_df["program_group"].iloc[0]
        if not a:
            continue
        tmp = pd.DataFrame({"a": a, "p": p})
        key = g
        if key not in gc_per_group:
            gc_per_group[key] = []
        gc_per_group[key].append(tmp)
    gc_final = {}
    for g, dfs in gc_per_group.items():
        sub = pd.concat(dfs, ignore_index=True)
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO or sub["a"].nunique() < 2:
            continue
        r, _ = spearmanr(sub["a"], sub["p"])
        if not np.isnan(r):
            gc_final[g] = r
    results["5 Group C"] = gc_final

    families = sorted(set(FAMILY.values()))
    missing_from_family = set()
    for baseline_pg in results.values():
        for g in baseline_pg:
            if g not in FAMILY:
                missing_from_family.add(g)
    if missing_from_family:
        print(f"WARNING: groups scored by a baseline but missing from FAMILY: {missing_from_family}\n")

    print("=== Per-family mean rho, all six baselines side by side ===")
    print("(NOT a generalization test -- these are parameter-free formulas with no cross-program")
    print(" training; this shows whether each baseline's OWN accuracy varies by program family.)\n")
    header = f"{'family':<22}" + "".join(f"{n.split()[0]:>7}" for n in results) + "  n_groups"
    print(header)
    for family in families:
        groups_in_family = [g for g, f in FAMILY.items() if f == family]
        row = f"{family:<22}"
        any_data = False
        for name, pg in results.items():
            rhos = [pg[g] for g in groups_in_family if g in pg]
            if rhos:
                row += f"{np.mean(rhos):>7.2f}"
                any_data = True
            else:
                row += f"{'--':>7}"
        row += f"  {len(groups_in_family)}"
        if any_data:
            print(row)

    print("\n=== Summary: best/worst family per baseline ===")
    for name, pg in results.items():
        fam_means = {}
        for family in families:
            groups_in_family = [g for g, f in FAMILY.items() if f == family]
            rhos = [pg[g] for g in groups_in_family if g in pg]
            if rhos:
                fam_means[family] = np.mean(rhos)
        if not fam_means:
            continue
        best = max(fam_means, key=fam_means.get)
        worst = min(fam_means, key=fam_means.get)
        print(f"{name:<24} best={best} ({fam_means[best]:.3f})   worst={worst} ({fam_means[worst]:.3f})   "
              f"spread={fam_means[best]-fam_means[worst]:.3f}")



if __name__ == "__main__":
    main()
