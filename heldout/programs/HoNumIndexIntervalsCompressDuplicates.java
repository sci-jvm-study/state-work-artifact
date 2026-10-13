// Derived from commons-numbers: commons-numbers-examples/examples-jmh/src/main/java/org/apache/commons/numbers/examples/jmh/arrays/IndexIntervals.java, method compressDuplicates(int[] data, int n).
// Origin: https://github.com/apache/commons-numbers, commit f9403ff37998b49c6b85273713847c856d8ee47b. Apache License 2.0. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoNumIndexIntervalsCompressDuplicates {
    private static int compressDuplicates(int[] data, int n) {
            
            int last = 0;
            int top = data[0];
            for (int i = 0; ++i < n;) {
                final int v = data[i];
                if (v == top) {
                    continue;
                }
                top = v;
                data[++last] = v;
            }
            return last + 1;
        }
    public static void classify(int data0, int data1, int data2, int data3, int n) {
        int[] dataArr = {data0, data1, data2, data3};
        try {
            compressDuplicates(dataArr, n);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0); }
}
