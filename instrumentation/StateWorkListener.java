package gov.nasa.jpf.symbc;

import gov.nasa.jpf.PropertyListenerAdapter;
import gov.nasa.jpf.search.Search;
import gov.nasa.jpf.symbc.numeric.PCChoiceGenerator;
import gov.nasa.jpf.symbc.numeric.SolverStats;
import gov.nasa.jpf.vm.ChoiceGenerator;
import gov.nasa.jpf.vm.ElementInfo;
import gov.nasa.jpf.vm.Instruction;
import gov.nasa.jpf.vm.ThreadInfo;
import gov.nasa.jpf.vm.VM;
import gov.nasa.jpf.symbc.StaticLookahead.Features;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

/**
 * StateWorkListener
 *
 * Measures the ACTUAL exploration work (instructions executed) of the
 * subtree rooted at every symbolic state, using JPF's own DFS traversal
 * as the reference exploration order (see the paper's methodology section).
 *
 * ---------------------------------------------------------------------
 * DESIGN NOTE:
 *
 * search.getStateId() at the moment stateBacktracked() fires refers to
 * the PARENT state we have just returned to -- NOT the child whose
 * subtree just finished. This is because DefaultBacktracker.backtrack()
 * calls SystemState.Memento.backtrack(ss), which restores ss.id to the
 * id that was saved on the PARENT when it descended into that child
 * (SystemState.java, Memento.backtrack(): "ss.id = id;").
 *
 * So this listener does NOT key work-tracking by search.getStateId() at
 * backtrack time. Instead it keeps its OWN stack, pushed on
 * stateAdvanced() and popped on stateBacktracked(). Because JPF's
 * search is a strict DFS (DFSearch.search()), every stateBacktracked()
 * event corresponds to exactly one pop of the most recently pushed,
 * not-yet-popped frame -- regardless of what id JPF itself reports at
 * that moment. This gives the correct per-state subtree instruction
 * count with natural bottom-up aggregation: a parent's own frame stays
 * on the stack while all its children push/pop underneath it, so when
 * the parent itself is finally popped, its instruction delta already
 * spans everything its descendants did.
 *
 * The root state is a special case: when backtrack() is attempted on
 * it, Backtracker.backtrack() returns false and DFSearch.search()
 * breaks out of its loop WITHOUT calling notifyStateBacktracked(). Any
 * frames still open when searchFinished() fires (there should be
 * exactly one -- the root) are closed there.
 * ---------------------------------------------------------------------
 *
 * Beyond the ground-truth work counters and state identity/structure
 * described above, this listener also records path-condition size,
 * choice-generator type/count, and (via StaticLookahead) the static
 * lookahead features used as model inputs -- see the CSV schema
 * documented in ../data/README.md for the full column list.
 */
public class StateWorkListener extends PropertyListenerAdapter {

    /** One entry per currently-open (advanced but not yet backtracked) state. */
    private static class Frame {
        final int stateId;
        final int parentId;
        final int depth;
        final long entryInstructionCount;
        final long entryAllocCount;
        final long entryGcCycles;
        final long entrySolverCalls;   // W_solver -- see SolverStats
        final long entrySolverNanos;
        final long entryWallClockNanos; // Used for construct validation (see ../results/01_construct_validation.txt):
                                         // System.nanoTime() at push, NOT a cumulative counter like the
                                         // others above -- the delta at pop is real elapsed wall-clock
                                         // time for this state's own subtree (used to check whether the
                                         // count-based W_engine/W_solver proxies actually track real time).
        final boolean isEndStateAtEntry;

        // ---- Group B (dynamic) features, snapshotted at entry ----
        // NOTE: the ChoiceGenerator captured here is curCg, the CG for the edge that was just taken to reach this state (the branch of the
        // parent), not a CG for the own future branch of this state, which does not exist yet at entry time (SystemState.java: "curCg: the
        // ChoiceGenerator used in the current transition"). It describes the branching factor of the edge leading here, without any
        // information about the unexplored future of the state.
        final String choiceGeneratorType;   // simple class name, or "NONE"
        final int choiceGeneratorTotal;     // total choices at the parent's CG, or -1
        final int choiceGeneratorProcessed; // choices already tried at that CG, or -1
        final int pathConditionSize;        // constraint count if the CG was symbolic, or -1
        final int threadCount;

        // ---- Group A (static lookahead) features, computed at entry ----
        // Intraprocedural only -- see StaticLookahead.java for scope notes.
        final Features staticFeatures;

