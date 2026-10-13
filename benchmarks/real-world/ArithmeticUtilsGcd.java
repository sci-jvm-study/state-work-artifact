// Extracted from Apache Commons Math 3.6.1
// org.apache.commons.math3.util.ArithmeticUtils (Apache License 2.0)
// Source: https://github.com/apache/commons-math/blob/MATH_3_6_1/src/main/java/org/apache/commons/math3/util/ArithmeticUtils.java
//
// MODIFICATIONS:
//   - `MathArithmeticException` (commons-math3, requires a large exception-hierarchy
//     dependency tree just to compile) replaced with standard `ArithmeticException`.
//     Same condition, same message content, no commons-math3 dependency needed.
//   - `FastMath.abs`/`FastMath.min` (commons-math3) replaced with `Math.abs`/`Math.min`
//     (java.lang) -- functionally identical for int arguments.
//   - A `main` method was added as a driver; it is not part of the original class.
//
// ALL BRANCHING AND LOOP LOGIC BELOW IS UNCHANGED FROM THE ORIGINAL -- every `if`,
// `while`, and arithmetic comparison is copied verbatim. This is the real binary GCD
// (Stein's algorithm, Knuth 4.5.2 Algorithm B) as shipped in a widely used, real
// open-source Java library.
public class ArithmeticUtilsGcd {

    public static int gcd(int p, int q) throws ArithmeticException {
        int a = p;
        int b = q;
        if (a == 0 ||
            b == 0) {
            if (a == Integer.MIN_VALUE ||
                b == Integer.MIN_VALUE) {
                throw new ArithmeticException("overflow: gcd(" + p + ", " + q + ") is 2^31");
            }
            return Math.abs(a + b);
        }

        long al = a;
        long bl = b;
        boolean useLong = false;
        if (a < 0) {
            if (Integer.MIN_VALUE == a) {
                useLong = true;
            } else {
                a = -a;
            }
            al = -al;
        }
        if (b < 0) {
            if (Integer.MIN_VALUE == b) {
                useLong = true;
            } else {
                b = -b;
            }
            bl = -bl;
        }
        if (useLong) {
            if (al == bl) {
                throw new ArithmeticException("overflow: gcd(" + p + ", " + q + ") is 2^31");
            }
            long blbu = bl;
            bl = al;
            al = blbu % al;
            if (al == 0) {
                if (bl > Integer.MAX_VALUE) {
                    throw new ArithmeticException("overflow: gcd(" + p + ", " + q + ") is 2^31");
                }
                return (int) bl;
            }
            blbu = bl;

            // Now "al" and "bl" fit in an "int".
            b = (int) al;
            a = (int) (blbu % al);
        }

        return gcdPositive(a, b);
    }

    private static int gcdPositive(int a, int b) {
        if (a == 0) {
            return b;
        } else if (b == 0) {
            return a;
        }

        // Make "a" and "b" odd, keeping track of common power of 2.
        final int aTwos = Integer.numberOfTrailingZeros(a);
        a >>= aTwos;
        final int bTwos = Integer.numberOfTrailingZeros(b);
        b >>= bTwos;
        final int shift = Math.min(aTwos, bTwos);

        // "a" and "b" are positive.
        // If a > b then "gcd(a, b)" is equal to "gcd(a - b, b)".
        // If a < b then "gcd(a, b)" is equal to "gcd(b - a, a)".
        // Hence, in the successive iterations:
        //  "a" becomes the absolute difference of the current values,
        //  "b" becomes the minimum of the current values.
        while (a != b) {
            final int delta = a - b;
            b = Math.min(a, b);
            a = Math.abs(delta);

            // Remove any power of 2 in "a" ("b" is guaranteed to be odd).
            a >>= Integer.numberOfTrailingZeros(a);
        }

        // Recover the common power of 2.
        return a << shift;
    }

    public static void main(String[] args) {
        gcd(12, 18);
    }
}
