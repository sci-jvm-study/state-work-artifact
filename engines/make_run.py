"""Prepares one COASTAL run folder for a benchmark: copies the program (adding a main() that calls the target once
with zeros if the source has none), writes the .properties and run.bat.

Usage: python make_run.py <source.java> <ClassName> <method> <nparams> <min> <max>
Environment: COASTAL_STRATEGY = DF (default) | BF | RAND      COASTAL_RUNROOT = runs (default) | runs_BF | runs_RAND
"""
import glob
import os
import sys

src_path, cls, method, nparams, lo, hi = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]
STRATEGY = os.environ.get("COASTAL_STRATEGY", "DF")
RUNROOT = os.environ.get("COASTAL_RUNROOT", "runs")
ENG = os.path.dirname(os.path.abspath(__file__))
run_dir = os.path.join(ENG, RUNROOT, cls)
os.makedirs(run_dir, exist_ok=True)

src = open(src_path, encoding="utf-8").read().rstrip()
assert src.endswith("}")
zeros = ", ".join(["0"] * nparams)
if "static void main" not in src:
    src = src[:-1] + "\n    public static void main(String[] args) { " + method + "(" + zeros + "); }\n}\n"
open(os.path.join(run_dir, cls + ".java"), "w", encoding="utf-8").write(src)

FACTORY = {
    "DF": "za.ac.sun.cs.coastal.strategy.pathbased.DepthFirstFactory",
    "BF": "za.ac.sun.cs.coastal.strategy.pathbased.BreadthFirstFactory",
    "RAND": "za.ac.sun.cs.coastal.strategy.pathbased.RandomPathFactory",
}[STRATEGY]
seed_line = "coastal.strategies.ST.seed = 12348765\n" if STRATEGY == "RAND" else ""

z3 = glob.glob(os.path.join(ENG, "z3", "*", "bin", "z3.exe"))[0].replace("\\", "/")
params = ", ".join("p%d: int" % i for i in range(nparams))
props = (
    "coastal.target.main = " + cls + "\n"
    "coastal.target.instrument = " + cls + "\n"
    "coastal.target.trigger = " + cls + "." + method + "(" + params + ")\n\n"
    "coastal.bounds.int.min = " + lo + "\n"
    "coastal.bounds.int.max = " + hi + "\n\n"
    "coastal.strategies = ST\n"
    "coastal.strategies.ST = " + FACTORY + "\n"
    "coastal.strategies.ST.threads = 1\n" + seed_line + "\n"
    "coastal.settings.solver = za.ac.sun.cs.coastal.solver.SolverZ3\n"
    "coastal.settings.solver.z3-args = -smt2 -in\n"
    "coastal.settings.solver.z3-path = " + z3 + "\n"
)
open(os.path.join(run_dir, cls + ".properties"), "w").write(props)

bat = (
    "@echo off\n"
    'cd /d "%~dp0"\n'
    "if not exist bin mkdir bin\n"
    "javac -g -XDstringConcat=inline -d bin " + cls + ".java\n"
    "if exist coastal_runs.csv del coastal_runs.csv\n"
    'java -ea "-Dcoastal.runlog=%~dp0coastal_runs.csv" -cp '
    '"%~dp0..\\coastal\\build\\install\\coastal\\lib\\*;%~dp0bin" '
    "za.ac.sun.cs.coastal.COASTAL " + cls + ".properties\n"
)
open(os.path.join(run_dir, "run.bat"), "w").write(bat)
print("prepared", run_dir)
