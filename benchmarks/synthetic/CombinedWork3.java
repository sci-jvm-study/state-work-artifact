public class CombinedWork3 {

    // Extends CombinedWork.java from 2 nested ifs (4 leaves) to 3 nested ifs
    // (8 leaves), keeping the same idea (each leaf has a different mix of
    // loop-iteration and allocation cost) but with more distinct profiles.
    public static int classify(int a, int b, int c) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    // heaviest: big loop + big allocation
                    Object[] junk = new Object[80];
                    int x = 0;
                    for (int i = 0; i < 80; i++) { x += i; junk[i] = new Object(); }
                    return 1;
                } else {
                    // big loop only
                    int x = 0;
                    for (int i = 0; i < 80; i++) { x += i; }
                    return 2;
                }
            } else {
                if (c > 0) {
                    // big allocation only
                    Object[] junk = new Object[80];
                    for (int i = 0; i < 80; i++) { junk[i] = new Object(); }
                    return 3;
                } else {
                    // small loop, no allocation
                    int x = 0;
                    for (int i = 0; i < 5; i++) { x += i; }
                    return 4;
                }
            }
        } else {
            if (b > 0) {
                if (c > 0) {
                    // small allocation only
                    Object[] junk = new Object[5];
                    for (int i = 0; i < 5; i++) { junk[i] = new Object(); }
                    return 5;
                } else {
                    // small loop + small allocation
                    Object[] junk = new Object[5];
                    int x = 0;
                    for (int i = 0; i < 5; i++) { x += i; junk[i] = new Object(); }
                    return 6;
                }
            } else {
                if (c > 0) {
                    // trivial
                    return 7;
                } else {
                    // trivial
                    return 8;
                }
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1);
    }
}