        Frame(int stateId, int parentId, int depth, long entryInstructionCount,
              long entryAllocCount, long entryGcCycles, long entrySolverCalls, long entrySolverNanos,
              long entryWallClockNanos, boolean isEndStateAtEntry,
              String choiceGeneratorType, int choiceGeneratorTotal, int choiceGeneratorProcessed,
              int pathConditionSize, int threadCount, Features staticFeatures) {
            this.stateId = stateId;
            this.parentId = parentId;
            this.depth = depth;
            this.entryInstructionCount = entryInstructionCount;
            this.entryAllocCount = entryAllocCount;
            this.entryGcCycles = entryGcCycles;
            this.entrySolverCalls = entrySolverCalls;
            this.entrySolverNanos = entrySolverNanos;
            this.entryWallClockNanos = entryWallClockNanos;
            this.isEndStateAtEntry = isEndStateAtEntry;
            this.choiceGeneratorType = choiceGeneratorType;
            this.choiceGeneratorTotal = choiceGeneratorTotal;
            this.choiceGeneratorProcessed = choiceGeneratorProcessed;
            this.pathConditionSize = pathConditionSize;
            this.threadCount = threadCount;
            this.staticFeatures = staticFeatures;
        }
    }

    // running counters, updated by low-level hooks
    private long instructionCount = 0;
    private long allocCount = 0;   // cumulative objects created (objectCreated hook)
    private long gcCycleCount = 0; // cumulative GC cycles (gcEnd hook)

    // our own DFS stack (NOT keyed by JPF's reported stateId at backtrack time)
    private final Deque<Frame> openStates = new ArrayDeque<>();

    // Own monotonic counter for the stateId written to the CSV. search.getStateId() is not
    // reliably unique per stateAdvanced() call in programs with many choices or iterations: it can
    // return the same id for different states, which would corrupt the parent-child structure
    // (actualSubtreeWork itself is computed from the push/pop order of the stack and never by id).
    // The listener therefore does not use JPF's own id for anything that has to be unique, as for the parentId above.
    private long nextOwnStateId = 0;

    // completed rows, written out once the whole search is done
    private final List<String> csvRows = new ArrayList<>();

    private long eventNumber = 0;

    // The per-event System.out.println happens inside the timed window of every open ancestor frame, so console output would inflate
    // wallClockNanos in proportion to the size of the subtree. Set -Dstatework.quiet=true to suppress it for timing runs (default: false).
    private static final boolean QUIET =
        Boolean.getBoolean("statework.quiet");

    // Actual Subtree Work: The number of JPF instructions executed after a state is entered and before that state’s DFS frame is closed.
    private static final String CSV_HEADER =
        "stateId,parentId,depth,"
        + "entryInstructionCount,exitInstructionCount,actualSubtreeWork,"
        + "entryAllocCount,exitAllocCount,actualAllocWork,"
        + "entryGcCycles,exitGcCycles,actualGcWork,"
        + "entrySolverCalls,exitSolverCalls,actualSolverCalls,"
        + "entrySolverNanos,exitSolverNanos,actualSolverNanos,"
        + "entryWallClockNanos,exitWallClockNanos,actualWallClockNanos,"
        + "isEndStateAtEntry,"
        + "choiceGeneratorType,choiceGeneratorTotal,choiceGeneratorProcessed,pathConditionSize,threadCount,"
        + "remainingBytecodesInMethod,reachableBranchCount,reachableLoopBackEdgeCount,"
        + "reachableVirtualCallCount,reachableAllocSiteCount,reachableAthrowCount";

    private static final String OUTPUT_FILE = "state_work_dataset.csv";

    // low-level counting: the same increment-only pattern as instructionCount, with the hooks objectCreated/objectReleased/gcEnd of
    // PropertyListenerAdapter. The allocation and GC counters complete the W_engine components of the work definition, alongside the
    // instruction count.
    @Override
    public void instructionExecuted(VM vm, ThreadInfo currentThread,
                                     Instruction nextInsn, Instruction executedInsn) {
        instructionCount++;
    }

    @Override
    public void objectCreated(VM vm, ThreadInfo currentThread, ElementInfo newObject) {
        allocCount++;
    }

    @Override
    public void gcEnd(VM vm) {
        gcCycleCount++;
    }

