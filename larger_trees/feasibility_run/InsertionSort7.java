// Feasibility run of the larger-trees study: insertion sort of 7 symbolic elements.
// sort(int[]) is the one of InsertionSort.java (SV-COMP sv-benchmarks, java/algorithms/InsertionSort-FunSat01, BSD-3-clause).
public class InsertionSort7 {

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

    public static void classify(int a, int b, int c, int d, int e, int f, int g) {
        int[] arr = {a, b, c, d, e, f, g};
        sort(arr);
    }

    public static void main(String[] args) {
        classify(7, 6, 5, 4, 3, 2, 1);
    }
}
