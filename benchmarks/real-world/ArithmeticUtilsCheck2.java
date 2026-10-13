// Same methods as ArithmeticUtilsCheck.java (Apache Commons Math 3.6.1,
// Apache-2.0, addAndCheck/mulAndCheck), with more chained operations (4 values, 3 operations).
public class ArithmeticUtilsCheck2 {

    public static int addAndCheck(int x, int y) throws ArithmeticException {
        long s = (long) x + (long) y;
        if (s < Integer.MIN_VALUE || s > Integer.MAX_VALUE) {
            throw new ArithmeticException("overflow: addition");
        }
        return (int) s;
    }

    public static int mulAndCheck(int x, int y) throws ArithmeticException {
        long m = ((long) x) * ((long) y);
        if (m < Integer.MIN_VALUE || m > Integer.MAX_VALUE) {
            throw new ArithmeticException("overflow: multiplication");
        }
        return (int) m;
    }

    public static void classify(int a, int b, int c, int d) {
        int s1 = addAndCheck(a, b);
        int s2 = mulAndCheck(s1, c);
        addAndCheck(s2, d);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4);
    }
}
