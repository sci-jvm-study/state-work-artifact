// Extracted from SV-COMP's sv-benchmarks corpus, java/algorithms/BellmanFord-FunSat01/Main.java
// Original authors: Sudeep Juvekar <sjuvekar@cs.berkeley.edu>, Jacob Burnim <jburnim@cs.berkeley.edu>
// Copyright (c) 2011, Regents of the University of California. All rights reserved.
// BSD 3-Clause License (same terms as other sv-comp/ files in this folder).
// Source: https://gitlab.com/sosy-lab/benchmarking/sv-benchmarks/-/blob/main/java/algorithms/BellmanFord-FunSat01/Main.java
//
// `runBellmanFord` copied verbatim: a triple-nested loop graph-relaxation algorithm over an array-indexed distance matrix.
//
// MODIFICATION: the number of vertices N is fixed to 2 (SV-COMP uses a symbolic V), so only the two off-diagonal edge weights
// (D[0*2+1], D[1*2+0]) are symbolic. jpf-symbc does not handle symbolic array sizes well.
public class BellmanFord {

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

    public static void classify(int edge01, int edge10) {
        final int N = 2;
        int[] D = new int[N * N];
        D[0 * N + 1] = edge01;
        D[1 * N + 0] = edge10;
        runBellmanFord(N, D, 0);
    }

    public static void main(String[] args) {
        classify(1, 1);
    }
}
