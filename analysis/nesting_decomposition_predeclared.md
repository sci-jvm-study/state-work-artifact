# Nesting decomposition of the live-count correlation: predeclaration

Written before `nesting_decomposition.py` was run. This is an exploratory analysis of existing data whose hypotheses are
stated first; whatever the outcome, all of it is reported.

## Idea
In any exploration order a state is created before its descendants, and its subtree work is at least that of any descendant (the descendant's
subtree is contained in it). So for every ancestor-descendant ("nested") pair the live count and the work move in opposite directions: the
later-created state has less or equal work. Only pairs of states in different branches ("non-nested") can be concordant. The hindsight subtree
size has the same nesting property, which would make it agree with work on nested pairs.

## Decomposition
Within each configuration, over all pairs of non-leaf states: concordant `C`, discordant `D`, tied `T` (equal work) for the pair (state id, work);
Kendall tau-a `(C - D) / (C + D + T)` splits exactly into nested and non-nested pairs. Counts are summed over the configurations of a program
group. The same split is computed for (hindsight subtree size, work), where a pair is concordant when both increase together.

## Hypotheses (stated before computing)
- H1 (mechanical check): no nested pair is concordant for (state id, work), in any configuration.
- H2: across the scoreable groups, the share of nested pairs is positively related to how negative the live-count tau is: Spearman between the share
  of nested pairs and minus the group's tau-a is at least 0.6.
- H3: on non-nested pairs alone the live count carries little signal: the macro tau-a of non-nested pairs lies within +-0.15 of zero.
- H4: for (hindsight subtree size, work), no nested pair is discordant, and its macro tau-a on non-nested pairs is clearly positive (at least 0.5).
- H5: the tau-a of the live count over all pairs correlates with the paper's group rho (Spearman >= 0.9), so the decomposition describes the same quantity.
Not predicted: which groups are the exceptions.

## Reporting
Per group table, macro summaries, the hypotheses as holds/fails, the groups where non-nested pairs are strongly positive or negative. Claims
are limited to these configurations. If a hypothesis fails it is reported as failed.
