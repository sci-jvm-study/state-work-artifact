# Benchmarks

Java sources and JPF run configurations of the three benchmark families. A `.java` file may have more than one `.jpf` configuration, for
example a variant with a wider symbolic range (`_wideR`) or a variant that uses the Choco solver instead of Z3 (`_choco`). The configurations
of one program form one program group in the analysis.

| Family | Java files | `.jpf` configurations | Description |
|---|---|---|---|
| `real-world/` | 46 | 55 | Methods from Apache Commons Lang and Math (30 files) and from TheAlgorithms/Java (16 files, `Ta*.java`, MIT), copied into a driver class whose header records the source, the licence and the change made for the driver. |
| `synthetic/` | 22 | 22 | Controlled programs that vary branching structure, recursion, dispatch depth and exception paths. |
| `sv-comp/` | 41 | 49 | Programs from the SV-COMP Java repository (sv-benchmarks) and from the example suite of jpf-symbc (sorting, tree and graph algorithms, arithmetic recurrences), with their attribution headers. |

The tables of the paper are computed from the 116 CSV files in `../data/`, so these sources are needed only to collect the data again. The corpus of the paper is those 116 files. Not every `.jpf` file has a CSV. `ArithmeticUtilsGcd`, `ArithmeticUtilsPow`,
`StringUtilsIsAlpha` and `StringUtilsIndexOfDifference` use bitwise operators on symbolic values, which the solver backends of jpf-symbc do not
support, and `ArithmeticUtilsCheck2` has no data either. `EvenOdd`, `HanoiSteps`, `PrecisionCompare` and `PrecisionRoundUnscaled` have one
CSV under the plain program name for their configurations.

## Naming

Taking `ArrayUtilsIndexOf` as the example, a program has these files:

- `ArrayUtilsIndexOf.java`: the program.
- `ArrayUtilsIndexOf_z3.jpf`: the default configuration (Z3, default symbolic range).
- `ArrayUtilsIndexOf_choco.jpf`: the same program with the Choco solver.
- `ArrayUtilsIndexOf_wideR.jpf`: the same program with a wider symbolic input range.

Some programs also exist in scaled versions with a number in the name (`ArrayUtilsIndexOf6.java`, `ArrayUtilsIndexOf6_z3.jpf`), which are
configurations of the same program group.

## Running a benchmark

Each `.jpf` file is a JPF configuration (`target`, `classpath = bin`, `sourcepath = .`, `symbolic.*` and
`listener=gov.nasa.jpf.symbc.StateWorkListener`, see `../instrumentation/README.md`). From a built JPF and jpf-symbc installation, run these
commands in the folder of the program (for example `real-world/`), with the native libraries of jpf-symbc (`jpf-symbc/lib`) on the `PATH` and in
`java.library.path`:

```
javac -g -d bin ArrayUtilsReverse.java
java -Dstatework.quiet=true -Djava.library.path=<jpf-symbc>/lib -jar <jpf-core>/build/RunJPF.jar ArrayUtilsReverse_z3.jpf
```

The run writes `state_work_dataset.csv`, the per-state table of this program and configuration. Its schema is in `../data/README.md`, and the
files of all runs are in `../data/`. Apart from the time columns, the table is identical to the file of the same program in `../data/`
(for `ArrayUtilsReverse`, 262 rows).
