# Corpus selection

How the programs added to the corpus were chosen, and what was screened out. The tables of the paper use `../data/`; this folder documents
the selection so that it can be repeated and checked. The selection rules are applied by the scripts in this folder.

## Sources screened

| Source | Version | License | Unit screened |
|---|---|---|---|
| sv-benchmarks, `java/` (SV-COMP Java tasks) | GitLab `sosy-lab/benchmarking/sv-benchmarks`, commit `ca46fe670b5dcbcd3495bd23689353a8ea1fb86b` | per task (MIT, BSD, Apache-2.0, ...) | task (`.yml`) |
| Apache Commons Lang | GitHub `apache/commons-lang`, commit `699d7e6` | Apache-2.0 | static method |
| Apache Commons Collections | `apache/commons-collections`, commit `a350e2c` | Apache-2.0 | static method |
| Apache Commons Math | `apache/commons-math`, commit `a3869a4` (modules `commons-math-core`, `commons-math-legacy-core`) | Apache-2.0 | static method |
| TheAlgorithms/Java | `TheAlgorithms/Java`, commit `dd8df80` | MIT | static method |

The first 49 program groups of the corpus (see the headers in `../benchmarks/*/`) were chosen with the same criteria. The screens
below were run over the complete sources and added the other 17.

## 1. SV-COMP Java tasks (`svcomp/`)

`screen.py` applies five stages to every task, each keeping only what passed the earlier ones (`funnel.txt`, per-task flags in `screen.csv`):

| Stage | Criterion | Tasks left |
|---|---|---|
| all | Java tasks in sv-benchmarks | 1033 |
| D | domain: general-purpose software or tool regression tests; not a domain model (MinePump: pump controller, rtems-lock-model: RTOS model) and not a security suite (securibench, juliet-java) | 846 |
| I | inputs read only with `Verifier.nondetInt()` | 231 |
| T | no bitwise operators (neither solver integration of jpf-symbc supports them symbolically), no String/float/double/long/char, threads, IO, reflection | 146 |
| V | every expected verdict is true (jpf-symbc stops at the first property violation, which would truncate the tree) | 54 |
| U | one task per program source | 54 |

`pool_table.py` gives the decision for each of the 54 (`pool.csv`, counts in `pool_summary.txt`): 15 are programs of the corpus
(14 that passed the screen as they are, plus `Primes` added here), 10 are variants of another task (same code, different
property or instance; code similarity >= 0.85), 2 (`MergeSortIterative`) are excluded because the file header does not grant a
redistributable license, 20 were adapted and run but have fewer than 5 non-leaf states,
2 pass that floor but are JBMC bytecode unit tests of a single instruction (`lookupswitch1`, `tableswitch1`) and are excluded, 4 could not be adapted mechanically (reasons in `pool.csv`) and 1 produced no JPF output.
Five programs of the corpus (`BinaryTreeInsert`, `ExSymExe15`, `ExSymExe20`, `ExSymExe25`, `Tsp`) come from tasks that fail the strict screen and were adapted by hand.

`adapt.py` turns a task's `main()` into `classify(int ...)`; `run_candidates.py` runs each adapted program on JPF and picks its input
range by one fixed rule (below); the per-attempt record is `tries_adapted.csv`.

## 2. Open-source libraries (`libraries/`)

`screen_methods.py` screens every static method of a library (`funnel.txt`, per-method result and first failing stage in
`candidates_<library>.csv`):

| Stage | Criterion |
|---|---|
| P | parameters only `int` and at most one `int[]` (filled from 4 symbolic ints), at most 6 symbolic ints in total |
| R | returns `int`, `boolean`, `void` or `int[]` |
| T | no bitwise operators, no float/double/long/char/String/generics/lambdas/instanceof/synchronized |
| C | every call is to an allow-listed JDK method (`Math.abs/min/max/signum`, `Integer.compare/signum`) or to a static method of the same file that passes P, R, T, C |
| K | every constant is a literal `static final int` of the same file |
| B | at least 5 code lines and a loop or conditional |

| Library | static methods | after P | after R | after T | after C | after K | after B (candidates) |
|---|---|---|---|---|---|---|---|
| Commons Lang | 2245 | 94 | 46 | 38 | 17 | 16 | 4 |
| Commons Collections | 751 | 26 | 16 | 11 | 4 | 4 | 0 |
| Commons Math (legacy-core) | 75 | 5 | 3 | 2 | 2 | 2 | 1 |
| Commons Math (core) | 180 | 21 | 21 | 16 | 2 | 2 | 0 |
| TheAlgorithms/Java | 1281 | 372 | 285 | 185 | 85 | 80 | 61 |

Of the 5 Commons candidates, `ArrayUtils.lastIndexOf`, `ArrayUtils.reverse` and `NumberUtils.max` (as `NumberUtilsMax3`) are in the corpus,
`NumberUtils.min` is the mirror image of `NumberUtils.max`, and `MathArrays.sequence` has 5 lines. For TheAlgorithms/Java, `gen_drivers.py`
writes one driver program per candidate (the method, its same-file helpers and constants copied verbatim; `classify()` builds int arrays
from symbolic ints and wraps the call in `try/catch RuntimeException`), `run_candidates.py` runs them, and `select_programs.py` applies
the selection rules (`selection_thealgorithms.txt` lists the decision for each of the 61):

1. the kept run has at least 5 non-leaf states (the paper's scoreability floor);
2. one program per source class (the method with the most non-leaf states);
3. no near-duplicates (code similarity >= 0.85 with a corpus program or a selected one);
4. no tree-isomorphic programs (same tree ignoring sibling order); the programs dropped by this rule are listed with their reason in
   `selection_thealgorithms.txt`.

Outcome of the 61 drivers: 18 with no usable JPF run (at the smallest range: timeout, no output, more than 1500 states or a compile failure), 15 below the floor, 7 excluded by
rule 2, 3 by rule 3, 2 by rule 4, **16 selected**. Together with `Primes` from SV-COMP, 17 programs were added to the corpus
(`../benchmarks/real-world/Ta*.java`, `../benchmarks/sv-comp/Primes.java`).

## Range rule (all added programs)

Symmetric symbolic range `[-k, k]`, `k` in {1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20}, ascending; the largest `k` whose exploration finishes
within 60 s with at most 1500 states is kept (`MAX_STATES`, `TIMEOUT` in `run_candidates.py`), and the search stops early when the
tree no longer grows. The first 49 program groups of the corpus use hand-chosen ranges in the same size regime.

## Not covered

- Tasks or methods that need symbolic `long`, `char`, `String`, `float`/`double`, bitwise operations or symbolic array lengths, and
  tasks whose expected verdict is false, are outside the screen by construction (they cannot be run to completion by the jpf-symbc
  configuration used here); the funnels show how many that is.
- The selection is purposive, not a random sample of the sources, and the sources are not a random sample of open-source Java.
- Method-level screening does not cover instance methods or classes (data structures driven by call sequences); the corpus contains
  a few such programs that were written by hand (e.g. `BankAccount`, `LinkedListFind`, `RbTreeInsert`).

## Re-running

`python svcomp/screen.py <sv-benchmarks>/java svcomp/screen.csv`, `python libraries/screen_methods.py <library>/src/main/java <name>`,
`python libraries/gen_drivers.py candidates_<library>.csv <src dir> <name> license_thealgorithms.txt <out dir>`, then
`python libraries/run_candidates.py <out dir>` (needs a JPF setup; set `JDK11_HOME`, `JPF_HOME`, optionally `JPF_ENV_BAT`), and
`python libraries/select_programs.py <out dir> <benchmark dirs...>`.
