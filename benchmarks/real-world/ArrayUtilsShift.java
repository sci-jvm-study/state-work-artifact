// Extracted from Apache Commons Lang3 3.14.0, ArrayUtils.shift(int[], int, int, int)
// and its internal swap(int[], int, int, int) helper. Apache License 2.0.
// Both copied verbatim. An in-place block-rotation ("juggling") algorithm: a while loop with three-way branching (offset against
// nOffset) that calls swap() repeatedly, itself a for loop.
//
// The control flow depends on the numeric value of `offset` and not on the array element values, so `offset` is symbolic.
public class ArrayUtilsShift {

    public static void swap(final int[] array, int offset1, int offset2, int len) {
        if (array == null || array.length == 0 || offset1 >= array.length || offset2 >= array.length) {
            return;
        }
        if (offset1 < 0) {
            offset1 = 0;
        }
        if (offset2 < 0) {
            offset2 = 0;
        }
        len = Math.min(Math.min(len, array.length - offset1), array.length - offset2);
        for (int i = 0; i < len; i++, offset1++, offset2++) {
            final int aux = array[offset1];
            array[offset1] = array[offset2];
            array[offset2] = aux;
        }
    }

    public static void shift(final int[] array, int startIndexInclusive, int endIndexExclusive, int offset) {
        if (array == null || startIndexInclusive >= array.length - 1 || endIndexExclusive <= 0) {
            return;
        }
        if (startIndexInclusive < 0) {
            startIndexInclusive = 0;
        }
        if (endIndexExclusive >= array.length) {
            endIndexExclusive = array.length;
        }
        int n = endIndexExclusive - startIndexInclusive;
        if (n <= 1) {
            return;
        }
        offset %= n;
        if (offset < 0) {
            offset += n;
        }
        while (n > 1 && offset > 0) {
            final int nOffset = n - offset;
            if (offset > nOffset) {
                swap(array, startIndexInclusive, startIndexInclusive + n - nOffset, nOffset);
                n = offset;
                offset -= nOffset;
            } else if (offset < nOffset) {
                swap(array, startIndexInclusive, startIndexInclusive + nOffset, offset);
                startIndexInclusive += offset;
                n = nOffset;
            } else {
                swap(array, startIndexInclusive, startIndexInclusive + nOffset, offset);
                break;
            }
        }
    }

    public static void classify(int offset) {
        int[] array = {1, 2, 3, 4, 5, 6};
        shift(array, 0, array.length, offset);
    }

    public static void main(String[] args) {
        classify(2);
    }
}
