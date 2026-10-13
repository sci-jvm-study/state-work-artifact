"""Models M1 to M5 under leave-one-program-out (LOPO) cross-validation, on non-leaf states only (leaves have zero work by construction).

Reads every archived CSV in ../data/<family>/<Program>.csv and fits simple models to log(1 + actualSubtreeWork). It reports the pooled
Spearman rho (one value over all rows, dominated by the large groups) and the macro Spearman rho (the mean of each program group's own rho,
so every group counts equally) side by side. This file also holds the data loading, the feature groups and the metrics that most other
scripts import.

Splits are made by program group and never by state, because ancestors and siblings share subtrees and a state-level split leaks. All
variants of one algorithm (wider range, more elements) are held out together. PROGRAM_GROUP_OVERRIDES lists the groups explicitly, because a
filename suffix such as InsertionSort5 cannot tell a variant from an unrelated program. A new variant must be added by hand, and a program that
is not listed is its own group.

Usage:
    python models_m1_to_m5.py"""

import glob
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
from sklearn.linear_model import LinearRegression

# Maps a config/program name (CSV filename, no extension) to the underlying
# algorithm it shares with other entries -- these are held out TOGETHER in
# LOPO, never split across train/test. Add to this by hand whenever a new
# variant (range, element count, whatever) of an EXISTING program is created.
PROGRAM_GROUP_OVERRIDES = {
    "InsertionSort5": "InsertionSort",
    "InsertionSort_wideR": "InsertionSort",
    "Tsp_wideR": "Tsp",
    "ArrayUtilsIndexOf_wideR": "ArrayUtilsIndexOf",
    "ArrayUtilsIndexOf6": "ArrayUtilsIndexOf",
    "ArrayUtilsIsSorted6": "ArrayUtilsIsSorted",
    "BellmanFord_wideR": "BellmanFord",
    "BinaryTreeInsert4": "BinaryTreeInsert",
    "BinaryTreeInsert5": "BinaryTreeInsert",
    "SortedListInsert5": "SortedListInsert",
    "NumberUtilsMaxArray6": "NumberUtilsMaxArray",
    # BranchTree, BranchTree4 and BranchTree5 are the same symmetric-tree algorithm at different depths.
    "BranchTree4": "BranchTree",
    "BranchTree5": "BranchTree",
    "BellmanFord3": "BellmanFord",
    "CombinedWork3": "CombinedWork",
    "HeapWork3": "HeapWork",
    "UnequalWork3": "UnequalWork",
    "UnevenTree2": "UnevenTree",
    "Tsp4": "Tsp",
    "ArrayUtilsIndexOf8": "ArrayUtilsIndexOf",
    "ArrayUtilsLastIndexOf8": "ArrayUtilsLastIndexOf",
    "NumberUtilsMaxArray8": "NumberUtilsMaxArray",
    "Learn2": "Learn",
    "CombinedWork4": "CombinedWork",
    "UnevenTree3": "UnevenTree",
    "HeapWork4": "HeapWork",
    "UnequalWork4": "UnequalWork",
    "BinaryTreeInsertSearch": "BinaryTreeInsert",
    "InsertionSort6": "InsertionSort",
    "ArrayUtilsIndexOf10": "ArrayUtilsIndexOf",
    "ArrayUtilsLastIndexOf10": "ArrayUtilsLastIndexOf",
    "ArrayUtilsIsSorted8": "ArrayUtilsIsSorted",
    "NumberUtilsMaxArray10": "NumberUtilsMaxArray",
    "SortedListInsert6": "SortedListInsert",
    "BellmanFord4": "BellmanFord",
    "EuclideanGcd_wideR": "EuclideanGcd",
    "BranchTree6": "BranchTree",
    "HeapWork5": "HeapWork",
    "CombinedWork5": "CombinedWork",
    "UnequalWork5": "UnequalWork",
    "UnevenTree4": "UnevenTree",
    # RbTreeInsert is its own new program_group (no siblings yet, so no
    # override entry needed -- defaults to own name).
    "RbTreeInsert2": "RbTreeInsert",
    "BankAccountChain": "BankAccount",
    "LinkedListFind5": "LinkedListFind",
    # BankAccount_choco and ArrayUtilsIndexOf_choco have the same tree as their Z3 counterparts, so they are pooled with them and are not
    # treated as independent LOPO units. RecursiveAddition_choco is deliberately not mapped: its tree differs (162 states against 21), and
    # pooling it with RecursiveAddition, which is in the training fold of nearly every other group, would change the training data of almost
    # every fold. Left unmapped, it forms its own program group.
    "BankAccount_choco": "BankAccount",
    "ArrayUtilsIndexOf_choco": "ArrayUtilsIndexOf",
    # Four more pairs with the same structure as their Z3 counterpart (same row count, leaf count and maximum depth):
    "ValidateInclusiveBetween_choco": "ValidateInclusiveBetween",
    "NumberUtilsMaxArray_choco": "NumberUtilsMaxArray",
    "NumberUtilsMax3_choco": "NumberUtilsMax3",
    "MutableIntOps_choco": "MutableIntOps",
}


