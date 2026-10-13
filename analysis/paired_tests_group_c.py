"""Paired per-group significance checks on the fair-comparison population (Group-C-eligible groups). Reuses the analysis pipeline functions,
nothing reimplemented:
  * M6-RF (max_features="sqrt", n_estimators=200, seed 42) and M6 linear vs Group C
  * Knuth probing (30 probes, seed 42, fit_knuth_probing_baseline's own walk) vs Group C
Two-sided Wilcoxon signed-rank test on per-group rho; wins/losses use the |delta rho| > 0.05 tie threshold used throughout the paper.

Usage: python paired_tests_group_c.py"""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, spearmanr
from sklearn.ensemble import RandomForestRegressor
from models_m1_to_m5 import load_all, run_lopo, rank_biserial  
from fit_hybrid_model import attach_group_c_predictions, eligible_groups, M6_FEATURES, group_c_rho_on  
import fit_knuth_probing_baseline as kb  

df = load_all()
nl = df[df["isEndStateAtEntry"] == False].copy()  
nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
nl, _ = attach_group_c_predictions(nl)
scored = nl.dropna(subset=["groupC_pred"])
elig = eligible_groups(scored)
sub = scored[scored.program_group.isin(elig)]
_, _, gc = group_c_rho_on(sub)

rf = lambda: RandomForestRegressor(n_estimators=200, max_depth=None, min_samples_leaf=1,
                                   max_features="sqrt", random_state=42)
m6 = run_lopo(sub, elig, M6_FEATURES, model_factory=rf)["per_group_rho"]
m6_lin = run_lopo(sub, elig, M6_FEATURES)["per_group_rho"]  # default linear regression

rng = np.random.default_rng(kb.SEED)
rows = []
for program, prog_df in df.groupby("program"):
    actuals, pred, _ = kb.knuth_probe_predictions(prog_df, rng)
    g = prog_df["program_group"].iloc[0]
    rows += [(g, a, p) for a, p in zip(actuals, pred)]
kd = pd.DataFrame(rows, columns=["program_group", "actual", "pred"])
kn = {g: spearmanr(s.actual, s.pred)[0] for g, s in kd.groupby("program_group")
      if len(s) >= 5 and s.actual.nunique() > 1 and s.pred.nunique() > 1}

for name, pg in [("M6-RF", m6), ("M6 linear", m6_lin), ("Knuth 30-probe", kn)]:
    common = sorted(set(pg) & set(gc))
    a = np.array([pg[g] for g in common]); b = np.array([gc[g] for g in common]); d = a - b
    r_rb = rank_biserial(a, b)
    print(f"{name} vs Group C: n={len(common)} macro {a.mean():.3f} vs {b.mean():.3f}, "
          f"median diff {np.median(d):+.3f}, wins/losses(|d|>0.05) {(d>0.05).sum()}/{(d<-0.05).sum()}, "
          f"Wilcoxon p={wilcoxon(a, b).pvalue:.4f}, rank-biserial r={r_rb:+.2f}")
    print("  sorted per-group diffs:", np.round(np.sort(d), 2))
    boot = np.random.default_rng(42).choice(d, (2000, len(d))).mean(axis=1)  # no equivalence test, only an interval for the mean difference
    print(f"  mean per-group difference {d.mean():+.3f}, 95% bootstrap interval over groups [{np.percentile(boot, 2.5):+.2f}, {np.percentile(boot, 97.5):+.2f}]")
