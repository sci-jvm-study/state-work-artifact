// Extracted from jpf-symbc's own example suite,
// src/examples/sequences/LinkedList.java. Origin:
// https://github.com/SymbolicPathFinder/jpf-symbc -- Apache License 2.0
// (per-file header confirmed). insertFront()/find() copied verbatim: a generic singly-linked list. The traversal terminates on a
// value match (current.data != x), not on length or index.
public class LinkedListFind {

    static class LinkedListNode {
        int data;
        LinkedListNode next;

        LinkedListNode(int x) {
            data = x;
            next = null;
        }
    }

    private LinkedListNode head;

    boolean insertFront(int x) {
        LinkedListNode newNode = new LinkedListNode(x);
        newNode.next = head;
        head = newNode;
        return true;
    }

    boolean find(int x) {
        LinkedListNode current = head;
        while (current != null && current.data != x)
            current = current.next;
        return current != null;
    }

    public static void classify(int a, int b, int c, int x) {
        LinkedListFind list = new LinkedListFind();
        list.insertFront(a);
        list.insertFront(b);
        list.insertFront(c);
        list.find(x);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 2);
    }
}
