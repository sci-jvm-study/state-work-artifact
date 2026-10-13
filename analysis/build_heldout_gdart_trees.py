"""Held-out-layout version of build_gdart_trees.py: builds state trees for the 9 held-out programs'
engines/gdart_runs/<Program>/out.txt + work.csv, reusing build_gdart_trees.py's own parse/
to_coastal_format/nparams_of so the tree definition and run-validity checks are identical.

Usage: python build_heldout_gdart_trees.py"""
import os
import sys

import pandas as pd

ANALYSIS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # the root of this package
ENGINES_ROOT = os.path.join(ROOT, "engines")  # needs engines/gdart_runs/ (raw GDart logs, not shipped)
sys.path.insert(0, ENGINES_ROOT)
sys.path.insert(0, ANALYSIS)
import build_trees as bt  
import build_gdart_trees as bg  

JPF_DATA_DIR = os.path.join(ROOT, "heldout", "data")
OUT_DIR = os.path.join(ROOT, "heldout", "data_gdart")

PROGRAMS = [
    "HoAllKadaneKadaneSum",
    "HoAllSelectionSortSelection",
    "HoAllShellSortShell",
    "HoJaiLowerBoundLowerBound",
    "HoNumIndexIntervalsCompressDuplicates",
    "HoNumPartitionCountIndices",
    "HoNumSortingSort",
    "HoNumSortingSortIndicesInsertionSort",
    "HoRngAliasMethodDiscreteSamplerFillRemainingIndices",
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = []
    for prog in PROGRAMS:
        parsed, err = bg.parse(prog)
        jpf_csv = os.path.join(JPF_DATA_DIR, prog + ".csv")
        jpf_rows = sum(1 for _ in open(jpf_csv)) - 1 if os.path.exists(jpf_csv) else -1
        if err:
            summary.append((prog, 0, 0, 0, jpf_rows, err))
            continue
        runs, work, complete = parsed
        lines, status = bg.to_coastal_format(prog, runs, work, complete)
        if status != "clean" or not lines:
            summary.append((prog, len(runs), 0, 0, jpf_rows, status if status != "clean" else "no-valid-runs"))
            continue
        tmp = os.path.join(ENGINES_ROOT, "gdart_runs", prog, "coastal_runs.csv")
        with open(tmp, "w", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        raw, nruns = bt.build(tmp)
        df = bt.compress(raw)
        df.to_csv(os.path.join(OUT_DIR, prog + ".csv"), index=False)
        summary.append((prog, nruns, len(df), int((~df.isEndStateAtEntry).sum()), jpf_rows, "clean"))

    print(f"{'program':<55}{'runs':>6}{'nodes':>7}{'nonleaf':>8}{'JPF_states':>11}  status")
    for s in summary:
        print(f"{s[0]:<55}{s[1]:>6}{s[2]:>7}{s[3]:>8}{s[4]:>11}  {s[5]}")
    pd.DataFrame(summary, columns=["program", "runs", "nodes", "nonleaf", "jpf_states", "status"]).to_csv(
        os.path.join(ROOT, "Artifacts", "heldout", "run_status_gdart.csv"), index=False)


if __name__ == "__main__":
    main()
