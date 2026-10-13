// Extracted from jpf-symbc's own example suite, src/examples/strings/PassCheck.java. Origin:
// https://github.com/SymbolicPathFinder/jpf-symbc -- Apache License 2.0.
// MODIFICATION: driver adapted to symbolic int parameters.
public class PassCheck {

    private static final String PASSWORD = "Pa$$w0rd";

    static boolean passCheckInsecure(int c0, int c1, int c2, int c3, int c4, int c5, int c6, int c7) {
        int[] p = {c0, c1, c2, c3, c4, c5, c6, c7};
        for (int i = 0; i < p.length; i++) {
            if (p[i] != PASSWORD.charAt(i)) {
                return false;
            }
        }
        return true;
    }

    static boolean passCheckSecure(int c0, int c1, int c2, int c3, int c4, int c5, int c6, int c7) {
        int[] p = {c0, c1, c2, c3, c4, c5, c6, c7};
        boolean matched = true;
        for (int i = 0; i < p.length; i++) {
            matched = matched && p[i] != PASSWORD.charAt(i);
        }
        return matched;
    }

    public static void classify(int c0, int c1, int c2, int c3, int c4, int c5, int c6, int c7) {
        passCheckInsecure(c0, c1, c2, c3, c4, c5, c6, c7);
        passCheckSecure(c0, c1, c2, c3, c4, c5, c6, c7);
    }

    public static void main(String[] args) {
        classify('P', 'a', '$', '$', 'w', '0', 'r', 'd');
    }
}