def program_group_of(program_name: str) -> str:
    """Returns the underlying-algorithm group for LOPO splitting. See the
    module docstring and PROGRAM_GROUP_OVERRIDES above."""
    return PROGRAM_GROUP_OVERRIDES.get(program_name, program_name)

# The archived datasets live in ../data/, one level up from this file.
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

FEATURE_GROUPS = {
    "M1_depth_only": ["depth"],
    "M2_static_only": [
        "remainingBytecodesInMethod", "reachableBranchCount",
        "reachableLoopBackEdgeCount", "reachableVirtualCallCount",
        "reachableAllocSiteCount", "reachableAthrowCount",
    ],
    "M3_dynamic_only": [
        "choiceGeneratorTotal", "choiceGeneratorProcessed",
        "pathConditionSize", "threadCount",
    ],
    "M5_static_plus_dynamic": [
        "remainingBytecodesInMethod", "reachableBranchCount",
        "reachableLoopBackEdgeCount", "reachableVirtualCallCount",
        "reachableAllocSiteCount", "reachableAthrowCount",
        "choiceGeneratorTotal", "choiceGeneratorProcessed",
        "pathConditionSize", "threadCount",
    ],
}


def load_all():
    rows = []
    for path in glob.glob(os.path.join(DATA_DIR, "*", "*.csv")):
        family = os.path.basename(os.path.dirname(path))
        program = os.path.splitext(os.path.basename(path))[0]
        df = pd.read_csv(path)
        df["family"] = family
        df["program"] = program
        df["program_group"] = program_group_of(program)
        rows.append(df)
    from prune import mark_pruned
    return mark_pruned(pd.concat(rows, ignore_index=True))


# Minimum non-leaf rows a held-out group must have before its own Spearman
# rho counts toward the macro average. With exactly 2 points, Spearman rho is always
# +-1 (only two rank orderings exist), which carries no information
# (scipy.stats.spearmanr([1,2],[5,3]) gives exactly -1.0). 5 is still
# a small sample for a rank correlation, but is the point where at least
# more than 2 distinct rank orderings become possible.
MIN_ROWS_FOR_GROUP_RHO = 5

# Bootstrap resamples for the macro-rho confidence interval below. Resamples
# PROGRAM GROUPS (with replacement), not individual rows -- rows within one
# program's state tree are not independent of each other (they share the
# same code, the same ground-truth listener run, and overlapping ancestry
# in the search tree), so row-level bootstrapping would understate the real
# uncertainty. Group-level resampling is the standard fix for exactly this
# clustered-data situation.
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 42


def concordance_index(actual, pred):
    """Concordance index -- fraction of comparable
    pairs (i,j) with actual_i != actual_j where the predicted order agrees
    with the actual order (ties in pred count as half-credit, standard
    survival-analysis C-index convention). Implemented via Kendall's tau-b
    (scipy, O(n log n)) rather than a naive O(n^2) pairwise loop -- for
    untied data, C = (tau_b + 1) / 2 exactly; scipy's tau-b already applies
    the standard tie correction, so this is the correct concordance index,
    not an approximation."""
    from scipy.stats import kendalltau
    actual = np.asarray(actual)
    pred = np.asarray(pred)
    if len(actual) < 2 or len(set(actual)) < 2 or len(set(pred)) < 2:
        return float("nan")
    tau, _ = kendalltau(actual, pred)
    if np.isnan(tau):
        return float("nan")
    return (tau + 1.0) / 2.0


