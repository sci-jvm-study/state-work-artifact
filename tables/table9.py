"""Table 9: macro rho on the nine held-out programs (P9).  Usage: python table9.py"""
import re

from common import output, section, table, f3

held = output("heldout_eval.py", "40_heldout_evaluation.txt")
depth = output("depth_rule.py", "60_depth_rule.txt")

block = section(held, "ALL HELD-OUT PROGRAMS (pre-registered set)", "Pre-registered hypotheses")
v = {}
for m in re.finditer(r"^\s+(.+?)\s+groups=(\d+)\s+macro rho = ([+-]\d+\.\d+)\s+\[([+-]\d+\.\d+), ([+-]\d+\.\d+)\]", block, re.M):
    v[m.group(1).strip()] = (float(m.group(3)), float(m.group(4)), float(m.group(5)), int(m.group(2)))
d = float(re.search(r"depth rule, P9.*?macro rho = ([+-]\d+\.\d+)", depth).group(1))

sib = v["Group C"]
rows = [
    ("Live count", f3(v["floor"][0])),
    ("Final subtree size", f3(v["hindsight"][0])),
    ("JPF built-in estimator", f3(v["JPF built-in"][0])),
    ("JPFBar", f3(v["JPFBar"][0])),
    ("Sibling mean", f"{f3(sib[0])} [{f3(sib[1])}, {f3(sib[2])}]"),
    ("Knuth probing, 30 probes", f3(v["Knuth 30"][0])),
    ("M5 Random Forest", f3(v["M5 RF"][0])),
    ("M6 Random Forest", f3(v["M6 RF"][0])),
    ("Depth rule (post hoc)", f3(d)),
]
n_def = min(v["Group C"][3], v["M6 RF"][3])
table("Table 9. Macro rho on the nine held-out programs (P9). The sibling mean and M6 are defined on %d of the 9 programs, and the interval of\n"
      "the sibling mean is a 95%% bootstrap interval over programs." % n_def, ("Estimator", "Macro rho"), rows)
