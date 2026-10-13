"""What are the 4,054 'non-leaf' states with no recorded child and zero work?
A state is 'not an end state when entered' (isEndStateAtEntry == False). Of those, some have recorded children and
some have none. Prints how the childless ones look: work, instruction counters, choice generator, path-condition
size, and which program groups they sit in. Usage: python zero_work_states.py > ../results/61_zero_work_states.txt"""
import glob
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
fr = []
for f in sorted(glob.glob(os.path.join(HERE, "..", "data", "*", "*.csv"))):
    d = pd.read_csv(f)
    d["grp"] = os.path.basename(f)[:-4]
    fr.append(d)
d = pd.concat(fr, ignore_index=True)
kids = set(zip(d.grp, d.parentId))
d["haskid"] = [(g, s) in kids for g, s in zip(d.grp, d.stateId)]
ne = d[~d.isEndStateAtEntry]
z = ne[~ne.haskid]
o = ne[ne.haskid]
print(f"States: {len(d)}; not end states when entered: {len(ne)}")
print(f"  with a recorded child: {len(o)} (min work {o.actualSubtreeWork.min()})")
print(f"  without a recorded child: {len(z)} ({100 * len(z) / len(ne):.1f}%)")
print(f"\nChildless states: work values {sorted(z.actualSubtreeWork.unique())}; "
      f"entry == exit instruction count in {100 * (z.entryInstructionCount == z.exitInstructionCount).mean():.0f}%")
print(f"Path-condition size at entry: {z.pathConditionSize.value_counts().to_dict()}")
print(f"Choice generator types: {z.choiceGeneratorType.value_counts().to_dict()}")
print(f"Choice generator totals (number of choices): {z.choiceGeneratorTotal.value_counts().to_dict()}")
print(f"For comparison, states with children: totals {o.choiceGeneratorTotal.value_counts().head(4).to_dict()}, "
      f"median path-condition size {o.pathConditionSize.median()}")
print("\nData files containing such states (count, share of that file's not-end states):")
tot = ne.groupby("grp").size()
for g, n in z.groupby("grp").size().sort_values(ascending=False).items():
    print(f"  {g:38s}{n:6d}  {100 * n / tot[g]:5.1f}%")
print(f"Data files (configurations) with any: {z.grp.nunique()} of {d.grp.nunique()}")