def r_squared_log(actual_log, pred_log):
    """R^2 on the log1p scale (the scale on which every model is fitted) -- 1 - SS_res/SS_tot. Standard coefficient of
    determination, one of the paper's four reported evaluation metrics."""
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    if len(actual_log) < 2:
        return float("nan")
    ss_res = np.sum((actual_log - pred_log) ** 2)
    ss_tot = np.sum((actual_log - actual_log.mean()) ** 2)
    if ss_tot == 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def relative_mae(actual_log, pred_log):
    """Relative MAE on the original (not log) work scale: mean(|actual - pred|) / mean(actual), after inverting the log1p transform.
    Linear models (M2, M5) can extrapolate far outside the range on held-out rows with feature combinations that are not in the training
    data. After expm1() a single such row gives an enormous error that dominates this mean-based ratio (M2 and M5 reach billions on this
    corpus). relative_mae_median() is robust to this, and both are reported."""
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    actual_orig = np.expm1(actual_log)
    pred_orig = np.expm1(np.clip(pred_log, -50, 50))  # guard against inf/overflow, not against large-but-finite
    denom = actual_orig.mean()
    if denom == 0 or len(actual_orig) == 0:
        return float("nan")
    return float(np.mean(np.abs(actual_orig - pred_orig)) / denom)


def relative_mae_median(actual_log, pred_log):
    """Median-based counterpart to relative_mae() -- median(|actual-pred|) /
    median(actual), robust to the single-catastrophic-outlier fragility
    relative_mae() can surface for linear models under LOPO extrapolation.
    Report alongside the mean version, not instead of it -- the divergence
    between them (when it occurs) IS the finding."""
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    actual_orig = np.expm1(actual_log)
    pred_orig = np.expm1(np.clip(pred_log, -50, 50))
    denom = np.median(actual_orig)
    if denom == 0 or len(actual_orig) == 0:
        return float("nan")
    return float(np.median(np.abs(actual_orig - pred_orig)) / denom)


def macro_average(per_group_rho, weight_fn=None):
    """Mean of per-group rho values, optionally weighted. weight_fn(group,
    n_rows) -> weight; None means every included group counts equally
    (the plain macro average)."""
    if not per_group_rho:
        return float("nan")
    if weight_fn is None:
        return float(np.mean(list(per_group_rho.values())))
    weights = np.array([weight_fn(g) for g in per_group_rho])
    values = np.array(list(per_group_rho.values()))
    return float(np.average(values, weights=weights))


def holm_bonferroni(pvalues, alpha=0.05):
    r"""Holm-Bonferroni step-down correction for a family of hypothesis tests (Holm 1979; recommended for software-engineering paired
    comparisons by Arcuri and Briand~\cite{arcuri2014hitchhiker}). pvalues: list of raw p-values (any order). Returns a list of
    (adjusted p-value, reject at alpha) in the SAME order as the input, where adjusted p-values are monotone non-decreasing in rank
    (the standard reporting convention) and a hypothesis is rejected iff its adjusted p is below alpha."""
    n = len(pvalues)
    order = sorted(range(n), key=lambda i: pvalues[i])
    adj = [0.0] * n
    running_max = 0.0
    for rank, i in enumerate(order):
        raw_adj = min((n - rank) * pvalues[i], 1.0)
        running_max = max(running_max, raw_adj)
        adj[i] = running_max
    return [(adj[i], adj[i] < alpha) for i in range(n)]


