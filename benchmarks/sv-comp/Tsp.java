// Extracted from SV-COMP's sv-benchmarks corpus, java/algorithms/Tsp-FunSat01/Main.java
// Original author: Sudeep Juvekar <sjuvekar@cs.berkeley.edu>
// Copyright (c) 2011, Regents of the University of California. All rights reserved.
// BSD 3-Clause License (same terms as other sv-comp/ files in this folder).
// Source: https://gitlab.com/sosy-lab/benchmarking/sv-benchmarks/-/blob/main/java/algorithms/Tsp-FunSat01/Main.java
//
// `TspSolver.search`/`solve`/`bound` copied verbatim: a branch-and-bound backtracking search over city permutations, with
// recursion that contains a `for` loop in each call, 2D-array-indexed state and a mutable `visited[]` array threaded through
// the recursion.
//
// MODIFICATION: N is fixed to 3 cities (SV-COMP uses a symbolic N). The six off-diagonal distances are symbolic; the diagonal
// entries are never read by the algorithm and are left as 0.
public class Tsp {

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

    public static void classify(int d01, int d02, int d10, int d12, int d20, int d21) {
        final int N = 3;
        int[][] D = new int[N][N];
        D[0][1] = d01;
        D[0][2] = d02;
        D[1][0] = d10;
        D[1][2] = d12;
        D[2][0] = d20;
        D[2][1] = d21;

        TspSolver solver = new TspSolver(N, D);
        solver.solve();
    }

    public static void main(String[] args) {
        classify(1, 2, 1, 3, 2, 3);
    }
}
