public class UnevenTree {

    public static int classify(int a, int b, int c) {
        if (a > 0) {
            // Large subtree: b and c both branch
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
            // Small subtree: only b branches
            if (b > 0) {
                return 5;
            } else {
                return 6;
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1);
    }
}