// Same class body as LinkedListFind.java (see that file for full
// provenance/license). insertFront()/find() copied verbatim. 5 inserted
// elements instead of 3, for more traversal-length diversity in find().
public class LinkedListFind5 {

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

    public static void classify(int a, int b, int c, int d, int e, int x) {
        LinkedListFind5 list = new LinkedListFind5();
        list.insertFront(a);
        list.insertFront(b);
        list.insertFront(c);
        list.insertFront(d);
        list.insertFront(e);
        list.find(x);
    }

    public static void main(String[] args) {
        classify(1, 2, 3, 4, 5, 3);
    }
}