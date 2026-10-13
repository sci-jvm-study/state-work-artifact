// Derived from java: algorithms/dynamic-programming/Kadane.java, method kadaneSum(int[] arr).
// Origin: https://github.com/AllAlgorithms/java, commit 1af0c0bab97d9a03a7665894c067fac66c96fcc5. MIT License, Copyright (c) 2018 All Algorithms and its contributors. Method bodies copied verbatim (comments removed).
// MODIFICATION (this study): the method, the static helpers it calls and the int constants it uses are copied verbatim (comments
// removed) into this class; classify() is the symbolic entry point (int arrays are built from 4 symbolic ints and the call
// is wrapped in try/catch RuntimeException so that a thrown exception ends the path). Program logic unchanged.
public class HoAllKadaneKadaneSum {
    public static int kadaneSum(int[] arr) {
    		int osum = arr[0];
    		int csum = arr[0];
    		for (int i = 1; i < arr.length; i++) {
    			if (csum + arr[i] < arr[i]) {
    				csum = arr[i];
    			} else {
    				csum += arr[i];
    			}
    			if (csum > osum) {
    				osum = csum;
    			}
    		}
    
    		return osum;
    	}
    public static void classify(int arr0, int arr1, int arr2, int arr3) {
        int[] arrArr = {arr0, arr1, arr2, arr3};
        try {
            kadaneSum(arrArr);
        } catch (RuntimeException e) {
        }
    }
    public static void main(String[] args) { classify(0, 0, 0, 0); }
}
