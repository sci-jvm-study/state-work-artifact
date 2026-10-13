public class HeapWork {

    // The hidden cost driver is object allocation (measured by allocCount/allocWork). Same tree shape on both branches (2 leaves each),
    // so the cost difference is invisible to the structure of the state tree.
    public static int classify(int a, int b) {

        if (a > 0) {

            if (b > 0) {
                // Heavy branch: allocate many small objects.
                Object[] junk = new Object[200];
                for (int i = 0; i < 200; i++) {
                    junk[i] = new Object();
                }
                return 1;
            } else {
                return 2;
            }

        } else {

            if (b > 0) {
                // Light branch: allocate almost nothing.
                Object[] junk = new Object[2];
                for (int i = 0; i < 2; i++) {
                    junk[i] = new Object();
                }
                return 3;
            } else {
                return 4;
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1);
    }
}
