public class BranchTree5 {

    // 5 nested symbolic branches -> complete binary decision tree of depth 5
    // (31 non-leaf internal states, 32 leaves) -- same family as
    // BranchTree.java/BranchTree4.java, one more level.
    public static int classify(int a, int b, int c, int d, int e) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) { return 1; } else { return 2; }
                    } else {
                        if (e > 0) { return 3; } else { return 4; }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) { return 5; } else { return 6; }
                    } else {
                        if (e > 0) { return 7; } else { return 8; }
                    }
                }
            } else {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) { return 9; } else { return 10; }
                    } else {
                        if (e > 0) { return 11; } else { return 12; }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) { return 13; } else { return 14; }
                    } else {
                        if (e > 0) { return 15; } else { return 16; }
                    }
                }
            }
        } else {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) { return 17; } else { return 18; }
                    } else {
                        if (e > 0) { return 19; } else { return 20; }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) { return 21; } else { return 22; }
                    } else {
                        if (e > 0) { return 23; } else { return 24; }
                    }
                }
            } else {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) { return 25; } else { return 26; }
                    } else {
                        if (e > 0) { return 27; } else { return 28; }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) { return 29; } else { return 30; }
                    } else {
                        if (e > 0) { return 31; } else { return 32; }
                    }
                }
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1, 1);
    }
}
