// Extracted from Apache Commons Lang3 3.14.0
// org.apache.commons.lang3.ArrayUtils.indexOf(int[], int, int)
// Source: https://github.com/apache/commons-lang/blob/rel/commons-lang-3.14.0/src/main/java/org/apache/commons/lang3/ArrayUtils.java
// Apache License 2.0. No modifications -- copied verbatim (the only external
// symbol used, INDEX_NOT_FOUND, is inlined as the literal -1 it is defined to be
// elsewhere in the same class, to avoid pulling in the rest of ArrayUtils).
//
// The cost of this method depends on where in the array the match occurs (early exit at the first matching iteration) or on a
// full scan if it never matches. All four array elements and the search value are symbolic, so different symbolic paths
// correspond to different match positions.
public class ArrayUtilsIndexOf {

    private static final int INDEX_NOT_FOUND = -1;

    public static int indexOf(final int[] array, final int valueToFind, int startIndex) {
        if (array == null) {
            return INDEX_NOT_FOUND;
        }
        if (startIndex < 0) {
            startIndex = 0;
        }
        for (int i = startIndex; i < array.length; i++) {
            if (valueToFind == array[i]) {
                return i;
            }
        }
        return INDEX_NOT_FOUND;
    }

    public static int classify(int a, int b, int c, int d, int target) {
        int[] array = {a, b, c, d};
        return indexOf(array, target, 0);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 3);
    }
}
