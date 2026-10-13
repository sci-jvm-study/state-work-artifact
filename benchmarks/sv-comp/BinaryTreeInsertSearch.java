// Same algorithm as BinaryTreeInsert.java (sv-benchmarks java/algorithms/
// BinaryTreeSearch-FunSat01, BSD-3-clause) -- both insert() AND search()
// both insert() and search() are copied verbatim (the full purpose of the original benchmark: insert several values, then search
// for one).
public class BinaryTreeInsertSearch {

    private static class Node {
        int value;
        Node left;
        Node right;

        Node(int v, Node l, Node r) {
            value = v;
            left = l;
            right = r;
        }
    }

    private Node root = null;

    public void insert(int v) {
        if (root == null) {
            root = new Node(v, null, null);
            return;
        }
        Node curr = root;
        while (true) {
            if (curr.value < v) {
                if (curr.right != null) {
                    curr = curr.right;
                } else {
                    curr.right = new Node(v, null, null);
                    break;
                }
            } else if (curr.value > v) {
                if (curr.left != null) {
                    curr = curr.left;
                } else {
                    curr.left = new Node(v, null, null);
                    break;
                }
            } else {
                break;
            }
        }
    }

    public boolean search(int v) {
        Node curr = root;
        while (curr != null) {
            if (curr.value == v) {
                return true;
            } else if (curr.value < v) {
                curr = curr.right;
            } else {
                curr = curr.left;
            }
        }
        return false;
    }

    public static boolean classify(int a, int b, int c, int target) {
        BinaryTreeInsertSearch tree = new BinaryTreeInsertSearch();
        tree.insert(a);
        tree.insert(b);
        tree.insert(c);
        return tree.search(target);
    }

    public static void main(String[] args) {
        classify(3, 1, 4, 1);
    }
}
