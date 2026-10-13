// Extracted from Apache Commons Math 3.6.1, org.apache.commons.math3.util.ArithmeticUtils
// (addAndCheck(int,int), mulAndCheck(int,int)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-math/blob/MATH_3_6_1/src/main/java/org/apache/commons/math3/util/ArithmeticUtils.java
//
// These overflow-checked arithmetic methods use only widening casts to long and plain comparisons (no bitwise operators).
//
// MODIFICATION: `MathArithmeticException` is replaced by the standard `ArithmeticException`.
public class ArithmeticUtilsCheck {

    public static int addAndCheck(int x, int y) throws ArithmeticException {
        long s = (long) x + (long) y;
        if (s < Integer.MIN_VALUE || s > Integer.MAX_VALUE) {
            throw new ArithmeticException("overflow: addition");
        }
        return (int) s;
    }

    public static int mulAndCheck(int x, int y) throws ArithmeticException {
        long m = ((long) x) * ((long) y);
        if (m < Integer.MIN_VALUE || m > Integer.MAX_VALUE) {
            throw new ArithmeticException("overflow: multiplication");
        }
        return (int) m;
    }

    public static void classify(int a, int b, int c) {
        int sum = addAndCheck(a, b);
        mulAndCheck(sum, c);
    }

    public static void main(String[] args) {
        classify(1, 2, 3);
    }
}
