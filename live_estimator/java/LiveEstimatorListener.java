package gov.nasa.jpf.symbc;

import gov.nasa.jpf.Config;
import gov.nasa.jpf.PropertyListenerAdapter;
import gov.nasa.jpf.search.Search;
import gov.nasa.jpf.symbc.StaticLookahead.Features;
import gov.nasa.jpf.symbc.numeric.PCChoiceGenerator;
import gov.nasa.jpf.symbc.numeric.PathCondition;
import gov.nasa.jpf.vm.ChoiceGenerator;
import gov.nasa.jpf.vm.Instruction;
import gov.nasa.jpf.vm.VM;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * Runs a frozen M5 Random Forest inside the search, using only what is available at state entry, and optionally caps each
 * prediction at the already-capped prediction of the state on top of the DFS stack (its parent).
 *
 * Properties: liveest.mode = none | features | rf | rfcap; liveest.model = path of the exported forest (m5_rf.bin);
 * liveest.timers = true to time feature extraction and prediction-plus-capping per run; liveest.log = true to write per-state
 * features and predictions to liveest.logfile.
 *
 * The DFS bookkeeping (push on stateAdvanced, pop on stateBacktracked) is identical in every mode, so differences between modes
 * isolate the work of the estimator itself.
 */
public class LiveEstimatorListener extends PropertyListenerAdapter {

    private static final int NONE = 0, FEATURES = 1, RF = 2, RFCAP = 3;
    private static final int NFEAT = 10;

    private final int mode;
    private final boolean timers;
    private final boolean log;
    private final String logFile;

    // forest, one array set per tree
    private int nTrees;
    private int[][] left, right, feat;
    private double[][] thr, val;

    private final double[] x = new double[NFEAT];
    private double[] capStack = new double[4096];
    private int[] idStack = new int[4096];
    private int sp = 0;
    private int nextId = 0;

    private long checksum = 0;
    private long nonLeaf = 0;
    private long tSearchStart, tSearchEnd;
    private long tFeat = 0, tPredCap = 0;
    private final StringBuilder rows = new StringBuilder();

    public LiveEstimatorListener(Config conf) {
        String m = conf.getString("liveest.mode", "rfcap");
        switch (m) {
            case "none": mode = NONE; break;
            case "features": mode = FEATURES; break;
            case "rf": mode = RF; break;
            default: mode = RFCAP; break;
        }
        timers = conf.getBoolean("liveest.timers", false);
        log = conf.getBoolean("liveest.log", false);
        logFile = conf.getString("liveest.logfile", "live_predictions.csv");
        if (mode >= RF) {
            try {
                loadForest(conf.getString("liveest.model"));
            } catch (IOException e) {
                throw new RuntimeException("cannot load forest: " + e.getMessage(), e);
            }
        }
        if (log) {
            rows.append("stateId,parentId,isEnd,remainingBytecodesInMethod,reachableBranchCount,reachableLoopBackEdgeCount,"
                + "reachableVirtualCallCount,reachableAllocSiteCount,reachableAthrowCount,choiceGeneratorTotal,"
                + "choiceGeneratorProcessed,pathConditionSize,threadCount,raw,capped\n");
        }
    }

