// Extracted from Apache Commons Math 3.6.1, CombinatoricsUtils.binomialCoefficient(int,int).
// Apache License 2.0. Source: https://github.com/apache/commons-math/blob/MATH_3_6_1/src/main/java/org/apache/commons/math3/util/CombinatoricsUtils.java
//
// Only the n <= 61 tier of the real method is extracted: the trivial-return cases and the multiplicative loop. The tiers for
// larger n call ArithmeticUtils.gcd(), which uses a bit shift by a symbolic amount that neither solver backend supports.
//
// `checkBinomial`'s two plain comparisons inlined as standard exceptions
// (same reasoning as ArithmeticUtilsGcd.java/ArithmeticUtilsCheck.java).
public class BinomialCoefficient {

    public static long binomialCoefficient(final int n, final int k) {
        if (n < k) {
            throw new IllegalArgumentException("k > n");
        }
        if (n < 0) {
            throw new IllegalArgumentException("n < 0");
        }

        if ((n == k) || (k == 0)) {
            return 1;
        }
        if ((k == 1) || (k == n - 1)) {
            return n;
        }
        if (k > n / 2) {
            return binomialCoefficient(n, n - k);
        }

        // n <= 61 case only (see scope note above) -- naive multiplicative
        // formula, cannot overflow for n in this range.
        long result = 1;
        int i = n - k + 1;
        for (int j = 1; j <= k; j++) {
            result = result * i / j;
            i++;
        }
        return result;
    }

    public static void classify(int n, int k) {
        // Caught so JPF explores the full state space instead of halting the
        // search at the first uncaught IllegalArgumentException (k>n or n<0
        // are reachable under this symbolic range).
        try {
            binomialCoefficient(n, k);
        } catch (IllegalArgumentException e) {
            // expected for invalid (n, k) combinations
        }
    }

    public static void main(String[] args) {
        classify(10, 4);
    }
}
