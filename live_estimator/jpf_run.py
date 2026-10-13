"""Shared helper: run one JPF configuration with the Windows environment that Z3 needs."""
import os
import re
import subprocess
import time

# JPF_HOME: folder that contains jpf-core and jpf-symbc (built as described in instrumentation/README.md)
JPF = os.environ.get("JPF_HOME", r"<JPF folder>")
SPFLIB = JPF + r"\jpf-symbc\lib"
RUNJAR = JPF + r"\jpf-core\build\RunJPF.jar"
JAVA_HOME = os.environ.get("JAVA_HOME", r"<JDK 11 folder>")
JAVA = JAVA_HOME + r"\bin\java.exe"
PROGRAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programs")
MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "m5_rf.bin")

NAMES = ["HoAllKadaneKadaneSum", "HoAllSelectionSortSelection", "HoAllShellSortShell", "HoJaiLowerBoundLowerBound",
         "HoNumIndexIntervalsCompressDuplicates", "HoNumPartitionCountIndices", "HoNumSortingSort",
         "HoNumSortingSortIndicesInsertionSort", "HoRngAliasMethodDiscreteSamplerFillRemainingIndices"]

ENV = dict(os.environ)
ENV["PATH"] = JAVA_HOME + r"\bin;" + SPFLIB + ";" + ENV.get("PATH", "")

SUMMARY = re.compile(r"\[LiveEstimator\] (.*)")


def run_jpf(prog, listeners, props=None, jvm_flags=(), timeout=600):
    """Returns (summary dict or None, wall seconds, stdout tail). Output files land in PROGRAMS (the cwd)."""
    cmd = [JAVA, "-Djava.library.path=" + SPFLIB, *jvm_flags, "-jar", RUNJAR, prog + ".jpf", "+listener=" + ",".join(listeners)]
    for k, v in (props or {}).items():
        cmd.append(f"+{k}={v}")
    t0 = time.perf_counter()
    r = subprocess.run(cmd, cwd=PROGRAMS, capture_output=True, text=True, timeout=timeout, env=ENV)
    wall = time.perf_counter() - t0
    m = SUMMARY.search(r.stdout or "")
    summary = dict(kv.split("=") for kv in m.group(1).split()) if m else None
    return summary, wall, (r.stdout or "")[-400:] + " || " + (r.stderr or "")[-400:]
