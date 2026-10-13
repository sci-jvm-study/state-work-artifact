// Extracted from Apache Commons Lang3 3.14.0, ArrayUtils.lastIndexOf(int[], int, int).
// Apache License 2.0. Source: https://github.com/apache/commons-lang/blob/rel/commons-lang-3.14.0/src/main/java/org/apache/commons/lang3/ArrayUtils.java
//
// Searches backward from the end of the array, unlike ArrayUtilsIndexOf.java. `INDEX_NOT_FOUND` is inlined as -1, as in
// ArrayUtilsIndexOf.java.
public class ArrayUtilsLastIndexOf {

    private static final int INDEX_NOT_FOUND = -1;

    public static int lastIndexOf(final int[] array, final int valueToFind, int startIndex) {
        if (array == null || startIndex < 0) {
            return INDEX_NOT_FOUND;
        }
        if (startIndex >= array.length) {
            startIndex = array.length - 1;
        }
        for (int i = startIndex; i >= 0; i--) {
            if (valueToFind == array[i]) {
                return i;
            }
        }
        return INDEX_NOT_FOUND;
    }

    public static int classify(int a, int b, int c, int d, int e, int f, int target) {
        int[] array = {a, b, c, d, e, f};
        return lastIndexOf(array, target, array.length - 1);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 6, 4);
    }
}
