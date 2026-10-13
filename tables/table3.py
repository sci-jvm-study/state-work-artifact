"""Table 3: one-line answers with their key numbers.  Usage: python table3.py"""
import re

from common import output, section, table, f3

base = output("fit_all_baselines_fair_comparison.py", "06_baselines_fair_comparison.txt")
depth = output("depth_rule.py", "60_depth_rule.txt")
knuth = output("fit_knuth_online_cost_analysis.py", "14_knuth_online_cost.txt")

p55 = section(base, "TABLE A", "FAIR COMPARISON") if "TABLE A" in base else base
live_p55 = float(re.search(r"^6 State-count floor\s+55\s+(-?\d+\.\d+)", base, re.M).group(1))
p29 = section(base, "FAIR COMPARISON: same population all six can score", "Per-group rho")


def p29row(name):
    return float(re.search(rf"^\d {re.escape(name)}\s+29\s+(-?\d+\.\d+)", p29, re.M).group(1))


m6rf = p29row("M6 RandomForest")
depth_p55 = float(re.search(r"depth rule, P55.*?macro rho = ([+-]\d+\.\d+)", depth).group(1))
median = float(re.search(r"Median:\s+(\d+\.\d+)%", knuth).group(1)) / 100

rows = [
    ("RQ1", "The live count is negatively related to work, almost entirely through nested pairs.", f"rho = {f3(live_p55)} (P55)"),
    ("RQ2", "Progress estimators transfer poorly. Probing and the sibling mean are exceptions.",
     f"{f3(p29row('Knuth probing'))} and {f3(p29row('Group C'))} (P29)"),
    ("RQ3", "Richer features help little. History is best where it exists, and a post hoc depth rule ranks higher.",
     f"{f3(m6rf)}, and {f3(depth_p55)} (post hoc reference)"),
    ("RQ4", "Probing costs more than the work it estimates, so its advantage disappears.", f"median {median:.1f}x"),
]
print("Table 3. One-line answers with their key numbers (the answers are text, the key numbers are computed).")
for rq, ans, key in rows:
    print(f"{rq}  {key}\n     {ans}")
print()
