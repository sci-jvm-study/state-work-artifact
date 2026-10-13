"""Sums Truffle CPU-tracer execution counts over the entries whose source file is one of the TARGET program's files
(comma-separated basenames in argv[2]); prints "runIndex,total". The harness file Main.java is never among the targets, so
the constant per-run cost of reading the symbolic inputs is not counted."""
import json
import sys

path, targets, run = sys.argv[1], set(sys.argv[2].split(",")), sys.argv[3]
total = 0
try:
    prof = json.load(open(path))["profile"]
    for e in prof:
        sec = e.get("source_section") or {}
        if sec.get("path", "").split("/")[-1] in targets:
            total += int(e["count"])
except Exception as ex:  # a failed run is recorded as -1 so it can be excluded, never silently counted as 0
    print(f"{run},-1", flush=True)
    sys.stderr.write(f"sum_counts failed: {ex}\n")
    sys.exit(0)
print(f"{run},{total}", flush=True)
