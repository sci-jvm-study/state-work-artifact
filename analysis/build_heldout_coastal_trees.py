"""Build COASTAL-format state trees for the 9 held-out programs, reusing build_trees.py's
parse_run/compress/build functions. The main build_trees.py driver is hardcoded for the main
corpus's directory layout, so this is a standalone driver for the held-out layout.

Usage: python build_heldout_coastal_trees.py"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engines"))
from build_trees import build, compress

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
RUNS_DIR = os.path.join(ROOT, "engines", "runs_heldout")
JPF_DATA_DIR = os.path.join(ROOT, "Artifacts", "heldout", "data")
OUT_DIR = os.path.join(ROOT, "Artifacts", "heldout", "data_coastal")

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
        run_csv = os.path.join(RUNS_DIR, prog, "coastal_runs.csv")
        if not os.path.exists(run_csv) or os.path.getsize(run_csv) == 0:
            print(f"{prog}: missing/empty coastal_runs.csv, skipped")
            continue
        raw, nruns = build(run_csv)
        df = compress(raw)
        df.to_csv(os.path.join(OUT_DIR, prog + ".csv"), index=False)
        jpf_csv = os.path.join(JPF_DATA_DIR, prog + ".csv")
        jpf_rows = sum(1 for _ in open(jpf_csv)) - 1 if os.path.exists(jpf_csv) else -1
        summary.append((prog, nruns, len(df), int((~df.isEndStateAtEntry).sum()), jpf_rows))

    print(f"{'program':<55}{'runs':>6}{'nodes':>7}{'nonleaf':>8}{'JPF_states':>11}")
    for s in summary:
        print(f"{s[0]:<55}{s[1]:>6}{s[2]:>7}{s[3]:>8}{s[4]:>11}")
    pd.DataFrame(summary, columns=["program", "runs", "nodes", "nonleaf", "jpf_states"]).to_csv(
        os.path.join(ROOT, "Artifacts", "heldout", "run_status_coastal.csv"), index=False)
    print(len(summary), "programs written to", OUT_DIR)


if __name__ == "__main__":
    main()
