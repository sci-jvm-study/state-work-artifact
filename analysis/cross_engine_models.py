"""
Cross-engine replication of the paper's learned models, leave-one-program-out (LOPO), on the SAME programs
in JPF and COASTAL, with the paper's own feature lists and code paths (run_lopo, attach_group_c_predictions,
eligible_groups, FEATURE_GROUPS, tuned Random Forest: n_estimators=200, max_features="sqrt", seed 42, NOT re-tuned):

  M1 depth | M2 static | M3 dynamic | M5 static+dynamic (linear and RF) | M6 = M5 + Group C prediction (linear and RF)
  Gated  = M6-RF where the history feature exists (eligible groups), else the M5-RF fallback trained on the mixed pool
           (the paper's coverage-aware combination, same construction as fit_hybrid_model.full_corpus_gated_evaluation)

COASTAL columns: pathConditionSize = branch-conjunct count; choiceGeneratorTotal/Processed = sibling count and rank;
static features = port of jpf-symbc StaticLookahead evaluated at the node's program counter (engines/static_features.py,
validated against JPF's logged values by engines/validate_static.py); threadCount = 1 (as in JPF's non-leaf rows).

Usage: python cross_engine_models.py [--coastal data_coastal2|data_coastal2_BF] [--subset exact|all] [--back-if]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from scipy.stats import wilcoxon

sys.path.insert(0, os.path.dirname(__file__))
import cross_engine_replication as cer
from models_m1_to_m5 import run_lopo, macro_average, bootstrap_macro_ci, FEATURE_GROUPS, rank_biserial
from fit_hybrid_model import attach_group_c_predictions, eligible_groups

M1 = FEATURE_GROUPS["M1_depth_only"]
M2 = FEATURE_GROUPS["M2_static_only"]
M3 = FEATURE_GROUPS["M3_dynamic_only"]
M5 = FEATURE_GROUPS["M5_static_plus_dynamic"]
M6 = M5 + ["groupC_pred"]


def rf():
    return RandomForestRegressor(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt", random_state=42)


def evaluate(df):
    nl = df[df["isEndStateAtEntry"] == False].copy()
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    groups = sorted(nl["program_group"].unique())
    out = {}
    out["M1 depth"] = run_lopo(nl, groups, M1, model_factory=LinearRegression)["per_group_rho"]
    out["M2 static"] = run_lopo(nl, groups, M2, model_factory=LinearRegression)["per_group_rho"]
    out["M3 dynamic"] = run_lopo(nl, groups, M3, model_factory=LinearRegression)["per_group_rho"]
    out["M5 static+dynamic"] = run_lopo(nl, groups, M5, model_factory=LinearRegression)["per_group_rho"]
    m5rf = run_lopo(nl, groups, M5, model_factory=rf)["per_group_rho"]
    out["M5-RF"] = m5rf
    nl2, _ = attach_group_c_predictions(nl)
    scored = nl2.dropna(subset=["groupC_pred"]).copy()
    elig = eligible_groups(scored)
    sub = scored[scored["program_group"].isin(elig)]
    out["M6 linear"] = run_lopo(sub, elig, M6, model_factory=LinearRegression)["per_group_rho"]
    m6rf = run_lopo(sub, elig, M6, model_factory=rf)["per_group_rho"]
    out["M6-RF"] = m6rf
    gated = dict(m6rf)
    for g, r in m5rf.items():
        if g not in elig:
            gated[g] = r
    out["Gated M6-RF/M5-RF"] = gated
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--coastal", default="data_coastal2")
    ap.add_argument("--subset", default="exact", choices=["all", "exact"])
    ap.add_argument("--also", default=None, help="second tree set (e.g. data_coastal2_BF): keep only programs that are also clean and exact there")
    a = ap.parse_args()
    st = pd.read_csv(os.path.join(cer.ROOT, "engines", "run_status_" + a.coastal + ".csv"))
    clean = st[st["status"] == "clean"]
    if a.subset == "exact":
        clean = clean[clean["nodes"] == clean["jpf_states"]]
    programs = set(clean["program"])
    if a.also:
        st2 = pd.read_csv(os.path.join(cer.ROOT, "engines", "run_status_" + a.also + ".csv"))
        c2 = st2[st2["status"] == "clean"]
        if a.subset == "exact":
            c2 = c2[c2["nodes"] == c2["jpf_states"]]
        programs &= set(c2["program"])
    jpf = cer.load(cer.JPF_DIR, programs)
    coa = cer.load(os.path.join(cer.ROOT, "engines", "data", a.coastal), programs, coastal=True)
    print(f"{len(programs)} programs ({a.subset} tree-size agreement), COASTAL data = {a.coastal}\n")
    rj, rc = evaluate(jpf), evaluate(coa)
    print(f"{'model':<22}{'JPF (own groups)':>20}{'COASTAL (own groups)':>24}   | same groups: n, JPF, COASTAL, Wilcoxon p")
    for m in rj:
        mj, mc = macro_average(rj[m]), macro_average(rc[m])
        shared = sorted(set(rj[m]) & set(rc[m]))
        aj = {g: rj[m][g] for g in shared}
        ac = {g: rc[m][g] for g in shared}
        d = np.array([aj[g] - ac[g] for g in shared])
        pw = wilcoxon(d).pvalue if len(d) >= 5 and np.any(d != 0) else float("nan")
        rrb = rank_biserial(np.array([aj[g] for g in shared]), np.array([ac[g] for g in shared])) if len(shared) >= 1 else float("nan")
        print(f"{m:<22}{mj:>10.3f} (n={len(rj[m]):>2}){mc:>14.3f} (n={len(rc[m]):>2})   | {len(shared):>2}  "
              f"{macro_average(aj):7.4f}  {macro_average(ac):7.4f}  p={pw:.3f}  r={rrb:+.3f}")
