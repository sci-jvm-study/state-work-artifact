// Extracted from Apache Commons Math 3.6.1, org.apache.commons.math3.util.ArithmeticUtils
// (pow(int,int), mulAndCheck(int,int)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-math/blob/MATH_3_6_1/src/main/java/org/apache/commons/math3/util/ArithmeticUtils.java
//
// pow: exponentiation by squaring, a loop- and branch-heavy numerical algorithm with overflow-exception handling (via
// mulAndCheck, shared verbatim with ArithmeticUtilsCheck.java).
//
// MODIFICATION: NotPositiveException and MathArithmeticException are replaced by the standard ArithmeticException (this avoids
// pulling in the exception hierarchy of Commons Math for one method).
public class ArithmeticUtilsPow {

    public static int mulAndCheck(int x, int y) throws ArithmeticException {
        long m = ((long) x) * ((long) y);
        if (m < Integer.MIN_VALUE || m > Integer.MAX_VALUE) {
            throw new ArithmeticException("overflow: multiplication");
        }
        return (int) m;
    }

    public static int pow(final int k, final int e) throws ArithmeticException {
        if (e < 0) {
            throw new ArithmeticException("negative exponent: " + e);
        }
        int exp = e;
        int result = 1;
        int k2p = k;
        while (true) {
            if ((exp & 0x1) != 0) {
                result = mulAndCheck(result, k2p);
            }
            exp >>= 1;
            if (exp == 0) {
                break;
            }
            k2p = mulAndCheck(k2p, k2p);
        }
        return result;
    }

    public static void classify(int k, int e) {
        pow(k, e);
    }

    public static void main(String[] args) {
        classify(2, 10);
    }
}
