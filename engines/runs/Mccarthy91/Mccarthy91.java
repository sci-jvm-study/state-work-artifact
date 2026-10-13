// Extracted from sv-benchmarks java/jayhorn-recursive/SatMccarthy91/Main.java.
// Origin: https://github.com/jayhorn/cav_experiments (MIT License).
// f(int) copied verbatim: the McCarthy 91 function, with a self-call nested inside another self-call (f(f(n+11))).
public class Mccarthy91 {

    private static int f(int n) {
        if (n > 100) return n - 10;
        else return f(f(n + 11));
    }

    public static void classify(int n) {
        f(n);
    }

    public static void main(String[] args) {
        classify(95);
    }
}