"""Decision for every SV-COMP Java task that passed screen.py (the 'pool'), in one table (pool.csv) plus counts:

  in_corpus        the task's program is already a program group of the study (mapping CORPUS below, from the file headers)
  variant          same program with a different property/instance: code similarity >= 0.85 with an in-corpus task or another pool task
  license          MergeSortIterative: its file header does not grant a redistributable license
  run: <outcome>   adapted (adapt.py), run on JPF with the range rule of run_candidates.py, and
                     selected                       >= 5 non-leaf states and open-source software
                     bytecode unit test (excluded)  passes the floor, but tests single bytecode instructions (JBMC regression suite)
                     below floor                    fewer than 5 non-leaf states
                     not adapted                    adapt.py cannot transform it mechanically (reason in the note)
                     no result                      adapted, but JPF wrote no output (error or timeout)

Usage: python pool_table.py <sv-benchmarks/java dir> <screen.csv> <adapted dir with tries.csv> [out.csv]"""
import csv
import difflib
import os
import re
import sys

import pandas as pd

JAVA, SCREEN, ADAPTED = sys.argv[1:4]
OUT = sys.argv[4] if len(sys.argv) > 4 else "pool.csv"

CORPUS = {  # task -> program group of the study
    "jayhorn-recursive/SatAckermann01": "Ackermann", "jayhorn-recursive/SatHanoi01": "ApplyHanoi, HanoiSteps",
    "algorithms/BellmanFord-FunSat01": "BellmanFord", "algorithms/BinaryTreeSearch-FunSat01": "BinaryTreeInsert",
    "jayhorn-recursive/SatGcd": "EuclideanGcd", "jayhorn-recursive/SatEvenOdd01": "EvenOdd",
    "jpf-regression/ExSymExe15_true": "ExSymExe15", "jpf-regression/ExSymExe20_true": "ExSymExe20", "jpf-regression/ExSymExe25_true": "ExSymExe25",
    "jpf-regression/ExSymExeResearch_true": "ExSymExeResearch", "jpf-regression/ExSymExeSimple_true": "ExSymExeSimple",
    "jpf-regression/ExSymExeSuzette_true": "ExSymExeSuzette", "jayhorn-recursive/SatFibonacci01": "Fibonacci",
    "algorithms/InsertionSort-FunSat01": "InsertionSort", "jayhorn-recursive/SatMccarthy91": "Mccarthy91",
    "jayhorn-recursive/SatAddition01": "RecursiveAddition", "algorithms/SortedListInsert-FunSat01": "SortedListInsert",
    "algorithms/Tsp-FunSat01": "Tsp", "jayhorn-recursive/SatMultCommutative01": "MultCommutative", "jayhorn-recursive/SatPrimes01": "Primes",
}
NAME = {  # class name used by adapt.py
    "jayhorn-recursive/SatPrimes01": "Primes", "argv-tasks/StrictLineReader": "StrictLineReader", "jbmc-regression/aastore_aaload1": "JbmcAastoreAaload1",
    "jbmc-regression/array1": "JbmcArray1", "jbmc-regression/array2": "JbmcArray2", "jbmc-regression/arraylength1": "JbmcArraylength1",
    "jbmc-regression/arrayread1": "JbmcArrayread1", "jbmc-regression/assert1": "JbmcAssert1", "jbmc-regression/assert5": "JbmcAssert5",
    "jbmc-regression/assert6": "JbmcAssert6", "jbmc-regression/if_expr1": "JbmcIfExpr1", "jbmc-regression/if_icmp1": "JbmcIfIcmp1",
    "jbmc-regression/lookupswitch1": "JbmcLookupswitch1", "jbmc-regression/tableswitch1": "JbmcTableswitch1", "jbmc-regression/list1": "JbmcList1",
    "jdart-regression/list2": "JdartList2", "jpf-regression/ExDarko_true": "ExDarko", "jpf-regression/ExGenSymExe_true": "ExGenSymExe",
    "jpf-regression/ExLazy_true": "ExLazy", "jpf-regression/ExSymExe7_true": "ExSymExe7", "jpf-regression/ExSymExe10_true": "ExSymExe10",
    "jpf-regression/ExSymExe11_true": "ExSymExe11", "jpf-regression/ExSymExe13_true": "ExSymExe13", "jpf-regression/ExSymExe19_true": "ExSymExe19",
    "jpf-regression/ExSymExeSwitch_true": "ExSymExeSwitch", "jpf-regression/ExSymExeTestAssignments_true": "ExSymExeTestAssignments",
    "jpf-regression/ExSymExeTestClassFields_true": "ExSymExeTestClassFields", "jpf-regression/TestLazy_true": "TestLazy",
}


NOT_ADAPTED = {  # adapt.py could not transform these mechanically
    "StrictLineReader": "inputs are static field initializers, one of them the length of a byte[] (symbolic array length)",
    "JbmcArray1": "two source files", "JbmcList1": "nondet input read in a helper class", "JdartList2": "nondet input read in a helper class",
}


def code(sources):
    t = "\n".join(open(os.path.join(JAVA, s), encoding="utf-8", errors="replace").read() for s in sources)
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"//[^\n]*", "", t))


rows = [r for r in csv.DictReader(open(SCREEN, encoding="utf-8")) if r["passed_all"] == "True"]
C = {r["task"][:-4]: code(r["sources"].split(";")) for r in rows}
tries = pd.read_csv(os.path.join(ADAPTED, "tries.csv"))
best = tries[tries.outcome == "ok"].sort_values(["program", "k"]).groupby("program").tail(1).set_index("program")
out = []
for r in rows:
    t = r["task"][:-4]
    if t in CORPUS:
        out.append((t, "in_corpus", CORPUS[t], ""))
        continue
    sim = max(((difflib.SequenceMatcher(None, C[t], C[c], autojunk=False).ratio(), c) for c in CORPUS if c in C), default=(0, ""))
    if "MergeSortIterative" in t:
        out.append((t, "license", "", ""))
    elif sim[0] >= 0.85:
        out.append((t, "variant", sim[1], f"{sim[0]:.2f}"))
    else:
        n = NAME.get(t)
        if n in NOT_ADAPTED:
            out.append((t, "run: not adapted", n, NOT_ADAPTED[n]))
            continue
        if n not in best.index:
            out.append((t, "run: no result", n, "adapted, JPF wrote no output (error or timeout)"))
            continue
        b = best.loc[n]
        if b.nonleaf < 5:
            out.append((t, "run: below floor", n, f"{int(b.nonleaf)} non-leaf states (k={int(b.k)})"))
        elif t.startswith("jbmc-regression") or t.startswith("jdart-regression"):
            out.append((t, "run: bytecode unit test (excluded)", n, f"{int(b.nonleaf)} non-leaf states (k={int(b.k)})"))
        else:
            out.append((t, "run: selected", n, f"{int(b.nonleaf)} non-leaf states (k={int(b.k)})"))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["task", "decision", "detail", "note"])
    w.writerows(out)
from collections import Counter
c = Counter(o[1] for o in out)
print(len(out), "pool tasks")
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print(f"  {v:3d}  {k}")
