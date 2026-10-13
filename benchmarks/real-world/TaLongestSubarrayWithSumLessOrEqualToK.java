// Derived from thealgorithms-java: com/thealgorithms/slidingwindow/LongestSubarrayWithSumLessOrEqualToK.java, method longestSubarrayWithSumLEK(int[] arr, int k).
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
public class TaLongestSubarrayWithSumLessOrEqualToK {
    public static int longestSubarrayWithSumLEK(int[] arr, int k) {
            int maxLength = 0; 
            int currentSum = 0; 
            int left = 0; 
    
            for (int right = 0; right < arr.length; right++) {
                currentSum += arr[right]; 
    
                
                while (currentSum > k && left <= right) {
                    currentSum -= arr[left]; 
                    left++; 
                }
    
                
                maxLength = Math.max(maxLength, right - left + 1);
            }
    
            return maxLength; 
        }
    public static void classify(int arr0, int arr1, int arr2, int arr3, int k) {
        int[] arrArr = {arr0, arr1, arr2, arr3};
        try {
            longestSubarrayWithSumLEK(arrArr, k);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0); }
}
