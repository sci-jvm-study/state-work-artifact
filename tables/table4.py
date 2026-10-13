"""Table 4: macro Spearman rho on P29 with 95% bootstrap confidence intervals.  Usage: python table4.py"""
import re

from common import output, section, table, f3

text = output("fit_all_baselines_fair_comparison.py", "06_baselines_fair_comparison.txt")
block = section(text, "FAIR COMPARISON: same population all six can score", "Per-group rho")
rows = {}
for m in re.finditer(r"^\d (.+?)\s+(\d+)\s+(-?\d+\.\d+)\s+\[(-?\d+\.\d+),(-?\d+\.\d+)\]", block, re.M):
    rows[m.group(1).strip()] = (float(m.group(3)), float(m.group(4)), float(m.group(5)), int(m.group(2)))

# paper row label, row name in the script output, extra work to obtain
PAPER = [
    ("JPF built-in estimator", "JPF built-in", "none"),
    ("JPFBar", "JPFBar", "none"),
    ("Live count", "State-count floor", "none"),
    ("Kilby weighted backtrack", "Kilby WBE", "none"),
    ("Sibling mean (M4)", "Group C", "none"),
    ("M6 linear", "M6 Linear", "none (a fitted model)"),
    ("M6 Random Forest", "M6 RandomForest", "none (a fitted model)"),
    ("Knuth probing, 30 probes (replay)", "Knuth probing", "see Section 5.4"),
]
out = []
for label, key, extra in PAPER:
    r, lo, hi, n = rows[key]
    assert n == 29, (key, n)
    out.append((label, f3(r), f"[{f3(lo)}, {f3(hi)}]", extra))
table("Table 4. Macro Spearman rho on P29 with 95% bootstrap confidence intervals (CI).",
      ("Method", "Macro rho", "95% CI", "Extra work to obtain"), out)
