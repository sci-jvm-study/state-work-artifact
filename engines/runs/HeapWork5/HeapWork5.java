public class HeapWork5 {

    // 5-variable graduated allocation-count gradient, same idea as
    // HeapWork4.java, one more independent branch.
    public static int classify(int a, int b, int c, int d, int e) {
        int count = 0;
        if (a > 0) count += 60;
        if (b > 0) count += 20;
        if (c > 0) count += 10;
        if (d > 0) count += 5;
        if (e > 0) count += 2;

        Object[] junk = new Object[count > 0 ? count : 1];
        for (int i = 0; i < count; i++) {
            junk[i] = new Object();
        }
        return count;
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1, 1);
    }
}