// Extracted from sv-benchmarks java/jpf-regression/ExSymExe25_true/Main.java
// (aggregated from jpf-symbc's own regression suite).
// Origin: https://github.com/sosy-lab/sv-benchmarks -- Apache License 2.0.
// test() logic copied verbatim (the assert-false branch marker is kept as a no-op comment, because the search is not halted on
// assertion or uncaught-exception properties), adapted to classify().
public class ExSymExe25 {

    static void test(int x, int y, int z) {
        y = z + 1;
        z = z + x;
        x = x + 3;
        if (z > 0) {
            // original: assert-checked branch, kept for its own sake
        } else {
            // original: else branch
        }
        if (x > 0) {
            // original: else branch
        } else {
            // original: assert false branch
        }
    }

    public static void classify(int x, int y, int z) {
        test(x, y, z);
    }

    public static void main(String[] args) {
        classify(1, 2, 3);
    }
}