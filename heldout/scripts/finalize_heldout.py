"""Held-out corpus, step 3: copy the selected programs, their JPF configurations (range k of the selection run) and the archived
per-state data into heldout/, and copy the selection log, the candidate lists and the try log."""
import csv
import os
import re
import shutil

H = os.environ.get("HELDOUT_WORK", r"<working folder of the held-out selection>")
A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this package's heldout/ folder
G = os.path.join(H, "gen_all")
for d in ("programs", "data", "selection"):
    os.makedirs(os.path.join(A, d), exist_ok=True)
rows = list(csv.DictReader(open(os.path.join(G, "selected.csv"), encoding="utf-8")))
for r in rows:
    n, k = r["program"], int(r["k"])
    src = open(os.path.join(G, n + ".java"), encoding="utf-8").read()
    m = re.search(r"static void classify\(([^)]*)\)", src)
    npar = len([x for x in m.group(1).split(",") if x.strip()])
    shutil.copyfile(os.path.join(G, n + ".java"), os.path.join(A, "programs", n + ".java"))
    shutil.copyfile(os.path.join(G, "kept", n + ".csv"), os.path.join(A, "data", n + ".csv"))
    open(os.path.join(A, "programs", n + "_z3.jpf"), "w", newline="\n").write(
        f"target = {n}\nclasspath = bin\nsourcepath = .\nsymbolic.method = {n}.classify({'#'.join(['sym'] * npar)})\n"
        f"symbolic.min_int = {-k}\nsymbolic.max_int = {k}\nsymbolic.dp = z3\nlistener = gov.nasa.jpf.symbc.StateWorkListener\n")
shutil.copyfile(os.path.join(G, "selected.csv"), os.path.join(A, "selection", "selected.csv"))
shutil.copyfile(os.path.join(G, "tries.csv"), os.path.join(A, "selection", "tries.csv"))
shutil.copyfile(os.path.join(H, "selection_heldout.txt"), os.path.join(A, "selection", "selection_decisions.txt"))
for f in os.listdir(H):
    if f.startswith("candidates_") and f.endswith(".csv"):
        shutil.copyfile(os.path.join(H, f), os.path.join(A, "selection", f))
print(len(rows), "programs copied")
