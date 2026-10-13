# Held-out corpus: pre-registration

Written before any program of this held-out set was run on JPF or scored. Everything below is fixed in advance; the
results are reported whatever they are.

## Purpose
This set tests the conclusions on programs that were not used for selection rules, model fitting or tuning.

## Sources (shallow clones, licence checked before use)
| Library | Commit | Licence |
|---|---|---|
| apache/commons-numbers | f9403ff37998b49c6b85273713847c856d8ee47b | Apache-2.0 |
| apache/commons-rng | 6e5a0056b1a8405771431478f3e7c134dee35c14 | Apache-2.0 |
| phishman3579/java-algorithms-implementation | f2d115704691e8e4f6cfe490231d0adb0c3ce7d0 | Apache-2.0 |
| AllAlgorithms/java | 1af0c0bab97d9a03a7665894c067fac66c96fcc5 | MIT |

Also cloned and screened, contributing no candidate: apache/commons-codec (68289e5), apache/commons-statistics (316f510). The libraries were chosen by availability and
size, not by looking at any result; two of the four are algorithm collections, like TheAlgorithms/Java in the main corpus.

## Rules (the same mechanical rules as the main corpus, no new criteria)
1. Method-level screen `corpus_selection/libraries/screen_methods.py` (stages P, R, T, C, K, B, unchanged). Methods in test sources (`src/test`, `*Test.java`)
   are not library code and are excluded.
2. Driver generation `corpus_selection/libraries/gen_drivers.py` (method, same-file helpers and constants copied verbatim; int and int[] inputs).
3. Range rule `corpus_selection/libraries/run_candidates.py`: symmetric range [-k, k], the largest k in the fixed list whose search ends within 60 s with at most
   1,500 states.
4. Selection `corpus_selection/libraries/select_programs.py`: at least 5 non-leaf states; one program per source class (the largest tree); drop a program whose code has
   similarity >= 0.85 with a main-corpus program or an already selected one; drop a program whose tree is isomorphic to an already selected one.
Every decision is listed, including drops.

## Models and estimators (frozen)
Trained once on all 66 program groups of the main corpus with the settings of the paper (M5 and M6 linear; M5 and M6 random forest with
`max_features = 'sqrt'` (selected by the nested cross-validation of `analysis/fit_nested_cv_rf_tuning.py`), 200 trees, seed 42; M6 trained on the history-eligible groups only). No refitting, tuning or feature change on held-out
data. The baselines (state-count floor, hindsight subtree size, JPF built-in, JPFBar, Kilby WBE, Group C, Knuth with 30 probes, seed 42) have
no parameters.

## Measures
As in the main paper: macro Spearman rho over held-out groups with at least 5 non-leaf states and non-constant work, with a group bootstrap
interval; the calibration statistics of `analysis/calibration_analysis.py`; the partitioning replay of `analysis/load_balance_replay.py`.

## Hypotheses (from the main corpus, stated before the run)
- H1: the state-count floor has negative macro rho.
- H2: hindsight subtree size has macro rho >= 0.90.
- H3: JPF's built-in estimator and JPFBar have macro rho within +-0.30 of zero.
- H4: Group C has positive macro rho where it can be scored.
No hypothesis is stated for the learned models, calibration or the partitioning replay; they are reported as measured.

## Reporting
All programs and all results are reported, including hypotheses that fail. With fewer than 8 scoreable groups the results are described as
descriptive only and no replication claim is made.
