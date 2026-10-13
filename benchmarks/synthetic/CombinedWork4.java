public class CombinedWork4 {

    // Extends CombinedWork3.java from 3 nested ifs (8 leaves) to 4 (16
    // leaves), same idea: each leaf has a different mix of loop-iteration
    // and allocation cost.
    public static int classify(int a, int b, int c, int d) {
        int loopCount = 0;
        int allocCount = 0;

        if (a > 0) { loopCount += 60; }
        if (b > 0) { loopCount += 20; }
        if (c > 0) { allocCount += 60; }
        if (d > 0) { allocCount += 20; }

        int x = 0;
        for (int i = 0; i < loopCount; i++) { x += i; }

        Object[] junk = new Object[allocCount > 0 ? allocCount : 1];
        for (int i = 0; i < allocCount; i++) { junk[i] = new Object(); }

        return x + allocCount;
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1);
    }
}
