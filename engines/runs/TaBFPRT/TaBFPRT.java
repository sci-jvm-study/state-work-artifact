// Derived from thealgorithms-java: com/thealgorithms/others/BFPRT.java, method insertionSort(int[] arr, int begin, int end).
// Origin: https://github.com/TheAlgorithms/Java, commit dd8df80. License (MIT), reproduced as required:
// MIT License
//
// Copyright (c) 2021 The Algorithms
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class TaBFPRT {
    public static void insertionSort(int[] arr, int begin, int end) {
            if (arr == null || arr.length < 2) {
                return;
            }
            for (int i = begin + 1; i != end + 1; i++) {
                for (int j = i; j != begin; j--) {
                    if (arr[j - 1] > arr[j]) {
                        swap(arr, j - 1, j);
                    } else {
                        break;
                    }
                }
            }
        }
    public static void swap(int[] arr, int i, int j) {
            int temp = arr[i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
    public static void classify(int arr0, int arr1, int arr2, int arr3, int begin, int end) {
        int[] arrArr = {arr0, arr1, arr2, arr3};
        try {
            insertionSort(arrArr, begin, end);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0, 0); }
}