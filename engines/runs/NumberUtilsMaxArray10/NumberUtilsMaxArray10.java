// Same algorithm as NumberUtilsMaxArray.java (Apache Commons Lang3 3.14.0,
// Apache-2.0). 10 elements instead of 4/6/8.
public class NumberUtilsMaxArray10 {

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

    public static int classify(int a, int b, int c, int d, int e, int f, int g, int h, int i, int j) {
        return max(a, b, c, d, e, f, g, h, i, j);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
    }
}