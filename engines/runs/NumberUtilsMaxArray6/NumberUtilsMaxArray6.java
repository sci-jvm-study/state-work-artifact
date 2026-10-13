// Same algorithm as NumberUtilsMaxArray.java (Apache Commons Lang3 3.14.0,
// Apache-2.0). max(int...) copied verbatim. 6 elements instead of 4.
public class NumberUtilsMaxArray6 {

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

    public static int classify(int a, int b, int c, int d, int e, int f) {
        return max(a, b, c, d, e, f);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 6);
    }
}