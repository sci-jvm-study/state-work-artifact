"""Larger trees: applies the rule of PREDECLARATION.md to the canonical Z3 configuration of every program group.

For each program group that has data in ../data, the program is run with the symmetric symbolic range [-k, k] for increasing k, starting at
the first k of K_LIST that is larger than the range of the benchmark configuration. The run of the largest k before the first stop is kept.
A stop is a search with more than MAX_STATES states, a search that takes more than TIMEOUT seconds, or a search with the same number of
states as the previous k (the tree no longer grows).

Needs JPF with jpf-symbc and the StateWorkListener (../instrumentation/README.md) and a JDK 11. Environment variables:
JPF_HOME (the folder that contains jpf-core and jpf-symbc) and JAVA_HOME.

Usage: python sweep.py [--workers 4] [--only Name1,Name2] [--out sweep_new]
Output in --out: runs/<Program>/k<k>/state_work_dataset.csv for every run, tries.csv (one row per run), kept/<Program>.csv and
kept/<Program>.k (the kept run and its range). The shipped tries.csv and kept/ are the output of this script.
"""
import argparse
import concurrent.futures as cf
import csv
import os
import re
import shutil
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "benchmarks")
DATA = os.path.join(HERE, "..", "data")
JPF = os.environ.get("JPF_HOME", r"<JPF folder>")
SPFLIB = JPF + r"\jpf-symbc\lib"
RUNJAR = JPF + r"\jpf-core\build\RunJPF.jar"
JAVA_HOME = os.environ.get("JAVA_HOME", r"<JDK 11 folder>")
JAVA = JAVA_HOME + r"\bin\java.exe"
JAVAC = JAVA_HOME + r"\bin\javac.exe"
K_LIST = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 50, 100]
MAX_STATES = 100000
TIMEOUT = 300
ENV = dict(os.environ)
ENV["PATH"] = JAVA_HOME + r"\bin;" + SPFLIB + ";" + ENV.get("PATH", "")


def programs():
    """The program groups with data: (family, name) for every <name>_z3.jpf of the benchmarks that has a CSV in ../data."""
    out = []
    for fam in ("real-world", "sv-comp", "synthetic"):
        for f in sorted(os.listdir(os.path.join(SRC, fam))):
            if f.endswith("_z3.jpf") and os.path.exists(os.path.join(DATA, fam, f[:-7] + ".csv")):
                out.append((fam, f[:-7]))
    return out


def compile_program(fam, name, out):
    """Compiles the Java source of the program (and what it uses) with debug information, once per program."""
    classes = os.path.abspath(os.path.join(out, "classes", fam))
    os.makedirs(classes, exist_ok=True)
    fam_dir = os.path.abspath(os.path.join(SRC, fam))
    subprocess.run([JAVAC, "-g", "-nowarn", "-d", classes, "-sourcepath", fam_dir, os.path.join(fam_dir, name + ".java")],
                   check=True, capture_output=True)
    return classes, fam_dir


def config(fam, name, k, path, classes, fam_dir):
    """Writes the benchmark configuration with the range [-k, k] and with absolute class and source paths."""
    t = open(os.path.join(SRC, fam, name + "_z3.jpf"), encoding="utf-8").read()
    t = re.sub(r"symbolic\.min_int\s*=\s*-?\d+", f"symbolic.min_int = {-k}", t)
    t = re.sub(r"symbolic\.max_int\s*=\s*-?\d+", f"symbolic.max_int = {k}", t)
    t = re.sub(r"^classpath\s*=.*$", "classpath = " + classes.replace("\\", "/"), t, flags=re.M)
    t = re.sub(r"^sourcepath\s*=.*$", "sourcepath = " + fam_dir.replace("\\", "/"), t, flags=re.M)
    open(path, "w", encoding="utf-8", newline="\n").write(t)


def run(fam, name, k, out, classes, fam_dir):
    d = os.path.join(out, "runs", name, f"k{k}")
    os.makedirs(d, exist_ok=True)
    cfg = os.path.join(d, name + "_z3.jpf")
    config(fam, name, k, cfg, classes, fam_dir)
    csv_out = os.path.join(d, "state_work_dataset.csv")
    if os.path.exists(csv_out):
        os.remove(csv_out)
    t0 = time.time()
    proc = subprocess.Popen([JAVA, "-Dstatework.quiet=true", "-Djava.library.path=" + SPFLIB, "-jar", RUNJAR, cfg], cwd=d,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=ENV)
    try:
        proc.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        proc.wait()
        return None, time.time() - t0, "timeout", csv_out
    dt = time.time() - t0
    if not os.path.exists(csv_out):
        return None, dt, "no-output", csv_out
    with open(csv_out, encoding="utf-8") as f:
        n = sum(1 for _ in f) - 1
    return n, dt, ("over-cap" if n > MAX_STATES else "ok"), csv_out


def one(fam, name, out):
    t = open(os.path.join(SRC, fam, name + "_z3.jpf"), encoding="utf-8").read()
    k0 = int(re.search(r"symbolic\.max_int\s*=\s*(-?\d+)", t).group(1))
    classes, fam_dir = compile_program(fam, name, out)
    tries, prev, kept = [], None, None
    for k in [k for k in K_LIST if k > k0]:
        n, dt, status, csv_out = run(fam, name, k, out, classes, fam_dir)
        tries.append((name, k, n if n is not None else 0, round(dt, 1), status))
        if status != "ok":
            break
        if prev == n:
            tries[-1] = (name, k, n, round(dt, 1), "no-growth")
            break
        kept = (k, n, csv_out)
        prev = n
    if kept:
        os.makedirs(os.path.join(out, "kept"), exist_ok=True)
        shutil.copyfile(kept[2], os.path.join(out, "kept", name + ".csv"))
        with open(os.path.join(out, "kept", name + ".k"), "w") as f:
            f.write(str(kept[0]))
    return name, k0, kept[0] if kept else None, kept[1] if kept else None, tries


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=os.path.join(HERE, "sweep_new"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    todo = programs()
    if a.only:
        s = set(a.only.split(","))
        todo = [p for p in todo if p[1] in s]
    rows = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for name, k0, k, n, tries in ex.map(lambda p: one(p[0], p[1], a.out), todo):
            rows.extend(tries)
            print(f"{name:<36} k0={k0:<4} kept k={k} states={n}", flush=True)
    with open(os.path.join(a.out, "tries.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["program", "k", "states", "seconds", "outcome"])
        w.writerows(rows)
