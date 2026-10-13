// Extracted from Apache Commons Lang3, org.apache.commons.lang3.mutable.MutableInt
// (constructor, add(int), subtract(int), compareTo(MutableInt)) -- Apache License 2.0.
// Source: https://github.com/apache/commons-lang/blob/master/src/main/java/org/apache/commons/lang3/mutable/MutableInt.java
//
// A class with encapsulated state (the `value` field) that is mutated across several method calls. The original class extends
// java.lang.Number and implements Comparable<MutableInt> and Mutable<Number>; it is trimmed to the fields and methods that the
// driver calls (add, subtract, compareTo).
public class MutableIntOps {

    private int value;

    public MutableIntOps(final int value) {
        this.value = value;
    }

    public void add(final int operand) {
        this.value += operand;
    }

    public void subtract(final int operand) {
        this.value -= operand;
    }

    public int compareTo(final MutableIntOps other) {
        return Integer.compare(this.value, other.value);
    }

    public static void classify(int initial, int delta1, int delta2, int otherInitial) {
        MutableIntOps a = new MutableIntOps(initial);
        a.add(delta1);
        a.subtract(delta2);
        MutableIntOps b = new MutableIntOps(otherInitial);
        a.compareTo(b);
    }

    public static void main(String[] args) {
        classify(0, 5, 2, 3);
    }
}
