# Nesting-consistency of per-state predictions: predeclaration

Written before `nesting_consistency.py` was run.

## Question
The nesting analysis shows that for every ancestor-descendant pair the ancestor's subtree work is larger. Does a per-state estimator (M5 Random
Forest, leave-one-group-out, static and dynamic features) violate this ordering, and does enforcing it with information available at prediction
time improve its rank accuracy?

## Post-processing (past-only)
Let `W^(s)` be the model's prediction for a non-leaf state `s`, in work units (`expm1` of the log prediction), and `spent(p, c) = entry(c) - entry(p)`
the instructions already executed inside the parent's subtree when `c` is entered. States are processed in creation order, so the parent's adjusted
value is known when `c` is created.
- Variant A (cap by ancestor estimate): `W'(c) = min(W^(c), W'(parent))`.
- Variant B (cap by remaining ancestor estimate): `W'(c) = min(W^(c), max(W'(parent) - spent(p, c), 1))`.
The root keeps its own prediction. Nothing from the state's own future or from its descendants is used; no parameter is fitted.

## Measures (main corpus, 55 scoreable groups, rows pooled per group as everywhere else)
1. Nesting violations of the raw M5-RF: over nested pairs of non-leaf states, the share with `W^(anc) < W^(desc)`, `=` and `>`, macro over groups.
2. Macro Spearman rho of raw, A and B; number of groups that improve or worsen by more than 0.05.

## Adoption rule (A or B, each judged on its own)
Adopted for further study only if the macro rho over the 55 groups rises by at least 0.03 over raw M5-RF and at most 5 groups worsen by more than
0.05. Then it is frozen and run once on the nine held-out programs. Otherwise it is reported as a negative result and not proposed.
