public class BranchTree6 {

    // 6 nested symbolic branches -> complete binary decision tree of depth 6
    // (63 non-leaf internal states, 64 leaves) -- same family as
    // BranchTree.java/BranchTree4.java/BranchTree5.java, one more level.
    public static int classify(int a, int b, int c, int d, int e, int f) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 1; } else { return 2; }
                        } else {
                            if (f > 0) { return 3; } else { return 4; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 5; } else { return 6; }
                        } else {
                            if (f > 0) { return 7; } else { return 8; }
                        }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 9; } else { return 10; }
                        } else {
                            if (f > 0) { return 11; } else { return 12; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 13; } else { return 14; }
                        } else {
                            if (f > 0) { return 15; } else { return 16; }
                        }
                    }
                }
            } else {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 17; } else { return 18; }
                        } else {
                            if (f > 0) { return 19; } else { return 20; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 21; } else { return 22; }
                        } else {
                            if (f > 0) { return 23; } else { return 24; }
                        }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 25; } else { return 26; }
                        } else {
                            if (f > 0) { return 27; } else { return 28; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 29; } else { return 30; }
                        } else {
                            if (f > 0) { return 31; } else { return 32; }
                        }
                    }
                }
            }
        } else {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 33; } else { return 34; }
                        } else {
                            if (f > 0) { return 35; } else { return 36; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 37; } else { return 38; }
                        } else {
                            if (f > 0) { return 39; } else { return 40; }
                        }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 41; } else { return 42; }
                        } else {
                            if (f > 0) { return 43; } else { return 44; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 45; } else { return 46; }
                        } else {
                            if (f > 0) { return 47; } else { return 48; }
                        }
                    }
                }
            } else {
                if (c > 0) {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 49; } else { return 50; }
                        } else {
                            if (f > 0) { return 51; } else { return 52; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 53; } else { return 54; }
                        } else {
                            if (f > 0) { return 55; } else { return 56; }
                        }
                    }
                } else {
                    if (d > 0) {
                        if (e > 0) {
                            if (f > 0) { return 57; } else { return 58; }
                        } else {
                            if (f > 0) { return 59; } else { return 60; }
                        }
                    } else {
                        if (e > 0) {
                            if (f > 0) { return 61; } else { return 62; }
                        } else {
                            if (f > 0) { return 63; } else { return 64; }
                        }
                    }
                }
            }
        }
    }

    public static void main(String[] args) {
        classify(1, 1, 1, 1, 1, 1);
    }
}
