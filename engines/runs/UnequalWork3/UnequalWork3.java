public class UnequalWork3 {

    // Extends UnequalWork.java (2 nested ifs, 2 loop-count profiles) to 3
    // nested ifs with 4 graduated loop-iteration-count profiles
    // (5, 20, 60, 150), the loop-count analogue of HeapWork3.java's
    // allocation-count gradient.
    public static int classify(int a, int b, int c) {
        int count;
        if (a > 0) {
            count = (b > 0) ? (c > 0 ? 150 : 60) : (c > 0 ? 20 : 5);
        } else {
            count = (b > 0) ? (c > 0 ? 60 : 20) : (c > 0 ? 20 : 5);
        }
        int x = 0;
        for (int i = 0; i < count; i++) {
            x = x + i;
        }
        return x;
    }

    public static void main(String[] args) {
        classify(1, 1, 1);
    }
}