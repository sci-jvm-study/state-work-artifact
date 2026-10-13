"""Table 5: macro rho of the models under three splits.  Usage: python table5.py"""
import re

from common import output, section, table, f3

splits = output("fit_generalization_splits.py", "09_generalization_splits.txt")
models = output("models_m1_to_m5.py", "02_models_m1_to_m5.txt")
gated = output("fit_all_baselines_fair_comparison.py", "06_baselines_fair_comparison.txt")
depth = output("depth_rule.py", "60_depth_rule.txt")


def split_row(name):
    m = re.search(rf"^{name}\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", splits, re.M)
    return [float(m.group(i)) for i in (1, 2, 3)]


def groups(name):
    # first model table of models_m1_to_m5.py: the last column is the number of scored groups
    m = re.search(rf"^{name}\s+-?\d+\.\d+\s+-?\d+\.\d+\s+\[.*?\]\s+-?\d+\.\d+\s+(\d+)", models, re.M)
    return int(m.group(1))


def rho(pattern, text):
    return float(re.search(pattern + r".*?macro rho = ([+-]\d+\.\d+)", text).group(1))


def gated_row(name):
    return float(re.search(rf"^{re.escape(name)}\s+55/55\s+(-?\d+\.\d+)", gated, re.M).group(1))


rows = []
for label, key in [("M1, depth (linear)", "M1_depth_only"), ("M2, static (linear)", "M2_static_only"),
                   ("M3, dynamic (linear)", "M3_dynamic_only")]:
    w, p, o = split_row(key)
    rows.append((label, groups(key), f3(w), f3(p), f3(o)))
rows.append(("M3, dynamic (Random Forest)", 55, "--", f3(rho(r"M3 Random Forest \(LOPO\), P55", depth)), "--"))
w, p, o = split_row("M5_static_plus_dynamic")
rows.append(("M5, static and dynamic (linear)", groups("M5_static_plus_dynamic"), f3(w), f3(p), f3(o)))
rows.append(("M5, static and dynamic (Random Forest)", 55, "--", f3(gated_row("M5 alone, RF (no gating)")), "--"))
rows.append(("Combined (M6-RF, M5-RF elsewhere)", 55, "--", f3(gated_row("Gated M6-RF+M5-RF")), "--"))
rows.append(("Depth rule (post hoc, no fitting)", 55, "--", f3(rho(r"depth rule, P55", depth)), "--"))
table("Table 5. Macro rho of the models under three splits.", ("Model", "Groups", "Within", "LOPO", "LOFO"), rows)
