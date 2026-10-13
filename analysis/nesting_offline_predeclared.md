# Offline (global) nesting-consistent projection of M5-RF predictions: predeclaration

Written before `nesting_offline.py` was run.

## Question
The online rule (`nesting_consistency.py`, variant A) caps each state's prediction at its already-capped parent's, using only earlier
predictions in creation order. Does jointly adjusting every prediction of a whole tree at once, allowed to use predictions from anywhere in the
tree (not just ancestors processed so far), recover more accuracy than the online rule? This bounds how much headroom the "use nesting" idea has
left, not a new deployable estimator: it needs the whole tree's raw predictions before adjusting any of them, so it cannot run live.

## Method
For each configuration, adjust the raw M5-RF log-work predictions of all non-leaf states to the closest values (least squares) that satisfy
`adjusted(parent) >= adjusted(child)` for every parent-child pair of non-leaf states, using the standard bottom-up pooling algorithm for isotonic
regression on a rooted tree (process states in decreasing stateId order, i.e. descendants before ancestors; for a state, start a pool at its own
raw value and merge with each child's pool, heaviest-first, while the pool's value is below the child pool's, until no child pool exceeds it).
Every pool's value is a weight-1 mean of its raw members, so the result is an exact least-squares projection onto the nesting-consistent set.
Correctness is checked mechanically: every adjusted parent-child pair must satisfy `>=`, with no exceptions.

## Measures
Macro Spearman rho of raw, the online cap (A), and the offline projection, over the 55 scoreable groups; grouped by the tree-size bands of
`nesting_decomposition.py` (post hoc, as there); how much of the online-to-offline gap (if any) is closed.

## Reporting
Whatever the result. If the offline projection is close to the online cap, that is reported as evidence the online rule already captures most of
the available headroom. If it is clearly better, that is reported as an open question for future work, not implemented as a live estimator here.
