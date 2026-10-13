// Extracted from jpf-symbc's own example suite,
// src/examples/strings/StringSearch.java (search_3 method). Origin:
// https://github.com/SymbolicPathFinder/jpf-symbc -- Apache License 2.0
// (repo-wide license; file itself has no distinct per-file header, but is
// an original small example within the Apache-2.0 repo, not third-party
// code). Copied verbatim: a generic string-manipulation utility. The string `s` is concrete (symbolic strings are not used); only
// the int character code `c` is symbolic, and the branches compare it with the fixed string content.
public class StringSearchReplace {

    static String search_3(int c, String s) {
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == c) {
                s = s.substring(0, i).concat(s.substring(i + 1));
            }
        }
        return s;
    }

    public static void classify(int c) {
        search_3(c, "banana");
    }

    public static void main(String[] args) {
        classify('a');
    }
}