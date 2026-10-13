// Extracted from sv-benchmarks java/jpf-regression/ExSymExeResearch_true/Main.java
// (aggregated from jpf-symbc's own regression suite).
// Origin: https://github.com/sosy-lab/sv-benchmarks -- Apache License 2.0.
// test() logic copied verbatim, adapted to classify().
public class ExSymExeResearch {

    static int test(int a, int b) {
        int result = 0;
        if (a >= 0 && a < 100 && b >= 0 && b < 100) {
            int sum = a + b;
            int diff = a - b;
            int temp;
            if (sum > 0) {
                temp = a;
            } else {
                temp = b;
            }
            if (temp < diff) {
                result = temp;
            } else {
                result = diff;
            }
        }
        return result;
    }

    public static void classify(int a, int b) {
        test(a, b);
    }

    public static void main(String[] args) {
        classify(1, 2);
    }
}
