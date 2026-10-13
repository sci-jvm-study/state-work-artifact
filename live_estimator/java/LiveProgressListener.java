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
import java.util.Arrays;

/**
 * Logs, at every state entry, the inputs of three progress bars (see live_progress_stage2_predeclared.md):
 *  - JPF built-in StateCountEstimator percent,
 *  - JPFBar (sum of path weights of end states entered before this event),
 *  - the remaining-work estimate R of the model bar (capped and raw M5 Random Forest), defined at non-end-state events.
 * The model bar itself is D/(D+R) with D the executed instruction count, taken from StateWorkListener's output.
 *
 * Properties: liveprog.model = exported forest (m5_rf.bin), liveprog.logfile = output csv.
 */
public class LiveProgressListener extends PropertyListenerAdapter {

    private static final int NFEAT = 10;

    private final String logFile;
    private int nTrees;
    private int[][] left, right, feat;
    private double[][] thr, val;

    private final double[] x = new double[NFEAT];
    private int cap = 4096;
    private double[] capLogStack = new double[cap];
    private double[] deltaStack = new double[cap];
    private double[] percentStack = new double[cap];
    private double[] prefCapStack = new double[cap];
    private double[] prefRawStack = new double[cap];
    private int sp = 0;
    private int nextId = 0;
    private double jpfbarSum = 0.0;
    private final StringBuilder rows = new StringBuilder();

    public LiveProgressListener(Config conf) {
        logFile = conf.getString("liveprog.logfile", "live_progress.csv");
        try {
            loadForest(conf.getString("liveprog.model"));
        } catch (IOException e) {
            throw new RuntimeException("cannot load forest: " + e.getMessage(), e);
        }
        rows.append("stateId,isEnd,n,p,rawLog,capLog,Rcap,Rraw,builtin,jpfbar\n");
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

    @Override
    public void stateAdvanced(Search search) {
        int id = nextId++;
        boolean isEnd = search.isEndState();
        VM vm = search.getVM();
        ChoiceGenerator<?> cg = vm.getChoiceGenerator();
        int n = (cg == null) ? -1 : cg.getTotalNumberOfChoices();
        int p = (cg == null) ? -1 : cg.getProcessedNumberOfChoices();

        double rawLog = Double.NaN, capLog = Double.NaN, wRaw = 0.0, wCap = 0.0;
        if (!isEnd) {
            int pcSize = -1;
            if (cg instanceof PCChoiceGenerator) {
                PathCondition pc = ((PCChoiceGenerator) cg).getCurrentPC();
                if (pc != null) pcSize = pc.count();
            }
            Instruction insn = vm.getCurrentThread() == null ? null : vm.getCurrentThread().getPC();
            Features sf = StaticLookahead.compute(insn);
            x[0] = sf.remainingBytecodesInMethod;
            x[1] = sf.reachableBranchCount;
            x[2] = sf.reachableLoopBackEdgeCount;
            x[3] = sf.reachableVirtualCallCount;
            x[4] = sf.reachableAllocSiteCount;
            x[5] = sf.reachableAthrowCount;
            x[6] = n;
            x[7] = p;
            x[8] = pcSize;
            x[9] = vm.getThreadList().length();
            rawLog = predict(x);
            capLog = LiveEstimatorListener.capAgainst(rawLog, sp > 0 ? capLogStack[sp - 1] : Double.NaN);
            wRaw = Math.expm1(rawLog);
            wCap = Math.expm1(capLog);
        }

        boolean validN = !(n == -1 || n == 0);
        double parentDelta = sp > 0 ? deltaStack[sp - 1] : 1.0;
        double parentPercent = sp > 0 ? percentStack[sp - 1] : 0.0;
        double delta = validN ? parentDelta / n : parentDelta;
        double percent = parentPercent;
        if (validN) percent += delta * (p == -1 ? 0 : Math.max(0, p - 1));
        double builtin = (sp == 0) ? 1.0 : percent;

        double u = (validN && p >= 0) ? Math.max(0, n - p) : 0.0;
        double prefCap = (sp > 0 ? prefCapStack[sp - 1] : 0.0) + u * wCap;
        double prefRaw = (sp > 0 ? prefRawStack[sp - 1] : 0.0) + u * wRaw;
        double rCap = isEnd ? Double.NaN : wCap + prefCap;
        double rRaw = isEnd ? Double.NaN : wRaw + prefRaw;

        double jpfbarBefore = jpfbarSum;
        if (isEnd) jpfbarSum += delta;

        rows.append(id).append(',').append(isEnd).append(',').append(n).append(',').append(p).append(',')
            .append(Double.isNaN(rawLog) ? "" : Double.toString(rawLog)).append(',')
            .append(Double.isNaN(capLog) ? "" : Double.toString(capLog)).append(',')
            .append(Double.isNaN(rCap) ? "" : Double.toString(rCap)).append(',')
            .append(Double.isNaN(rRaw) ? "" : Double.toString(rRaw)).append(',')
            .append(Double.toString(builtin)).append(',').append(Double.toString(jpfbarBefore)).append('\n');

        if (sp == cap) {
            cap *= 2;
            capLogStack = Arrays.copyOf(capLogStack, cap);
            deltaStack = Arrays.copyOf(deltaStack, cap);
            percentStack = Arrays.copyOf(percentStack, cap);
            prefCapStack = Arrays.copyOf(prefCapStack, cap);
            prefRawStack = Arrays.copyOf(prefRawStack, cap);
        }
        capLogStack[sp] = capLog;
        deltaStack[sp] = delta;
        percentStack[sp] = percent;
        prefCapStack[sp] = prefCap;
        prefRawStack[sp] = prefRaw;
        sp++;
    }

    @Override
    public void stateBacktracked(Search search) {
        if (sp > 0) sp--;
    }

    @Override
    public void searchFinished(Search search) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(logFile))) {
            pw.print(rows);
        } catch (IOException e) {
            System.out.println("[LiveProgress] FAILED to write log: " + e.getMessage());
        }
        System.out.println("[LiveProgress] states=" + nextId + " jpfbarFinal=" + jpfbarSum);
    }
}
