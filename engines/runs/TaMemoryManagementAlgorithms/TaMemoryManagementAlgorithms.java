// Derived from thealgorithms-java: com/thealgorithms/others/MemoryManagementAlgorithms.java, method findBestFit(int[] blockSizes, int processSize).
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
public class TaMemoryManagementAlgorithms {
    static final int NO_ALLOCATION = -255;
    private static int findBestFit(int[] blockSizes, int processSize) {
            
            
            int minDiff = findMaxElement(blockSizes);
            int index = NO_ALLOCATION; 
                                       
            
            for (int i = 0; i < blockSizes.length; i++) { 
                if (blockSizes[i] - processSize < minDiff && blockSizes[i] - processSize >= 0) {
                    minDiff = blockSizes[i] - processSize;
                    index = i;
                }
            }
            return index;
        }
    private static int findMaxElement(int[] array) {
            int max = -1;
            for (int value : array) {
                if (value > max) {
                    max = value;
                }
            }
            return max;
        }
    public static void classify(int blockSizes0, int blockSizes1, int blockSizes2, int blockSizes3, int processSize) {
        int[] blockSizesArr = {blockSizes0, blockSizes1, blockSizes2, blockSizes3};
        try {
            findBestFit(blockSizesArr, processSize);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0, 0); }
}