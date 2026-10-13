"""Final cross-engine table: for each method, macro Spearman rho over the groups scoreable in ALL THREE columns
(JPF-DFS, COASTAL-DFS, COASTAL-BFS), on the programs where COASTAL's tree has exactly JPF's node count.
Also pairwise paired Wilcoxon (JPF vs each COASTAL order). 4 decimals so rounding can be checked by hand.
Usage: python final_table.py [exact|all]   (run from anywhere; imports analysis/models)"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
import cross_engine_replication as cer 
from models_m1_to_m5 import macro_average, rank_biserial 

subset = sys.argv[1] if len(sys.argv) > 1 else "exact"
ROOT = cer.ROOT
st = {n: pd.read_csv(os.path.join(ROOT, "engines", f"run_status_{n}.csv")) for n in ("data_coastal2", "data_coastal2_BF")}
clean = {n: s[s["status"] == "clean"] for n, s in st.items()}
if subset == "exact":
    clean = {n: c[c["nodes"] == c["jpf_states"]] for n, c in clean.items()}
programs = set(clean["data_coastal2"]["program"]) & set(clean["data_coastal2_BF"]["program"])
print(f"{len(programs)} programs ({subset})")

cols = {
    "JPF-DFS": cer.load(cer.JPF_DIR, programs),
    "COASTAL-DFS": cer.load(os.path.join(ROOT, "engines", "data", "data_coastal2"), programs, coastal=True),
    "COASTAL-BFS": cer.load(os.path.join(ROOT, "engines", "data", "data_coastal2_BF"), programs, coastal=True),
}
preds = {k: cer.predictions(v) for k, v in cols.items()}
methods = ["floor", "hindsight", "jpfbuiltin", "jpfbar", "kilby", "groupC", "knuth30"]
rho = {k: {m: cer.group_rhos(p, m) for m in methods} for k, p in preds.items()}

print(f"\n{'method':<11}{'groups':>7}{'JPF-DFS':>10}{'COA-DFS':>10}{'COA-BFS':>10}   Wilcoxon p (JPF vs DFS / vs BFS)   rank-biserial r (JPF vs DFS / vs BFS)")
for m in methods:
    shared = sorted(set.intersection(*[set(rho[k][m]) for k in cols]))
    vals = {k: np.array([rho[k][m][g] for g in shared]) for k in cols}
    p, r = [], []
    for k in ("COASTAL-DFS", "COASTAL-BFS"):
        d = vals["JPF-DFS"] - vals[k]
        p.append(wilcoxon(d).pvalue if len(d) >= 5 and np.any(d != 0) else float("nan"))
        r.append(rank_biserial(vals["JPF-DFS"], vals[k]))
    print(f"{m:<11}{len(shared):>7}{vals['JPF-DFS'].mean():>10.4f}{vals['COASTAL-DFS'].mean():>10.4f}"
          f"{vals['COASTAL-BFS'].mean():>10.4f}   {p[0]:.3f} / {p[1]:.3f}   {r[0]:+.2f} / {r[1]:+.2f}")
