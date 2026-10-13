// Same algorithm as BinaryTreeInsert.java (sv-benchmarks java/algorithms/
// BinaryTreeSearch-FunSat01, BSD-3-clause). insert() copied verbatim. Only
// the driver differs: 5 inserted values instead of 3.
public class BinaryTreeInsert5 {

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

    public static void classify(int a, int b, int c, int d, int e) {
        BinaryTreeInsert5 tree = new BinaryTreeInsert5();
        tree.insert(a);
        tree.insert(b);
        tree.insert(c);
        tree.insert(d);
        tree.insert(e);
    }

    public static void main(String[] args) {
        classify(3, 1, 4, 1, 5);
    }
}
