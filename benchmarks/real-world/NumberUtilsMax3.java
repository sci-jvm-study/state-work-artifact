// Extracted from Apache Commons Lang3 3.14.0
// org.apache.commons.lang3.math.NumberUtils.max(int, int, int)
// Source: https://github.com/apache/commons-lang/blob/rel/commons-lang-3.14.0/src/main/java/org/apache/commons/lang3/math/NumberUtils.java
// Apache License 2.0. No modifications -- copied verbatim (this overload has no
// dependencies outside java.lang).
public class NumberUtilsMax3 {

    public static int max(int a, final int b, final int c) {
        if (b > a) {
            a = b;
        }
        if (c > a) {
            a = c;
        }
        return a;
    }

    public static void main(String[] args) {
        max(1, 2, 3);
    }
}
