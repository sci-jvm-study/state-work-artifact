// Extracted from sv-benchmarks java/jpf-regression/ExSymExeSimple_true/Main.java
// (jpf-symbc's own regression suite). Origin:
// https://github.com/sosy-lab/sv-benchmarks -- Apache License 2.0 (per-file
// NASA copyright header verified directly). test() logic copied verbatim
// (println/assert-false dropped), adapted to classify(). The original driver
// called test(arg, arg+1) (coupled params); made both independently
// symbolic here to also exercise the a==b branch.
public class ExSymExeSimple {

    static void test(int a, int b) {
        if (a > b) {
            // ">" branch (assert-false site in the original)
        } else if (a == b) {
            // "eq" branch
        } else {
            // "<" branch
        }
    }

    public static void classify(int a, int b) {
        test(a, b);
    }

    public static void main(String[] args) {
        classify(1, 2);
    }
}
