// Same algorithm as BellmanFord.java (sv-benchmarks java/algorithms/
// BellmanFord-FunSat01, BSD-3-clause). runBellmanFord() copied verbatim.
// N=4 vertices instead of 3 (12 symbolic edge weights instead of 6).
public class BellmanFord4 {

    static final int INFINITY = Integer.MAX_VALUE;

    static int[] runBellmanFord(int N, int[] D, int src) {
        int[] dist = new int[N];
        boolean[] infinite = new boolean[N];
        for (int i = 0; i < N; i++) {
            dist[i] = INFINITY;
            infinite[i] = true;
        }
        dist[src] = 0;
        infinite[src] = false;

        int k;
        for (k = 0; k < N; k++) {
            boolean relaxed = false;
            for (int i = 0; i < N; i++) {
                for (int j = 0; j < N; j++) {
                    if (i == j) continue;
                    if (!infinite[i]) {
                        if (dist[j] > dist[i] + D[i * N + j]) {
                            dist[j] = dist[i] + D[i * N + j];
                            infinite[j] = false;
                            relaxed = true;
                        }
                    }
                }
            }
            if (!relaxed) break;
        }

        return dist;
    }

    public static void classify(int d01, int d02, int d03, int d10, int d12, int d13,
                                 int d20, int d21, int d23, int d30, int d31, int d32) {
        final int N = 4;
        int[] D = new int[N * N];
        D[0 * N + 1] = d01;
        D[0 * N + 2] = d02;
        D[0 * N + 3] = d03;
        D[1 * N + 0] = d10;
        D[1 * N + 2] = d12;
        D[1 * N + 3] = d13;
        D[2 * N + 0] = d20;
        D[2 * N + 1] = d21;
        D[2 * N + 3] = d23;
        D[3 * N + 0] = d30;
        D[3 * N + 1] = d31;
        D[3 * N + 2] = d32;
        runBellmanFord(N, D, 0);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 1, 3, 2, 2, 3, 1, 3, 2, 1);
    }
}