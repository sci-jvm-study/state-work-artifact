public class Learn2 {

    // Extends Learn.java's asymmetric pattern with a 3rd variable: the
    // a>0 branch goes 2 levels deep (b, then c), the a<=0 branch returns
    // immediately -- same idea as Learn.java, one level deeper.
    public static int classify(int a, int b, int c) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    return 1;
                } else {
                    return 2;
                }
            } else {
                return 3;
            }
        } else {
            return 4;
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1);
    }
}
