"""Feasibility run of the larger-trees study. Compiles InsertionSort7, runs it on JPF with the StateWorkListener and prints the time and the
number of states of the search.

Needs JPF with jpf-symbc (../../instrumentation/README.md) and a JDK 11. Environment variables: JPF_HOME (the folder that contains jpf-core
and jpf-symbc) and JAVA_HOME.

Usage: python run_one.py [timeout_seconds]
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
JPF = os.environ.get("JPF_HOME", r"<JPF folder>")
SPFLIB = JPF + r"\jpf-symbc\lib"
RUNJAR = JPF + r"\jpf-core\build\RunJPF.jar"
JAVA_HOME = os.environ.get("JAVA_HOME", r"<JDK 11 folder>")
JAVA = JAVA_HOME + r"\bin\java.exe"
JAVAC = JAVA_HOME + r"\bin\javac.exe"
env = dict(os.environ)
env["PATH"] = JAVA_HOME + r"\bin;" + SPFLIB + ";" + env.get("PATH", "")

timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 600
os.makedirs(os.path.join(HERE, "bin"), exist_ok=True)
subprocess.run([JAVAC, "-g", "-d", os.path.join(HERE, "bin"), os.path.join(HERE, "InsertionSort7.java")], check=True)
csv = os.path.join(HERE, "state_work_dataset.csv")
if os.path.exists(csv):
    os.remove(csv)
cmd = [JAVA, "-Dstatework.quiet=true", "-Djava.library.path=" + SPFLIB, "-jar", RUNJAR, "InsertionSort7_z3.jpf"]
t0 = time.time()
try:
    subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=timeout, env=env)
    status = "finished"
except subprocess.TimeoutExpired:
    status = "timeout"
dt = time.time() - t0
rows = 0
if os.path.exists(csv):
    with open(csv, encoding="utf-8") as f:
        rows = sum(1 for _ in f) - 1
print(f"InsertionSort7: {status} in {dt:.1f} s, {rows} state rows")
