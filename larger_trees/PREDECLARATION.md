# Larger trees: predeclaration

Written before any program of the set below was run on JPF or scored. One program (`InsertionSort7`, not part of the set) was run once to learn how long a tree of about 10,000 states takes (12 seconds) and how many rows it produces. No estimator was evaluated on it.

## Question
All programs of the main corpus have at most 1,500 states. Do the findings hold on larger trees (up to 100,000 states)? The main corpus already suggests that the live count weakens as trees grow (Figure 2 of the paper) and that probing is cheaper than exploring only for large subtrees (Section 5.4). This study measures both on larger trees.

## Programs (a mechanical rule, no choice by hand)
Start from the canonical Z3 configuration of every program group of the main corpus that has recorded data (`<Program>_z3.jpf`, integer parameters only). Keep its source and its symbolic input range `[-k0, k0]`.
1. Run the program with the symmetric range `[-k, k]`, `k` in 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 50, 100, ascending, starting at the first `k` larger than `k0`.
2. Stop at the first `k` whose search has more than 100,000 states, takes more than 300 seconds, or has the same number of states as the previous `k` (the tree no longer grows). Keep the run of the largest `k` before that.
3. A kept run belongs to the **large set** if it has at least 5,000 states. Programs without such a run are not used and are listed.
4. Everything uses depth-first search, Z3, `StateWorkListener` with `-Dstatework.quiet=true`, the pruned-choice treatment of `analysis/prune.py`, and the code of the main analysis.

## Estimators and measures
The estimators and models of the paper (M5 and M6, linear and Random Forest, `max_features = 'sqrt'`, seed 42; baselines without parameters; Knuth with 30 probes, seed 42; programs in sorted order). A program of the large set is the same program as a group of the main corpus, only with a wider range. The learned models are therefore fitted, for each program of the large set, on the main-corpus rows of the other 65 groups (leave-one-program-out, as in the paper), so that the program itself is not in the training data. Nothing is refitted or tuned on the large set. Macro Spearman rho over the groups with at least five non-leaf states and non-constant work, with a bootstrap interval over groups, as in the paper. Also the median cost of 30 probes relative to the work of the state (Section 5.4).

## Hypotheses (stated before the run)
- H1: the live count has macro rho of at most +0.10 on the large set.
- H2: the final subtree size has macro rho of at least 0.90.
- H3: the sibling mean has a positive macro rho where it is defined, and a higher one than the live count.
- H4: Knuth probing with 30 probes has macro rho of at least 0.80.
- H5: the median cost of 30 probes relative to the work of the state is above 1 (probing costs more than exploring).

No hypothesis is stated for the learned models, the depth rule or the load-balancing replay. They are reported as measured, as post hoc where applicable.

## Reporting
All programs of the large set and all results are reported, including hypotheses that fail and programs that do not grow. If fewer than 8 groups are scoreable, the results are descriptive only.
