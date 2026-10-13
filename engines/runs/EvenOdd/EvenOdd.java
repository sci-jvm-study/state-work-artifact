// Extracted from sv-benchmarks java/jayhorn-recursive/SatEvenOdd01/Main.java.
// Origin: https://github.com/jayhorn/cav_experiments (MIT License).
// isOdd()/isEven() copied verbatim: mutual recursion (two functions that call each other alternately).
public class EvenOdd {

    static int isOdd(int n) {
        if (n == 0) {
            return 0;
        } else if (n == 1) {
            return 1;
        } else {
            return isEven(n - 1);
        }
    }

    static int isEven(int n) {
        if (n == 0) {
            return 1;
        } else if (n == 1) {
            return 0;
        } else {
            return isOdd(n - 1);
        }
    }

    public static void classify(int n) {
        isOdd(n);
    }

    public static void main(String[] args) {
        classify(7);
    }
}