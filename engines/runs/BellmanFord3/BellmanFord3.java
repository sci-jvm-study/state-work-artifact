// Same algorithm as BellmanFord.java (sv-benchmarks java/algorithms/
// BellmanFord-FunSat01, BSD-3-clause). runBellmanFord() copied verbatim.
// N=3 vertices instead of 2. At N=2, dist[1] starts at the concrete sentinel Integer.MAX_VALUE, so the relaxation check is always
// true. At N=3 intermediate distances become finite during the relaxation, so later comparisons depend on the symbolic edge weights.
public class BellmanFord3 {

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

    public static void classify(int d01, int d02, int d10, int d12, int d20, int d21) {
        final int N = 3;
        int[] D = new int[N * N];
        D[0 * N + 1] = d01;
        D[0 * N + 2] = d02;
        D[1 * N + 0] = d10;
        D[1 * N + 2] = d12;
        D[2 * N + 0] = d20;
        D[2 * N + 1] = d21;
        runBellmanFord(N, D, 0);
    }

    public static void main(String[] args) {
        classify(1, 2, 1, 3, 2, 3);
    }
}