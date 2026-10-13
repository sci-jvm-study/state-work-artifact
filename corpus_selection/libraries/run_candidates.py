"""Compiles the adapted SV-COMP programs (adapt.py output) and runs each on JPF/jpf-symbc (z3, StateWorkListener) to choose its
symbolic input range by one fixed rule: symmetric range [-k, k] for k in K_LIST, ascending; keep the largest k whose exploration
finishes within TIMEOUT seconds with at most MAX_STATES states (the paper's corpus stays in the same size regime); the run that
produced the kept range is the archived data. A program whose smallest range already fails is reported as such.
Records every attempted (program, k, states, non-leaf states, seconds, outcome) in tries.csv.

Usage: python run_candidates.py <adapted dir> [Name1,Name2,...]   (Windows; needs the JPF setup of ../../instrumentation/README.md)"""
import csv
import os
import shutil
import subprocess
import sys
import time

import pandas as pd

D = os.path.abspath(sys.argv[1])
ONLY = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
K_LIST = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20]
MAX_STATES = 1500
TIMEOUT = 60
JDK = os.environ["JDK11_HOME"]          # JDK 11 (jpf-core requirement)
JPF = os.environ["JPF_HOME"]            # folder holding jpf-core and jpf-symbc (built, see ../../instrumentation/README.md)
JPF_ENV = os.environ.get("JPF_ENV_BAT", "")  # optional .bat that sets JAVA_HOME / PATH for JPF (Windows)
BIN = os.path.join(D, "bin")
os.makedirs(BIN, exist_ok=True)
os.makedirs(os.path.join(D, "kept"), exist_ok=True)


def cfg(name, k):
    p = os.path.join(D, f"{name}_z3.jpf")
    with open(p, "w", newline="\n") as f:
        f.write(f"target = {name}\nclasspath = {BIN.replace(chr(92), '/')}\nsourcepath = {D.replace(chr(92), '/')}\n"
                f"symbolic.method = {name}.classify(SYMS)\nsymbolic.min_int = {-k}\nsymbolic.max_int = {k}\nsymbolic.dp = z3\n"
                "listener = gov.nasa.jpf.symbc.StateWorkListener\n")
    return p


def nparams(name):
    import re
    src = open(os.path.join(D, name + ".java"), encoding="utf-8").read()
    m = re.search(r"static void classify\(([^)]*)\)", src)
    return len([x for x in m.group(1).split(",") if x.strip()])


def run_jpf(name, k):
    p = cfg(name, k)
    txt = open(p).read().replace("SYMS", "#".join(["sym"] * nparams(name)))
    open(p, "w", newline="\n").write(txt)
    out = os.path.join(D, "state_work_dataset.csv")
    if os.path.exists(out):
        os.remove(out)
    env_call = f'call "{JPF_ENV}" >nul\r\n' if JPF_ENV else ""
    bat = (f'@echo off\r\n{env_call}set "SPFLIB={JPF}\\jpf-symbc\\lib"\r\ncd /d "{D}"\r\n'
           f'java -Dstatework.quiet=true -Djava.library.path="%SPFLIB%" -jar "{JPF}\\jpf-core\\build\\RunJPF.jar" "{p}" > run.log 2>&1\r\n')
    open(os.path.join(D, "run1.bat"), "w").write(bat)
    t0 = time.time()
    try:
        subprocess.run(["cmd", "/c", os.path.join(D, "run1.bat")], timeout=TIMEOUT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/IM", "java.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return None, time.time() - t0, "timeout"
    dt = time.time() - t0
    if not os.path.exists(out):
        return None, dt, "no-output"
    df = pd.read_csv(out)
    return df, dt, "ok"


tries = []
names = sorted(f[:-5] for f in os.listdir(D) if f.endswith(".java"))
for name in names:
    if ONLY and name not in ONLY:
        continue
    r = subprocess.run([os.path.join(JDK, "bin", "javac.exe"), "-g", "-d", BIN, os.path.join(D, name + ".java")], capture_output=True, text=True)
    if r.returncode:
        print(name, "COMPILE FAILED", r.stderr[:200])
        tries.append((name, 0, 0, 0, 0, "compile-failed"))
        continue
    kept, prev = None, None
    for k in K_LIST:
        df, dt, status = run_jpf(name, k)
        if df is None:
            tries.append((name, k, 0, 0, round(dt, 1), status))
            break
        nl = int((~df["isEndStateAtEntry"].astype(str).str.lower().eq("true")).sum())
        tries.append((name, k, len(df), nl, round(dt, 1), "ok" if len(df) <= MAX_STATES else "over-cap"))
        if len(df) > MAX_STATES:
            break
        kept = k
        shutil.copyfile(os.path.join(D, "state_work_dataset.csv"), os.path.join(D, "kept", name + ".csv"))
        if prev == len(df):
            break  # the tree no longer grows with the range: larger ranges add nothing
        prev = len(df)
    last = [t for t in tries if t[0] == name]
    print(f"{name:<26} kept k={kept}  " + " ".join(f"k{t[1]}:{t[2]}({t[3]})" for t in last))
pd.DataFrame(tries, columns=["program", "k", "states", "nonleaf", "seconds", "outcome"]).to_csv(os.path.join(D, "tries.csv"), index=False)
