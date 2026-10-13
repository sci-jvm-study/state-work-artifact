"""Depth rule on the 49 program groups of the corpus before the selection screens (post hoc). The fitted depth model M1 has
macro rho -0.689 there (results/34); the rule prediction = -depth has no fitted sign, so this prints what it gives on the same groups.
Usage: python depth_rule_49.py > ../results/65_depth_rule_49.txt"""
import os
import shutil
import sys
import tempfile

import numpy as np
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import models_m1_to_m5 as fp  
from models_m1_to_m5 import macro_average, bootstrap_macro_ci, MIN_ROWS_FOR_GROUP_RHO  

added = set(open(os.path.join(HERE, "..", "corpus_selection", "added_programs.txt")).read().split())
src = os.path.join(HERE, "..", "data")
tmp = tempfile.mkdtemp()
for cat in os.listdir(src):
    if os.path.isdir(os.path.join(src, cat)):
        os.makedirs(os.path.join(tmp, cat))
        for f in os.listdir(os.path.join(src, cat)):
            if f.endswith(".csv") and f[:-4] not in added:
                shutil.copyfile(os.path.join(src, cat, f), os.path.join(tmp, cat, f))
fp.DATA_DIR = tmp
df = fp.load_all()
shutil.rmtree(tmp)
nl = df[df.isEndStateAtEntry == False]  
out = {}
for g, s in nl.groupby("program_group"):
    if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s.actualSubtreeWork.nunique() > 1 and s.depth.nunique() > 1:
        out[g] = spearmanr(s.actualSubtreeWork, -s.depth)[0]
ci = bootstrap_macro_ci(out)
label = "all-rows analysis (pruned choices kept as rows)" if os.environ.get("KEEP_PRUNED_CHOICES") == "1" else "main analysis (pruned choices are leaves)"
print(f"[{label}] depth rule, the {df.program_group.nunique()} groups before the selection screens, scored groups = {len(out)}: "
      f"macro rho = {macro_average(out):+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}]")
print(f"negative in {sum(v < 0 for v in out.values())} of {len(out)} groups")
nz = nl[nl.actualSubtreeWork > 0]
out2 = {}
for g, s in nz.groupby("program_group"):
    if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s.actualSubtreeWork.nunique() > 1 and s.depth.nunique() > 1:
        out2[g] = spearmanr(s.actualSubtreeWork, -s.depth)[0]
print(f"same, pruned choices left out of the scoring: macro rho = {macro_average(out2):+.3f} ({len(out2)} groups; negative in {sum(v < 0 for v in out2.values())})")
