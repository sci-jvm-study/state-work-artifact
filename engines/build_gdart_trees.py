"""Turns each engines/gdart_runs/<Program>/out.txt (GDart's DSE log: one block per concrete run with its Decision{...} lines and a
status line) plus work.csv (per-run total from the Truffle CPU tracer, see gdart_bin/executor.sh) into state-tree CSVs with the
same columns as the JPF/COASTAL trees, using engines/build_trees.py's own build() and compress() so the tree definition is identical.

Harness handling: Main.java restricts every int parameter with Verifier.assume(lo <= p && p <= hi), which the concolic engine sees
as 2 branch decisions per parameter at the start of every path. Runs that satisfy the bounds carry those 2*nparams decisions with
branchId 0 (asserted below); they are stripped. Runs that violate a bound never reach the program (work 0) and are dropped; both
criteria must agree for every run or the program is flagged.

Work: GDart's per-run total counts executions of statements and method entries in the TARGET program's source files (Truffle
CPU tracer), inclusive of the prefix that every run re-executes. Per-branch cumulative counts do not exist, so every cumulative
count is 0 and a node's work is the sum of the totals of the runs through it (build_trees' 'full' definition; suffix == full here).

Usage: python build_gdart_trees.py"""
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_trees as bt

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEC = re.compile(r"^Decision\{condition=(.*), branches=(\d+), branchId=(-?\d+), assumption=(true|false)\}\s*$")
STATUS = re.compile(r"^(OK|ERROR|BUGGY|DIVERGED|SKIPPED|ASSUMPTION|TAINT)[A-Z ]*:")


def nparams_of(prog):
    txt = open(os.path.join(ROOT, "engines", "gdart_runs", prog, "Main.java")).read()
    return txt.count("Verifier.nondetInt()")


def parse(prog):
    out = os.path.join(ROOT, "engines", "gdart_runs", prog, "out.txt")
    if os.path.exists(out):
        lines = open(out, encoding="utf-8", errors="replace").read().splitlines()
    elif os.path.exists(out + ".gz"):  # very large logs are stored compressed
        import gzip
        lines = gzip.open(out + ".gz", "rt", encoding="utf-8", errors="replace").read().splitlines()
    else:
        return None, "no-output"
    complete = any("[END OF OUTPUT]" in l for l in lines)
    runs, cur = [], None
    for l in lines:
        if l.startswith("/w/gdart_bin/executor.sh"):
            cur = {"decisions": [], "status": None}
            runs.append(cur)
        elif cur is not None:
            m = DEC.match(l)
            if m:
                cur["decisions"].append((m.group(1), int(m.group(3)), m.group(4) == "true"))
            else:
                s = STATUS.match(l)
                if s and cur["status"] is None:
                    cur["status"] = s.group(1)
    wpath = os.path.join(ROOT, "engines", "gdart_runs", prog, "work.csv")
    work = {}
    if os.path.exists(wpath):
        for l in open(wpath):
            if l.strip():
                i, w = l.strip().split(",")
                work[int(i)] = int(w)
    return (runs, work, complete), None


def to_coastal_format(prog, runs, work, complete):
    """Return (list of run lines in coastal_runs.csv format, status string)."""
    k = 2 * nparams_of(prog)
    lines, valid = [], 0
    bad_status = {r["status"] for r in runs if r["status"] in ("BUGGY", "DIVERGED", "ERROR")}
    if not complete:
        return [], "not-finished"
    if bad_status:
        return [], "gdart-" + "+".join(sorted(bad_status)).lower()
    if len(work) != len(runs) or any(v < 0 for v in work.values()):
        return [], "work-missing"
    for i, r in enumerate(runs, start=1):
        dec = r["decisions"]
        prefix_ok = len(dec) > k and all(b == 0 for _, b, _ in dec[:k])
        ran = work[i] > 0
        if prefix_ok != ran:
            return [], "abnormal-run"
        if not ran:
            continue  # assumption-violating run: the program never executed
        body = dec[k:]
        toks = "".join(f"{c}#{b}@0@-1\t" for c, b, _ in body)
        lines.append(f"{valid},{work[i]},{toks}")
        valid += 1
    return lines, "clean"


if __name__ == "__main__":
    out_root = os.path.join(ROOT, "engines", "data", "data_gdart")
    summary = []
    for cat in bt.CATS:
        for prog_csv in sorted(os.listdir(os.path.join(ROOT, "data", cat))):
            prog = prog_csv[:-4]
            if not os.path.isdir(os.path.join(ROOT, "engines", "gdart_runs", prog)):
                continue
            parsed, err = parse(prog)
            if err:
                summary.append((cat, prog, 0, 0, 0, 0, err))
                continue
            runs, work, complete = parsed
            lines, status = to_coastal_format(prog, runs, work, complete)
            jpf_rows = sum(1 for _ in open(os.path.join(ROOT, "data", cat, prog_csv))) - 1
            if status != "clean" or not lines:
                summary.append((cat, prog, len(runs), 0, 0, jpf_rows, status if status != "clean" else "no-valid-runs"))
                continue
            tmp = os.path.join(ROOT, "engines", "gdart_runs", prog, "coastal_runs.csv")
            with open(tmp, "w", newline="\n") as f:
                f.write("\n".join(lines) + "\n")
            raw, nruns = bt.build(tmp)
            df = bt.compress(raw)
            os.makedirs(os.path.join(out_root, cat), exist_ok=True)
            df.to_csv(os.path.join(out_root, cat, prog + ".csv"), index=False)
            summary.append((cat, prog, nruns, len(df), int((~df.isEndStateAtEntry).sum()), jpf_rows, "clean"))
    print(f"{'category':<11}{'program':<30}{'runs':>6}{'nodes':>7}{'nonleaf':>8}{'JPF_states':>11}  status")
    for s in summary:
        print(f"{s[0]:<11}{s[1]:<30}{s[2]:>6}{s[3]:>7}{s[4]:>8}{s[5]:>11}  {s[6]}")
    pd.DataFrame(summary, columns=["category", "program", "runs", "nodes", "nonleaf", "jpf_states", "status"]).to_csv(
        os.path.join(ROOT, "engines", "run_status_data_gdart.csv"), index=False)
