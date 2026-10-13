// Extracted from sv-benchmarks java/jpf-regression/ExSymExeSuzette_true/Main.java
// (sv-benchmarks aggregates this from jpf-symbc's own regression suite).
// Origin: https://github.com/sosy-lab/sv-benchmarks -- Apache License 2.0
// (top-level LICENSE.Apache-2.0.txt; each jpf-regression Main.java also
// carries its own "Copyright (C) 2014, United States Government (NASA)"
// Apache-2.0 header). method_a/method_b copied verbatim, driver adapted to classify() (Verifier calls replaced by symbolic
// method parameters, no algorithmic change).
public class ExSymExeSuzette {

    static int method_a(int x, int y) {
        if (x > 10) {
            return x;
        }
        if (y > 10) {
            return y;
        }
        return 0;
    }

    static int method_b(int z) {
        if (z > 10) {
            return z + 1;
        } else {
            return z - 1;
        }
    }

    public static void classify(int x, int y) {
        int v = method_a(x, y);
        method_b(v);
    }

    public static void main(String[] args) {
        classify(1, 2);
    }
}
