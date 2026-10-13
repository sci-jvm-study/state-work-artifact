"""Pruned choices. At a symbolic array access, jpf-symbc creates one choice per possible index and ignores at once (setIgnored(true), e.g.
IALOAD.java lines 107-130) every choice whose path condition is unsatisfiable. The listener records such a choice as a state that is not an end
state when entered, has no child and has zero work. These are infeasible alternatives and not explored states, so they are treated as leaves:
they stay in the recorded tree (JPF's own state counts and node counts are unchanged), but they are not scored, not used for training, and Group C
does not average over them.

mark_pruned(df) works on the rows of one program or on a frame with a `program` column. Set the environment variable KEEP_PRUNED_CHOICES=1 to
keep the pruned choices as ordinary rows (the all-rows analysis of the sensitivity results), or REMOVE_PRUNED_CHOICES=1 to remove them from the
tree altogether (used only for the Knuth probing sensitivity, results/69)."""
import os

import pandas as pd

KEEP = os.environ.get("KEEP_PRUNED_CHOICES") == "1"


def mark_pruned(df):
    df = df.copy()
    if "program" in df.columns:
        has_child = set(zip(df["program"], df["parentId"]))
        key = list(zip(df["program"], df["stateId"]))
    else:
        has_child = set(df["parentId"])
        key = list(df["stateId"])
    child = pd.Series([k in has_child for k in key], index=df.index)
    df["pruned"] = (~df["isEndStateAtEntry"].astype(bool)) & (~child)
    if os.environ.get("REMOVE_PRUNED_CHOICES") == "1":
        # third treatment, for the Knuth probing sensitivity only: the rows are taken out of the tree altogether
        return df[~df["pruned"]].reset_index(drop=True)
    if not KEEP:
        df.loc[df["pruned"], "isEndStateAtEntry"] = True
    return df
