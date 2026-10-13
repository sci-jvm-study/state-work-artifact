"""Shared helpers of the table scripts.

Every table script runs the analysis scripts that the table needs on the data in ../data (or on the engine trees in ../engines/data)
and prints the table as it appears in the paper. With --from-archive a script reads the archived outputs in ../results instead of running
the analysis, which takes seconds.
"""
import os
import re
from decimal import Decimal, ROUND_HALF_UP
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = "--from-archive" in sys.argv


def run(script, args=(), folder="analysis", env=None):
    """Runs a script of the package and returns its standard output."""
    e = dict(os.environ)
    e.update(env or {})
    e["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, script, *args], cwd=os.path.join(ROOT, folder), env=e,
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        sys.exit(f"{script} failed:\n{p.stderr[-2000:]}")
    return p.stdout


def archived(name):
    return open(os.path.join(ROOT, "results", name), encoding="utf-8").read()


def output(script, archive_name, args=(), folder="analysis", env=None):
    """The output of a script: archived file with --from-archive, otherwise a fresh run."""
    return archived(archive_name) if ARCHIVE else run(script, args, folder, env)


def section(text, start, end=None):
    """Part of the text after the first occurrence of start and before the next occurrence of end."""
    if start not in text:
        sys.exit(f"missing section: {start}")
    part = text.split(start, 1)[1]
    return part.split(end, 1)[0] if end and end in part else part


def num(x):
    return float(x)


def f3(x):
    """Three decimals, with halves rounded up (0.2355 gives 0.236), as the paper does."""
    d = Decimal(repr(x)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return f"{d:.3f}" if not (d == 0 and x < 0) else "-0.000"


def table(title, header, rows):
    """Prints a table with left-aligned first column and right-aligned others."""
    cols = list(zip(header, *rows))
    w = [max(len(str(c)) for c in col) for col in cols]
    print(title)
    print("  ".join(str(h).ljust(w[0]) if i == 0 else str(h).rjust(w[i]) for i, h in enumerate(header)))
    for r in rows:
        print("  ".join(str(c).ljust(w[0]) if i == 0 else str(c).rjust(w[i]) for i, c in enumerate(r)))
    print()
