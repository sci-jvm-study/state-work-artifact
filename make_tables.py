"""Prints Tables 3 to 9 of the paper, each computed from the data by the scripts in tables/.

Usage (from this folder):
    python make_tables.py                 # run the analyses on the data (about 10 minutes in total)
    python make_tables.py --from-archive  # read the archived outputs in results/ (seconds)
    python make_tables.py 4 7             # only some tables
Tables 1 and 2 contain no computed numbers.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
flags = [a for a in sys.argv[1:] if a.startswith("--")]
which = [a for a in sys.argv[1:] if not a.startswith("--")] or ["3", "4", "5", "6", "7", "8", "9"]
for t in which:
    p = subprocess.run([sys.executable, f"table{t}.py", *flags], cwd=os.path.join(HERE, "tables"))
    if p.returncode != 0:
        sys.exit(f"table {t} failed")
