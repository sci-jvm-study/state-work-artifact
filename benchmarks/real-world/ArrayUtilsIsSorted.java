// Extracted from Apache Commons Lang3 3.14.0
// org.apache.commons.lang3.ArrayUtils.isSorted(int[])
// Source: https://github.com/apache/commons-lang/blob/rel/commons-lang-3.14.0/src/main/java/org/apache/commons/lang3/ArrayUtils.java
// Apache License 2.0.
//
// MODIFICATIONS (documented): `getLength(Object)` (a one-line null-safe
// java.lang.reflect.Array.getLength wrapper, operating on the concrete array
// reference, never symbolic) inlined as a plain `array.length` check.
// `NumberUtils.compare(int,int)` (Commons Lang3's own trivial int comparator)
// inlined as `Integer.compare`, which is definitionally the same operation --
// avoids pulling in the whole NumberUtils class for one comparison call.
// Loop and branching logic is otherwise unchanged.
//
// This loop exits early on the first out-of-order pair and not on a value match.
public class ArrayUtilsIsSorted {

    public static boolean isSorted(final int[] array) {
        if (array == null || array.length < 2) {
            return true;
        }

        int previous = array[0];
        final int n = array.length;
        for (int i = 1; i < n; i++) {
            final int current = array[i];
            if (Integer.compare(previous, current) > 0) {
                return false;
            }
            previous = current;
        }
        return true;
    }

    public static boolean classify(int a, int b, int c, int d) {
        int[] array = {a, b, c, d};
        return isSorted(array);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4);
    }
}
