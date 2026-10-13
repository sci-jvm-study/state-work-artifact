// Extracted from sv-benchmarks java/jayhorn-recursive/Ackermann01/Main.java.
// Origin: https://github.com/jayhorn/cav_experiments (MIT License).
// ack() copied verbatim: the classic Ackermann function with doubly nested recursion (ack(m-1, ack(m, n-1))).
// The symbolic range is much narrower than the reference range of SV-COMP (m: 0..3, n: 0..23).
public class Ackermann {

    public static int ack(int m, int n) {
        if (m == 0) {
            return n + 1;
        }
        if (n == 0) {
            return ack(m - 1, 1);
        }
        return ack(m - 1, ack(m, n - 1));
    }

    public static void classify(int m, int n) {
        ack(m, n);
    }

    public static void main(String[] args) {
        classify(2, 2);
    }
}
