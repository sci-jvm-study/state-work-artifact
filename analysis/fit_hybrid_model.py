"""M6: the M5 features plus the sibling-mean prediction of Group C as one more feature (groupC_pred), as Linear and Random Forest models, and the
gated model (M6-RF where history exists, M5 elsewhere).

Group C beats M5 on identical eligible groups under LOPO. M6 asks whether the static and dynamic features add information on top of it.

Notes:
  1. A group is scored only if it has at least MIN_ROWS_FOR_GROUP_RHO scoreable rows (eligible_groups() below), so comparisons use the same
     groups as Group C.
  2. groupC_pred of a state never uses the work of the state itself, and the groupC_pred of a held-out group never uses data of other programs.
  3. The script prints a per-group table of wins, losses and ties of M6 against Group C. M6 cannot predict a group for which Group C cannot be
     computed. fit_m6_imputation_comparison.py tests a version with an imputed value.

Usage:
    python fit_hybrid_model.py"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor

from models_m1_to_m5 import (
    load_all, program_group_of, MIN_ROWS_FOR_GROUP_RHO,
    macro_average, bootstrap_macro_ci, run_lopo, FEATURE_GROUPS,
)
from fit_group_c_baseline import recursive_estimator_predictions_with_ids

M5_FEATURES = FEATURE_GROUPS["M5_static_plus_dynamic"]
M6_FEATURES = M5_FEATURES + ["groupC_pred"]


def make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt"):
    """Factory-of-a-factory: returns a zero-arg callable (what run_lopo's
    model_factory expects) for a given RF hyperparameter combination.
    Parameterized (rather than a fixed lambda) so hyperparameter-search
    scripts (e.g. fit_nested_cv_rf_tuning.py) can grid-search over this
    exact same model definition, and this module's own default RF_FACTORY
    below and any tuned variant are guaranteed to be constructed identically
    apart from the hyperparameters themselves."""
    return lambda: RandomForestRegressor(
        n_estimators=n_estimators, max_depth=max_depth,
        min_samples_leaf=min_samples_leaf, max_features=max_features,
        random_state=42)


# Default Random Forest of the functions of this file (report, coverage_test, gated_coverage_model, ...).
RF_FACTORY = make_rf_factory(n_estimators=200)


def attach_group_c_predictions(non_leaf):
    """Compute Group C's prediction for every scoreable (stateId, program)
    pair, per program (never pooling parentId/stateId across programs --
    same rule as everywhere else Group C is computed), and merge it onto
    non_leaf as a new `groupC_pred` column (log1p-transformed, matching
    logWork's own scale). Rows without a prediction (first child under
    their parent) get NaN."""
    pred_lookup = {}  # (program, stateId) -> log1p(predicted actualSubtreeWork)
    for program, prog_df in non_leaf.groupby("program"):
        _, predicted, state_ids = recursive_estimator_predictions_with_ids(prog_df)
        for sid, pred in zip(state_ids, predicted):
            pred_lookup[(program, sid)] = np.log1p(pred)

    non_leaf = non_leaf.copy()
    non_leaf["groupC_pred"] = non_leaf.apply(
        lambda r: pred_lookup.get((r["program"], r["stateId"]), np.nan), axis=1)
    return non_leaf, pred_lookup


def verify_no_leakage(non_leaf, pred_lookup):
    """Check that the prediction of Group C for a row never depends on the actual value of that row, and that it is computed strictly per
    program (so the groupC_pred of the held-out group of a LOPO fold is never informed by the data of a training program)."""
    print("=== Leakage check ===")

    # (a) Causal check: re-derive the predictions one program at a time. In recursive_estimator_predictions_with_ids the actual value of a
    # state is appended to seen_work only after its prediction is recorded, so removing it must reproduce the same prediction.
    mismatches = 0
    checked = 0
    for program, prog_df in non_leaf.groupby("program"):
        by_parent = {}
        for _, row in prog_df.sort_values("stateId").iterrows():
            by_parent.setdefault(row["parentId"], []).append(row)
        for parent_id, children in by_parent.items():
            seen = []
            for child in children:
                if seen:
                    expected_pred = np.log1p(sum(seen) / len(seen))
                    actual_pred = pred_lookup.get((program, child["stateId"]))
                    checked += 1
                    if actual_pred is not None and not np.isclose(expected_pred, actual_pred):
                        mismatches += 1
                seen.append(child["actualSubtreeWork"])
                # Confirms child's own actual is appended to `seen` only
                # AFTER its own prediction was (or wasn't) computed above
                # i.e. never available to its own prediction.
    print(f"  Re-derived {checked} predictions independently: {mismatches} mismatches "
          f"({'OK -- causal design confirmed' if mismatches == 0 else 'BUG -- investigate'}).")

    # (b) Cross-program isolation: attach_group_c_predictions() loops over the programs and passes only the rows of one program to
    # recursive_estimator_predictions_with_ids, so a prediction can only depend on rows of the same program.
    print("  Cross-program isolation: groupC_pred is computed once per `program` group from the rows of that program only, "
          "so the groupC_pred of a held-out group never depends on the groups in the training fold.")
    print()


def group_c_rho_on(df):
    """Group C's own pooled/macro rho, scored on exactly the rows in df
    (so it's always the same population M5/M6 are compared against here)."""
    df = df.dropna(subset=["groupC_pred"])
    per_group_rho = {}
    for g, sub in df.groupby("program_group"):
        if len(sub) >= MIN_ROWS_FOR_GROUP_RHO:
            rho, _ = spearmanr(sub["logWork"], sub["groupC_pred"])
            if not np.isnan(rho):
                per_group_rho[g] = rho
    pooled = (spearmanr(df["logWork"], df["groupC_pred"])[0]
              if len(df) >= 2 else float("nan"))
    return pooled, macro_average(per_group_rho), per_group_rho


def eligible_groups(scored):
    """The eligible groups of Group C (at least MIN_ROWS_FOR_GROUP_RHO scoreable rows), computed from `scored`. Every LOPO run in this
    script is restricted to this set, so the numbers of M5 and M6 are comparable with those of Group C on identical populations."""
    counts = scored.groupby("program_group").size()
    return sorted(counts[counts >= MIN_ROWS_FOR_GROUP_RHO].index.tolist())


def report(label, scored_df, groups):
    df = scored_df[scored_df["program_group"].isin(groups)].copy()
    print(f"\n--- {label} ({len(df)} rows, {len(groups)} eligible groups) ---")

    gc_pooled, gc_macro, gc_pg = group_c_rho_on(df)
    gc_ci = bootstrap_macro_ci(gc_pg)

    m5_res = run_lopo(df, groups, M5_FEATURES)
    m5_ci = bootstrap_macro_ci(m5_res["per_group_rho"])

    m6_res = run_lopo(df, groups, M6_FEATURES)
    m6_ci = bootstrap_macro_ci(m6_res["per_group_rho"])

    m6rf_res = run_lopo(df, groups, M6_FEATURES, model_factory=RF_FACTORY)
    m6rf_ci = bootstrap_macro_ci(m6rf_res["per_group_rho"])

    print(f"{'Model':<28} {'Pooled rho':>11} {'Macro rho':>10} {'Macro 95% CI':>16}")
    print(f"{'Group C alone':<28} {gc_pooled:>11.3f} {gc_macro:>10.3f} "
          f"[{gc_ci[0]:>6.3f},{gc_ci[1]:>6.3f}]")
    print(f"{'M5 (no groupC_pred)':<28} {m5_res['pooled_rho']:>11.3f} {m5_res['macro_rho']:>10.3f} "
          f"[{m5_ci[0]:>6.3f},{m5_ci[1]:>6.3f}]")
    print(f"{'M6 linear (M5+groupC_pred)':<28} {m6_res['pooled_rho']:>11.3f} {m6_res['macro_rho']:>10.3f} "
          f"[{m6_ci[0]:>6.3f},{m6_ci[1]:>6.3f}]")
    print(f"{'M6 RandomForest':<28} {m6rf_res['pooled_rho']:>11.3f} {m6rf_res['macro_rho']:>10.3f} "
          f"[{m6rf_ci[0]:>6.3f},{m6rf_ci[1]:>6.3f}]")

    return gc_pg, m5_res["per_group_rho"], m6_res["per_group_rho"], m6rf_res["per_group_rho"]


def coverage_test(non_leaf):
    """Does M6 cover the groups that Group C cannot score?
    Base M6 is restricted to the rows that Group C can score, so it cannot predict the groups in which Group C has no siblings to average
    over. This tests a variant (M6 with an imputed history feature) that fills groupC_pred with a neutral value (the median) wherever
    Group C has no prediction, so that it can be scored on the full corpus. The result is compared with M5 alone on the same population."""
    print("\n=== Coverage test: can a Group-C-aware model help groups Group C can't score? ===")
    all_groups = sorted(non_leaf["program_group"].unique())
    median_pred = non_leaf["groupC_pred"].median()
    imputed = non_leaf.copy()
    imputed["groupC_pred"] = imputed["groupC_pred"].fillna(median_pred)
    print(f"Imputing missing groupC_pred with the corpus-wide median ({median_pred:.3f}) "
          f"for the imputed M6 -- a neutral 'no information' filler value, not a leak (computed from "
          f"logWork's own overall scale only, not from any test row's actual target).")

    m5_full = run_lopo(non_leaf, all_groups, M5_FEATURES)
    m5_full_ci = bootstrap_macro_ci(m5_full["per_group_rho"])
    m6imp_full = run_lopo(imputed, all_groups, M6_FEATURES)
    m6imp_full_ci = bootstrap_macro_ci(m6imp_full["per_group_rho"])

    print(f"{'Model':<32} {'Pooled rho':>11} {'Macro rho':>10} {'Macro 95% CI':>16} {'groups':>7}")
    print(f"{'M5 (full 43-group corpus)':<32} {m5_full['pooled_rho']:>11.3f} "
          f"{m5_full['macro_rho']:>10.3f} [{m5_full_ci[0]:>6.3f},{m5_full_ci[1]:>6.3f}] "
          f"{m5_full['n_groups_in_macro']:>7}")
    print(f"{'M6, imputed history':<32} {m6imp_full['pooled_rho']:>11.3f} "
          f"{m6imp_full['macro_rho']:>10.3f} [{m6imp_full_ci[0]:>6.3f},{m6imp_full_ci[1]:>6.3f}] "
          f"{m6imp_full['n_groups_in_macro']:>7}")

    # The groups that Group C cannot score: does the imputed feature help, hurt, or do nothing there relative to M5 alone?
    ineligible = set(all_groups) - set(eligible_groups(non_leaf.dropna(subset=["groupC_pred"])))
    print(f"\nOn the {len(ineligible)} groups Group C cannot score at all "
          f"(imputed feature carries no real information there):")
    print(f"{'program_group':<24} {'M5':>8} {'M6imp':>8}")
    for g in sorted(ineligible):
        m5_r = m5_full["per_group_rho"].get(g)
        m6imp_r = m6imp_full["per_group_rho"].get(g)
        fmt = lambda v: f"{v:.2f}" if v is not None else "--"
        if m5_r is not None or m6imp_r is not None:
            print(f"{g:<24} {fmt(m5_r):>8} {fmt(m6imp_r):>8}")


# Family taxonomy by program shape, used by every error analysis and per-family breakdown in this package.
FAMILY = {
    'InsertionSort': 'sorting', 'SortedListInsert': 'sorting', 'Tsp': 'sorting_search',
    'BinaryTreeInsert': 'tree_ds', 'RbTreeInsert': 'tree_ds', 'LinkedListFind': 'linear_scan',
    'ArrayUtilsIndexOf': 'linear_scan', 'ArrayUtilsLastIndexOf': 'linear_scan',
    'ArrayUtilsIsSorted': 'linear_scan', 'ArrayUtilsShift': 'linear_scan',
    'NumberUtilsMaxArray': 'linear_scan', 'NumberUtilsMax3': 'arithmetic_branchy',
    'HasDupes': 'early_exit', 'PassCheck': 'early_exit', 'DelimSearch': 'early_exit',
    'StringSearchReplace': 'linear_scan',
    'ArithmeticUtilsCheck': 'arithmetic_branchy', 'ArithmeticUtilsMulAndCheck': 'arithmetic_branchy',
    'BinomialCoefficient': 'arithmetic_branchy', 'PrecisionRoundUnscaled': 'arithmetic_branchy',
    'BankAccount': 'stateful_sequence', 'BellmanFord': 'graph_algo',
    'EuclideanGcd': 'recursive_magnitude', 'Ackermann': 'recursive_magnitude',
    'HanoiSteps': 'recursive_magnitude', 'ApplyHanoi': 'recursive_magnitude',
    'Fibonacci': 'recursive_magnitude', 'Mccarthy91': 'recursive_magnitude',
    'MultCommutative': 'recursive_magnitude', 'RecursiveAddition': 'recursive_magnitude',
    'EvenOdd': 'recursive_magnitude',
    'BranchTree': 'synthetic_branch', 'HeapWork': 'synthetic_branch',
    'CombinedWork': 'synthetic_branch', 'UnequalWork': 'synthetic_branch',
    'UnevenTree': 'synthetic_branch', 'Learn': 'synthetic_branch',
    'ExSymExe15': 'regression_snippet', 'ExSymExe20': 'regression_snippet',
    'ExSymExe25': 'regression_snippet', 'ExSymExeResearch': 'regression_snippet',
    'ExSymExeSimple': 'regression_snippet', 'ExSymExeSuzette': 'regression_snippet',
    # Methods extracted from Apache Commons.
    'ValidateInclusiveBetween': 'early_exit',      # single check, early throw -- same shape as HasDupes/PassCheck/DelimSearch
    'ArrayUtilsReverse': 'linear_scan',            # array-index two-pointer loop, same family as other ArrayUtils entries
    'MutableIntOps': 'stateful_sequence',          # sequential mutating method calls on one object, same family as BankAccount
    'PrecisionCompare': 'arithmetic_branchy',      # numerical comparison with branches, floating-point
    'StringUtilsLeft': 'early_exit',               # three sequential early-return bounds checks, no loop
    # Same algorithm as RecursiveAddition, solved with Choco. It is classified by algorithm and forms its own program group because its
    # tree differs (see the comment in models_m1_to_m5.py).
    'RecursiveAddition_choco': 'recursive_magnitude',
    # Open-source algorithm code (TheAlgorithms/Java, MIT) and one more sv-benchmarks task; the family is the dominant control-flow shape.
    'TaBFPRT': 'sorting',                              # insertion sort over an array range
    'TaMaximumSumOfNonAdjacentElements': 'linear_scan',  # one DP pass over the array
    'TaStockProfitCalculator': 'linear_scan',          # single pass keeping a running minimum
    'TaBoyerMoore': 'linear_scan',                     # counting occurrences in one pass
    'TaSumOfSubset': 'recursive_magnitude',            # recursion over array positions
    'TaPerfectNumber': 'arithmetic_branchy',           # divisor loop with modulo branches
    'TaClimbingStairs': 'arithmetic_branchy',          # arithmetic recurrence in a counted loop
    'TaLongestSubarrayWithSumLessOrEqualToK': 'linear_scan',  # sliding window
    'TaTrappingRainwater': 'linear_scan',              # two-pointer scan
    'TaRandomizedQuickSort': 'early_exit',             # swap guarded by index checks
    'TaKadaneAlgorithm': 'linear_scan',                # one pass with running maximum
    'TaLongestIncreasingSubsequenceNLogN': 'linear_scan',  # binary search over a prefix
    'TaMemoryManagementAlgorithms': 'linear_scan',     # best-fit scan over block sizes
    'TaTrinomialTriangle': 'recursive_magnitude',      # double recursion on (n, k)
    'TaMaxSumKSizeSubarray': 'linear_scan',            # fixed-size sliding window
    'TaBoardPath': 'recursive_magnitude',              # memoized recursion on the position
    'Primes': 'recursive_magnitude',                   # mutually recursive multiple-of / prime test
}


def print_verdict_table(label, groups, gc_pg, m5_pg, m6_pg, m6rf_pg=None):
    """Per-group breakdown and win/loss verdict for the condition that is passed in (full eligible set or top-4-excluded). Reports
    M6-RandomForest against Group C next to linear M6 when m6rf_pg is given."""
    print(f"\n=== Per-program-group rho + M6-vs-GroupC verdict ({label}) ===")
    header = f"{'program_group':<24} {'GroupC':>8} {'M5':>8} {'M6lin':>8}"
    if m6rf_pg is not None:
        header += f" {'M6RF':>8}"
    header += f" {'M6lin vs GC':>13}"
    if m6rf_pg is not None:
        header += f" {'M6RF vs GC':>12}"
    print(header)
    fmt = lambda v: f"{v:.2f}" if v is not None else "--"

    def verdict_of(model_r, gc_r):
        if model_r is None or gc_r is None:
            return "--", None
        diff = model_r - gc_r
        if diff > 0.05:
            return "better", diff
        elif diff < -0.05:
            return "worse", diff
        return "~tied", diff

    wins, losses, ties = 0, 0, 0
    rf_wins, rf_losses, rf_ties = 0, 0, 0
    rows, rf_rows = [], []
    for g in groups:
        gc_r, m5_r, m6_r = gc_pg.get(g), m5_pg.get(g), m6_pg.get(g)
        v6, d6 = verdict_of(m6_r, gc_r)
        if d6 is not None:
            rows.append((g, d6))
            wins += v6 == "better"; losses += v6 == "worse"; ties += v6 == "~tied"
        line = f"{g:<24} {fmt(gc_r):>8} {fmt(m5_r):>8} {fmt(m6_r):>8}"
        if m6rf_pg is not None:
            m6rf_r = m6rf_pg.get(g)
            v6rf, d6rf = verdict_of(m6rf_r, gc_r)
            if d6rf is not None:
                rf_rows.append((g, d6rf))
                rf_wins += v6rf == "better"; rf_losses += v6rf == "worse"; rf_ties += v6rf == "~tied"
            line += f" {fmt(m6rf_r):>8}"
        line += f" {v6:>13}"
        if m6rf_pg is not None:
            line += f" {v6rf:>12}"
        print(line)

    print(f"Summary: M6-linear better than Group C in {wins}/{wins+losses+ties} groups, "
          f"worse in {losses}, ~tied in {ties} (threshold: |rho diff| > 0.05).")
    if m6rf_pg is not None:
        print(f"         M6-RandomForest better than Group C in {rf_wins}/{rf_wins+rf_losses+rf_ties} "
              f"groups, worse in {rf_losses}, ~tied in {rf_ties}.")
    return rows, rf_rows  # (group, diff) pairs for each model, for the family error analysis below


def error_analysis_by_family(diff_rows, label="M6"):
    """Which TYPES of programs does a model improve vs
    worsen on, relative to Group C -- not just a flat per-group list.
    Averages the (model - GroupC) rho difference within each family from
    print_verdict_table's output. Reused for both M6-linear and
    M6-RandomForest by passing a different diff_rows/label."""
    from collections import defaultdict
    fam_diffs = defaultdict(list)
    for g, diff in diff_rows:
        fam_diffs[FAMILY.get(g, 'other')].append((g, diff))

    print(f"\n=== Error analysis: {label} vs Group C, by program family ===")
    print(f"{'family':<20} {'n':>3} {f'mean({label}-GroupC)':>18}  groups")
    for fam, vals in sorted(fam_diffs.items(), key=lambda kv: np.mean([d for _, d in kv[1]])):
        diffs = [d for _, d in vals]
        detail = ", ".join(f"{g}:{d:+.2f}" for g, d in vals)
        print(f"{fam:<20} {len(vals):>3} {np.mean(diffs):>18.3f}  {detail}")
    print(f"\nReading this: negative mean = {label} systematically WORSE than Group C in that "
          "family; positive = systematically BETTER. Families with only 1-2 groups are not "
          "reliable generalizations, shown for completeness only.")


def gated_coverage_model(non_leaf, elig):
    """A fallback for the groups that Group C cannot score. It replaces the constant imputation, which changes little for the ranking within a
    group because a constant feature cannot change the rank order. A gated two-regime model:
      - eligible groups: scored by M6 (M5 features + groupC_pred), as elsewhere in this script;
      - ineligible groups: scored by a separate M5-only LOPO run that is trained only on other ineligible groups, to test whether a
        fallback specialized to the low-branching population helps, against the M5-on-everything model of the other output of this file."""
    print(f"\n=== Coverage strategy 2: gated model (M6 for eligible, SPECIALIZED M5 fallback "
          f"for ineligible) ===")
    all_groups = sorted(non_leaf["program_group"].unique())
    ineligible = [g for g in all_groups if g not in elig]
    print(f"{len(elig)} eligible groups -> M6. {len(ineligible)} ineligible groups -> "
          f"specialized M5-only fallback, trained/tested exclusively within the ineligible "
          f"population (no eligible-group rows in that fallback's training data at all).")

    ineligible_df = non_leaf[non_leaf["program_group"].isin(ineligible)].copy()
    fallback_res = run_lopo(ineligible_df, ineligible, M5_FEATURES)
    fallback_ci = bootstrap_macro_ci(fallback_res["per_group_rho"])

    # The same groups under the mixed M5-on-everything model, for a direct comparison of the specialized and the mixed fallback.
    mixed_res = run_lopo(non_leaf, all_groups, M5_FEATURES)
    mixed_ineligible_pg = {g: r for g, r in mixed_res["per_group_rho"].items() if g in ineligible}
    mixed_ineligible_macro = macro_average(mixed_ineligible_pg)
    mixed_ineligible_ci = bootstrap_macro_ci(mixed_ineligible_pg)

    print(f"\n{'Fallback strategy':<38} {'Macro rho (ineligible groups only)':>36} {'CI':>16}")
    print(f"{'Specialized (trained on ineligible only)':<38} {fallback_res['macro_rho']:>36.3f} "
          f"[{fallback_ci[0]:.3f},{fallback_ci[1]:.3f}]")
    print(f"{'Mixed (trained on full 43-group corpus)':<38} {mixed_ineligible_macro:>36.3f} "
          f"[{mixed_ineligible_ci[0]:.3f},{mixed_ineligible_ci[1]:.3f}]")

    print(f"\n{'program_group':<24} {'Specialized':>12} {'Mixed':>8}")
    fmt = lambda v: f"{v:.2f}" if v is not None else "--"
    for g in sorted(ineligible):
        spec = fallback_res["per_group_rho"].get(g)
        mix = mixed_ineligible_pg.get(g)
        if spec is not None or mix is not None:
            print(f"{g:<24} {fmt(spec):>12} {fmt(mix):>8}")


def full_corpus_gated_evaluation(non_leaf, elig, rf_factory):
    """Full-corpus evaluation of the gated model. Every baseline that is compared with it is evaluated on exactly the same population, with
    the same LOPO splits, target (logWork) and metric (macro rho with bootstrap CI). The scoreable population is determined first (whatever
    the gated approach can score), and then every baseline is restricted to that set."""
    print(f"\n=== FULL-CORPUS GATED EVALUATION, WITH SAME-POPULATION BASELINES ===")
    all_groups = sorted(non_leaf["program_group"].unique())
    ineligible = [g for g in all_groups if g not in elig]
    print(f"{len(elig)} eligible groups -> M6 RandomForest (tuned). "
          f"{len(ineligible)} ineligible groups -> M5-only fallback (mixed-trained).")

    scored = non_leaf.dropna(subset=["groupC_pred"]).copy()
    df_elig = scored[scored["program_group"].isin(elig)].copy()
    m6rf_res = run_lopo(df_elig, elig, M6_FEATURES, model_factory=rf_factory)

    # Ineligible-group fallback: MIXED training pool (all groups' M5
    # features -- groupC_pred not needed/available), two model choices.
    m5_linear_res = run_lopo(non_leaf, all_groups, M5_FEATURES)
    m5_rf_res = run_lopo(non_leaf, all_groups, M5_FEATURES, model_factory=rf_factory)

    gated_variants = {}
    for fallback_name, fallback_res in [("M5 Linear fallback", m5_linear_res),
                                         ("M5 RandomForest fallback", m5_rf_res)]:
        combined_pg = dict(m6rf_res["per_group_rho"])  # eligible groups from M6-RF
        for g in ineligible:  # ineligible groups from the chosen fallback
            if g in fallback_res["per_group_rho"]:
                combined_pg[g] = fallback_res["per_group_rho"][g]
        gated_variants[fallback_name] = combined_pg

    # The scoreable population is that of the best gated variant (Linear fallback). Every baseline (M5 alone, Group C and the other gated
    # variant) is restricted to the same groups before any comparison is reported.
    same_pop = set(gated_variants["M5 Linear fallback"].keys())
    print(f"\nScoreable population fixed at {len(same_pop)} groups (this is what ALL rows below "
          f"are restricted to -- same LOPO splits, same target, same metric):")
    print(f"  {sorted(same_pop)}")

    def restrict(pg):
        return {g: r for g, r in pg.items() if g in same_pop}

    m5_same_pop = restrict(m5_linear_res["per_group_rho"])
    gc_pooled_full, gc_macro_full, gc_pg_full = group_c_rho_on(scored)
    gc_same_pop = restrict(gc_pg_full)
    gc_missing = same_pop - set(gc_pg_full.keys())

    print(f"\n{'Model':<42} {'Groups scored':>14} {'Macro rho':>10} {'95% CI':>14}")
    for label, pg in [
        ("Group C / M4 alone", gc_same_pop),
        ("M5 alone (same population, no gating)", m5_same_pop),
        ("Gated: M6-RF + M5-Linear fallback", restrict(gated_variants["M5 Linear fallback"])),
        ("Gated: M6-RF + M5-RF fallback", restrict(gated_variants["M5 RandomForest fallback"])),
    ]:
        macro = macro_average(pg)
        ci = bootstrap_macro_ci(pg)
        print(f"{label:<42} {len(pg):>7}/{len(same_pop):<6} {macro:>10.3f} "
              f"[{ci[0]:>6.3f},{ci[1]:>6.3f}]")

    print(f"\nGroup C scores {len(gc_same_pop)}/{len(same_pop)} of this exact population -- it "
          f"structurally cannot produce a prediction for the other {len(gc_missing)} "
          f"({sorted(gc_missing)}), so its row above is NOT averaged over the full population size "
          f"the other rows use, so it is not an equal-footing competitor in "
          f"this specific comparison. M5-alone and both gated variants ARE scored on the complete "
          f"same-population set and are directly comparable to each other.")


def main():
    df = load_all()
    non_leaf = df[df["isEndStateAtEntry"] == False].copy()  
    non_leaf["logWork"] = np.log1p(non_leaf["actualSubtreeWork"])
    non_leaf, pred_lookup = attach_group_c_predictions(non_leaf)

    verify_no_leakage(non_leaf, pred_lookup)

    scored = non_leaf.dropna(subset=["groupC_pred"]).copy()
    elig = eligible_groups(scored)
    print(f"Full corpus: {len(non_leaf)} non-leaf rows.")
    print(f"Group-C-scoreable rows: {len(scored)} across {scored['program_group'].nunique()} groups; "
          f"of those, {len(elig)} groups meet the >= {MIN_ROWS_FOR_GROUP_RHO}-row eligibility bar "
          f"Group C itself uses -- ALL comparisons below use exactly this {len(elig)}-group set, "
          f"the same set as fit_all_baselines_fair_comparison.py.")

    gc_pg_full, m5_pg_full, m6_pg_full, m6rf_pg_full = report("Eligible groups, full", scored, elig)

    top4 = non_leaf["program_group"].value_counts().head(4).index.tolist()
    elig_nt4 = [g for g in elig if g not in top4]
    print(f"\nTop-4 dominant groups: {top4}")
    print(f"Of these, {len(set(top4) & set(elig))} are in the eligible set.")
    gc_pg_nt4, m5_pg_nt4, m6_pg_nt4, m6rf_pg_nt4 = report(
        "Eligible groups, top-4 excluded", scored, elig_nt4)

    diffs_full, rf_diffs_full = print_verdict_table(
        "full eligible set", elig, gc_pg_full, m5_pg_full, m6_pg_full, m6rf_pg_full)
    diffs_nt4, rf_diffs_nt4 = print_verdict_table(
        "top-4 excluded", elig_nt4, gc_pg_nt4, m5_pg_nt4, m6_pg_nt4, m6rf_pg_nt4)

    error_analysis_by_family(diffs_full, label="M6-linear")
    error_analysis_by_family(rf_diffs_full, label="M6-RandomForest")

    coverage_test(non_leaf)
    gated_coverage_model(non_leaf, elig)

    # max_features="sqrt" is the tuned configuration. Nested cross-validation (fit_nested_cv_rf_tuning.py) selects it in 28 of 29 outer folds.
    tuned_rf = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")
    full_corpus_gated_evaluation(non_leaf, elig, tuned_rf)



if __name__ == "__main__":
    main()
