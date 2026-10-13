public class HeapWork3 {

    // Extends HeapWork.java (2 nested ifs, 2 alloc profiles) to 3 nested ifs
    // with 4 graduated allocation-count profiles (0, 20, 60, 150 objects),
    // to give a finer-grained, non-structural allocation-cost gradient.
    public static int classify(int a, int b, int c) {
        int count;
        if (a > 0) {
            count = (b > 0) ? (c > 0 ? 150 : 60) : (c > 0 ? 20 : 0);
        } else {
            count = (b > 0) ? (c > 0 ? 60 : 20) : (c > 0 ? 20 : 0);
        }
        Object[] junk = new Object[count > 0 ? count : 1];
        for (int i = 0; i < count; i++) {
            junk[i] = new Object();
        }
        return count;
    }

    public static void main(String[] args) {
        classify(1, 1, 1);
    }
}