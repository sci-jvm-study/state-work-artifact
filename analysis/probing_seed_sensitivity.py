"""Seed sensitivity of random probing. The probes of fit_knuth_probing_baseline.py are random, so this repeats the 30-probe estimate of every
non-leaf state with ten other seeds and prints the macro Spearman rho over the scoreable program groups (population P55) for each seed.

Usage: python probing_seed_sensitivity.py > ../results/71_probing_seed_sensitivity.txt"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, macro_average, MIN_ROWS_FOR_GROUP_RHO
from fit_knuth_probing_baseline import knuth_probe_predictions, N_PROBES, SEED

SEEDS = [SEED] + list(range(1, 11))


def macro_rho(df, seed):
    rng = np.random.default_rng(seed)
    acts, preds, groups = [], [], []
    for program, prog_df in df.groupby("program"):
        a, p, _ = knuth_probe_predictions(prog_df, rng)
        acts.extend(a)
        preds.extend(p)
        groups.extend([prog_df["program_group"].iloc[0]] * len(a))
    scored = pd.DataFrame({"program_group": groups, "actual": acts, "pred": preds})
    per_group = {}
    for g, sub in scored.groupby("program_group"):
        if len(sub) < MIN_ROWS_FOR_GROUP_RHO or sub["actual"].nunique() < 2 or sub["pred"].nunique() < 2:
            continue
        r = spearmanr(sub["actual"], sub["pred"])[0]
        if not np.isnan(r):
            per_group[g] = r
    return macro_average(per_group), len(per_group)


def main():
    df = load_all()
    print(f"Macro Spearman rho of Knuth probing ({N_PROBES} probes per state), population P55, by random seed.")
    print("The seed of the main analysis is", SEED, "\n")
    print(f"{'seed':>6}{'macro rho':>12}{'groups':>8}")
    vals = []
    for s in SEEDS:
        m, n = macro_rho(df, s)
        vals.append(m)
        print(f"{s:>6}{m:>12.3f}{n:>8}", flush=True)
    other = np.array(vals[1:])
    print(f"\nTen other seeds: min {other.min():.3f}, max {other.max():.3f}, mean {other.mean():.3f}, standard deviation {other.std(ddof=1):.3f}")


if __name__ == "__main__":
    main()
