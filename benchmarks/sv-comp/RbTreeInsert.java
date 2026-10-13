// Extracted from jpf-symbc's own example suite, src/examples/rbt/TreeMap.java
// ("From William Deng"). Origin:
// https://github.com/SymbolicPathFinder/jpf-symbc -- Apache License 2.0
// (NASA copyright header, confirmed by fetching the raw file directly).
// put()/genTreeS2_1()/fixAfterInsertion()/rotateLeft()/rotateRight() and the color-accessor helpers copied verbatim. Only the
// seed-tree-then-insert path is kept: containsKey/remove/firstKey/successor/deleteEntry/fixAfterDeletion/equals/hashCode/toString
// are dropped (hashCode() uses a bitwise `^`, which neither solver backend supports symbolically).
// MODIFICATION: the original's `Verify.ignoreIf(...)` ordering guards in genTreeS2_1 (a JPF-specific path-pruning API) are
// dropped, so some seeded trees violate the strict BST ordering. put() allocates a fresh Entry object per symbolic branch.
public class RbTreeInsert {

    static final boolean RED = false;
    static final boolean BLACK = true;

    static class Entry {
        int key;
        Object value;
        Entry left = null;
        Entry right = null;
        Entry parent;
        boolean color = BLACK;

        Entry() {
            parent = null;
            value = null;
            color = BLACK;
            left = null;
            right = null;
            key = -1;
        }

        Entry(int key, Object value, Entry parent) {
            this.key = key;
            this.value = value;
            this.parent = parent;
        }
    }

    Entry root = null;
    int size = 0;
    int modCount = 0;

    private void incrementSize() {
        modCount++;
        size++;
    }

    private int compare(int k1, int k2) {
        if (k1 < k2) {
            return -1;
        } else if (k1 == k2) {
            return 0;
        } else {
            return 1;
        }
    }

    void genTreeS2_1(int key1, int key2) {
        Entry r = new Entry();
        this.root = r;
        r.key = key1;
        Entry child = new Entry();
        child.key = key2;
        r.left = child;
        child.parent = r;
        child.color = RED;
    }

    Object put(int key, Object value) {
        Entry t = root;

        if (t == null) {
            incrementSize();
            root = new Entry();
            root.key = key;
            root.value = value;
            return null;
        }

        while (true) {
            int cmp = compare(key, t.key);
            if (cmp == 0) {
                Object old = t.value;
                t.value = value;
                return old;
            } else if (cmp < 0) {
                if (t.left != null) {
                    t = t.left;
                } else {
                    incrementSize();
                    t.left = new Entry(key, value, t);
                    fixAfterInsertion(t.left);
                    return null;
                }
            } else {
                if (t.right != null) {
                    t = t.right;
                } else {
                    incrementSize();
                    t.right = new Entry(key, value, t);
                    fixAfterInsertion(t.right);
                    return null;
                }
            }
        }
    }

    private static boolean colorOf(Entry p) {
        return (p == null ? BLACK : p.color);
    }

    private static Entry parentOf(Entry p) {
        return (p == null ? null : p.parent);
    }

    private static void setColor(Entry p, boolean c) {
        if (p != null)
            p.color = c;
    }

    private static Entry leftOf(Entry p) {
        return (p == null) ? null : p.left;
    }

    private static Entry rightOf(Entry p) {
        return (p == null) ? null : p.right;
    }

    private void rotateLeft(Entry p) {
        Entry r = p.right;
        p.right = r.left;
        if (r.left != null)
            r.left.parent = p;
        r.parent = p.parent;
        if (p.parent == null)
            root = r;
        else if (p.parent.left == p)
            p.parent.left = r;
        else
            p.parent.right = r;
        r.left = p;
        p.parent = r;
    }

    private void rotateRight(Entry p) {
        Entry l = p.left;
        p.left = l.right;
        if (l.right != null)
            l.right.parent = p;
        l.parent = p.parent;
        if (p.parent == null)
            root = l;
        else if (p.parent.right == p)
            p.parent.right = l;
        else
            p.parent.left = l;
        l.right = p;
        p.parent = l;
    }

    private void fixAfterInsertion(Entry x) {
        x.color = RED;

        while (x != null && x != root && x.parent.color == RED) {
            if (parentOf(x) == leftOf(parentOf(parentOf(x)))) {
                Entry y = rightOf(parentOf(parentOf(x)));
                if (colorOf(y) == RED) {
                    setColor(parentOf(x), BLACK);
                    setColor(y, BLACK);
                    setColor(parentOf(parentOf(x)), RED);
                    x = parentOf(parentOf(x));
                } else {
                    if (x == rightOf(parentOf(x))) {
                        x = parentOf(x);
                        rotateLeft(x);
                    }
                    setColor(parentOf(x), BLACK);
                    setColor(parentOf(parentOf(x)), RED);
                    if (parentOf(parentOf(x)) != null)
                        rotateRight(parentOf(parentOf(x)));
                }
            } else {
                Entry y = leftOf(parentOf(parentOf(x)));
                if (colorOf(y) == RED) {
                    setColor(parentOf(x), BLACK);
                    setColor(y, BLACK);
                    setColor(parentOf(parentOf(x)), RED);
                    x = parentOf(parentOf(x));
                } else {
                    if (x == leftOf(parentOf(x))) {
                        x = parentOf(x);
                        rotateRight(x);
                    }
                    setColor(parentOf(x), BLACK);
                    setColor(parentOf(parentOf(x)), RED);
                    if (parentOf(parentOf(x)) != null)
                        rotateLeft(parentOf(parentOf(x)));
                }
            }
        }
        root.color = BLACK;
    }

    public static void classify(int key1, int key2, int key3) {
        RbTreeInsert tm = new RbTreeInsert();
        tm.genTreeS2_1(key1, key2);
        tm.put(key3, null);
    }

    public static void main(String[] args) {
        classify(5, 2, 8);
    }
}
