"""Runs the JPF corpus's programs on COASTAL (patched, see coastal.patch).

For every program whose canonical `<Program>_z3.jpf` config exists and whose JPF state-tree has at most
MAX_JPF_ROWS rows, this reads target class / method / parameter count / int bounds from the .jpf file,
prepares an engines/runs/<Program>/ folder (make_run.py) and runs COASTAL with a wall-clock timeout.
The per-run log coastal_runs.csv (one row per concrete execution) is the raw data.

Usage: python run_batch.py [--max-rows 300] [--workers 8] [--timeout 1500] [--only Name1,Name2]
"""
import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CATS = ["synthetic", "real-world", "sv-comp"]
RUNROOT = os.environ.get("COASTAL_RUNROOT", "runs")


def jpf_info(path):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"^symbolic\.method\s*=\s*(\w+)\.(\w+)\(([^)]*)\)", txt, re.M)
    lo = re.search(r"symbolic\.min_int\s*=\s*(-?\d+)", txt)
    hi = re.search(r"symbolic\.max_int\s*=\s*(-?\d+)", txt)
    if not (m and lo and hi):
        return None
    params = [p for p in m.group(3).split("#")]
    if not all(p == "sym" for p in params):
        return None
    return m.group(1), m.group(2), len(params), lo.group(1), hi.group(1)


def jpf_rows(cat, prog):
    p = os.path.join(ROOT, "data", cat, prog + ".csv")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def run_one(job):
    cat, prog, cls, method, n, lo, hi = job
    src = os.path.join(ROOT, "benchmarks", cat, cls + ".java")
    if not os.path.exists(src):
        return prog, "no-source", 0
    r = subprocess.run([sys.executable, os.path.join(ROOT, "engines", "make_run.py"), src, cls, method, str(n), lo, hi],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return prog, "prepare-failed: " + r.stderr[-200:], 0
    run_dir = os.path.join(ROOT, "engines", RUNROOT, cls)
    t0 = time.time()
    try:
        with open(os.path.join(run_dir, "out.txt"), "w") as out:
            subprocess.run(["cmd", "/c", os.path.join(run_dir, "run.bat")], stdout=out, stderr=subprocess.STDOUT,
                           timeout=TIMEOUT)
        status = "done"
    except subprocess.TimeoutExpired:
        status = "TIMEOUT"
        subprocess.run(["taskkill", "/F", "/T", "/FI", f"WINDOWTITLE eq {cls}*"], capture_output=True)
    csv = os.path.join(run_dir, "coastal_runs.csv")
    runs = sum(1 for _ in open(csv)) if os.path.exists(csv) else 0
    return prog, status, runs, round(time.time() - t0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rows", type=int, default=300)
    ap.add_argument("--min-rows", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=1500)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    TIMEOUT = a.timeout
    only = set(x for x in a.only.split(",") if x)
    jobs = []
    for cat in CATS:
        for f in sorted(os.listdir(os.path.join(ROOT, "benchmarks", cat))):
            if not f.endswith("_z3.jpf"):
                continue
            prog = f[:-len("_z3.jpf")]
            if only and prog not in only:
                continue
            rows = jpf_rows(cat, prog)
            if rows is None or rows > a.max_rows or rows < a.min_rows:
                continue
            info = jpf_info(os.path.join(ROOT, "benchmarks", cat, f))
            if info is None:
                continue
            jobs.append((cat, prog) + info)
    print(len(jobs), "jobs", flush=True)
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for res in ex.map(run_one, jobs):
            print(res, flush=True)
