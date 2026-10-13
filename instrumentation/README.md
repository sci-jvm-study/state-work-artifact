# Instrumentation

The per-state subtree exploration work `W(s)` is measured by instrumenting Java PathFinder's symbolic-execution extension, jpf-symbc,
on top of unmodified jpf-core. The recorded output is in `../data/`, so this folder is needed only to collect the data again.

## Base versions

- `jpf-core`: https://github.com/javapathfinder/jpf-core.git, commit `df58f6e86dcd749e1f460bcd6127e043a401926c`. **Unmodified** — no instrumentation changes needed here.
- `jpf-symbc`: https://github.com/SymbolicPathFinder/jpf-symbc.git, commit `c98bfae2969e51923006e4c922c0f4e4a1cfbdfb`. **Modified** — see below.

## How to apply

1. Clone `jpf-core` at the commit above; build with `ant` (JDK 11).
2. Clone `jpf-symbc` at the commit above.
3. Apply `jpf-symbc.patch` (`git apply jpf-symbc.patch` from the `jpf-symbc` root) — this is a 2-file,
   14-line change to `jpf.properties` (native-library lookup key for modern Windows) and
   `src/main/gov/nasa/jpf/symbc/numeric/SymbolicConstraintsGeneral.java` (solver-call counting hook).
4. Copy the three files below into `jpf-symbc/src/main/gov/nasa/jpf/symbc/` (and `numeric/` for
   `SolverStats.java`) — these are new files, not modifications to existing jpf-symbc code:
   - `StateWorkListener.java` → `src/main/gov/nasa/jpf/symbc/`
   - `StaticLookahead.java` → `src/main/gov/nasa/jpf/symbc/`
   - `SolverStats.java` → `src/main/gov/nasa/jpf/symbc/numeric/`
5. Rebuild jpf-symbc (`ant clean build`).
6. Register the listener for a run via `.jpf` config: `listener=gov.nasa.jpf.symbc.StateWorkListener`
   (see any `.jpf` file under `../benchmarks/`).

## What each file does

- **`StateWorkListener.java`** — the core instrumentation. A JPF `SearchListener` that, on every
  state push (`stateAdvanced`), snapshots per-state counters (bytecode-instruction count, heap
  allocation count, GC cycle count, solver-call count and cumulative solver nanoseconds, wall-clock
  nanoseconds via `System.nanoTime()`) plus the static/dynamic feature values defined in
  `StaticLookahead.java`. On backtrack (`stateBacktracked`) and at search end
  (`searchFinished`), it computes each snapshotted state's actual subtree work as the delta between
  its own entry and exit counters, and writes one CSV row per state to
  `<program>.csv` (schema documented in `../data/README.md`). A `-Dstatework.quiet=true` system
  property suppresses this listener's own per-event console output, because that logging inflates the
  wall-clock time that is recorded. All wall-clock numbers in `../results/` were collected with this flag on.

- **`StaticLookahead.java`** — computes the paper's static-lookahead features (reachable
  branch/loop/call/allocation/throw sites and remaining bytecodes from the current program counter,
  via one-time bytecode/CFG analysis per method, O(1) lookup thereafter) plus the dynamic-state
  features (path-condition size, choice-generator counts, thread count) read directly from JPF's own
  `VM`/`ChoiceGenerator` state at each state push.

- **`SolverStats.java`** — two static counters (`cumulativeSolveNanos`, `invocationCount`)
  incremented at the single dispatch point every constraint-solver backend (z3, choco) passes
  through (`SymbolicConstraintsGeneral.solve()`, patched by `jpf-symbc.patch`), so solver cost is
  captured regardless of which backend a given `.jpf` config selects.

- **`jpf-symbc.patch`** — the two small upstream-file changes described above.
