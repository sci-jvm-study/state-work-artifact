// Extracted from Apache Commons Lang3, org.apache.commons.lang3.StringUtils
// (indexOfDifference(CharSequence,CharSequence)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-lang/blob/master/src/main/java/org/apache/commons/lang3/StringUtils.java
// indexOfDifference() copied verbatim (INDEX_NOT_FOUND inlined as -1, the
// method's own constant value, per the source).
//
// A string-comparison algorithm: a search for the point of divergence, with a surrogate-pair edge case.
//
// SYMBOLIC INPUT: the compared string is concrete (a fixed base string). Two symbolic ints mutate one character of a copy of it
// before the comparison: `pos` (bounds-checked) selects the character and `newChar` supplies the replacement code point. The
// character-by-character comparison loop is driven by symbolic ints, without symbolic strings.
public class StringUtilsIndexOfDifference {

    private static final int INDEX_NOT_FOUND = -1;

    public static int indexOfDifference(final CharSequence cs1, final CharSequence cs2) {
        if (cs1 == cs2) {
            return INDEX_NOT_FOUND;
        }
        if (cs1 == null || cs2 == null) {
            return 0;
        }
        int i;
        for (i = 0; i < cs1.length() && i < cs2.length(); ++i) {
            if (cs1.charAt(i) != cs2.charAt(i)) {
                break;
            }
        }
        if (i > 0 && i < cs1.length() && i < cs2.length() && Character.isHighSurrogate(cs1.charAt(i - 1))
                && (Character.isLowSurrogate(cs1.charAt(i)) || Character.isLowSurrogate(cs2.charAt(i)))) {
            i--;
        }
        if (i < cs2.length() || i < cs1.length()) {
            return i;
        }
        return INDEX_NOT_FOUND;
    }

    public static void classify(int pos, int newChar) {
        // Driver-only logic (not part of the extracted library method): both symbolic ints share one jpf-symbc range, so `pos` is mapped
        // into a valid string index via floorMod.
        String base = "hello";
        int idx = Math.floorMod(pos, base.length());
        char[] chars = base.toCharArray();
        chars[idx] = (char) newChar;
        String mutated = new String(chars);
        indexOfDifference(mutated, base);
    }

    public static void main(String[] args) {
        classify(1, 'a');
    }
}
