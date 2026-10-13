// Same algorithm as SortedListInsert.java (sv-benchmarks java/algorithms/
// SortedListInsert-FunSat01, BSD-3-clause). List.insert() copied verbatim
// (still recursive). Only the driver differs: 5 inserted values instead
// of 3.
public class SortedListInsert5 {

    private static class ListNode {
        public int x;
        public ListNode next;

        private static final int SENTINEL = Integer.MAX_VALUE;

        private ListNode(int x, ListNode next) {
            this.x = x;
            this.next = next;
        }

        public ListNode() {
            this(SENTINEL, null);
        }

        public void insert(int data) {
            if (data > this.x) {
                next.insert(data);
            } else {
                next = new ListNode(x, next);
                x = data;
            }
        }
    }

    public static void classify(int a, int b, int c, int d, int e) {
        ListNode list = new ListNode();
        list.insert(a);
        list.insert(b);
        list.insert(c);
        list.insert(d);
        list.insert(e);
    }

    public static void main(String[] args) {
        classify(3, 1, 4, 1, 5);
    }
}