// Extracted from sv-benchmarks java/jdart-regression/addition01/Main.java
// (a modification of jayhorn-recursive's own MIT-licensed benchmark; MIT
// license, see /java/jayhorn-recursive/LICENSE per the source file header).
// addition() copied verbatim: computes m+n by repeated recursive increment or decrement, with a third parameter (c) that tracks the
// recursion depth for a bound check. The direction of the recursion depends on whether n is positive or negative.
public class RecursiveAddition {

    public static int addition(int m, int n, int c) {
        if (n == 0) {
            return m;
        }
        if (c >= 150) {
            throw new IllegalStateException("bound exceeded");
        }
        if (n > 0) {
            return addition(m + 1, n - 1, ++c);
        } else {
            return addition(m - 1, n + 1, ++c);
        }
    }

    public static int classify(int m, int n) {
        return addition(m, n, 0);
    }

    public static void main(String[] args) {
        classify(3, 4);
    }
}