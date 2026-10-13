# Artifact for "When Counting States Misleads: Estimating the Work of a Single State in Java Symbolic Execution"

This package contains the data, the scripts and the outputs behind every table, figure and number of the paper. All scripts are
deterministic (fixed seeds), and every table of the paper can be recomputed from the data in this package.

## Requirements

- Python 3 with `pandas`, `numpy`, `scipy` and `scikit-learn` (`pip install -r analysis/requirements.txt`; the versions used are listed in that
  file). The results were produced with Python 3.13 on Windows 11.
- A JDK on `PATH` (for `javap`), which the static features of the COASTAL trees need (results 19, 20, 21 and 58).
- `bash` for `reproduce.sh` (Git Bash on Windows). `make_tables.py` needs only Python.

JPF, COASTAL and GDart are not needed to reproduce the tables. They are needed only to collect the data again (see "Beyond the tables").

## Reproducing the tables

Run these commands in this folder.

```
pip install -r analysis/requirements.txt
python make_tables.py 4          # one table, here Table 4 (about 2 minutes)
python make_tables.py            # Tables 3 to 9 (about 10 minutes)
python make_tables.py --from-archive   # the same tables from the files in results/ (seconds)
```

Each table is printed in the format of the paper. The scripts that compute it are in `analysis/` and `engines/`, and the table scripts are in
`tables/`. Tables 1 and 2 of the paper contain no computed numbers.

## Reproducing every result file

```
bash reproduce.sh results        # rewrites results/ (and the two figures); under an hour
bash reproduce.sh                # writes to results_new/ instead, to compare with results/
```

With the second form, every `.txt` file of `results_new/` is identical to the file of the same name in `results/`. The exception is
`33_coastal_attempts.txt`, which is not regenerated (see below). Two CSV files (`44_nesting_decomposition_groups.csv`
and `47_nesting_offline_groups.csv`) are always written to `results/`, because other scripts and the figures read them there.

## Layout

| Folder | Content |
|---|---|
| `data/` | One CSV per configuration (116 files), one row per state. The schema is in `data/README.md`. |
| `analysis/` | The scripts that compute the results. `models_m1_to_m5.py` (data loading, models M1 to M5, metrics), `fit_hybrid_model.py` (M6, gating) and `prune.py` (pruned choices) are imported by most of them. Also the predeclaration notes of the nesting analyses. |
| `tables/`, `make_tables.py` | One script per table (3 to 9). Each runs the analysis scripts it needs and prints the table as in the paper. |
| `results/` | The output of each script, numbered as in the table below. |
| `figures/` | `make_figures.py` writes Figure 1 and Figure 2. |
| `engines/` | The COASTAL and GDart harnesses, the patch, the compiled classes, the state trees built from their logs and the status of every run. |
| `heldout/` | The nine held-out programs, their preregistration, data, trees on the other engines and the selection record. |
| `live_estimator/` | The live listener, the two predeclaration notes, the raw live runs and the results of the live check. |
| `instrumentation/` | The JPF listener that records the per-state counters, the static lookahead, the solver counter, the patch for jpf-symbc and the build steps. |
| `benchmarks/` | The Java sources and `.jpf` configurations of the 66 program groups (116 configurations). |
| `larger_trees/` | The check on larger trees (wider symbolic ranges): the predeclaration, the sweep, the kept runs and the evaluation. |
| `corpus_selection/` | How the programs added to the corpus were screened and selected (49 chosen first, 17 added by mechanical screens). |

## Names in the scripts and the result files

| In scripts and results | In the paper |
|---|---|
| `actualSubtreeWork` | work `W(s)` below a state |
| `stateId`, "state-count floor", `floor` | live count (number of states created before the state) |
| `hindsight`, `nodeCount` | final subtree size `N(s)` |
| `Group C` | sibling mean (model M4, the history feature of M6) |
| `Knuth`, `Knuth 30` | random probing, 30 probes |
| `Kilby WBE` | weighted backtrack estimator |
| `JPF built-in`, `JPFBar` | the two progress estimators of JPF |
| `M1` to `M6`, `M5 RF`, `M6 RF` | the models of Table 2 (linear or Random Forest) |
| "gated" model | combined model (M6 where history exists, M5 elsewhere) |
| `-depth` | depth rule |
| cap, variant A | capping at the parent's capped prediction |
| "P55", "P29", "P9" | the populations of Section 4 (55 scoreable groups, 29 with history, nine held-out programs) |
| `pruned` | pruned choices (`analysis/prune.py`) |

