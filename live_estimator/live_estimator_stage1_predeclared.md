# Live estimator, Stage 1: fidelity and overhead (predeclaration)

Written before any live-listener run was made.

## Question
Every result in the paper about learned estimators is a replay on recorded trees. Two things a replay cannot show:
1. Does an estimator that runs inside the search, using only what a live search has at state entry, produce the same predictions as the replay?
2. What does running it cost in wall-clock time? A replay does not measure the cost of the model itself.

## What is built
`LiveEstimatorListener` (new file, jpf-symbc; `StateWorkListener` is not modified, so no archived data changes). At every state entry that is not an end state it:
- reads the ten M5 features exactly as `StateWorkListener` does (six static lookahead features at the current program counter; choice-generator total and processed, path-condition size, thread count);
- evaluates a frozen M5 Random Forest (exported from scikit-learn, evaluated in Java);
- caps the prediction at the already-capped prediction of the state on top of the DFS stack (its parent).

The model is the one of `heldout_eval.py`: fit on all non-leaf rows of the 66 main groups, 200 trees, `max_features='sqrt'` (the value chosen by the nested cross-validation), `random_state=42`, training rows sorted by (program, stateId), target `log1p(actualSubtreeWork)`, pruned choices treated as leaves (`analysis/prune.py`). No held-out data touched the fit.

Programs: the nine held-out programs, JPF z3 configurations as archived. M6 (needs sibling history) and probing are not in Stage 1.

## Conditions (each run is a fresh JVM)
- `none`: the listener is present only to record search start and end (`searchStarted`, `searchFinished`, `System.nanoTime`).
- `features`: ten features computed at every non-end state, folded into a checksum (so the work cannot be removed).
- `rf`: features plus Random Forest prediction.
- `rfcap`: features, prediction and capping.
- `rfcap-timed`: as `rfcap`, with `System.nanoTime` around feature extraction and around prediction-plus-capping, accumulated per run.
- `fidelity` (separate runs): `StateWorkListener` and `LiveEstimatorListener` together; the latter writes per-state raw and capped predictions.

## Hypotheses and bars

**H1, fidelity.** For every non-leaf state of every held-out program in the `fidelity` runs:
- (a) the feature vector of the new run equals the archived one (`heldout/data/Ho*.csv`) for the same stateId, except where the archive and a rerun are known to differ (reported);
- (b) the live raw prediction equals the offline prediction from the same run's features (scikit-learn `predict`) with absolute difference at most 1e-6 in log space;
- (c) the live capped prediction equals the offline capped prediction (`nesting_consistency.adjust`) with absolute difference at most 1e-6 in log space;
- (d) as a consequence, the live macro rho, raw and capped, equals the macro rho of scikit-learn and of the capping rule on the same states, to 1e-6.
H1 holds only if (a) to (d) all hold. Any failure is diagnosed and reported.

**H2, overhead.** Using search time `S0(p)`, the median over repetitions of (`searchFinished` minus `searchStarted`) in condition `none`:
- (a) the sum over programs of the median `rfcap-timed` prediction-plus-capping time is at most 5% of the sum of `S0(p)`;
- (b) the capping operation (read parent's capped value, minimum, write) costs at most 1% of the prediction cost per state. It is too small for per-state `nanoTime`, so it is measured by a loop microbenchmark inside the same JVM class (10^7 operations after warm-up) and compared with the measured prediction time per state.
Feature extraction is reported separately (any learned estimator needs it) and has no bar.

**Descriptive, no bar:** paired end-to-end differences in search time between `none`, `features`, `rf`, `rfcap` (median, interquartile range); the measured prediction time per state next to the counterfactual probing cost of the same programs; the machine (CPU, OS, JDK).

## Protocol
- 15 repetitions per (program, condition); one discarded warm-up run per program before its timed runs.
- Run order shuffled with seed 42, sequential (never parallel), nothing else heavy running on the machine.
- Report whatever comes out.

## Reporting
All numbers go into `results/` of this folder with the scripts that produce them.

Pruned choices are predicted like every other state during the search but are leaves, so they are not scored.
