// Extracted from sv-benchmarks java/jayhorn-recursive/SatFibonacci01/Main.java.
// Origin: https://github.com/jayhorn/cav_experiments (MIT License).
// fibonacci(int) copied verbatim: double recursion (the method calls itself twice per call).
// MODIFICATION: the driver is replaced (the Verifier.nondetInt() harness of SV-COMP became a plain symbolic-parameter classify()).
public class Fibonacci {

    static int fibonacci(int n) {
        if (n < 1) {
            return 0;
        } else if (n == 1) {
            return 1;
        } else {
            return fibonacci(n - 1) + fibonacci(n - 2);
        }
    }

    public static void classify(int n) {
        fibonacci(n);
    }

    public static void main(String[] args) {
        classify(4);
    }
}