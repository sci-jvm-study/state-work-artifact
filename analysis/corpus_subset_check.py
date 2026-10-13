"""Sensitivity of the main results to the corpus composition: the same scripts are run on the corpus without the 17 programs added by
the selection screens (../corpus_selection/added_programs.txt), i.e. on the 49 program groups of the corpus before the screens.
Runs models_m1_to_m5 (models M1-M5), fit_node_count_baseline (state-count floor and hindsight N(s)),
fit_all_baselines_fair_comparison (baselines and M6 on the same population) and fit_hybrid_model (M6 and the gated model) against a
temporary copy of the data with those programs removed, and prints their output one after another.

Usage: python corpus_subset_check.py"""
import contextlib
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import models_m1_to_m5 as fp

added = set(open(os.path.join(HERE, "..", "corpus_selection", "added_programs.txt")).read().split())
src = os.path.join(HERE, "..", "data")
tmp = tempfile.mkdtemp()
kept = 0
for cat in os.listdir(src):
    if not os.path.isdir(os.path.join(src, cat)):
        continue
    os.makedirs(os.path.join(tmp, cat))
    for f in os.listdir(os.path.join(src, cat)):
        if f.endswith(".csv") and f[:-4] not in added:
            shutil.copyfile(os.path.join(src, cat, f), os.path.join(tmp, cat, f))
            kept += 1
fp.DATA_DIR = tmp
print(f"corpus without the {len(added)} added programs: {kept} configurations\n")
for name in ("models_m1_to_m5", "fit_node_count_baseline", "fit_all_baselines_fair_comparison", "fit_hybrid_model"):
    print("=" * 100 + f"\n{name}\n" + "=" * 100)
    mod = __import__(name)
    mod.main()
shutil.rmtree(tmp)
