# Live check of the M5 Random Forest and progress bars (Section 5.6, "A live check")

A JPF listener that reads the ten M5 features at every state, runs the frozen M5 Random Forest and caps the prediction, run on the nine
held-out programs. It also builds progress bars from the predicted remaining work. The two predeclaration notes fix the hypotheses, the
measures and the bars before the runs.

| File or folder | Content |
|---|---|
| `live_estimator_stage1_predeclared.md` | Fidelity and overhead hypotheses and bars (H1, H2). |
| `live_progress_stage2_predeclared.md` | The progress-bar construction, the two JPF baselines, the metric and the bars (H1 to H3). H3 (the offline extension to the main corpus) is not evaluated. |
| `java/` | `LiveEstimatorListener.java` (features, frozen M5 Random Forest, capping, timers, capping microbenchmark) and `LiveProgressListener.java` (inputs of the three progress bars). New files for jpf-symbc. Copy them to `jpf-symbc/src/main/gov/nasa/jpf/symbc/` and run `ant build`. |
| `programs/` | The nine held-out programs: compiled classes (`bin/`) and JPF configurations without the `listener` line (the scripts add it on the command line). The sources are in `../heldout/programs/`. |
| `runs/fidelity/`, `runs/progress/` | Raw output of both listeners: per program the work file of `StateWorkListener` and the live file. The analysis scripts below read these and need no JPF. |
| `bench/` | Isolated loop that times one prediction after JVM warm-up (`ForestBench.java`, `export_features.py`). |
| `results/` | Outputs, listed below. |

## Scripts

All scripts are deterministic. The scripts that start JPF (`fidelity.py run`, `timing.py`, `progress.py run`) take the locations of JPF and
the JDK from the environment variables `JPF_HOME` and `JAVA_HOME` (see `jpf_run.py`). The others use only files of this package.

```
pip install -r ../analysis/requirements.txt
python export_rf.py              # fits the frozen M5 Random Forest (as ../analysis/heldout_eval.py) and writes model/ (about 34 MB, not shipped)
python fidelity.py check         # fidelity (H1), needs model/            -> results/h1_fidelity.csv
python overhead_analysis.py      # overhead (H2)                          -> results/h2_overhead.txt
python overhead_addendum.py      # per-program shares, sum of the parts   -> results/h2_overhead_addendum.txt
python progress.py h1            # progress bars, offline against live    -> results/stage2_h1.csv
python progress.py h2            # progress bars, accuracy                -> results/stage2_h2.txt
```

Collecting the live data again needs JPF: `fidelity.py run`, `timing.py` (675 timing runs) and `progress.py run`.

## Results

| File | Content |
|---|---|
| `results/h1_fidelity.csv` | Live against offline predictions, features, structure and work, per program. |
| `results/h2_overhead.txt`, `h2_overhead_per_program.csv`, `timing_raw.csv`, `cap_microbench.txt` | Overhead per program and summed (prediction and capping 5.90% of the search time, against a limit of 5%), the 675 raw timing runs, and the capping microbenchmark. |
| `results/h2_overhead_addendum.txt`, `overhead_extrapolation.txt`, `forest_bench.txt` | Prediction and capping together with feature extraction (8.0% summed, 3.4% to 12.6% for single programs), the cost of one prediction in an isolated loop, and the arithmetic for longer searches (an extrapolation, not a measurement). |
| `results/stage2_h1.csv`, `stage2_h2.csv`, `stage2_h2.txt` | Progress bars: offline reconstruction against live values, and the mean error of the three bars (34.8 percentage points for the model bar against 30.2 for JPF's built-in estimator and 33.4 for JPFBar). |

## Limits

One machine (Windows 11, i5-13450HX, JDK 11), JPF only, the M5 Random Forest with capping only, and nine small programs whose searches last
0.2 to 0.5 s. Timings vary from machine to machine.
