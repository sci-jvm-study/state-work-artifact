// Extracted from Apache Commons Lang3 3.14.0
// org.apache.commons.lang3.math.NumberUtils.max(int...)
// Source: https://github.com/apache/commons-lang/blob/rel/commons-lang-3.14.0/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
// Apache License 2.0.
//
// MODIFICATION: the original calls a private helper `validateArray(Object)` (java.util.Objects.requireNonNull and Validate.isTrue of
// Commons Lang3). The two null and empty checks on the concrete array reference are inlined as plain `NullPointerException` and
// `IllegalArgumentException` throws. The loop and comparison logic is unchanged.
//
// The array has a fixed, concrete length (4), so the branching comes from the loop and the comparisons and not from a symbolic
// array length (which jpf-symbc does not handle well).
public class NumberUtilsMaxArray {

    public static int max(final int... array) {
        if (array == null) {
            throw new NullPointerException("array");
        }
        if (array.length == 0) {
            throw new IllegalArgumentException("Array cannot be empty.");
        }

        int max = array[0];
        for (int j = 1; j < array.length; j++) {
            if (array[j] > max) {
                max = array[j];
            }
        }

        return max;
    }

    public static int classify(int a, int b, int c, int d) {
        return max(a, b, c, d);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4);
    }
}
