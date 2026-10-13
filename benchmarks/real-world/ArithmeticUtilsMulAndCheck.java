// Extracted from Apache Commons Math3 (org.apache.commons.math3.util.ArithmeticUtils),
// https://github.com/apache/commons-math (tag MATH_3_6_1) -- Apache License 2.0.
// mulAndCheck(long,long) copied verbatim. Deeply nested sign and overflow branching on the symbolic a and b, with a single self-call
// when a > b (the arguments are swapped so that a <= b afterwards), a recursion of depth 1.
public class ArithmeticUtilsMulAndCheck {

    public static long mulAndCheck(long a, long b) {
        long ret;
        if (a > b) {
            ret = mulAndCheck(b, a);
        } else {
            if (a < 0) {
                if (b < 0) {
                    if (a >= Long.MAX_VALUE / b) {
                        ret = a * b;
                    } else {
                        throw new ArithmeticException("overflow in multiplication");
                    }
                } else if (b > 0) {
                    if (Long.MIN_VALUE / b <= a) {
                        ret = a * b;
                    } else {
                        throw new ArithmeticException("overflow in multiplication");
                    }
                } else {
                    ret = 0;
                }
            } else if (a > 0) {
                if (a <= Long.MAX_VALUE / b) {
                    ret = a * b;
                } else {
                    throw new ArithmeticException("overflow in multiplication");
                }
            } else {
                ret = 0;
            }
        }
        return ret;
    }

    public static void classify(int a, int b) {
        try {
            mulAndCheck(a, b);
        } catch (ArithmeticException e) {
            // unreachable at this input scale, kept for parity with the original method
        }
    }

    public static void main(String[] args) {
        classify(2, 3);
    }
}
