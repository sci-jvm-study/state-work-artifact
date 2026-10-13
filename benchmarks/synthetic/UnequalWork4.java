public class UnequalWork4 {

    // 4-variable graduated loop-iteration-count gradient, the loop-count
    // analogue of HeapWork4.java.
    public static int classify(int a, int b, int c, int d) {
        int count = 0;
        if (a > 0) count += 60;
        if (b > 0) count += 20;
        if (c > 0) count += 10;
        if (d > 0) count += 5;

        int x = 0;
        for (int i = 0; i < count; i++) {
            x = x + i;
        }
        return x;
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1);
    }
}
