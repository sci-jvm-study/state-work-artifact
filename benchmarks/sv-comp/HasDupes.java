// Extracted from jpf-symbc's own example suite,
// src/examples/strings/MasterMind.java -- only the hasDupes(int) method (the rest of that file is an adapted guess-a-number game
// loop of uncertain provenance; hasDupes() itself is a self-contained digit-arithmetic utility inside the Apache-2.0-licensed
// jpf-symbc repo). Origin:
// https://github.com/SymbolicPathFinder/jpf-symbc -- Apache License 2.0.
// Copied verbatim. Pure integer arithmetic: repeated-digit detection via % and /.
public class HasDupes {

    static boolean hasDupes(int num) {
        boolean[] digs = new boolean[10];
        while (num > 0) {
            if (digs[num % 10])
                return true;
            digs[num % 10] = true;
            num /= 10;
        }
        return false;
    }

    public static void classify(int num) {
        hasDupes(num);
    }

    public static void main(String[] args) {
        classify(1234);
    }
}
