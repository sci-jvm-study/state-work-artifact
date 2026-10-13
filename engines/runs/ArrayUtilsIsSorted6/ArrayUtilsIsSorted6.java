// Same algorithm as ArrayUtilsIsSorted.java (Apache Commons Lang3 3.14.0,
// Apache-2.0). isSorted() copied verbatim. Only the driver differs: 6
// elements instead of 4.
public class ArrayUtilsIsSorted6 {

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

    public static boolean classify(int a, int b, int c, int d, int e, int f) {
        int[] array = {a, b, c, d, e, f};
        return isSorted(array);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 6);
    }
}