public class BranchTree4 {

    // 4 nested symbolic branches: a complete binary decision tree of depth 4 (16 leaves, 15 internal states).
    public static int classify(int a, int b, int c, int d) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) { return 1; } else { return 2; }
                } else {
                    if (d > 0) { return 3; } else { return 4; }
                }
            } else {
                if (c > 0) {
                    if (d > 0) { return 5; } else { return 6; }
                } else {
                    if (d > 0) { return 7; } else { return 8; }
                }
            }
        } else {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) { return 9; } else { return 10; }
                } else {
                    if (d > 0) { return 11; } else { return 12; }
                }
            } else {
                if (c > 0) {
                    if (d > 0) { return 13; } else { return 14; }
                } else {
                    if (d > 0) { return 15; } else { return 16; }
                }
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1);
    }
}