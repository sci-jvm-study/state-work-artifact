"""Held-out-layout version of make_gdart_run.py: reads from heldout/programs/ instead of
benchmarks/<category>/. Creates engines/gdart_runs/<Program>/ (same output dir as the main corpus run,
since run_one.sh hardcodes /w/gdart_runs/$D and the Ho* names don't collide with any main-corpus program).

Usage: python make_gdart_run_heldout.py <Program>"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # the root of this package
prog = sys.argv[1]
src_dir = os.path.join(ROOT, "heldout", "programs")
jpf = open(os.path.join(src_dir, prog + "_z3.jpf"), encoding="utf-8").read()
m = re.search(r"^symbolic\.method\s*=\s*(\w+)\.(\w+)\(([^)]*)\)", jpf, re.M)
cls, method, params = m.group(1), m.group(2), m.group(3).split("#")
assert all(p == "sym" for p in params), "only all-int programs"
lo = re.search(r"symbolic\.min_int\s*=\s*(-?\d+)", jpf).group(1)
hi = re.search(r"symbolic\.max_int\s*=\s*(-?\d+)", jpf).group(1)
out = os.path.join(ROOT, "engines", "gdart_runs", prog)
os.makedirs(out, exist_ok=True)
shutil.copyfile(os.path.join(src_dir, cls + ".java"), os.path.join(out, cls + ".java"))
lines = ["import tools.aqua.concolic.Verifier;", "", "public class Main {", "    public static void main(String[] args) {"]
for i in range(len(params)):
    lines.append(f"        int p{i} = Verifier.nondetInt();")
    lines.append(f"        Verifier.assume(p{i} >= {lo} && p{i} <= {hi});")
lines.append(f"        {cls}.{method}(" + ", ".join(f"p{i}" for i in range(len(params))) + ");")
lines += ["    }", "}", ""]
with open(os.path.join(out, "Main.java"), "w", newline="\n") as f:
    f.write("\n".join(lines))
print("prepared", out, cls, method, len(params), lo, hi)
