// Derived from java: algorithms/sorting/ShellSort.java, method shell(int[] a).
// Origin: https://github.com/AllAlgorithms/java, commit 1af0c0bab97d9a03a7665894c067fac66c96fcc5. MIT License, Copyright (c) 2018 All Algorithms and its contributors. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoAllShellSortShell {
    static void shell(int[] a) {
            int l = 0, r = a.length - 1, h;
            for (h = 0; h <= (r - 1) / 9; h = 3 * h + 1)
                ;
            for (; h > 0; h /= 3)
                for (int i = l + h; i <= r; i++) {
                    int j = i, v = a[i];
                    while (j >= l + h && v < a[j - h]) {
                        a[j] = a[j - h];
                        j -= h;
                    }
                    a[j] = v;
                }
        }
    public static void classify(int a0, int a1, int a2, int a3) {
        int[] aArr = {a0, a1, a2, a3};
        try {
            shell(aArr);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0); }
}
