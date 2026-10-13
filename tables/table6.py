"""Table 6: accuracy of Knuth probing against its live cost, on P55.  Usage: python table6.py"""
import re

from common import output, section, table, f3

text = output("fit_knuth_online_cost_analysis.py", "14_knuth_online_cost.txt")
block = section(text, "B. Accuracy vs. probe count", "=== C.")
rows = []
for m in re.finditer(r"^\s+(\d+)\s+(-?\d+\.\d+)\s+\[(-?\d+\.\d+),(-?\d+\.\d+)\]\s+(\d+\.\d+)%", block, re.M):
    k = int(m.group(1))
    if k in (1, 5, 10, 30):
        # the cost is printed as a percentage of the state's own work; the paper gives it as a multiple
        rows.append((k, f3(float(m.group(2))), f"[{f3(float(m.group(3)))}, {f3(float(m.group(4)))}]",
                     f"{float(m.group(5)) / 100:.1f}x"))
assert len(rows) == 4
table("Table 6. Accuracy of Knuth probing against its cost in a live search, on P55.",
      ("Probes", "Macro rho", "95% CI", "Median cost relative to W(s)"), rows)
