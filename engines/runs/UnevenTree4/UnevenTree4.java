public class UnevenTree4 {

    // A fourth asymmetry pattern: four branches of different depths under
    // one root (1-deep, 2-deep, 3-deep, 4-deep), extending
    // UnevenTree3.java's three-tier asymmetry by one more tier.
    public static int classify(int a, int b, int c, int d, int e) {
        if (a > 0) {
            // shallow: returns immediately
            return 1;
        } else if (b > 0) {
            // tier 2: one more check
            if (c > 0) {
                return 2;
            } else {
                return 3;
            }
        } else if (c > 0) {
            // tier 3: two more checks
            if (d > 0) {
                return 4;
            } else {
                return 5;
            }
        } else {
            // tier 4 (deepest): three more checks
            if (d > 0) {
                if (e > 0) {
                    return 6;
                } else {
                    return 7;
                }
            } else {
                if (e > 0) {
                    return 8;
                } else {
                    return 9;
                }
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1, 1);
    }
}