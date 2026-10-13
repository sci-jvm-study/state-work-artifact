"""Creates engines/gdart_runs/<Program>/ (Main.java harness + the program's sources) from a JPF configuration.
The harness reads every int parameter with Verifier.nondetInt(), restricts it to the JPF range with Verifier.assume(), and calls the
target method exactly like the JPF configuration does.

Usage: python make_gdart_run.py <category> <Program>"""
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
cat, prog = sys.argv[1], sys.argv[2]
jpf = open(os.path.join(ROOT, "benchmarks", cat, prog + "_z3.jpf"), encoding="utf-8").read()
m = re.search(r"^symbolic\.method\s*=\s*(\w+)\.(\w+)\(([^)]*)\)", jpf, re.M)
cls, method, params = m.group(1), m.group(2), m.group(3).split("#")
assert all(p == "sym" for p in params), "only all-int programs"
lo = re.search(r"symbolic\.min_int\s*=\s*(-?\d+)", jpf).group(1)
hi = re.search(r"symbolic\.max_int\s*=\s*(-?\d+)", jpf).group(1)
out = os.path.join(ROOT, "engines", "gdart_runs", prog)
os.makedirs(out, exist_ok=True)
src_dir = os.path.join(ROOT, "benchmarks", cat)
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
