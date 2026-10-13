# Live progress bar, Stage 2: accuracy of a bar built from per-state work predictions (predeclaration)

Written before any Stage 2 run or analysis. Builds on Stage 1 (`live_estimator_stage1_predeclared.md`).

## Question
The motivation is progress reporting. Does a progress bar built from the live per-state work predictions track the share of the search's work that is really done better than the two progress bars that ship for JPF?

## True progress
For a state creation event `e` (every `stateAdvanced`, leaves included): `tau_e = D_e / D_total`, where `D_e` is the number of instructions executed since the root state was entered (`entryInstructionCount` of the state minus that of the root, from `StateWorkListener`) and `D_total` is the work of the root's subtree, i.e. of the whole search. Instructions are the paper's primary work measure. (Secondary, descriptive only: the same with wall-clock time.)

*Executed work* is measured from the entry of the root and not from the raw instruction counter, which also contains the JVM's start-up instructions executed before the root is entered (about 88% of the counter's final value on these programs). Those instructions are not search work and not what the `W` of the paper measures.

## The three live bars (all computed from information available at the event)
Let the open DFS stack at event `e` be states `s_1 ... s_k` (`s_k` is the state just entered). Let `n_i`, `p_i` be the choice generator's total and processed choice counts at the entry of `s_i` (the paper's `choiceGeneratorTotal`, `choiceGeneratorProcessed`); levels with `n_i` in {-1, 0} are skipped, as in the paper's baselines.

1. **JPF built-in** (native `StateCountEstimator.percent`): `percent = sum_i delta_i * (p_i - 1)` with `delta_i = prod_{j<=i} 1/n_j`. Reported value: `percent` (empty path: 1.0, as in the source).
2. **JPFBar**: sum of path weights `prod_j 1/n_j` over all end states entered strictly before event `e`.
3. **Model bar (not tuned)**: `bar_e = D_e / (D_e + R_e)`, with `R_e` defined at the events where a prediction is made (state entries that are not end states) as `R_e = W^(s_k) + sum_{i=1..k} (n_i - p_i)^+ * W^(s_i)`, where `W^(s) = expm1(prediction)` is the live M5 Random Forest prediction of state `s`'s subtree work. Reading: remaining work = the entered state's own predicted subtree, plus, at every open level, its unexplored siblings, each assumed to cost what the open sibling at that level was predicted to cost. At end-state events no new prediction exists, so the estimate of remaining work is reduced by the work executed since the last prediction: `R_e = max(0, R_last - (D_e - D_last))`. `D_e` is exact (already executed); only unexplored work is estimated.

   *End states* do not get `W^ = 0`, which would make the bar assume that the unexplored siblings of every end state cost nothing and would produce a spurious saw-tooth. The rule above is used instead: re-estimate only where a prediction exists, otherwise subtract the executed work.
   - **capped variant (primary)**: `W^` from the capped prediction of Stage 1 (the paper's deployable rule).
   - **raw variant (descriptive)**: uncapped prediction.
   - **oracle-sibling bound (descriptive, not live)**: `W^` replaced by the true `actualSubtreeWork`. This isolates how much error comes from the sibling-similarity assumption rather than from the predictions.

All values are clipped to [0, 1]. The model is the frozen Stage 1 model (fit on the 66 main groups only).

## Metric
Primary: **time-weighted mean absolute error** in percentage points, `100 * sum_e |bar_e - tau_e| * (tau_{e+1} - tau_e)` (the bar's error averaged over the duration of the run; the last event extends to `tau = 1`). Secondary: event-weighted mean absolute error; maximum absolute error; absolute error at the first event with `tau` >= 10%, 20%, ..., 90%.

## Programs
- **Held-out (live)**: the nine held-out programs, `StateWorkListener` and a new `LiveProgressListener` in the same run, which logs per-event values of bars 1, 2, 3 (capped and raw) and the predictions.
- **Main corpus (offline extension)**: programs with at least 30 states (the filter of the paper's whole-run progress paragraph), model predictions from leave-one-group-out M5 Random Forests (raw, then capped by variant A of `nesting_consistency.py`), bars computed from the recorded trees by the offline implementation validated in H1.

## Hypotheses and bars
**H1, offline reconstruction is faithful.** An offline (Python) implementation of bars 1, 2, 3 from the recorded tree, the entry counters and the logged predictions equals the live-logged values on every event of the nine held-out programs, relative difference at most 1e-9. The live listener does not count instructions, so for the model bar it logs `R_e` only at the non-end-state events (where a prediction is made); the subtraction at end-state events uses the instruction counter of `StateWorkListener`, and bars 1 and 2 are logged at every event. H1 gates the extension: if it fails, the corpus extension is not run.

**H2, primary, nine held-out programs.** The capped model bar has a lower macro (mean over the nine programs) time-weighted mean absolute error than JPF built-in and than JPFBar, and is lower than each of them in at least 7 of the 9 programs.

**H3, extension, main corpus.** Per-program errors are averaged within each program group, then compared over groups. For each of the two baselines: macro error gain of the capped model bar of at least 2 percentage points and paired Wilcoxon raw p < 0.05 (two-sided, matched by group). Both baselines must be beaten for H3 to hold.

**Descriptive, no bar:** absolute error levels; raw against capped model bar; the oracle-sibling bound; wall-clock progress as the target; error at checkpoints; example curves.

## Reporting
Whatever comes out, including if the model bar loses to a baseline, is reported in `results/`. If H2 fails, the progress-bar claim is not made.
