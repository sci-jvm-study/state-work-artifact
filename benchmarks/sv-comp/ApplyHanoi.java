// Extracted from sv-benchmarks java/jayhorn-recursive/SatHanoi01/Main.java.
// Origin: https://github.com/jayhorn/cav_experiments (MIT License).
// applyHanoi() copied verbatim: double recursion (the method calls itself twice) with three int parameters threaded through
// the recursive calls (from, to, via) and a static-field side effect (counter).
public class ApplyHanoi {

    static int counter;

    static void applyHanoi(int n, int from, int to, int via) {
        if (n == 0) {
            return;
        }
        counter++;
        applyHanoi(n - 1, from, via, to);
        applyHanoi(n - 1, via, to, from);
    }

    public static void classify(int n) {
        counter = 0;
        applyHanoi(n, 1, 3, 2);
    }

    public static void main(String[] args) {
        classify(3);
    }
}
