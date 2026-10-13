// Same algorithm as ArrayUtilsIsSorted.java (Apache Commons Lang3 3.14.0,
// Apache-2.0). isSorted() copied verbatim. 8 elements instead of 4/6 --
// linear scan with early exit, growth roughly linear in element count.
public class ArrayUtilsIsSorted8 {

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

    public static boolean classify(int a, int b, int c, int d, int e, int f, int g, int h) {
        int[] array = {a, b, c, d, e, f, g, h};
        return isSorted(array);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 6, 7, 8);
    }
}
