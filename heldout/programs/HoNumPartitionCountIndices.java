// Derived from commons-numbers: commons-numbers-examples/examples-jmh/src/main/java/org/apache/commons/numbers/examples/jmh/arrays/Partition.java, method countIndices(int[] indices, int count, int right).
// Origin: https://github.com/apache/commons-numbers, commit f9403ff37998b49c6b85273713847c856d8ee47b. Apache License 2.0. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoNumPartitionCountIndices {
    static int countIndices(int[] indices, int count, int right) {
            int end = count;
            
            while (--end >= 0) {
                if (indices[end] <= right) {
                    break;
                }
            }
            for (int i = end; --i >= 0;) {
                final int k = indices[i];
                if (k > right) {
                    
                    indices[i] = indices[end];
                    indices[end] = k;
                    end--;
                }
            }
            return end + 1;
        }
    public static void classify(int indices0, int indices1, int indices2, int indices3, int count, int right) {
        int[] indicesArr = {indices0, indices1, indices2, indices3};
        try {
            countIndices(indicesArr, count, right);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0, 0); }
}
