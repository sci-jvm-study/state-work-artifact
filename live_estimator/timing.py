"""H2 of live_estimator_stage1_predeclared.md: overhead of the live estimator.

15 repetitions per (program, condition); one discarded warm-up run per program; all timed runs shuffled together with seed 42,
run strictly one after another, each in a fresh JVM. Raw rows go to results/timing_raw.csv.

Usage: python timing.py"""
import csv
import os
import random
import time

from jpf_run import MODEL, NAMES, run_jpf

HERE = os.path.dirname(os.path.abspath(__file__))
LISTENER = "gov.nasa.jpf.symbc.LiveEstimatorListener"
CONDITIONS = {
    "none": {"liveest.mode": "none"},
    "features": {"liveest.mode": "features"},
    "rf": {"liveest.mode": "rf", "liveest.model": MODEL},
    "rfcap": {"liveest.mode": "rfcap", "liveest.model": MODEL},
    "rfcap-timed": {"liveest.mode": "rfcap", "liveest.model": MODEL, "liveest.timers": "true"},
}
REPS = 15

for prog in NAMES:  # warm-up, discarded
    run_jpf(prog, [LISTENER], CONDITIONS["rfcap"])

jobs = [(p, c, r) for p in NAMES for c in CONDITIONS for r in range(REPS)]
random.Random(42).shuffle(jobs)

out = os.path.join(HERE, "results", "timing_raw.csv")
t0 = time.time()
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["program", "condition", "rep", "order", "states", "nonleaf", "searchNs", "featNs", "predCapNs", "wallS"])
    for i, (p, c, r) in enumerate(jobs):
        s, wall, tail = run_jpf(p, [LISTENER], CONDITIONS[c])
        if s is None:
            print("FAILED", p, c, r, tail, flush=True)
            continue
        w.writerow([p, c, r, i, s["states"], s["nonleaf"], s["searchNs"], s["featNs"], s["predCapNs"], f"{wall:.3f}"])
        f.flush()
        if i % 50 == 0:
            print(f"{i}/{len(jobs)} done, {time.time() - t0:.0f}s elapsed", flush=True)
print("finished", flush=True)
