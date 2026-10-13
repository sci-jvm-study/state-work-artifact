#!/bin/bash
# usage: run_one.sh <program dir under /w/gdart_runs> [extra -D flags]
# Runs GDart (DSE + SPouT/Espresso, svcomp23 distribution) on <dir>/Main.java + the program's sources with DFS exploration until
# completion, using the executor wrapper so each concrete run also reports a per-run work total (work.csv).
G=/w/gdart_bin/gdart
D=$1; shift
ESP=$G/SPouT/sdk/mxbuild/linux-amd64/GRAALVM_ESPRESSO_NATIVE_CE_JAVA17/graalvm-espresso-native-ce-java17-22.2.0.1-dev
export GDART_WORKDIR=/w/gdart_runs/$D
rm -f $GDART_WORKDIR/.n $GDART_WORKDIR/work.csv; : > $GDART_WORKDIR/work.csv
export GDART_TARGETS=$(cd $GDART_WORKDIR && ls *.java | grep -v '^Main.java$' | tr '\n' ',' | sed 's/,$//')
work=$(mktemp -d)
cp -a $GDART_WORKDIR/*.java $work/
cp $G/verifier-stub/target/verifier-stub-1.0.jar $work/
cd $work
CP="$work:$work/verifier-stub-1.0.jar"
$ESP/bin/javac -cp $CP Main.java $(ls *.java | grep -v '^Main.java$' | tr '\n' ' ') || exit 1
$ESP/bin/java -Xmx1g -cp $G/dse/target/dse-0.0.1-SNAPSHOT-jar-with-dependencies.jar tools.aqua.dse.DSELauncher \
  -Ddse.witness=false -Ddse.dp=z3 -Ddse.b64encode=true -Dtaint.flow=OFF -Ddse.terminate.on=completion -Ddse.explore=dfs "$@" \
  -Ddse.executor=/w/gdart_bin/executor.sh -Ddse.executor.args="-cp $CP -Dconcolic.execution=true -Dtaint.flow=OFF Main" -Ddse.sources=$CP