    // DFS tracking
    @Override
    public void stateAdvanced(Search search) {
        int stateId = (int) nextOwnStateId++;
        int depth = search.getDepth();
        int parentId = openStates.isEmpty() ? -1 : openStates.peek().stateId;
        boolean isEnd = search.isEndState();

        // ---- Group B feature extraction (entry-time only, no future info) ----
        VM vm = search.getVM();
        ChoiceGenerator<?> cg = vm.getChoiceGenerator();

        String cgType = (cg == null) ? "NONE" : cg.getClass().getSimpleName();
        int cgTotal = (cg == null) ? -1 : cg.getTotalNumberOfChoices();
        int cgProcessed = (cg == null) ? -1 : cg.getProcessedNumberOfChoices();

        int pcSize = -1;
        if (cg instanceof PCChoiceGenerator) {
            gov.nasa.jpf.symbc.numeric.PathCondition pc = ((PCChoiceGenerator) cg).getCurrentPC();
            if (pc != null) {
                pcSize = pc.count();
            }
        }

        int threadCount = vm.getThreadList().length();

        // ---- Group A: static lookahead from the current program counter ----
        Instruction pc = vm.getCurrentThread() == null ? null : vm.getCurrentThread().getPC();
        Features staticFeatures = StaticLookahead.compute(pc);

        Frame f = new Frame(stateId, parentId, depth, instructionCount, allocCount, gcCycleCount,
                             SolverStats.invocationCount, SolverStats.cumulativeSolveNanos,
                             System.nanoTime(), isEnd,
                             cgType, cgTotal, cgProcessed, pcSize, threadCount, staticFeatures);
        openStates.push(f);

        if (!QUIET) System.out.println(
            "EVENT " + (++eventNumber) + " ADVANCED"
            + "  stateId=" + stateId
            + "  parentId=" + parentId
            + "  depth=" + depth
            + "  isNewState=" + search.isNewState()
            + "  isEndState=" + isEnd
            + "  instructionCount=" + instructionCount
            + "  allocCount=" + allocCount
            + "  gcCycles=" + gcCycleCount
            + "  cgType=" + cgType
            + "  cgTotal=" + cgTotal
            + "  cgProcessed=" + cgProcessed
            + "  pcSize=" + pcSize
            + "  threads=" + threadCount
            + "  remainingBC=" + staticFeatures.remainingBytecodesInMethod
            + "  branchesAhead=" + staticFeatures.reachableBranchCount
            + "  loopEdgesAhead=" + staticFeatures.reachableLoopBackEdgeCount
            + "  virtualCallsAhead=" + staticFeatures.reachableVirtualCallCount
            + "  allocSitesAhead=" + staticFeatures.reachableAllocSiteCount
            + "  athrowsAhead=" + staticFeatures.reachableAthrowCount
        );
    }

    @Override
    public void stateBacktracked(Search search) {
        if (openStates.isEmpty()) {
            // Should not happen given the DFS loop structure; guard so that the search does not crash.
            System.out.println("WARNING: stateBacktracked fired with empty stack");
            return;
        }

        Frame completed = openStates.pop();
        long work = instructionCount - completed.entryInstructionCount;
        long allocWork = allocCount - completed.entryAllocCount;
        long gcWork = gcCycleCount - completed.entryGcCycles;
        long solverCallWork = SolverStats.invocationCount - completed.entrySolverCalls;
        long solverNanoWork = SolverStats.cumulativeSolveNanos - completed.entrySolverNanos;
        long exitWallClockNanos = System.nanoTime();
        long wallClockWork = exitWallClockNanos - completed.entryWallClockNanos;

        recordRow(completed, instructionCount, work, allocCount, allocWork, gcCycleCount, gcWork,
                  SolverStats.invocationCount, solverCallWork, SolverStats.cumulativeSolveNanos, solverNanoWork,
                  exitWallClockNanos, wallClockWork);

        if (!QUIET) System.out.println(
            "EVENT " + (++eventNumber) + " BACKTRACKED"
            + "  completedStateId=" + completed.stateId
            + "  parentId=" + completed.parentId
            + "  depth=" + completed.depth
            + "  entryInstr=" + completed.entryInstructionCount
            + "  exitInstr=" + instructionCount
            + "  actualSubtreeWork=" + work
            + "  allocWork=" + allocWork
            + "  gcWork=" + gcWork
            + "  solverCalls=" + solverCallWork
            + "  solverNanos=" + solverNanoWork
            + "  wallClockNanos=" + wallClockWork
            + "  (now at parent stateId=" + search.getStateId() + ")"
        );
    }

