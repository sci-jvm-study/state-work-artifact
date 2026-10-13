"""Compiles every benchmark program with a COASTAL run into runs/<Program>/bin, exactly as make_run.py's run.bat
does (same source transformation: a main() calling the target once with zeros is appended when the source has none; same javac
flags). The static-lookahead port (static_features.py, used by validate_static.py and
analysis/cross_engine_models.py) reads these class files. Needs a JDK 11 `javac` on PATH.

Usage: python compile_bins.py"""
import csv
import os
import subprocess
import sys

ENG = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(ENG, ".."))
sys.path.insert(0, ENG)
from run_batch import CATS, jpf_info

with open(os.path.join(ENG, "run_status_data_coastal2.csv"), encoding="utf-8") as f:
    HAS_RUN = {row["program"] for row in csv.DictReader(f)}

done = 0
for cat in CATS:
    for f in sorted(os.listdir(os.path.join(ROOT, "benchmarks", cat))):
        if not f.endswith("_z3.jpf"):
            continue
        info = jpf_info(os.path.join(ROOT, "benchmarks", cat, f))
        if info is None:
            continue
        cls, method, nparams = info[0], info[1], info[2]
        run_dir = os.path.join(ENG, "runs", cls)
        if cls not in HAS_RUN:
            continue
        src = open(os.path.join(ROOT, "benchmarks", cat, cls + ".java"), encoding="utf-8").read().rstrip()
        if "static void main" not in src:
            src = src[:-1] + "\n    public static void main(String[] args) { " + method + "(" + ", ".join(["0"] * nparams) + "); }\n}\n"
        os.makedirs(os.path.join(run_dir, "bin"), exist_ok=True)
        java = os.path.join(run_dir, cls + ".java")
        open(java, "w", encoding="utf-8").write(src)
        subprocess.run(["javac", "-g", "-XDstringConcat=inline", "-d", os.path.join(run_dir, "bin"), java], check=True)
        done += 1
print("compiled", done, "programs")
