// Extracted from sv-benchmarks java/jpf-regression/ExSymExe15_true/Main.java
// (jpf-symbc's own regression suite). Origin:
// https://github.com/sosy-lab/sv-benchmarks -- Apache License 2.0 (per-file
// NASA copyright header verified directly). test() logic copied verbatim
// (println/assert-false dropped), adapted to classify().
public class ExSymExe15 {

    static void test(int x, int z, int r) {
        int y = 3;
        r = x + z;
        z = x - y - 4;
        if (r <= 99) {
            // branch FOO1 (assert-false site in the original)
        } else {
            // branch FOO2
        }
        if (x <= z) {
            // branch BOO1
        } else {
            // branch BOO2
        }
    }

    public static void classify(int x, int z, int r) {
        test(x, z, r);
    }

    public static void main(String[] args) {
        classify(13000, 0, 0);
    }
}