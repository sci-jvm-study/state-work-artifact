// Same source as InsertionSort.java (see that file for full provenance/license:
// SV-COMP sv-benchmarks java/algorithms/InsertionSort-FunSat01, BSD-3-clause,
// Jacob Burnim). `sort(int[])` copied verbatim.
//
// 6 symbolic elements (6! = 720 orderings) instead of 5.
public class InsertionSort6 {

    public static void sort(int[] a) {
        final int N = a.length;
        for (int i = 1; i < N; i++) {
            int j = i - 1;
            int x = a[i];
            while ((j >= 0) && (a[j] > x)) {
                a[j + 1] = a[j];
                j--;
            }
            a[j + 1] = x;
        }
    }

    public static void classify(int a, int b, int c, int d, int e, int f) {
        int[] arr = {a, b, c, d, e, f};
        sort(arr);
    }

    public static void main(String[] args) {
        classify(6, 5, 4, 3, 2, 1);
    }
}
