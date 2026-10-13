"""Adapts SV-COMP Java tasks (sv-benchmarks) that passed screen.py to this study's convention (see benchmarks/sv-comp/*.java):
the task's Main class becomes <Name>, and the symbolic inputs that its main() read with Verifier.nondetInt() become the
parameters of `public static void classify(int ...)`, the method jpf-symbc runs symbolically. Nothing else in the program is changed.

  * `int x = Verifier.nondetInt();` in main()  ->  parameter x        (an inline Verifier.nondetInt() becomes parameter pN)
  * `Verifier.assume(c);` in main()            ->  `if (!(c)) { return; }`   (same path pruning; jpf-symbc has no Verifier class)
  * the original file header (source, license) is kept verbatim and a MODIFICATION note is added
  * a main() that calls classify with the lower bound of the range is added (COASTAL / plain execution need an entry point)

Anything this script cannot transform mechanically (a Verifier call outside main(), several source files) is reported.

Usage: python adapt.py <sv-benchmarks/java dir> <out dir>"""
import csv
import os
import re
import sys

JAVA, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

TASKS = {  # task (path under java/, no .yml) -> class name used in this study
    "jayhorn-recursive/SatPrimes01": "Primes",
    "argv-tasks/StrictLineReader": "StrictLineReader",
    "jbmc-regression/aastore_aaload1": "JbmcAastoreAaload1", "jbmc-regression/array1": "JbmcArray1", "jbmc-regression/array2": "JbmcArray2",
    "jbmc-regression/arraylength1": "JbmcArraylength1", "jbmc-regression/arrayread1": "JbmcArrayread1", "jbmc-regression/assert1": "JbmcAssert1",
    "jbmc-regression/assert5": "JbmcAssert5", "jbmc-regression/assert6": "JbmcAssert6", "jbmc-regression/if_expr1": "JbmcIfExpr1",
    "jbmc-regression/if_icmp1": "JbmcIfIcmp1", "jbmc-regression/lookupswitch1": "JbmcLookupswitch1", "jbmc-regression/tableswitch1": "JbmcTableswitch1",
    "jbmc-regression/list1": "JbmcList1", "jdart-regression/list2": "JdartList2",
    "jpf-regression/ExDarko_true": "ExDarko", "jpf-regression/ExGenSymExe_true": "ExGenSymExe", "jpf-regression/ExLazy_true": "ExLazy",
    "jpf-regression/ExSymExe7_true": "ExSymExe7", "jpf-regression/ExSymExe10_true": "ExSymExe10", "jpf-regression/ExSymExe11_true": "ExSymExe11",
    "jpf-regression/ExSymExe13_true": "ExSymExe13", "jpf-regression/ExSymExe19_true": "ExSymExe19", "jpf-regression/ExSymExeSwitch_true": "ExSymExeSwitch",
    "jpf-regression/ExSymExeTestAssignments_true": "ExSymExeTestAssignments", "jpf-regression/ExSymExeTestClassFields_true": "ExSymExeTestClassFields",
    "jpf-regression/TestLazy_true": "TestLazy",
}


def match_brace(s, i):
    d = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0:
                return j
    raise ValueError("unbalanced")


def adapt(task, name):
    d = os.path.join(JAVA, task)
    files = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".java")]
    if len(files) != 1:
        return None, f"{len(files)} source files"
    src = open(files[0], encoding="utf-8", errors="replace").read().replace("\r\n", "\n")
    m = re.search(r"public\s+static\s+void\s+main\s*\(\s*String\s*\[\]\s*\w+\s*\)\s*(throws\s+[\w.,\s]+)?\{", src)
    if not m:
        return None, "no main(String[])"
    b0 = m.end() - 1
    b1 = match_brace(src, b0)
    body = src[b0 + 1:b1]
    params, n = [], [0]

    def decl(mm):
        params.append(mm.group(2))
        return ""
    body = re.sub(r"(final\s+)?int\s+(\w+)\s*=\s*(?:\(int\)\s*)?Verifier\s*\.\s*nondetInt\(\)\s*;", decl, body)

    def inline(mm):
        n[0] += 1
        params.append(f"p{n[0]}")
        return f"p{n[0]}"
    body = re.sub(r"Verifier\s*\.\s*nondetInt\(\)", inline, body)
    body = re.sub(r"Verifier\s*\.\s*assume\s*\(((?:[^()]|\((?:[^()]|\([^()]*\))*\))*)\)\s*;", lambda mm: f"if (!({mm.group(1)})) {{ return; }}", body)
    if "Verifier" in body:
        return None, "Verifier call left in main()"
    head = src[:m.start()] + src[b1 + 1:]
    if re.search(r"Verifier\s*\.", head):
        return None, "Verifier call outside main()"
    if not params:
        return None, "no symbolic input in main()"
    # header comments / imports before the class
    cls = re.search(r"(public\s+)?class\s+Main\b", head)
    if not cls:
        return None, "no class Main"
    pre = re.sub(r"import\s+org\.sosy_lab\.sv_benchmarks\.Verifier\s*;\s*\n", "", head[:cls.start()])
    rest = re.sub(r"\bMain\b", name, head[cls.start():])
    body = re.sub(r"\bMain\b", name, body)
    sig = "    public static void classify(" + ", ".join("int " + p for p in params) + ") {"
    rest = rest.replace("{", "{\n" + sig + body.rstrip() + "\n    }\n" + "    public static void main(String[] args) { classify(" + ", ".join(["0"] * len(params)) + "); }\n", 1)
    note = (f"// MODIFICATION (this study): task {task}. Main renamed {name}; the symbolic inputs main() read with\n"
            f"// Verifier.nondetInt() are the parameters of classify(); Verifier.assume(c) became `if (!(c)) return;`. Program logic unchanged.\n")
    return pre.rstrip() + "\n" + note + rest, ""


report = []
for task, name in TASKS.items():
    code, why = adapt(task, name)
    if code is None:
        report.append((name, "NOT ADAPTED", why))
        continue
    open(os.path.join(OUT, name + ".java"), "w", encoding="utf-8", newline="\n").write(code)
    report.append((name, "adapted", re.search(r"classify\(([^)]*)\)", code).group(1)))
for r in report:
    print(f"{r[0]:<26}{r[1]:<13}{r[2]}")
