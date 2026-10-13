public class CombinedWork5 {

    // Extends CombinedWork4.java from 4 nested ifs (16 leaves) to 5 (32
    // leaves): 3 branches feed loopCount, 2 feed allocCount, keeping the
    // mixed loop/allocation-cost idea with one more independent branch.
    public static int classify(int a, int b, int c, int d, int e) {
        int loopCount = 0;
        int allocCount = 0;

        if (a > 0) { loopCount += 60; }
        if (b > 0) { loopCount += 20; }
        if (c > 0) { loopCount += 8; }
        if (d > 0) { allocCount += 60; }
        if (e > 0) { allocCount += 20; }

        int x = 0;
        for (int i = 0; i < loopCount; i++) { x += i; }

        Object[] junk = new Object[allocCount > 0 ? allocCount : 1];
        for (int i = 0; i < allocCount; i++) { junk[i] = new Object(); }

        return x + allocCount;
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1, 1);
    }
}