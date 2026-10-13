// Derived from commons-numbers: commons-numbers-arrays/src/main/java/org/apache/commons/numbers/arrays/Sorting.java, method sort(int[] x, int left, int right).
// Origin: https://github.com/apache/commons-numbers, commit f9403ff37998b49c6b85273713847c856d8ee47b. Apache License 2.0. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoNumSortingSort {
    static void sort(int[] x, int left, int right) {
            for (int i = left; ++i <= right;) {
                final int v = x[i];
                
                if (v < x[i - 1]) {
                    int j = i;
                    while (--j >= left && v < x[j]) {
                        x[j + 1] = x[j];
                    }
                    x[j + 1] = v;
                }
            }
        }
    public static void classify(int x0, int x1, int x2, int x3, int left, int right) {
        int[] xArr = {x0, x1, x2, x3};
        try {
            sort(xArr, left, right);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0, 0); }
}
