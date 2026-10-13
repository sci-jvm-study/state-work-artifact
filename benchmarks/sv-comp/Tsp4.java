// Same algorithm as Tsp.java (sv-benchmarks java/algorithms/Tsp-FunSat01,
// BSD-3-clause). TspSolver copied verbatim. 4 cities instead of 3 (12
// off-diagonal distances instead of 6).
public class Tsp4 {

    private static class TspSolver {
        private final int N;
        private final int[][] D;
        private final boolean[] visited;
        private int best;

        TspSolver(int N, int[][] D) {
            this.N = N;
            this.D = D;
            this.visited = new boolean[N];
        }

        int solve() {
            best = Integer.MAX_VALUE;
            for (int i = 0; i < N; i++) visited[i] = false;
            visited[0] = true;
            search(0, 0, N - 1);
            return best;
        }

        private int bound(int src, int length, int nLeft) {
            return length;
        }

        private void search(int src, int length, int nLeft) {
            if (nLeft == 0) {
                if (length + D[src][0] < best) best = length + D[src][0];
                return;
            }
            if (bound(src, length, nLeft) >= best) return;

            for (int i = 0; i < N; i++) {
                if (visited[i]) continue;
                visited[i] = true;
                search(i, length + D[src][i], nLeft - 1);
                visited[i] = false;
            }
        }
    }

    public static void classify(int d01, int d02, int d03, int d10, int d12, int d13,
                                 int d20, int d21, int d23, int d30, int d31, int d32) {
        final int N = 4;
        int[][] D = new int[N][N];
        D[0][1] = d01; D[0][2] = d02; D[0][3] = d03;
        D[1][0] = d10; D[1][2] = d12; D[1][3] = d13;
        D[2][0] = d20; D[2][1] = d21; D[2][3] = d23;
        D[3][0] = d30; D[3][1] = d31; D[3][2] = d32;

        TspSolver solver = new TspSolver(N, D);
        solver.solve();
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 1, 4, 5, 2, 4, 6, 3, 5, 6);
    }
}
