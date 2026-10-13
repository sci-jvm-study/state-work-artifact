// Extracted from sv-benchmarks java/jayhorn-recursive/SatGcd/Main.java.
// Origin: https://github.com/jayhorn/cav_experiments (MIT License).
// gcd() copied verbatim: Euclidean GCD by repeated subtraction, using comparisons only (no bitwise operators, which the solver
// backends do not support symbolically).
public class EuclideanGcd {

    static int gcd(int y1, int y2) {
        if (y1 <= 0 || y2 <= 0) {
            return 0;
        }
        if (y1 == y2) {
            return y1;
        }
        if (y1 > y2) {
            return gcd(y1 - y2, y2);
        }
        return gcd(y1, y2 - y1);
    }

    public static void classify(int a, int b) {
        gcd(a, b);
    }

    public static void main(String[] args) {
        classify(12, 8);
    }
}