def rank_biserial(a, b):
    """Matched-pairs rank-biserial correlation, the effect size that belongs with a paired (two-sided) Wilcoxon signed-rank test on a and b
    (Kerby 2014, 'The simple difference formula'; equivalently r = 1 - 4W/(n(n+1)) using the smaller signed-rank sum W). NOT the Vargha-Delaney
    A12 statistic: A12 is defined for two INDEPENDENT samples (its own Mann-Whitney U test); our comparisons are the same program groups scored
    twice.
    r in [-1, 1]; sign matches whether a tends to exceed b; |r| of about 0.1/0.3/0.5 is conventionally small/medium/large (same convention as A12,
    which r is on the same -1..1 scale as, doubled: r = 2*(A12-0.5)). Returns nan if fewer than 1 non-tied pair."""
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    d = d[d != 0]
    if len(d) == 0:
        return float("nan")
    ranks = rankdata(np.abs(d))
    w_pos = ranks[d > 0].sum()
    w_neg = ranks[d < 0].sum()
    return (w_pos - w_neg) / (w_pos + w_neg)


def bootstrap_macro_ci(per_group_rho, n_boot=N_BOOTSTRAP, seed=BOOTSTRAP_SEED):
    """95% percentile CI for the plain macro-average rho, resampling which
    program groups are included (with replacement) n_boot times."""
    groups = list(per_group_rho.keys())
    if len(groups) < 4:
        return (float("nan"), float("nan"))
    values = np.array([per_group_rho[g] for g in groups])
    rng = np.random.default_rng(seed)
    boot_means = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, len(values), size=len(values))
        boot_means[b] = values[idx].mean()
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return float(lo), float(hi)


def run_lopo(non_leaf, program_groups, features, sample_weighted=False, model_factory=None):
    """One LOPO pass for one feature set. If sample_weighted, each training
    row is weighted 1/(size of its own program_group) so the FIT itself
    doesn't get dominated by large groups -- this is the training-side
    counterpart to macro-averaging, which only rebalances the eval side.
    model_factory: zero-arg callable returning a fresh unfit sklearn-style
    regressor; defaults to LinearRegression (M1-M5's model throughout this
    project). Pass e.g. `lambda: RandomForestRegressor(n_estimators=200,
    random_state=42)` to run the same LOPO/macro/CI pipeline with a
    different model -- added so Random Forest could be compared against M5
    on identical footing rather than a separately-written pipeline."""
    if model_factory is None:
        model_factory = LinearRegression
    preds, actuals, groups_of_row = [], [], []
    per_group_rho = {}
    group_sizes = non_leaf["program_group"].value_counts().to_dict()

    for held_out in program_groups:
        train = non_leaf[non_leaf["program_group"] != held_out]
        test = non_leaf[non_leaf["program_group"] == held_out]
        if len(train) < 3 or len(test) == 0:
            continue

        X_train = train[features].values
        y_train = train["logWork"].values
        X_test = test[features].values
        y_test = test["logWork"].values

        model = model_factory()
        if sample_weighted:
            w = train["program_group"].map(group_sizes).apply(lambda n: 1.0 / n).values
            model.fit(X_train, y_train, sample_weight=w)
        else:
            model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        preds.extend(y_pred)
        actuals.extend(y_test)
        groups_of_row.extend([held_out] * len(y_test))

        if len(y_test) >= MIN_ROWS_FOR_GROUP_RHO and len(set(y_test)) >= 2 and len(set(y_pred)) >= 2:
            g_rho, _ = spearmanr(y_test, y_pred)
            if not np.isnan(g_rho):
                per_group_rho[held_out] = g_rho

    pooled_rho = (spearmanr(actuals, preds)[0]
                  if len(set(actuals)) >= 2 and len(set(preds)) >= 2 else float("nan"))
    return {
        "pooled_rho": pooled_rho,
        "macro_rho": macro_average(per_group_rho),
        "macro_rho_sqrtw": macro_average(per_group_rho, weight_fn=lambda g: np.sqrt(group_sizes[g])),
        "per_group_rho": per_group_rho,
        "n_groups_in_macro": len(per_group_rho),
        "preds": preds, "actuals": actuals, "groups_of_row": groups_of_row,
    }


