#!/bin/bash
# Replacement for GDart's executor.sh: runs the same Espresso (SPouT) command, and additionally counts, with Truffle's CPU tracer,
# the statement and root executions inside the TARGET program's source files for THIS run. stdout/stderr (the symbolic trace
# DSE parses) are left untouched; the per-run total is appended to $GDART_WORKDIR/work.csv as "runIndex,total".
G=/w/gdart_bin/gdart
ESP=$G/SPouT/sdk/mxbuild/linux-amd64/GRAALVM_ESPRESSO_NATIVE_CE_JAVA17/graalvm-espresso-native-ce-java17-22.2.0.1-dev
OUT=${GDART_WORKDIR:?}
n=$(cat "$OUT/.n" 2>/dev/null || echo 0)
n=$((n+1))
echo $n > "$OUT/.n"
CT=/tmp/ct_$$_$n.json
$ESP/bin/java -truffle -ea -Xmx3g -Xss1g -Djava.lang.invoke.stringConcat=BC_SB \
  --experimental-options --cputracer --cputracer.TraceStatements=true --cputracer.TraceRoots=true \
  --cputracer.Output=json --cputracer.OutputFile=$CT $@ 2> >(tee -a "$OUT/stderr.txt" >&2)
rc=$?
python3 /w/gdart_bin/sum_counts.py "$CT" "$GDART_TARGETS" "$n" >> "$OUT/work.csv"
rm -f "$CT"
exit $rc
