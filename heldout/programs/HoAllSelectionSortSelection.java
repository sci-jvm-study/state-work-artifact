// Derived from java: algorithms/sorting/SelectionSort.java, method selection(int[] a, int left, int right).
// Origin: https://github.com/AllAlgorithms/java, commit 1af0c0bab97d9a03a7665894c067fac66c96fcc5. MIT License, Copyright (c) 2018 All Algorithms and its contributors. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoAllSelectionSortSelection {
    static void selection(int[] a, int left, int right) {
            for (int i = left; i < right; i++) {
                int min = i;
                for (int j = i + 1; j <= right; j++)
                    if (a[j] < a[min])
                        min = j;
                int temp = a[i];
                a[i] = a[min];
                a[min] = temp;
            }
        }
    public static void classify(int a0, int a1, int a2, int a3, int left, int right) {
        int[] aArr = {a0, a1, a2, a3};
        try {
            selection(aArr, left, right);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0, 0); }
}
