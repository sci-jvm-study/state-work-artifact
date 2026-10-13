// Extracted from sv-benchmarks java/jpf-regression/ExSymExe20_true/Main.java
// (originally jpf-symbc's own regression suite, "test IF_ICMPLT, IADD & ISUB
// bytecodes"). Origin: https://github.com/sosy-lab/sv-benchmarks --
// Apache License 2.0 (per-file NASA copyright header verified directly).
// test() logic copied verbatim (println/assert-false dropped), adapted to classify(). Field params `z`, `r` in the original driver
// were plain ints (field=9, field2=0 by default); they are symbolic parameters here.
public class ExSymExe20 {

    static void test(int x, int z, int r) {
        int y = 3;
        r = x + z;
        x = z - y;
        z = r;
        if (z >= x) {
            // branch FOO1
        } else {
            // branch FOO2
        }
        if (x >= r) {
            // branch BOO1 (assert-false site in the original)
        } else {
            // branch BOO2
        }
    }

    public static void classify(int x, int z, int r) {
        test(x, z, r);
    }

    public static void main(String[] args) {
        classify(3, 9, 0);
    }
}
