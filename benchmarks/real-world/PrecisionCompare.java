// Extracted from Apache Commons Math 3.6.1, org.apache.commons.math3.util.Precision
// (compareTo(double,double,double), equals(double,double,double), equals(double,double,int))
// -- Apache License 2.0.
// Source: https://github.com/apache/commons-math/blob/MATH_3_6_1/src/main/java/org/apache/commons/math3/util/Precision.java
//
// A floating-point comparison algorithm (ULP-based equality via Double.doubleToRawLongBits). It uses the Choco solver, because the
// real-number decision procedure of Z3 (mkReal) does not work in this build.
//
// MODIFICATION: FastMath.abs is replaced by Math.abs.
public class PrecisionCompare {

    private static final long SGN_MASK = 0x8000000000000000L;
    private static final long POSITIVE_ZERO_DOUBLE_BITS = Double.doubleToRawLongBits(+0.0);
    private static final long NEGATIVE_ZERO_DOUBLE_BITS = Double.doubleToRawLongBits(-0.0);

    public static boolean equals(final double x, final double y, final int maxUlps) {
        final long xInt = Double.doubleToRawLongBits(x);
        final long yInt = Double.doubleToRawLongBits(y);

        final boolean isEqual;
        if (((xInt ^ yInt) & SGN_MASK) == 0L) {
            isEqual = Math.abs(xInt - yInt) <= maxUlps;
        } else {
            final long deltaPlus;
            final long deltaMinus;
            if (xInt < yInt) {
                deltaPlus = yInt - POSITIVE_ZERO_DOUBLE_BITS;
                deltaMinus = xInt - NEGATIVE_ZERO_DOUBLE_BITS;
            } else {
                deltaPlus = xInt - POSITIVE_ZERO_DOUBLE_BITS;
                deltaMinus = yInt - NEGATIVE_ZERO_DOUBLE_BITS;
            }
            if (deltaPlus > maxUlps) {
                isEqual = false;
            } else {
                isEqual = deltaMinus <= (maxUlps - deltaPlus);
            }
        }
        return isEqual && !Double.isNaN(x) && !Double.isNaN(y);
    }

    public static boolean equals(double x, double y, double eps) {
        return equals(x, y, 1) || Math.abs(y - x) <= eps;
    }

    public static int compareTo(double x, double y, double eps) {
        if (equals(x, y, eps)) {
            return 0;
        } else if (x < y) {
            return -1;
        }
        return 1;
    }

    public static void classify(double x, double y) {
        compareTo(x, y, 1.0e-6);
    }

    public static void main(String[] args) {
        classify(1.0, 1.0000001);
    }
}
