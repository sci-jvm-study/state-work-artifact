"""Table 8: macro rho on matched configurations for JPF, COASTAL and GDart.  Usage: python table8.py

The JPF and COASTAL columns come from engines/final_table.py (the compiled classes in engines/runs are shipped, so compile_bins.py
is not needed again), the GDart column from analysis/cross_engine_replication.py.
"""
import re

from common import output, section, table, f3

eng = output("final_table.py", "18_cross_engine_estimators.txt", ["exact"], folder="engines")
gd = output("cross_engine_replication.py", "27_gdart_replication.txt",
            ["--coastal", "data_gdart", "--subset", "exact", "--work", "full"])

first = {}
for m in re.finditer(r"^(\w+)\s+(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s", eng, re.M):
    first[m.group(1)] = (int(m.group(2)), float(m.group(3)), float(m.group(4)))

gblock = section(gd, "--- GDart (work = full)")
g = {}
for m in re.finditer(r"^\s+(\w+)\s+macro rho =\s+(-?\d+\.\d+)\s+\[.*?\]\s+scoreable groups = (\d+)", gblock, re.M):
    g[m.group(1)] = (float(m.group(2)), int(m.group(3)))

PAPER = [("Live count", "floor"), ("Final subtree size N(s)", "hindsight"), ("JPF built-in estimator", "jpfbuiltin"),
         ("JPFBar", "jpfbar"), ("Kilby weighted backtrack", "kilby"), ("Sibling mean", "groupC"),
         ("Knuth probing, 30 probes", "knuth30")]
rows = [(label, first[k][0], f3(first[k][1]), f3(first[k][2]), f3(g[k][0])) for label, k in PAPER]
n_gd = [g[k][1] for _, k in PAPER]
table("Table 8. Macro rho on matched configurations (JPF and COASTAL: the 68 configurations that match in both search orders;\n"
      "GDart: its own 65, so its column is unpaired). The number of scored groups is n (%d to %d for GDart)." % (min(n_gd), max(n_gd)),
      ("Method", "n", "JPF", "COASTAL", "GDart"), rows)