## Where each item of the paper comes from

Result files are in `results/` unless a path is given.

| Paper item | Source |
|---|---|
| Introduction: spread of work among states at equal depth | `32_work_ratio.txt` |
| Section 3.3: bytecode instructions track wall-clock time (0.851 and 0.719) | `01_construct_validation.txt` |
| Section 3.3: corpus without the 17 added programs | `34_pre_extension_subset.txt` |
| Pruned choices (4,054 states) and their sensitivity analyses | `61`, `62`, `63`, `63b`, `64`, `65`, `69` |
| Section 4: Random Forest tuning (nested cross-validation) | `05_nested_cv_rf_tuning.txt` |
| Table 3 (summary), Section 5.1: live count against work, populations P55 and P29 | `02_models_m1_to_m5.txt`, `06_baselines_fair_comparison.txt`, `16_node_count_vs_work.txt`, `37_floor_by_cost_measure.txt`, `44_nesting_decomposition.txt` (live count negative in 51 of 55 groups) |
| Figure 1 | `figures/make_figures.py` (`fig1_divergence`, reads `data/`) |
| Figure 2, nested and non-nested pairs, chain-shaped groups | `44_nesting_decomposition.txt`, `44_nesting_decomposition_groups.csv`, `66_non_nested_pairs.txt` |
| Table 4 (comparison on P29) | `06_baselines_fair_comparison.txt`, `29_paired_tests_group_c.txt`, `51_multiple_comparison_correction.txt` |
| Table 5 (models under three splits), depth rule, families | `02`, `04_model_m6_and_gated.txt`, `09_generalization_splits.txt`, `07_baselines_per_family.txt`, `60_depth_rule.txt`, `15_m6_imputation_comparison.txt` |
| Magnitude errors | `38_calibration.txt` |
| Table 6 (Knuth probing cost) and its stability over random seeds | `14_knuth_online_cost.txt`, `17_knuth_matched_population.txt`, `71_probing_seed_sensitivity.txt` |
| Table 7 (load balancing), probing charged | `39_load_balance_replay.txt`, `45_load_balance_probe_cost.txt` |
| Section 5.5 (capping) and the offline projection | `46_nesting_consistency.txt`, `47_nesting_offline.txt`, `47_nesting_offline_groups.csv`, `analysis/nesting_consistency_predeclared.md` |
| Table 8 (JPF, COASTAL, GDart) and the chain from 116 to 68 configurations | `18`, `19`, `20`, `21`, `27`, `33_coastal_attempts.txt`, `52`, `53`, `engines/run_status_*.csv` |
| Table 9 (held-out programs) and the predeclared hypotheses | `40_heldout_evaluation.txt`, `41_heldout_feature_overlap.txt`, `57`, `58`, `59`, `heldout/PREREGISTRATION.md` |
| Section 7: larger trees (live count, depth rule and probing cost on the two programs with at least 5,000 states) | `70_larger_trees.txt`, `larger_trees/` |
| Live check (5.9%, about 8.0%, 3.4% to 12.6%) and progress bars (34.8 against 30.2 and 33.4) | `live_estimator/results/h1_fidelity.csv`, `h2_overhead.txt`, `h2_overhead_addendum.txt`, `stage2_h2.txt` |

## Beyond the tables

- **Not regenerated:** `results/33_coastal_attempts.txt` (the outcome of every COASTAL attempt) needs the raw COASTAL logs, which are not
  shipped. The output is archived.
- **Collecting the data again** needs JPF (`instrumentation/README.md`; also for `larger_trees/sweep.py`), COASTAL or GDart (`engines/README.md`) and, for the live check,
  the listener of `live_estimator/README.md`. The fitted forest of the live check (`live_estimator/model/`, 34 MB) is not shipped; `export_rf.py`
  recreates it.
- **Environment variables** for external tools: `JAVAP` (default: `javap` on `PATH`) in `engines/static_features.py`, `JPF_HOME` and
  `JAVA_HOME` in `live_estimator/jpf_run.py` and `larger_trees/`, and `HELDOUT_WORK` in the two scripts of `heldout/scripts/`. Everything else uses paths relative
  to the package.
- **Timings** of the live check come from one machine and vary from machine to machine. The other results do not depend on the machine.