    @Override
    public void stateProcessed(Search search) {
        // Fires when forward() found no more unexplored choices from the
        // state currently on top of our stack. This does NOT itself close
        // the frame -- the actual pop happens on the *next* stateBacktracked()
        // call. Logged only for visibility; no accounting here, to avoid
        // double-counting a state's work.
        if (!QUIET) System.out.println(
            "EVENT " + (++eventNumber) + " PROCESSED"
            + "  stateId=" + search.getStateId()
            + "  depth=" + search.getDepth()
        );
    }

    @Override
    public void searchFinished(Search search) {
        // Close any states still open (the root, always; possibly others
        // if the search was aborted early) so every pushed state gets a row.
        while (!openStates.isEmpty()) {
            Frame completed = openStates.pop();
            long work = instructionCount - completed.entryInstructionCount;
            long allocWork = allocCount - completed.entryAllocCount;
            long gcWork = gcCycleCount - completed.entryGcCycles;
            long solverCallWork = SolverStats.invocationCount - completed.entrySolverCalls;
            long solverNanoWork = SolverStats.cumulativeSolveNanos - completed.entrySolverNanos;
            long exitWallClockNanos = System.nanoTime();
            long wallClockWork = exitWallClockNanos - completed.entryWallClockNanos;
            recordRow(completed, instructionCount, work, allocCount, allocWork, gcCycleCount, gcWork,
                      SolverStats.invocationCount, solverCallWork, SolverStats.cumulativeSolveNanos, solverNanoWork,
                      exitWallClockNanos, wallClockWork);

            if (!QUIET) System.out.println(
                "EVENT " + (++eventNumber) + " CLOSED-AT-SEARCH-END"
                + "  stateId=" + completed.stateId
                + "  parentId=" + completed.parentId
                + "  depth=" + completed.depth
                + "  actualSubtreeWork=" + work
                + "  allocWork=" + allocWork
                + "  gcWork=" + gcWork
                + "  solverCalls=" + solverCallWork
                + "  solverNanos=" + solverNanoWork
                + "  wallClockNanos=" + wallClockWork
            );
        }

        writeDataset();
    }

    // dataset output
    private void recordRow(Frame f, long exitInstructionCount, long work,
                            long exitAllocCount, long allocWork,
                            long exitGcCycles, long gcWork,
                            long exitSolverCalls, long solverCallWork,
                            long exitSolverNanos, long solverNanoWork,
                            long exitWallClockNanos, long wallClockWork) {
        csvRows.add(
            f.stateId + ","
            + f.parentId + ","
            + f.depth + ","
            + f.entryInstructionCount + ","
            + exitInstructionCount + ","
            + work + ","
            + f.entryAllocCount + ","
            + exitAllocCount + ","
            + allocWork + ","
            + f.entryGcCycles + ","
            + exitGcCycles + ","
            + gcWork + ","
            + f.entrySolverCalls + ","
            + exitSolverCalls + ","
            + solverCallWork + ","
            + f.entrySolverNanos + ","
            + exitSolverNanos + ","
            + solverNanoWork + ","
            + f.entryWallClockNanos + ","
            + exitWallClockNanos + ","
            + wallClockWork + ","
            + f.isEndStateAtEntry + ","
            + f.choiceGeneratorType + ","
            + f.choiceGeneratorTotal + ","
            + f.choiceGeneratorProcessed + ","
            + f.pathConditionSize + ","
            + f.threadCount + ","
            + f.staticFeatures.remainingBytecodesInMethod + ","
            + f.staticFeatures.reachableBranchCount + ","
            + f.staticFeatures.reachableLoopBackEdgeCount + ","
            + f.staticFeatures.reachableVirtualCallCount + ","
            + f.staticFeatures.reachableAllocSiteCount + ","
            + f.staticFeatures.reachableAthrowCount
        );
    }

    private void writeDataset() {
        try (PrintWriter pw = new PrintWriter(new FileWriter(OUTPUT_FILE))) {
            pw.println(CSV_HEADER);
            for (String row : csvRows) {
                pw.println(row);
            }
            System.out.println("[StateWorkListener] wrote " + csvRows.size()
                + " rows to " + OUTPUT_FILE);
        } catch (IOException e) {
            System.out.println("[StateWorkListener] FAILED to write dataset: " + e.getMessage());
        }
    }
}
