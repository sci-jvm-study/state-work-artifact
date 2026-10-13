"""Runs GDart (Docker image gdart-env, see gdart_bin/img/Dockerfile) on every program listed in gdart_candidates.csv, smallest JPF
tree first, N programs in parallel, with a per-program wall-clock timeout. Output: gdart_runs/<Program>/out.txt + work.csv;
timeouts are recorded in gdart_runs/<Program>/TIMEOUT and are reported as 'not-finished' by build_gdart_trees.py.

Usage: python run_gdart_batch.py [parallel=3] [timeout_s=1800]"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
par = int(sys.argv[1]) if len(sys.argv) > 1 else 3
tmo = int(sys.argv[2]) if len(sys.argv) > 2 else 1800
cand = pd.read_csv(os.path.join(ROOT, "gdart_candidates.csv")).sort_values("jpf_states")


def run(row):
    p = row.program
    d = os.path.join(ROOT, "gdart_runs", p)
    if os.path.exists(os.path.join(d, "out.txt")) and "[END OF OUTPUT]" in open(os.path.join(d, "out.txt"), errors="replace").read():
        return p, "skip-done"
    subprocess.run([sys.executable, os.path.join(ROOT, "make_gdart_run.py"), row.category, p], check=True, capture_output=True)
    name = f"gd_{p}"
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    for f in ("TIMEOUT",):
        if os.path.exists(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    try:
        subprocess.run(["docker", "run", "--rm", "--name", name, "-v", ROOT + ":/w", "gdart-env", "bash", "-c",
                        f"bash /w/gdart_bin/run_one.sh {p} > /w/gdart_runs/{p}/out.txt 2>&1"],
                       timeout=tmo, env={**os.environ, "MSYS_NO_PATHCONV": "1"})
        return p, "done"
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        open(os.path.join(d, "TIMEOUT"), "w").write(f"{tmo}s\n")
        return p, "timeout"


with ThreadPoolExecutor(par) as ex:
    for p, s in ex.map(run, [r for r in cand.itertuples()]):
        print(p, s, flush=True)
