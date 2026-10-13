// Same algorithm as ArrayUtilsIndexOf.java (Apache Commons Lang3 3.14.0,
// Apache-2.0). 8 elements instead of 4/6.
public class ArrayUtilsIndexOf8 {

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

    public static int classify(int a, int b, int c, int d, int e, int f, int g, int h, int target) {
        int[] array = {a, b, c, d, e, f, g, h};
        return indexOf(array, target, 0);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 6, 7, 8, 4);
    }
}
