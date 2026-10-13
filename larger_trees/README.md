# Larger trees

All programs of the main corpus have at most 1,500 states. This folder checks the findings on larger trees. For each program group, the
symbolic input range is widened step by step until the search has more than 100,000 states, takes more than 300 seconds, or stops growing.
The run of the largest range before that stop is kept. Programs whose kept run has at least 5,000 states form the large set. The rule, the
estimators and the hypotheses were written down in `PREDECLARATION.md` before any program of the set was run.

Section 7 of the paper (external validity) reports the outcome.

## Files

| File | Content |
|---|---|
| `PREDECLARATION.md` | The rule, the estimators and the measures, written before the runs. |
| `sweep.py` | Applies the rule to the canonical Z3 configuration of every program group (needs JPF). |
| `tries.csv` | Output of `sweep.py`: one row per run (program, range `k`, number of states, seconds, outcome). 71 programs, 164 runs. |
| `kept/` | Output of `sweep.py`: the kept run of each of the 64 programs that have one (`<Program>.csv`, the per-state table in the schema of `../data/README.md`, and `<Program>.k`, the range). |
| `eval_large.py` | Scores the parameter-free estimators on the programs of `kept/` that have at least 5,000 states. Output: `../results/70_larger_trees.txt`. |
| `feasibility_run/` | The one run that was made before the predeclaration, to learn how long a tree of about 10,000 states takes (`InsertionSort7`, not part of the set). |

## Reproducing the numbers of the paper

```
python eval_large.py             # a few seconds, prints the content of ../results/70_larger_trees.txt
```

This needs only the Python packages of `../analysis/requirements.txt`. `bash ../reproduce.sh` also writes this output as
`70_larger_trees.txt`.

## Running the sweep again

```
python sweep.py --out sweep_new  # about 20 minutes with 4 workers
python eval_large.py --kept sweep_new/kept
```

`sweep.py` needs JPF with jpf-symbc and the listener (`../instrumentation/README.md`) and a JDK 11. It reads the folders `JPF_HOME` (which
contains `jpf-core` and `jpf-symbc`) and `JAVA_HOME`. It compiles each program with `javac -g`, writes a configuration with the range `[-k, k]`,
and runs JPF. The number of states and all counters of a run are the same on every machine. Only the column `seconds` of `tries.csv` and the
time columns of the CSV files vary.

## Outcome

- 71 programs were tried. 64 have a kept run, and 62 of them stay below 5,000 states. The other seven have no kept run, because their
  first run with a wider range timed out (five programs) or wrote no output (two programs). Every run is a row of `tries.csv`.
- Two programs reach at least 5,000 states: `EuclideanGcd` (range 100, 12,177 states) and `TaSumOfSubset` (range 8, 14,999 states).

| Estimator | `EuclideanGcd` | `TaSumOfSubset` |
|---|---|---|
| Live count | -0.011 | +0.014 |
| Final subtree size N(s) | +0.985 | +0.956 |
| Depth rule (post hoc) | -0.032 | +0.336 |
| Sibling mean | +0.350 | +0.797 |
| Knuth probing, 30 probes | +0.888 | +0.879 |
| Median cost of 30 probes relative to the work of the state | 9.28x | 8.08x |

The paper reports the live count, the depth rule and the cost ratio. With only two programs in the large set, the macro correlations,
the bootstrap intervals and the five hypotheses of `PREDECLARATION.md` (which need at least eight scoreable groups) and the learned models
are not evaluated, as the predeclaration says for fewer than eight groups. The estimators are scored per program.
