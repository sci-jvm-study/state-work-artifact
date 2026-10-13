public class BranchTree {

    // Three nested symbolic branches: a complete binary decision tree of depth 3 (8 leaves).
    public static int classify(int a, int b, int c) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    return 1;
                } else {
                    return 2;
                }
            } else {
                if (c > 0) {
                    return 3;
                } else {
                    return 4;
                }
            }
        } else {
            if (b > 0) {
                if (c > 0) {
                    return 5;
                } else {
                    return 6;
                }
            } else {
                if (c > 0) {
                    return 7;
                } else {
                    return 8;
                }
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1);
    }
}
