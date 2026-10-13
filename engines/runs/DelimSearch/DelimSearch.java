// Extracted from jpf-symbc's own example suite,
// src/examples/strings/DelimSearch.java (search method). Origin:
// https://github.com/SymbolicPathFinder/jpf-symbc -- Apache License 2.0
// (repo-wide license; file has no distinct per-file header, an original small example within the Apache-2.0 repo, not
// third-party code). Copied verbatim in spirit: a double-nested loop with continue-based early match, a tokenizer routine that
// finds the first occurrence in a text of any character from a delimiter set.
// MODIFICATION: the original takes two String parameters (text, delims) compared via charAt(). Here `text` is concrete (symbolic
// Strings are not used) and 3 delimiter character codes are symbolic ints, matched against the char codes of the fixed text.
public class DelimSearch {

    static int search(String text, int d0, int d1, int d2) {
        int[] delims = {d0, d1, d2};
        for (int i = 0; i < text.length(); ++i) {
            for (int j = 0; j < delims.length; ++j) {
                if (text.charAt(i) != delims[j])
                    continue;
                return i;
            }
        }
        return text.length();
    }

    public static void classify(int d0, int d1, int d2) {
        search("hello, world", d0, d1, d2);
    }

    public static void main(String[] args) {
        classify(',', ' ', '!');
    }
}