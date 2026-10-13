"""Holm-Bonferroni correction (Holm 1979, recommended by Arcuri & Briand~\\cite{arcuri2014hitchhiker} for SE paired comparisons) within
each family of related paired Wilcoxon tests reported in the paper. A family is the set of tests that answer one comparison question
together (same table or paragraph); each family is corrected on its own, not across the whole paper, following standard practice.
Every p-value used here is parsed from the already-archived results/ files (not recomputed), so this script only re-derives the
correction, not the underlying statistics.

Family 1 (RQ3): M6-RF, M6 linear and Knuth-probing macro rho vs Group C, same 29-group population (results/29).
Family 2a/2b (Table 7): the five weights (M5 RF, M5 linear, Knuth 30, hindsight size, random) each vs count, at K=4 and K=8 separately
  (results/39; the M5RF-vs-M5linear and oracle-vs-M5RF rows are diagnostic, not part of this "beats count" claim, and are not corrected here).
Family 3 (RQ3/RQ4, probing-charged): Knuth-charged (spread over K workers) vs count, at 3 probe counts (30, 5, 1) x 2 K values = 6 tests
  (results/45).
Family 4a (external validity, Table 8 baselines): the 7 baselines each JPF vs COASTAL-DFS and JPF vs COASTAL-BFS = 14 tests (results/18).
Family 4b (external validity, models): the 8 models, JPF vs COASTAL once for the DFS tree set and once for the BFS tree set = 16 tests
  (results/19, 20).

Usage: python multiple_comparison_correction.py"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import holm_bonferroni 

# the folder with the result files that are read (default: ../results; reproduce.sh sets RESULTS_DIR)
R = os.environ.get("RESULTS_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def read(fname):
    return open(os.path.join(R, fname), encoding="utf-8").read()


def report(family_name, names, pvalues):
    corrected = holm_bonferroni(pvalues)
    print(f"\n{family_name} ({len(pvalues)} tests)")
    print(f"{'test':<48}{'raw p':>10}{'Holm p':>10}{'significant at 0.05':>22}")
    n_changed = 0
    for name, p, (adj, rej) in zip(names, pvalues, corrected):
        was_sig = p < 0.05
        if was_sig and not rej:
            n_changed += 1
        flag = "" if was_sig == rej else "  <-- changes"
        print(f"{name:<48}{p:>10.4g}{adj:>10.4g}{str(rej):>22}{flag}")
    print(f"  {n_changed} test(s) significant at raw p<0.05 lose significance after Holm correction.")
    return n_changed


total_changed = 0

# ---- Family 1: results/29 (paired_tests_group_c.py) ----
t29 = read("29_paired_tests_group_c.txt")
names1, p1 = [], []
for m in re.finditer(r"^(.+?) vs Group C:.*?Wilcoxon p=([\d.]+)", t29, re.M):
    names1.append(m.group(1))
    p1.append(float(m.group(2)))
total_changed += report("Family 1: RQ3, Group C comparisons (results/29)", names1, p1)

# ---- Family 2a/2b: results/39 (load_balance_replay.py), "X vs count" rows only ----
t39 = read("39_load_balance_replay.txt")
blocks = re.split(r"K = (\d+) workers:", t39)[1:]  # alternating: K, text
for i in range(0, len(blocks), 2):
    K, block = blocks[i], blocks[i + 1]
    block = block.split("=" * 20)[0]
    names2, p2 = [], []
    for m in re.finditer(r"^\s*(\S[\S ]*?)\s+vs count\s+mean difference.*?p = ([\d.eE+-]+)", block, re.M):
        names2.append(f"{m.group(1).strip()} vs count")
        p2.append(float(m.group(2)))
    if p2:
        total_changed += report(f"Family 2{'a' if K == '4' else 'b'}: Table 7, weights vs count, K={K} (results/39)", names2, p2)

# ---- Family 3: results/45 (load_balance_probe_cost.py), "Knuth, probing spread over K workers" rows ----
t45 = read("45_load_balance_probe_cost.txt")
sections = t45.split("##### probes per unit = ")
names3, p3 = [], []
for sec in sections[1:]:
    n_probes = sec.split("\n", 1)[0].strip()
    for Km in re.finditer(r"K = (\d+):(.*?)(?=\n=+\n|\Z)", sec, re.S):
        K, block = Km.group(1), Km.group(2)
        m = re.search(r"Knuth, probing spread over K workers\s+[\d.]+\s+\d+\s*/\s*worse\s*\d+\s+p = ([\d.eE+-]+)", block)
        if m:
            names3.append(f"Knuth charged ({n_probes} probes) vs count, K={K}")
            p3.append(float(m.group(1)))
total_changed += report("Family 3: RQ3/RQ4, probing-charged Knuth vs count (results/45)", names3, p3)

# ---- Family 4a: results/18 (final_table.py) ----
t18 = read("18_cross_engine_estimators.txt")
names4a, p4a = [], []
for line in t18.splitlines():
    m = re.match(r"^(\w+)\s+\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([\d.]+)\s*/\s*([\d.]+)", line)
    if m:
        method = m.group(1)
        names4a += [f"{method} JPF vs COASTAL-DFS", f"{method} JPF vs COASTAL-BFS"]
        p4a += [float(m.group(2)), float(m.group(3))]
if p4a:
    total_changed += report("Family 4a: external validity, baseline estimators (results/18)", names4a, p4a)

# ---- Family 4b: results/19, 20 (cross_engine_models.py) ----
names4b, p4b = [], []
for fname, order in [("19_cross_engine_models_dfs.txt", "DFS"), ("20_cross_engine_models_bfs.txt", "BFS")]:
    txt = read(fname)
    for line in txt.splitlines():
        m = re.match(r"^([\w\s\-/+]+?)\s+[\d.]+ \(n=\s*\d+\)\s+[\d.]+ \(n=\s*\d+\)\s+\|\s*\d+\s+[\d.]+\s+[\d.]+\s+p=([\d.]+)", line)
        if m:
            names4b.append(f"{m.group(1).strip()} JPF vs COASTAL-{order}")
            p4b.append(float(m.group(2)))
if p4b:
    total_changed += report("Family 4b: external validity, learned models (results/19, 20)", names4b, p4b)

print(f"\n{'=' * 92}\nTOTAL across all families: {total_changed} test(s) significant at raw p<0.05 lose significance after Holm-Bonferroni correction.")
