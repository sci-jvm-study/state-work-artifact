# Held-out programs

Nine programs from four libraries that were not used for any selection rule, model fit or tuning of the main corpus. Read
`PREREGISTRATION.md` first: it was written before any of these programs was run and fixes the sources, the rules, the frozen models, the
measures and the hypotheses.

| Folder | Content |
|---|---|
| `PREREGISTRATION.md` | Sources with commits and licences, rules, frozen models, measures, hypotheses H1-H4, reporting commitments. |
| `programs/` | The nine driver programs (`Ho*.java`) and their JPF configurations (`*_z3.jpf`, symmetric range chosen by the fixed range rule). Each file header names its origin and licence. |
| `data/` | The archived per-state data of the nine runs (schema of `../data/README.md`). |
| `data_coastal/`, `data_gdart/`, `run_status_coastal.csv`, `run_status_gdart.csv` | State trees of the nine programs on COASTAL and GDart and how each run ended. The trees have JPF's node count on both engines for four programs (Kadane, ShellSort, CompressDuplicates, InsertionSort), and on neither for the other five (engine undercoverage; one GDart run crashed in the engine). Evaluated by `../analysis/heldout_eval_other_engines.py` (results 57 to 59). |
| `coastal_bin/` | The classes COASTAL compiled for the nine programs; the static features of the COASTAL nodes are computed from them. |
| `selection/` | Candidate lists of the method screen for every library (`candidates_*.csv`, stage of the first failing screen), the range-rule tries (`tries.csv`), the decision for each generated driver (`selection_decisions.txt`) and the selected programs (`selected.csv`). |
| `scripts/` | The two helper scripts used to prepare the drivers (`prep_drivers.py`) and to copy the selected programs here (`finalize_heldout.py`); they read the working folder of the selection from the environment variable `HELDOUT_WORK`. |

Sources (shallow clones): apache/commons-numbers, apache/commons-rng, phishman3579/java-algorithms-implementation, AllAlgorithms/java (commits in
`PREREGISTRATION.md`); apache/commons-codec and apache/commons-statistics were screened and contributed no candidate. 28 methods passed the
method screen (test sources excluded), 22 ran to a kept result under the range rule, 9 were selected.

Steps (the scripts of `../corpus_selection/libraries/` are the ones used for the main corpus, with the driver prefix changed to `Ho...`):
`screen_methods.py <library> ...` -> `prep_drivers.py` (drops test sources, writes licence headers, runs `gen_drivers.py`) ->
`run_candidates.py <driver dir>` (range rule, needs the JPF setup) -> `select_programs.py <driver dir> <main corpus benchmark dirs>` ->
`finalize_heldout.py`. The evaluation needs only the archived data: run `python make_tables.py 9` from the root of the package (the call of `heldout_eval.py` is also in `reproduce.sh`).

Post hoc: `../analysis/heldout_feature_overlap.py` (results/41) finds that 81% of the feature vectors of
`HoJaiLowerBoundLowerBound` also occur in the main corpus's training rows, so `heldout_eval.py` also reports every result without that
program, labelled as a post-hoc sensitivity analysis. The hypotheses hold in both versions.
