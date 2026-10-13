// Same algorithm as ArrayUtilsLastIndexOf.java (Apache Commons Lang3 3.14.0,
// Apache-2.0). 10 elements instead of 6/8 (linear scan).
public class ArrayUtilsLastIndexOf10 {

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

    public static int classify(int a, int b, int c, int d, int e, int f, int g, int h, int i, int j, int target) {
        int[] array = {a, b, c, d, e, f, g, h, i, j};
        return lastIndexOf(array, target, array.length - 1);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 4);
    }
}
