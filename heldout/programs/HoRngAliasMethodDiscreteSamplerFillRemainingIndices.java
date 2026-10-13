// Derived from commons-rng: commons-rng-sampling/src/main/java/org/apache/commons/rng/sampling/distribution/AliasMethodDiscreteSampler.java, method fillRemainingIndices(final int length, final int[] indices, int small).
// Origin: https://github.com/apache/commons-rng, commit 6e5a0056b1a8405771431478f3e7c134dee35c14. Apache License 2.0. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoRngAliasMethodDiscreteSamplerFillRemainingIndices {
    private static int fillRemainingIndices(final int length, final int[] indices, int small) {
            int updatedSmall = small;
            for (int i = length; i < indices.length; i++) {
                indices[updatedSmall++] = i;
            }
            return updatedSmall;
        }
    public static void classify(int length, int indices0, int indices1, int indices2, int indices3, int small) {
        int[] indicesArr = {indices0, indices1, indices2, indices3};
        try {
            fillRemainingIndices(length, indicesArr, small);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0, 0); }
}
