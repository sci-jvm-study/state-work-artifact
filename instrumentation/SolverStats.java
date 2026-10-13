package gov.nasa.jpf.symbc.numeric;

/**
 * Global, cumulative counters of the constraint solver: the number of decision-procedure invocations and the cumulative solver time.
 * They give the solver part of the work, W_solver. StateWorkListener records the engine part, W_engine (bytecodes, allocations and GC
 * cycles).
 *
 * Incremented from exactly one place: SymbolicConstraintsGeneral.isSatisfiable(),
 * around the actual `pb.solve()` call -- the single dispatch point every
 * decision-procedure backend (z3, choco, etc, see the dp-selection switch
 * in that method) goes through. Never reset mid-search; StateWorkListener
 * reads these as running counters and computes deltas per state, as it does for
 * instructionCount, allocCount and gcCycleCount.
 *
 * Deliberately a plain static counter class, not a JPF listener hook of its
 * own: isSatisfiable() is called from deep inside jpf-symbc's own bytecode
 * instruction handling, not from a place StateWorkListener's own
 * PropertyListenerAdapter hooks (instructionExecuted/objectCreated/gcEnd)
 * can observe directly -- this is the same reason those three hooks exist
 * as instance methods on the listener while this needs to be a globally
 * reachable static counter instead.
 */
public class SolverStats {

    /** Number of times isSatisfiable() actually invoked pb.solve() (i.e.
     * excludes the early-return cases: empty PC, PC-length cap exceeded,
     * max-exploration-time exceeded, or dp=no_solver -- none of those reach
     * a real decision-procedure call). */
    public static long invocationCount = 0;

    /** Cumulative wall-clock nanoseconds spent inside pb.solve() calls
     * only -- not path-condition parsing/translation (PCParser.parse),
     * which happens in the translation layer, not the solver itself. */
    public static long cumulativeSolveNanos = 0;

    private SolverStats() {
    }
}
