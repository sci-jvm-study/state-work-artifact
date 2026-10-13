// Extracted from Apache Commons Lang3, org.apache.commons.lang3.StringUtils
// (isAlpha(CharSequence)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-lang/blob/master/src/main/java/org/apache/commons/lang3/StringUtils.java
// isEmpty(CharSequence) (a trivial helper: cs == null || cs.length() == 0)
// inlined directly, per the source.
//
// A per-character classification loop: a single forward scan with early exit on the first non-letter.
//
// SYMBOLIC INPUT: the tested string is built from a symbolic int converted to a single character, so symbolic strings are not used.
public class StringUtilsIsAlpha {

    public static boolean isAlpha(final CharSequence cs) {
        if (cs == null || cs.length() == 0) {
            return false;
        }
        final int sz = cs.length();
        for (int i = 0; i < sz;) {
            final int codePoint = Character.codePointAt(cs, i);
            if (!Character.isLetter(codePoint)) {
                return false;
            }
            i += Character.charCount(codePoint);
        }
        return true;
    }

    public static void classify(int codePoint) {
        String s = String.valueOf((char) codePoint);
        isAlpha(s);
    }

    public static void main(String[] args) {
        classify('a');
    }
}
