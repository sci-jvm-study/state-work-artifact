// Extracted from Apache Commons Math3 (org.apache.commons.math3.util.Precision),
// https://github.com/apache/commons-math (tag MATH_3_6_1) -- Apache License 2.0.
// roundUnscaled(double,double,int) copied verbatim, modulo one substitution: MathArithmeticException /
// MathIllegalArgumentException are replaced with plain ArithmeticException / IllegalArgumentException, to avoid the exception
// hierarchy of Commons Math for a single throw site. Math.floor/Math.ceil/Math.nextAfter are used in place of FastMath (identical
// semantics for this method).
public class PrecisionRoundUnscaled {

    static double roundUnscaled(double unscaled, double sign, int roundingMethod) {
        switch (roundingMethod) {
            case java.math.BigDecimal.ROUND_CEILING:
                if (sign == -1) {
                    unscaled = Math.floor(Math.nextAfter(unscaled, Double.NEGATIVE_INFINITY));
                } else {
                    unscaled = Math.ceil(Math.nextAfter(unscaled, Double.POSITIVE_INFINITY));
                }
                break;
            case java.math.BigDecimal.ROUND_DOWN:
                unscaled = Math.floor(Math.nextAfter(unscaled, Double.NEGATIVE_INFINITY));
                break;
            case java.math.BigDecimal.ROUND_FLOOR:
                if (sign == -1) {
                    unscaled = Math.ceil(Math.nextAfter(unscaled, Double.POSITIVE_INFINITY));
                } else {
                    unscaled = Math.floor(Math.nextAfter(unscaled, Double.NEGATIVE_INFINITY));
                }
                break;
            case java.math.BigDecimal.ROUND_HALF_DOWN: {
                unscaled = Math.nextAfter(unscaled, Double.NEGATIVE_INFINITY);
                double fraction = unscaled - Math.floor(unscaled);
                if (fraction > 0.5) {
                    unscaled = Math.ceil(unscaled);
                } else {
                    unscaled = Math.floor(unscaled);
                }
                break;
            }
            case java.math.BigDecimal.ROUND_HALF_EVEN: {
                double fraction = unscaled - Math.floor(unscaled);
                if (fraction > 0.5) {
                    unscaled = Math.ceil(unscaled);
                } else if (fraction < 0.5) {
                    unscaled = Math.floor(unscaled);
                } else {
                    if (Math.floor(unscaled) / 2.0 == Math.floor(Math.floor(unscaled) / 2.0)) {
                        unscaled = Math.floor(unscaled);
                    } else {
                        unscaled = Math.ceil(unscaled);
                    }
                }
                break;
            }
            case java.math.BigDecimal.ROUND_HALF_UP: {
                unscaled = Math.nextAfter(unscaled, Double.POSITIVE_INFINITY);
                double fraction = unscaled - Math.floor(unscaled);
                if (fraction >= 0.5) {
                    unscaled = Math.ceil(unscaled);
                } else {
                    unscaled = Math.floor(unscaled);
                }
                break;
            }
            case java.math.BigDecimal.ROUND_UNNECESSARY:
                if (unscaled != Math.floor(unscaled)) {
                    throw new ArithmeticException("rounding necessary");
                }
                break;
            case java.math.BigDecimal.ROUND_UP:
                if (unscaled != Math.floor(unscaled)) {
                    unscaled = Math.ceil(Math.nextAfter(unscaled, Double.POSITIVE_INFINITY));
                }
                break;
            default:
                throw new IllegalArgumentException("invalid rounding method");
        }
        return unscaled;
    }

    public static void classify(double unscaled, double sign, int roundingMethod) {
        try {
            roundUnscaled(unscaled, sign, roundingMethod);
        } catch (ArithmeticException | IllegalArgumentException e) {
            // expected on ROUND_UNNECESSARY / invalid-method branches
        }
    }

    public static void main(String[] args) {
        classify(1.5, 1, java.math.BigDecimal.ROUND_HALF_EVEN);
    }
}