def main():
    df = load_all()
    print(f"Loaded {len(df)} total state rows across {df['program'].nunique()} programs "
          f"({df['family'].nunique()} families).")

    # Leaves are trivially actualSubtreeWork == 0 and have sentinel -1 static
    # features (thread already terminated at entry) -- exclude them, they are
    # not an interesting or even well-defined prediction target/feature row.
    non_leaf = df[df["isEndStateAtEntry"] == False].copy()
    print(f"Non-leaf (internal) states: {len(non_leaf)}")

    non_leaf["logWork"] = np.log1p(non_leaf["actualSubtreeWork"])
    program_groups = sorted(non_leaf["program_group"].unique())
    n_configs = non_leaf["program"].nunique()
    if n_configs != len(program_groups):
        print(f"NOTE: {n_configs} configs collapse into {len(program_groups)} "
              f"program groups for LOPO (range-variants grouped together).")
    print(f"Program groups (LOPO units): {program_groups}\n")

    # Row-share check: a few large groups dominate the pooled rho, which is why the macro rho is reported next to it.
    group_sizes = non_leaf["program_group"].value_counts()
    top4_share = group_sizes.head(4).sum() / len(non_leaf)
    print("Row share check: top 4 program groups "
          f"({', '.join(group_sizes.head(4).index)}) hold "
          f"{top4_share:.1%} of all non-leaf rows.\n")

    print("=== A. Unweighted training (baseline) ===")
    print(f"{'Model':<24} {'Pooled rho':>11} {'Macro rho':>10} {'Macro 95% CI':>16} "
          f"{'sqrt(n)-weighted':>17} {'groups':>7}")
    per_group_mae = {}
    per_group_rho_table = {}
    unweighted_results = {}
    for model_name, features in FEATURE_GROUPS.items():
        res = run_lopo(non_leaf, program_groups, features, sample_weighted=False)
        unweighted_results[model_name] = res
        ci_lo, ci_hi = bootstrap_macro_ci(res["per_group_rho"])
        print(f"{model_name:<24} {res['pooled_rho']:>11.3f} {res['macro_rho']:>10.3f} "
              f"[{ci_lo:>6.3f},{ci_hi:>6.3f}] {res['macro_rho_sqrtw']:>17.3f} "
              f"{res['n_groups_in_macro']:>7}")

        errs = pd.DataFrame({"group": res["groups_of_row"],
                              "abs_err": np.abs(np.array(res["preds"]) - np.array(res["actuals"]))})
        per_group_mae[model_name] = errs.groupby("group")["abs_err"].mean().to_dict()
        per_group_rho_table[model_name] = res["per_group_rho"]

    print("\n=== B. Sample-weighted training (each row weighted 1/|its program_group|) ===")
    print("Tests whether the pooled/macro gap in section A is a TRAINING-side imbalance effect,")
    print("not just an evaluation-side one -- weighting flattens each group's influence on the fit itself.")
    print(f"{'Model':<24} {'Pooled rho':>11} {'Macro rho':>10} {'groups':>7}")
    for model_name, features in FEATURE_GROUPS.items():
        res = run_lopo(non_leaf, program_groups, features, sample_weighted=True)
        print(f"{model_name:<24} {res['pooled_rho']:>11.3f} {res['macro_rho']:>10.3f} "
              f"{res['n_groups_in_macro']:>7}")

    print("\n=== Per-program-group MAE (log-space), unweighted training, by model ===")
    header = f"{'program_group':<20}" + "".join(f"{m:>16}" for m in FEATURE_GROUPS)
    print(header)
    for g in program_groups:
        row = f"{g:<20}"
        for m in FEATURE_GROUPS:
            v = per_group_mae[m].get(g)
            row += f"{v:>16.2f}" if v is not None else f"{'--':>16}"
        print(row)

    print(f"\n=== Per-program-group Spearman rho, unweighted training, by model "
          f"(blank = < {MIN_ROWS_FOR_GROUP_RHO} rows, excluded from macro average) ===")
    print(header)
    for g in program_groups:
        row = f"{g:<20}"
        for m in FEATURE_GROUPS:
            v = per_group_rho_table[m].get(g)
            row += f"{v:>16.2f}" if v is not None else f"{'--':>16}"
        print(row)

    print("\nThe models are scored on log(1 + work) directly, without a program-level normalization of the target.")


if __name__ == "__main__":
    main()
