"""
Same-population comparison of the baselines (JPF built-in estimator, JPFBar, Knuth probing, Kilby WBE, Group C and the state-count floor).
Learch is not included: its target, the priority of a state-selection transition, has no per-state subtree-work value.

Each baseline script (fit_jpf_builtin_estimator_baseline.py, fit_jpfbar_baseline.py, fit_knuth_probing_baseline.py,
fit_kilby_wbe_baseline.py, fit_group_c_baseline.py) reports its macro rho over its own scoreable population, and these populations differ.
This script recomputes the per-group rho of every baseline and of the state-count floor (the live count), takes the population that every
baseline can score, and compares the macro rho on that same set.

Usage:
    python fit_all_baselines_fair_comparison.py
"""

import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(__file__))
from models_m1_to_m5 import ( 
    load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci,
)
from fit_jpf_builtin_estimator_baseline import state_count_estimator_predictions  
from fit_jpfbar_baseline import jpfbar_predictions  
from fit_knuth_probing_baseline import knuth_probe_predictions  
from fit_kilby_wbe_baseline import wbe_predictions  
from fit_group_c_baseline import recursive_estimator_predictions_with_ids  
import fit_hybrid_model as hm  
from fit_hybrid_model import (  
    attach_group_c_predictions, eligible_groups, M5_FEATURES, make_rf_factory,
)
from models_m1_to_m5 import run_lopo  


