public class Learn {

    // This method runs symbolically: JPF treats a and b as arbitrary ints.
    public static int classify(int a, int b) {
        if (a > 0) {
            if (b > 0) {
                return 1;        // path 1: a>0, b>0
            } else {
                return 2;        // path 2: a>0, b<=0
            }
        } else {
            return 3;            // path 3: a<=0
        }
    }

    public static void main(String[] args) {
        classify(5, 7);          // ye concrete values ignore ho jaayengi
    }
}
