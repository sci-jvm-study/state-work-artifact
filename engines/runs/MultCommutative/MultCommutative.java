// Extracted from sv-benchmarks java/jayhorn-recursive/SatMultCommutative01/Main.java.
// Origin: https://github.com/jayhorn/cav_experiments (MIT License).
// mult(int, int) copied verbatim. MODIFICATION: the driver is replaced (the Verifier.nondetInt() harness of SV-COMP became a plain
// symbolic-parameter classify()).
public class MultCommutative {

    static int mult(int n, int m) {
        if (m < 0) {
            return mult(n, -m);
        }
        if (m == 0) {
            return 0;
        }
        return n + mult(n, m - 1);
    }

    public static void classify(int n, int m) {
        mult(n, m);
    }

    public static void main(String[] args) {
        classify(3, 4);
    }
}