def per_group_rho_from(df, predictor_fn, needs_rng=False, rng=None):
    import pandas as pd
    all_a, all_p, all_g = [], [], []
    for program, prog_df in df.groupby("program"):
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

    print("Recomputing per-group rho for all six baselines...")
    rng = np.random.default_rng(42)

    results = {}
    results["1 JPF built-in"] = per_group_rho_from(df, state_count_estimator_predictions)
    results["2 JPFBar"] = per_group_rho_from(df, jpfbar_predictions)
    results["3 Knuth probing"] = per_group_rho_from(df, knuth_probe_predictions, needs_rng=True, rng=rng)
    results["4 Kilby WBE"] = per_group_rho_from(df, wbe_predictions)
    results["6 State-count floor"] = {}
    for g, sub in non_leaf.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
            continue
        if sub["stateId"].nunique() < 2 or sub["actualSubtreeWork"].nunique() < 2:
            continue
        r, _ = spearmanr(sub["stateId"], sub["actualSubtreeWork"])
        if not np.isnan(r):
            results["6 State-count floor"][g] = r

    # Group C uses only scoreable (non-first-child) rows, a different row population than the other five (which score every non-leaf row);
    # its per-group rho is computed as in fit_group_c_baseline.py. Leaves are excluded before the sibling structure is built, because
    # leaf rows would count as "seen siblings" with work 0 and would be scored themselves.
    gc_pg = {}
    for program, prog_df in non_leaf.groupby("program"):
        a, p, _ = recursive_estimator_predictions_with_ids(prog_df)
        g = prog_df["program_group"].iloc[0]
        if len(a) == 0:
            continue
        import pandas as pd
        tmp = pd.DataFrame({"a": a, "p": p})
        gc_pg.setdefault(g, []).append(tmp)
    gc_per_group = {}
    for g, dfs in gc_pg.items():
        import pandas as pd
        sub = pd.concat(dfs, ignore_index=True)
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO:
            continue
        if sub["a"].nunique() < 2 or sub["p"].nunique() < 2:
            continue
        r, _ = spearmanr(sub["a"], sub["p"])
        if not np.isnan(r):
            gc_per_group[g] = r
    results["5 Group C"] = gc_per_group

    # M6 models (linear and tuned RF), scored on Group C's own eligible
    # set the same population M6 is reported on in fit_hybrid_model.py.
    non_leaf_lw = non_leaf.copy()
    non_leaf_lw["logWork"] = np.log1p(non_leaf_lw["actualSubtreeWork"])
    non_leaf_lw, _ = attach_group_c_predictions(non_leaf_lw)
    scored_gc = non_leaf_lw.dropna(subset=["groupC_pred"]).copy()
    elig = eligible_groups(scored_gc)
    M6_FEATURES = M5_FEATURES + ["groupC_pred"]
    # max_features="sqrt": chosen by nested cross-validation (fit_nested_cv_rf_tuning.py), where 28 of 29 outer folds'
    # inner selections picked 'sqrt'.
    tuned_rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")

    # M6 is trained on the other eligible groups' rows only (the rule of fit_hybrid_model.py), so every M6 number in this package uses one training pool.
    scored_elig = scored_gc[scored_gc["program_group"].isin(elig)]
    m6lin_res = run_lopo(scored_elig, elig, M6_FEATURES)
    m6rf_res = run_lopo(scored_elig, elig, M6_FEATURES, model_factory=tuned_rf)
    results["7 M6 Linear"] = m6lin_res["per_group_rho"]
    results["8 M6 RandomForest"] = m6rf_res["per_group_rho"]

    print("\n=== Each baseline's OWN population (as individually reported) ===")
    print(f"{'Baseline':<24}{'Groups':>8}{'Macro rho':>12}")
    for name, pg in results.items():
        print(f"{name:<24}{len(pg):>8}{macro_average(pg):>12.3f}")

    same_pop = set.intersection(*[set(pg.keys()) for pg in results.values()])
    print(f"\n=== FAIR COMPARISON: same population all six can score ({len(same_pop)} groups) ===")
    print(f"Groups: {sorted(same_pop)}\n")

    def restrict(pg):
        return {g: r for g, r in pg.items() if g in same_pop}

    print(f"{'Baseline':<24}{'Groups':>8}{'Macro rho':>12}{'95% CI':>16}")
    for name, pg in results.items():
        r = restrict(pg)
        m = macro_average(r)
        ci = bootstrap_macro_ci(r)
        print(f"{name:<24}{len(r):>8}{m:>12.3f}  [{ci[0]:.3f},{ci[1]:.3f}]")

    print("\n=== Per-group rho, same population, all six side by side ===")
    header = f"{'group':<22}" + "".join(f"{n.split()[0]:>7}" for n in results)
    print(header)
    for g in sorted(same_pop):
        row = f"{g:<22}"
        for name, pg in results.items():
            row += f"{pg[g]:>7.2f}"
        print(row)

    # TABLE B: the larger population of the gated model. It is determined first and every other baseline is restricted to it (taking the
    # population from a baseline with a smaller reach would understate the coverage of the gated model). Group C cannot extend beyond its own
    # eligible groups, so it is shown with its partial coverage and not averaged over the full set.
    print("\n" + "=" * 78)
    print("=== TABLE B: gated M6-RF (eligible) + M5-RandomForest fallback (ineligible), ===")
    print("=== its own full scoreable population, other baselines restricted to it ===")
    # M5-RF is the fallback. On this corpus it beats the Linear fallback, because large, structurally different programs such as
    # ArrayUtilsReverse destabilize the global linear fit.

    all_groups = sorted(non_leaf["program_group"].unique())
    ineligible = [g for g in all_groups if g not in elig]
    m5_linear_res = run_lopo(non_leaf_lw, all_groups, M5_FEATURES)
    m5_rf_res = run_lopo(non_leaf_lw, all_groups, M5_FEATURES, model_factory=tuned_rf)

    gated_pg = dict(m6rf_res["per_group_rho"])
    for g in ineligible:
        if g in m5_rf_res["per_group_rho"]:
            gated_pg[g] = m5_rf_res["per_group_rho"][g]

    gated_pop = set(gated_pg.keys())
    print(f"\nGated model's own scoreable population: {len(gated_pop)} groups")

    # The baselines that are not structurally capped at the Group-C-eligible groups are restricted to the exact set of the gated model.
    print(f"\n{'Model':<24}{'Groups scored':>16}{'Macro rho':>12}{'95% CI':>16}")
    for name in ["1 JPF built-in", "2 JPFBar", "3 Knuth probing", "4 Kilby WBE",
                 "6 State-count floor"]:
        pg = results[name]
        r = {g: v for g, v in pg.items() if g in gated_pop}
        m = macro_average(r)
        ci = bootstrap_macro_ci(r)
        print(f"{name:<24}{len(r):>10}/{len(gated_pop):<5}{m:>12.3f}  [{ci[0]:.3f},{ci[1]:.3f}]")

    gc_r = {g: v for g, v in results["5 Group C"].items() if g in gated_pop}
    print(f"{'5 Group C':<24}{len(gc_r):>10}/{len(gated_pop):<5}{macro_average(gc_r):>12.3f}  "
          f"[{bootstrap_macro_ci(gc_r)[0]:.3f},{bootstrap_macro_ci(gc_r)[1]:.3f}]  "
          f"(structurally capped at its own {len(results['5 Group C'])} groups -- NOT averaged "
          f"over the full {len(gated_pop)}-group population, shown for context only)")

    m5_alone_lin_r = {g: v for g, v in m5_linear_res["per_group_rho"].items() if g in gated_pop}
    print(f"{'M5 alone, Linear (no gating)':<24}{len(m5_alone_lin_r):>10}/{len(gated_pop):<5}"
          f"{macro_average(m5_alone_lin_r):>12.3f}  [{bootstrap_macro_ci(m5_alone_lin_r)[0]:.3f},"
          f"{bootstrap_macro_ci(m5_alone_lin_r)[1]:.3f}]")

    m5_alone_rf_r = {g: v for g, v in m5_rf_res["per_group_rho"].items() if g in gated_pop}
    print(f"{'M5 alone, RF (no gating)':<24}{len(m5_alone_rf_r):>10}/{len(gated_pop):<5}"
          f"{macro_average(m5_alone_rf_r):>12.3f}  [{bootstrap_macro_ci(m5_alone_rf_r)[0]:.3f},"
          f"{bootstrap_macro_ci(m5_alone_rf_r)[1]:.3f}]")

    print(f"{'Gated M6-RF+M5-RF':<24}{len(gated_pg):>10}/{len(gated_pop):<5}"
          f"{macro_average(gated_pg):>12.3f}  [{bootstrap_macro_ci(gated_pg)[0]:.3f},"
          f"{bootstrap_macro_ci(gated_pg)[1]:.3f}]")



if __name__ == "__main__":
    main()