    private void loadForest(String path) throws IOException {
        try (DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(path), 1 << 20))) {
            if (in.readInt() != 0x4D355246) throw new IOException("bad magic");
            if (in.readInt() != NFEAT) throw new IOException("feature count mismatch");
            nTrees = in.readInt();
            left = new int[nTrees][];
            right = new int[nTrees][];
            feat = new int[nTrees][];
            thr = new double[nTrees][];
            val = new double[nTrees][];
            for (int t = 0; t < nTrees; t++) {
                int n = in.readInt();
                left[t] = new int[n];
                right[t] = new int[n];
                feat[t] = new int[n];
                thr[t] = new double[n];
                val[t] = new double[n];
                for (int i = 0; i < n; i++) left[t][i] = in.readInt();
                for (int i = 0; i < n; i++) right[t][i] = in.readInt();
                for (int i = 0; i < n; i++) feat[t][i] = in.readInt();
                for (int i = 0; i < n; i++) thr[t][i] = in.readDouble();
                for (int i = 0; i < n; i++) val[t][i] = in.readDouble();
            }
        }
    }

    private double predict(double[] v) {
        double sum = 0.0;
        for (int t = 0; t < nTrees; t++) {
            final int[] l = left[t], r = right[t], f = feat[t];
            final double[] th = thr[t];
            int n = 0;
            while (l[n] != -1) {
                n = (v[f[n]] <= th[n]) ? l[n] : r[n];
            }
            sum += val[t][n];
        }
        return sum / nTrees;
    }

    static double capAgainst(double raw, double parentCapped) {
        return (parentCapped == parentCapped) ? Math.min(raw, parentCapped) : raw;
    }

    @Override
    public void searchStarted(Search search) {
        tSearchStart = System.nanoTime();
    }

    @Override
    public void stateAdvanced(Search search) {
        int id = nextId++;
        boolean isEnd = search.isEndState();
        double raw = Double.NaN, capped = Double.NaN;

        if (mode != NONE && !isEnd) {
            long t0 = timers ? System.nanoTime() : 0L;
            VM vm = search.getVM();
            ChoiceGenerator<?> cg = vm.getChoiceGenerator();
            int cgTotal = (cg == null) ? -1 : cg.getTotalNumberOfChoices();
            int cgProcessed = (cg == null) ? -1 : cg.getProcessedNumberOfChoices();
            int pcSize = -1;
            if (cg instanceof PCChoiceGenerator) {
                PathCondition pc = ((PCChoiceGenerator) cg).getCurrentPC();
                if (pc != null) pcSize = pc.count();
            }
            int threads = vm.getThreadList().length();
            Instruction insn = vm.getCurrentThread() == null ? null : vm.getCurrentThread().getPC();
            Features sf = StaticLookahead.compute(insn);
            x[0] = sf.remainingBytecodesInMethod;
            x[1] = sf.reachableBranchCount;
            x[2] = sf.reachableLoopBackEdgeCount;
            x[3] = sf.reachableVirtualCallCount;
            x[4] = sf.reachableAllocSiteCount;
            x[5] = sf.reachableAthrowCount;
            x[6] = cgTotal;
            x[7] = cgProcessed;
            x[8] = pcSize;
            x[9] = threads;
            for (int i = 0; i < NFEAT; i++) checksum += (long) x[i] * (i + 1);
            nonLeaf++;
            long t1 = timers ? System.nanoTime() : 0L;

            if (mode >= RF) {
                raw = predict(x);
                capped = raw;
                if (mode == RFCAP) {
                    capped = capAgainst(raw, sp > 0 ? capStack[sp - 1] : Double.NaN);
                }
            }
            if (timers) {
                long t2 = System.nanoTime();
                tFeat += t1 - t0;
                tPredCap += t2 - t1;
            }
        }

        if (sp == capStack.length) {
            capStack = java.util.Arrays.copyOf(capStack, sp * 2);
            idStack = java.util.Arrays.copyOf(idStack, sp * 2);
        }
        if (log) {
            rows.append(id).append(',').append(sp > 0 ? idStack[sp - 1] : -1).append(',').append(isEnd);
            for (int i = 0; i < NFEAT; i++) rows.append(',').append(isEnd || mode == NONE ? "" : Long.toString((long) x[i]));
            rows.append(',').append(Double.isNaN(raw) ? "" : Double.toString(raw))
                .append(',').append(Double.isNaN(capped) ? "" : Double.toString(capped)).append('\n');
        }
        capStack[sp] = mode == RFCAP ? capped : Double.NaN;
        idStack[sp] = id;
        sp++;
    }

    @Override
    public void stateBacktracked(Search search) {
        if (sp > 0) sp--;
    }

    @Override
    public void searchFinished(Search search) {
        tSearchEnd = System.nanoTime();
        System.out.println("[LiveEstimator] mode=" + mode + " states=" + nextId + " nonleaf=" + nonLeaf
            + " searchNs=" + (tSearchEnd - tSearchStart) + " featNs=" + tFeat + " predCapNs=" + tPredCap
            + " checksum=" + checksum);
        if (log) {
            try (PrintWriter pw = new PrintWriter(new FileWriter(logFile))) {
                pw.print(rows);
            } catch (IOException e) {
                System.out.println("[LiveEstimator] FAILED to write log: " + e.getMessage());
            }
        }
    }

    /** Cost of the capping operation alone (read parent's value, minimum, store), per operation, in nanoseconds. */
    public static void main(String[] args) {
        final int n = 1 << 20;
        double[] raws = new double[n];
        java.util.Random rnd = new java.util.Random(42);
        for (int i = 0; i < n; i++) raws[i] = rnd.nextDouble() * 12.0;
        double[] stack = new double[64];
        double sink = 0;
        int ops = 20_000_000;
        for (int rep = 0; rep < 3; rep++) {
            int sp = 1;
            stack[0] = 8.0;
            long t0 = System.nanoTime();
            for (int i = 0; i < ops; i++) {
                double c = capAgainst(raws[i & (n - 1)], stack[sp - 1]);
                stack[sp] = c;
                sp = ((i & 7) < 4) ? Math.min(sp + 1, 60) : Math.max(sp - 1, 1);
                sink += c;
            }
            long t1 = System.nanoTime();
            if (rep > 0) System.out.println("capNsPerOp=" + ((t1 - t0) / (double) ops));
        }
        if (sink == 42.0) System.out.println("unreachable");
    }
}
