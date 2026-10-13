// Derived from thealgorithms-java: com/thealgorithms/dynamicprogramming/MaximumSumOfNonAdjacentElements.java, method getMaxSumApproach1(int[] arr).
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
public class TaMaximumSumOfNonAdjacentElements {
    public static int getMaxSumApproach1(int[] arr) {
            if (arr.length == 0) {
                return 0; 
            }
    
            int n = arr.length;
            int[] dp = new int[n];
    
            
            dp[0] = arr[0];
    
            for (int ind = 1; ind < n; ind++) {
    
                
                
                int notTake = dp[ind - 1];
    
                
                
                int take = arr[ind];
                if (ind > 1) {
                    take += dp[ind - 2];
                }
    
                
                dp[ind] = Math.max(take, notTake);
            }
    
            return dp[n - 1];
        }
    public static void classify(int arr0, int arr1, int arr2, int arr3) {
        int[] arrArr = {arr0, arr1, arr2, arr3};
        try {
            getMaxSumApproach1(arrArr);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0); }
}
