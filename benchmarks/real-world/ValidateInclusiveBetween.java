// Extracted from Apache Commons Lang3, org.apache.commons.lang3.Validate
// (inclusiveBetween(long,long,long)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-lang/blob/master/src/main/java/org/apache/commons/lang3/Validate.java
//
// A precondition check: a single range check with an exception on failure, no loop and no recursion.
//
// MODIFICATION: message uses String.valueOf concatenation instead of
// String.format (avoids pulling in the varargs message-formatting
// machinery for a single call site); functionally identical exception
// condition and control flow to the original.
public class ValidateInclusiveBetween {

    public static void inclusiveBetween(final long start, final long end, final long value) {
        if (value < start || value > end) {
            throw new IllegalArgumentException(
                "The value " + value + " is not in the specified inclusive range of " + start + " to " + end);
        }
    }

    public static void classify(int start, int end, int value) {
        inclusiveBetween(start, end, value);
    }

    public static void main(String[] args) {
        classify(0, 10, 5);
    }
}
