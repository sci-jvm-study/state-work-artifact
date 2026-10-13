"""Cross-engine check of two JPF-derived results on the same programs and the same protocol, for JPF, COASTAL and GDart:
  (1) Knuth probing's live cost: counterfactual cost of 30 probes (and 1 probe) as a fraction of the state's own subtree work,
      and its rank accuracy (same construction as fit_knuth_online_cost_analysis.py);
  (2) online capping of Random Forest predictions at the parent's already-capped prediction (variant A of nesting_consistency.py),
      against the raw predictions, for M3 (dynamic features; available on all three engines) and, where static features exist
      (JPF, COASTAL), M5 (static + dynamic).
Programs: those whose COASTAL trees have JPF's node count in both search orders and whose GDart trees have it too. Models are
fitted leave-one-program-group-out on these programs only (not on the 66-group main corpus). GDart work is the full-run count
(as in results/27). COASTAL static features need engines/compile_bins.py to have been run.

Usage: python cross_engine_cost_and_cap.py"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross_engine_replication as cer
from models_m1_to_m5 import MIN_ROWS_FOR_GROUP_RHO, macro_average, bootstrap_macro_ci, FEATURE_GROUPS
from fit_hybrid_model import make_rf_factory
from fit_knuth_online_cost_analysis import own_step_cost_map

SEED = 42
PROBES = (1, 30)
M3 = FEATURE_GROUPS["M3_dynamic_only"]
M5 = FEATURE_GROUPS["M5_static_plus_dynamic"]


def group_rhos(df, col):
    out = {}
    for g, s in df.groupby("program_group"):
        if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s["actual"].nunique() > 1 and s[col].nunique() > 1:
            out[g] = spearmanr(s["actual"], s[col])[0]
    return out


def knuth(df):
    rng = np.random.default_rng(SEED)
    rows = []
    for _, prog_df in df.groupby("program"):
        by_id, children, own_cost = own_step_cost_map(prog_df)
        group = prog_df["program_group"].iloc[0]
        for sid, row in by_id.items():
            if row["isEndStateAtEntry"]:
                continue
            est_sum = cost_sum = 0.0
            rec = {"program_group": group, "actual": row["actualSubtreeWork"]}
            for i in range(1, max(PROBES) + 1):
                cur, cum, prod, cost = sid, 0.0, 1.0, own_cost[sid]
                while children.get(cur):
                    kids = children[cur]
                    prod *= len(kids)
                    cum += prod
                    cur = kids[rng.integers(0, len(kids))]
                    cost += own_cost[cur]
                est_sum += cum
                cost_sum += cost
                if i in PROBES:
                    rec[f"pred{i}"] = est_sum / i
                    rec[f"cost{i}"] = cost_sum
            rows.append(rec)
    return pd.DataFrame(rows)


def cap(df, features):
    nl = df[df["isEndStateAtEntry"] == False].copy()  
    nl["logWork"] = np.log1p(nl["actualSubtreeWork"])
    raw = pd.Series(index=nl.index, dtype=float)
    for g in nl["program_group"].unique():
        tr, te = nl[nl["program_group"] != g], nl[nl["program_group"] == g]
        m = make_rf_factory(n_estimators=200, max_depth=None, min_samples_leaf=1, max_features="sqrt")()
        m.fit(tr[features].values, tr["logWork"].values)
        raw.loc[te.index] = m.predict(te[features].values)
    nl["raw"] = np.expm1(raw)
    nl["capped"] = np.nan
    for _, d in nl.groupby("program"):
        parent = dict(zip(d["stateId"], d["parentId"]))
        rw = dict(zip(d["stateId"], d["raw"]))
        capped = {}
        for sid in d.sort_values(["depth", "stateId"])["stateId"]:
            p = parent[sid]
            capped[sid] = min(rw[sid], capped[p]) if p in capped else rw[sid]
        nl.loc[d.index, "capped"] = [capped[s] for s in d["stateId"]]
    nl["actual"] = nl["actualSubtreeWork"]
    return nl


def report(label, df, models):
    print(f"--- {label} ---")
    k = knuth(df)
    for n in PROBES:
        res = group_rhos(k, f"pred{n}")
        pct = (100.0 * k[f"cost{n}"] / k["actual"]).replace([np.inf, -np.inf], np.nan).dropna()
        lo, hi = bootstrap_macro_ci(res)
        print(f"Knuth {n:>2} probe(s): macro rho {macro_average(res):+.3f} [{lo:+.3f}, {hi:+.3f}] over {len(res)} groups; "
              f"over the {len(pct)} of {len(k)} states with non-zero work: median live cost {pct.median():.0f}% of the state's own subtree work, "
              f"{100.0 * (pct > 100).mean():.1f}% of them cost more than exploring them fully")
    for name, feats in models:
        nl = cap(df, feats)
        raw, capped = group_rhos(nl, "raw"), group_rhos(nl, "capped")
        common = [g for g in raw if g in capped]
        diff = np.array([capped[g] - raw[g] for g in common])
        print(f"{name} RF: raw macro rho {macro_average(raw):+.3f} over {len(raw)} groups, capped {macro_average(capped):+.3f} over {len(capped)}; "
              f"on the {len(common)} groups both score: raw {macro_average({g: raw[g] for g in common}):+.3f} -> capped "
              f"{macro_average({g: capped[g] for g in common}):+.3f}; better by > 0.05 in {int((diff > 0.05).sum())}, "
              f"worse by > 0.05 in {int((diff < -0.05).sum())}")
    print()


def exact_programs(name):
    st = pd.read_csv(os.path.join(cer.ROOT, "engines", "run_status_" + name + ".csv"))
    return set(st[(st["status"] == "clean") & (st["nodes"] == st["jpf_states"])]["program"])


if __name__ == "__main__":
    programs = exact_programs("data_coastal2") & exact_programs("data_coastal2_BF") & exact_programs("data_gdart")
    print(f"{len(programs)} programs with JPF's node count on COASTAL (both orders) and on GDart\n")
    jpf = cer.load(cer.JPF_DIR, programs)
    coa = cer.load(os.path.join(cer.ROOT, "engines", "data", "data_coastal2"), programs, coastal=True)
    gd = cer.add_jpf_log_columns(cer.load(os.path.join(cer.ROOT, "engines", "data", "data_gdart"), programs))
    gd["threadCount"] = 1
    gd["actualSubtreeWork"] = gd["actualFullRunWork"]
    report("JPF", jpf, [("M3", M3), ("M5", M5)])
    report("COASTAL (depth-first)", coa, [("M3", M3), ("M5", M5)])
    report("GDart (work = full run; no static features, so M3 only)", gd, [("M3", M3)])
