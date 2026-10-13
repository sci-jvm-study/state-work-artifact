// Extracted from SV-COMP's sv-benchmarks corpus, java/algorithms/InsertionSort-FunSat01/Main.java
// Original author: Jacob Burnim <jburnim@cs.berkeley.edu>
// Copyright (c) 2011, Regents of the University of California. All rights reserved.
// BSD 3-Clause License -- see below.
// Source: https://gitlab.com/sosy-lab/benchmarking/sv-benchmarks/-/blob/main/java/algorithms/InsertionSort-FunSat01/Main.java
//
// Redistribution and use in source and binary forms, with or without modification, are permitted
// provided that the following conditions are met:
// 1. Redistributions of source code must retain the above copyright notice, this list of
//    conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright notice, this list of
//    conditions and the following disclaimer in the documentation and/or other materials provided
//    with the distribution.
// 3. Neither the name of the University of California, Berkeley nor the names of its contributors
//    may be used to endorse or promote products derived from this software without specific prior
//    written permission.
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
// IMPLIED WARRANTIES ARE DISCLAIMED.
//
// MODIFICATION: the original SV-COMP harness uses `Verifier.nondetInt()` to make the array length itself symbolic, which
// jpf-symbc does not handle well. The `sort(int[])` method (insertion sort with nested for and while loops) is copied verbatim.
// Only the driver was adapted: a fixed-length (4) array with all four elements symbolic.
public class InsertionSort {

    public static void sort(int[] a) {
        final int N = a.length;
        for (int i = 1; i < N; i++) { // N branches
            int j = i - 1;
            int x = a[i];
            // First branch (j >= 0):  2 + 3 + ... + N = N(N+1)/2 - 1 branches
            // Second branch (a[j] > x):  1 + 2 + ... + N-1 = (N-1)N/2 branches
            while ((j >= 0) && (a[j] > x)) {
                a[j + 1] = a[j];
                j--;
            }
            a[j + 1] = x;
        }
    }

    public static void classify(int a, int b, int c, int d) {
        int[] arr = {a, b, c, d};
        sort(arr);
    }

    public static void main(String[] args) {
        classify(4, 3, 2, 1);
    }
}