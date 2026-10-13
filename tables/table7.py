"""Table 7: load imbalance when open subtrees are divided among K workers.  Usage: python table7.py"""
import re

from common import ARCHIVE, archived, run, section, table

if ARCHIVE:
    t39 = section(archived("39_load_balance_replay.txt"), "##### units per worker = 4", "#####")
    t45_30 = section(archived("45_load_balance_probe_cost.txt"), "##### probes per unit = 30", "#####")
    t45_1 = section(archived("45_load_balance_probe_cost.txt"), "##### probes per unit = 1")
else:
    t39 = run("load_balance_replay.py", ["4"])
    t45_30 = run("load_balance_probe_cost.py", ["4", "30"])
    t45_1 = run("load_balance_probe_cost.py", ["4", "1"])


def by_k(text):
    """Splits an output into its K = 4 and K = 8 blocks."""
    out = {}
    for m in re.finditer(r"K = (\d+)[^\n]*\n(.*?)(?=\nK = \d|\Z)", text, re.S):
        out[int(m.group(1))] = m.group(2)
    return out


def value(block, row, col):
    m = re.search(rf"^{re.escape(row)}\s+(\d+\.\d+)", block, re.M)
    return m.group(1)


b39, b30, b1 = by_k(t39), by_k(t45_30), by_k(t45_1)
spec = [
    ("Equal weights (every unit has weight 1)", b39, "count"),
    ("M5 linear", b39, "M5 linear"),
    ("M5 Random Forest", b39, "M5 RF"),
    ("Knuth, 30 probes, probing not charged", b39, "Knuth 30"),
    ("Knuth, 30 probes, probing charged", b30, "Knuth, probing spread over K workers"),
    ("Knuth, 1 probe, probing charged", b1, "Knuth, probing spread over K workers"),
    ("Final subtree size", b39, "hindsight size"),
    ("True work", b39, "oracle"),
]
rows = [(label, value(b[4], row, 0), value(b[8], row, 0)) for label, b, row in spec]
table("Table 7. Load imbalance (largest worker load over the balanced load, macro mean over groups).",
      ("Weights", "K=4", "K=8"), rows)
