"""Held-out corpus, step 1: drop test-source candidates, write licence headers, generate drivers (one output dir per library)."""
import csv
import os
import re
import subprocess
import sys

H = os.environ.get("HELDOUT_WORK", r"<working folder of the held-out selection>")
S = r"<directory with the cloned libraries>"
LIBS = {  # name: (src root, prefix, commit, url, licence line)
    "commons-numbers": ("commons-numbers", "HoNum", "f9403ff37998b49c6b85273713847c856d8ee47b", "https://github.com/apache/commons-numbers", "Apache License 2.0"),
    "commons-rng": ("commons-rng", "HoRng", "6e5a0056b1a8405771431478f3e7c134dee35c14", "https://github.com/apache/commons-rng", "Apache License 2.0"),
    "java-algorithms-implementation": ("java-algorithms-implementation", "HoJai", "f2d115704691e8e4f6cfe490231d0adb0c3ce7d0", "https://github.com/phishman3579/java-algorithms-implementation", "Apache License 2.0"),
    "java": ("java", "HoAll", "1af0c0bab97d9a03a7665894c067fac66c96fcc5", "https://github.com/AllAlgorithms/java", "MIT License, Copyright (c) 2018 All Algorithms and its contributors"),
}
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "corpus_selection", "libraries", "gen_drivers.py"), encoding="utf-8").read()
for lib, (root, prefix, commit, url, lic) in LIBS.items():
    rows = list(csv.DictReader(open(os.path.join(H, f"candidates_{lib}.csv"), encoding="utf-8")))
    keep = [r for r in rows if r["failed_stage"] != "-" or not re.search(r"(^|/)src/test/|Test\.java$", r["file"])]
    dropped = [r for r in rows if r["failed_stage"] == "-" and r not in keep]
    out_csv = os.path.join(H, f"cand_nontest_{lib}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(keep)
    print(lib, "passing screen:", sum(r["failed_stage"] == "-" for r in rows), "| test sources dropped:", [(r["file"].split("/")[-1], r["method"]) for r in dropped])
    hdr = os.path.join(H, f"license_{lib}.txt")
    open(hdr, "w", encoding="utf-8").write(f"// Origin: {url}, commit {commit}. {lic}. Method bodies copied verbatim (comments removed).\n")
    g = src.replace('"Ta" +', repr(prefix) + " +")
    assert g != src
    gp = os.path.join(H, "gen_drivers_tmp.py")
    open(gp, "w", encoding="utf-8").write(g)
    r = subprocess.run([sys.executable, gp, out_csv, os.path.join(S, root), lib, hdr, os.path.join(H, "gen", lib)], capture_output=True, text=True)
    print(r.stdout.strip()[-400:], r.stderr.strip()[-300:])
os.remove(os.path.join(H, "gen_drivers_tmp.py"))
