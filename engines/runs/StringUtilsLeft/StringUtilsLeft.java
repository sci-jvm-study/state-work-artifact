// Extracted from Apache Commons Lang3, org.apache.commons.lang3.StringUtils
// (left(String,int)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-lang/blob/master/src/main/java/org/apache/commons/lang3/StringUtils.java
//
// A bounds-clamping substring extraction with three sequential early-return checks and no loop.
//
// SYMBOLIC INPUT: the source string is concrete (a fixed test string). The `len` parameter is symbolic and drives all three branches
// (negative length, length exceeding the string, normal truncation).
public class StringUtilsLeft {

    public static String left(final String str, final int len) {
        if (str == null) {
            return null;
        }
        if (len < 0) {
            return "";
        }
        if (str.length() <= len) {
            return str;
        }
        return str.substring(0, len);
    }

    public static void classify(int len) {
        left("symbolicexecution", len);
    }

    public static void main(String[] args) {
        classify(5);
    }
}