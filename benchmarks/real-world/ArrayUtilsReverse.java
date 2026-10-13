// Extracted from Apache Commons Lang3, org.apache.commons.lang3.ArrayUtils
// (reverse(int[]), reverse(int[],int,int)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-lang/blob/master/src/main/java/org/apache/commons/lang3/ArrayUtils.java
// max0() (a trivial private helper, Math.max(0, other)) inlined directly,
// per the source.
//
// In-place array reversal: a two-pointer swap loop with range clamping.
public class ArrayUtilsReverse {

    private static int max0(final int other) {
        return Math.max(0, other);
    }

    public static void reverse(final int[] array, final int startIndexInclusive, final int endIndexExclusive) {
        if (array == null) {
            return;
        }
        int i = Math.max(startIndexInclusive, 0);
        int j = max0(Math.min(array.length, endIndexExclusive)) - 1;
        int tmp;
        while (j > i) {
            tmp = array[j];
            array[j] = array[i];
            array[i] = tmp;
            j--;
            i++;
        }
    }

    public static void classify(int start, int end) {
        int[] array = {1, 2, 3, 4, 5};
        reverse(array, start, end);
    }

    public static void main(String[] args) {
        classify(0, 5);
    }
}
