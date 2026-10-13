public class UnevenTree2 {

    // More pronounced asymmetry than UnevenTree.java: one branch goes 3
    // levels deep, the other returns immediately -- a bigger structural
    // depth gap between the two subtrees under the root.
    public static int classify(int a, int b, int c) {
        if (a > 0) {
            // deep subtree
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
            // shallow subtree -- returns immediately, no further branching
            return 5;
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1);
    }
}
