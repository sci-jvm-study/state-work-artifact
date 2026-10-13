// Extracted from SV-COMP's sv-benchmarks corpus, java/algorithms/BinaryTreeSearch-FunSat01/Main.java
// Original authors: Sudeep Juvekar <sjuvekar@cs.berkeley.edu>, Jacob Burnim <jburnim@cs.berkeley.edu>
// Copyright (c) 2011, Regents of the University of California. All rights reserved.
// BSD 3-Clause License (same terms as InsertionSort.java in this folder).
// Source: https://gitlab.com/sosy-lab/benchmarking/sv-benchmarks/-/blob/main/java/algorithms/BinaryTreeSearch-FunSat01/Main.java
//
// `insert(int)` is copied verbatim: insertion into a linked binary search tree, with heap allocation (`new Node`) and a
// pointer-chasing `while(true)` loop whose length depends on the shape of the tree.
//
// MODIFICATION: only the driver. Three symbolic values are inserted in a fixed sequence into one tree, instead of the
// symbolic-length randomized sequence of SV-COMP.
public class BinaryTreeInsert {

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

    public static void classify(int a, int b, int c) {
        BinaryTreeInsert tree = new BinaryTreeInsert();
        tree.insert(a);
        tree.insert(b);
        tree.insert(c);
    }

    public static void main(String[] args) {
        classify(2, 1, 3);
    }
}
