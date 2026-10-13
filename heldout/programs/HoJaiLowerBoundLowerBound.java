// Derived from java-algorithms-implementation: src/com/jwetherell/algorithms/search/LowerBound.java, method lowerBound(int[] array, int length, int value).
// Origin: https://github.com/phishman3579/java-algorithms-implementation, commit f2d115704691e8e4f6cfe490231d0adb0c3ce7d0. Apache License 2.0. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoJaiLowerBoundLowerBound {
    public static int lowerBound(int[] array, int length, int value) {
            int low = 0;
            int high = length;
            while (low < high) {
                final int mid = (low + high) / 2;
                
                if (value <= array[mid]) {
                    high = mid;
                } else {
                    low = mid + 1;
                }
            }
            return low;
        }
    public static void classify(int array0, int array1, int array2, int array3, int length, int value) {
        int[] arrayArr = {array0, array1, array2, array3};
        try {
            lowerBound(arrayArr, length, value);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0, 0); }
}
