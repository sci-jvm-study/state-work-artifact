// Extracted from SV-COMP's sv-benchmarks corpus, java/algorithms/SortedListInsert-FunSat01/Main.java
// Original author: Jacob Burnim <jburnim@cs.berkeley.edu>
// Copyright (c) 2011, Regents of the University of California. All rights reserved.
// BSD 3-Clause License (same terms as InsertionSort.java / BinaryTreeInsert.java in this folder).
// Source: https://gitlab.com/sosy-lab/benchmarking/sv-benchmarks/-/blob/main/java/algorithms/SortedListInsert-FunSat01/Main.java
//
// `List.insert(int)` is copied verbatim. Its repeated work comes from recursion (`next.insert(data)`) and not from a loop.
//
// MODIFICATION: only the driver. Three symbolic values are inserted in a fixed sequence into one list, instead of the
// symbolic-length randomized sequence of SV-COMP.
public class SortedListInsert {

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

    public static void classify(int a, int b, int c) {
        ListNode list = new ListNode();
        list.insert(a);
        list.insert(b);
        list.insert(c);
    }

    public static void main(String[] args) {
        classify(2, 1, 3);
    }
}