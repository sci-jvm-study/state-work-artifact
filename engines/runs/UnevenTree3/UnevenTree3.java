public class UnevenTree3 {

    // A third asymmetry pattern: three branches of different depths under
    // one root (1-deep, 2-deep, 3-deep), rather than the 2-way splits in
    // UnevenTree.java/UnevenTree2.java.
    public static int classify(int a, int b, int c, int d) {
        if (a > 0) {
            // shallow: returns immediately
            return 1;
        } else if (b > 0) {
            // medium: one more check
            if (c > 0) {
                return 2;
            } else {
                return 3;
            }
        } else {
            // deep: two more checks
            if (c > 0) {
                if (d > 0) {
                    return 4;
                } else {
                    return 5;
                }
            } else {
                if (d > 0) {
                    return 6;
                } else {
                    return 7;
                }
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1);
    }
}