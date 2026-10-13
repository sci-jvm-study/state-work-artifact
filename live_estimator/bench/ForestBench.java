import java.io.*;
import java.nio.file.*;
import java.util.*;

public class ForestBench {
    static int nTrees; static int[][] L, R, F; static double[][] T, V;
    static void load(String path) throws IOException {
        try (DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(path), 1 << 20))) {
            in.readInt(); in.readInt(); nTrees = in.readInt();
            L = new int[nTrees][]; R = new int[nTrees][]; F = new int[nTrees][]; T = new double[nTrees][]; V = new double[nTrees][];
            for (int t = 0; t < nTrees; t++) {
                int n = in.readInt();
                L[t] = new int[n]; R[t] = new int[n]; F[t] = new int[n]; T[t] = new double[n]; V[t] = new double[n];
                for (int i = 0; i < n; i++) L[t][i] = in.readInt();
                for (int i = 0; i < n; i++) R[t][i] = in.readInt();
                for (int i = 0; i < n; i++) F[t][i] = in.readInt();
                for (int i = 0; i < n; i++) T[t][i] = in.readDouble();
                for (int i = 0; i < n; i++) V[t][i] = in.readDouble();
            }
        }
    }
    static double predict(double[] v) {
        double sum = 0.0;
        for (int t = 0; t < nTrees; t++) {
            final int[] l = L[t], r = R[t], f = F[t]; final double[] th = T[t];
            int n = 0;
            while (l[n] != -1) n = (v[f[n]] <= th[n]) ? l[n] : r[n];
            sum += V[t][n];
        }
        return sum / nTrees;
    }
    public static void main(String[] a) throws Exception {
        load(a[0]);
        List<double[]> rows = new ArrayList<>();
        for (String line : Files.readAllLines(Paths.get(a[1]))) {
            String[] p = line.split(","); double[] x = new double[p.length];
            for (int i = 0; i < p.length; i++) x[i] = Double.parseDouble(p[i]);
            rows.add(x);
        }
        double sink = 0; int n = rows.size();
        for (int rep = 0; rep < 8; rep++) {
            long t0 = System.nanoTime();
            int calls = 0;
            for (int k = 0; k < 40; k++) for (double[] x : rows) { sink += predict(x); calls++; }
            long t1 = System.nanoTime();
            System.out.printf("rep %d: %.2f us per prediction (%d calls)%n", rep, (t1 - t0) / 1e3 / calls, calls);
        }
        if (sink == 1.0) System.out.println("x");
    }
}
