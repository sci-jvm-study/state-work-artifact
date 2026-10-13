public class UnequalWork {

    public static int classify(int a, int b) {

    if (a > 0) {

        if (b > 0) {
            for (int i = 0; i < 100; i++) {
                int x = i * i;
            }
            return 1;
        } else {
            return 2;
        }

    } else {

        if (b > 0) {
            for (int i = 0; i < 5; i++) {
                int x = i * i;
            }
            return 3;
        } else {
            return 4;
        }
    }
}

    public static void main(String[] args) {
        classify(1, 1);
    }
}