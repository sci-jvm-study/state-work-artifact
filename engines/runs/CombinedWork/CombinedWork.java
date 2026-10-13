public class CombinedWork {

    // Four leaves under two nested ifs, each with a different cost profile that combines loop iterations and allocations. Same tree
    // shape on all four branches; only the hidden cost differs.
    public static int classify(int a, int b) {
        if (a > 0) {
            if (b > 0) {
                // heavy loop AND heavy allocation
                Object[] junk = new Object[100];
                int x = 0;
                for (int i = 0; i < 100; i++) {
                    x = x + i;
                    junk[i] = new Object();
                }
                return 1;
            } else {
                // heavy loop, NO allocation
                int x = 0;
                for (int i = 0; i < 100; i++) {
                    x = x + i;
                }
                return 2;
            }
        } else {
            if (b > 0) {
                // NO loop, heavy allocation
                Object[] junk = new Object[100];
                for (int i = 0; i < 100; i++) {
                    junk[i] = new Object();
                }
                return 3;
            } else {
                // neither -- trivial
                return 4;
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1);
    }
}