# Data

One CSV per program configuration (116 files: 47 in `real-world/`, 22 in `synthetic/`, 47 in `sv-comp/`), one row per symbolic-execution state.
Each file was written by `StateWorkListener.java` (see `../instrumentation/README.md`) while JPF ran the corresponding `.jpf` configuration of
`../benchmarks/`. These files are the input of the scripts in `../analysis/`.

## Corpus in numbers

- 116 configurations, grouped into 66 **program groups**. A group is one program. A program has several configurations when it is run with
  different solvers (`_choco`) or symbolic ranges (`_wideR`), and a leave-one-program-out split holds out all configurations of a group together.
- 16,762 rows (states). 10,621 rows are not end states when entered. Of these, 4,054 are **pruned choices**: alternatives that jpf-symbc
  discards at once because their path condition is unsatisfiable. They have no child and no work, and the analysis treats them as leaves
  (`../analysis/prune.py`). The remaining 6,567 rows are the non-leaf states of the paper.
- 55 of the 66 groups have at least five non-leaf states and can be scored (population P55).

## Columns

| Column | Meaning |
|---|---|
| `stateId` | Id of the state in the JPF search. States are numbered in creation order, so this is the live count of the paper. |
| `parentId` | Id of the parent state (`-1` for the root). |
| `depth` | Depth of the state in the search tree (1 for the root). |
| `isEndStateAtEntry` | `True` if the state is an end state (no child, the program terminates). Its work is 0. |
| `entryInstructionCount`, `exitInstructionCount` | Value of the bytecode-instruction counter when the search enters the state and when it backtracks out of it. |
| `actualSubtreeWork` | The work `W(s)` of the paper: `exitInstructionCount - entryInstructionCount`, the bytecode instructions executed in the subtree of the state under exhaustive depth-first search. |
| `entryAllocCount`, `exitAllocCount`, `actualAllocWork` | The same for heap allocations. |
| `entryGcCycles`, `exitGcCycles`, `actualGcWork` | The same for garbage-collection cycles. |
| `entrySolverCalls`, `exitSolverCalls`, `actualSolverCalls` | The same for constraint-solver calls. |
| `entrySolverNanos`, `exitSolverNanos`, `actualSolverNanos` | The same for cumulative solver time in nanoseconds. |
| `entryWallClockNanos`, `exitWallClockNanos`, `actualWallClockNanos` | The same for wall-clock time (`System.nanoTime()`), recorded with the listener's console output switched off (`-Dstatework.quiet=true`, see `../instrumentation/README.md`). Used only for the check that instructions track time (`../results/01_construct_validation.txt`). |
| `choiceGeneratorType` | Class of the JPF choice generator that is active at the state. |
| `choiceGeneratorTotal`, `choiceGeneratorProcessed` | Number of alternatives of the active choice generator, and how many of them have been processed. Dynamic features. |
| `pathConditionSize` | Number of constraints in the path condition. Dynamic feature. |
| `threadCount` | Number of live threads. Dynamic feature. |
| `remainingBytecodesInMethod` | Bytecodes between the current position and the end of the method. Static feature. |
| `reachableBranchCount`, `reachableLoopBackEdgeCount`, `reachableVirtualCallCount`, `reachableAllocSiteCount`, `reachableAthrowCount` | Branches, loop back-edges, virtual calls, allocation sites and `athrow` sites that the control flow of the method can still reach from the current position. Static features. |

The six static and four dynamic features are the ten features of the paper.

## Loading

`../analysis/models_m1_to_m5.py` (`load_all()`) reads all files and adds two columns. `program` is the file name without extension (for example
`ArrayUtilsReverse_choco`). `program_group` maps a configuration to its group (`ArrayUtilsReverse_choco` to `ArrayUtilsReverse`) through an explicit
table, so that a leave-one-program-out split never trains on one configuration of a program and tests on another.

## Exploration order

All files come from one exhaustive depth-first search per configuration, the default order of JPF. Work and subtree size depend on the order
of exploration (Section 3 of the paper).
