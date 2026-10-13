// Extracted from sv-benchmarks java/jayhorn-recursive/SatHanoi01/Main.java -- the function hanoi() of that file (applyHanoi() is
// ApplyHanoi.java). Origin:
// https://github.com/jayhorn/cav_experiments (MIT License).
// hanoi() copied verbatim: single linear self-recursion computing the optimal step count (2*hanoi(n-1)+1).
public class HanoiSteps {

    static int hanoi(int n) {
        if (n == 1) {
            return 1;
        }
        return 2 * (hanoi(n - 1)) + 1;
    }

    public static void classify(int n) {
        hanoi(n);
    }

    public static void main(String[] args) {
        classify(4);
    }
}