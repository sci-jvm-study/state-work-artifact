"""Nesting decomposition of the live-count correlation (see nesting_decomposition_predeclared.md, written before this script was run).

Per configuration, over all pairs of non-leaf states (a, b) with stateId(a) < stateId(b): the pair is NESTED if a is an ancestor of b, else
NON-NESTED. For (state id, work) a pair is concordant if work(a) < work(b), discordant if work(a) > work(b), tied if equal. Kendall tau-a =
(C - D) / (C + D + T) splits exactly into the two classes. Counts are summed over the configurations of a program group. The same split is
computed for (hindsight subtree size N, work), where a pair is concordant when N and work order the two states the same way.

Usage: python nesting_decomposition.py"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models_m1_to_m5 import load_all, MIN_ROWS_FOR_GROUP_RHO, macro_average  
from floor_by_cost_measure import subtree_sizes  


def counts(order_key, W, nested):
    """order_key, W: arrays over the non-leaf states sorted by stateId; nested[i, j] True if i is an ancestor of j (i < j).
    Returns dict with C, D, T for nested and non-nested pairs of (order_key, W)."""
    n = len(W)
    iu = np.triu_indices(n, k=1)
    a, b = iu
    if order_key is None:  # live count: earlier id vs later id
        s = np.sign(W[b] - W[a])
    else:  # hindsight: sign agreement between key and work
        s = np.sign(order_key[b] - order_key[a]) * np.sign(W[b] - W[a])
        tie_key = order_key[b] == order_key[a]
    nest = nested[a, b]
    out = {}
    for name, m in (("nested", nest), ("other", ~nest)):
        ss = s[m]
        out[name] = (int((ss > 0).sum()), int((ss < 0).sum()), int((ss == 0).sum()))
    return out


def main():
    df = load_all().sort_values(["program", "stateId"])
    rows = []
    tot = {}
    for prog, d in df.groupby("program"):
        g = d["program_group"].iloc[0]
        d = d.reset_index(drop=True)
        size_all = pd.Series(subtree_sizes(d), index=d.index)
        nlmask = ~d["isEndStateAtEntry"].astype(str).str.lower().eq("true")
        n_l = d[nlmask]
        ids = n_l["stateId"].to_numpy()
        if len(ids) < 2:
            continue
        pos = {int(i): k for k, i in enumerate(ids)}
        par = dict(zip(d["stateId"], d["parentId"]))
        nested = np.zeros((len(ids), len(ids)), dtype=bool)
        for j, sid in enumerate(ids):
            a = par[sid]
            while a in par:
                if a in pos:
                    nested[pos[a], j] = True
                a = par[a]
        W = n_l["actualSubtreeWork"].to_numpy(dtype=float)
        N = size_all[nlmask].to_numpy(dtype=float)
        live = counts(None, W, nested)
        hind = counts(N, W, nested)
        key = g
        acc = tot.setdefault(key, {"live": {"nested": np.zeros(3), "other": np.zeros(3)}, "hind": {"nested": np.zeros(3), "other": np.zeros(3)}, "n": 0})
        for k in ("nested", "other"):
            acc["live"][k] += np.array(live[k])
            acc["hind"][k] += np.array(hind[k])
        acc["n"] += len(ids)

    # paper's group rho of the live count (rows of all configurations pooled), for the check H5
    nl = df[~df["isEndStateAtEntry"].astype(str).str.lower().eq("true")]
    paper_rho = {}
    for g, s in nl.groupby("program_group"):
        if len(s) >= MIN_ROWS_FOR_GROUP_RHO and s["actualSubtreeWork"].nunique() > 1:
            paper_rho[g] = spearmanr(s["stateId"], s["actualSubtreeWork"])[0]

    recs = []
    for g in paper_rho:
        a = tot[g]
        ln, lo = a["live"]["nested"], a["live"]["other"]
        hn, ho = a["hind"]["nested"], a["hind"]["other"]
        Nn, No = ln.sum(), lo.sum()
        tau = lambda c: (c[0] - c[1]) / c.sum() if c.sum() else np.nan
        recs.append({"group": g, "nonleaf": a["n"], "share_nested": Nn / (Nn + No), "tie_in_nested": ln[2] / Nn if Nn else np.nan,
                     "live_concordant_nested": int(ln[0]),
                     "tau_all": tau(ln + lo), "tau_nested": tau(ln), "tau_other": tau(lo),
                     "contrib_nested": (ln[0] - ln[1]) / (Nn + No), "contrib_other": (lo[0] - lo[1]) / (Nn + No),
                     "h_tau_nested": tau(hn), "h_discordant_nested": int(hn[1]), "h_tau_other": tau(ho), "rho_paper": paper_rho[g]})
    R = pd.DataFrame(recs).sort_values("tau_all")
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 100)
    print(f"scoreable groups: {len(R)}\n")
    show = ["group", "nonleaf", "share_nested", "tie_in_nested", "tau_all", "tau_nested", "tau_other", "h_tau_nested", "h_tau_other", "rho_paper"]
    print(R[show].round(2).to_string(index=False))
    print("\nMacro over groups (mean of the group values):")
    for c in ("share_nested", "tie_in_nested", "tau_all", "contrib_nested", "contrib_other", "tau_nested", "tau_other", "h_tau_nested", "h_tau_other", "rho_paper"):
        print(f"  {c:<16} {R[c].mean():+.3f}   (median {R[c].median():+.3f})")
    print(f"\nLive count against work (rho_paper), per group: negative in {int((R['rho_paper'] < 0).sum())} of {len(R)} groups, at or below -0.5 in {int((R['rho_paper'] <= -0.5).sum())}, highest value {R['rho_paper'].max():+.3f}")
    print("\nHypotheses (predeclared):")
    h1 = int(R["live_concordant_nested"].sum())
    print(f"  H1 concordant nested pairs for (state id, work): {h1} -> {'holds' if h1 == 0 else 'FAILS'}")
    r2 = spearmanr(R["share_nested"], -R["tau_all"])[0]
    print(f"  H2 Spearman(share of nested pairs, -tau_all) = {r2:+.2f} -> {'holds' if r2 >= 0.6 else 'FAILS'} (>= 0.6)")
    m3 = R["tau_other"].mean()
    print(f"  H3 macro tau-a of non-nested pairs = {m3:+.3f} -> {'holds' if abs(m3) <= 0.15 else 'FAILS'} (within +-0.15)")
    h4d = int(R["h_discordant_nested"].sum())
    m4 = R["h_tau_other"].mean()
    print(f"  H4 discordant nested pairs for (hindsight size, work): {h4d}; macro tau-a on non-nested pairs {m4:+.3f} -> "
          f"{'holds' if (h4d == 0 and m4 >= 0.5) else 'FAILS'}")
    r5 = spearmanr(R["tau_all"], R["rho_paper"])[0]
    print(f"  H5 Spearman(tau_all, paper group rho) = {r5:+.3f} -> {'holds' if r5 >= 0.9 else 'FAILS'} (>= 0.9)")
    print("\nBy tree size, POST HOC (bands chosen after seeing the data, not predeclared): macro over groups by number of non-leaf states")
    print(f"  Spearman(non-leaf states, tau_all) = {spearmanr(R['nonleaf'], R['tau_all'])[0]:+.2f}; Spearman(non-leaf states, share of nested pairs) = {spearmanr(R['nonleaf'], R['share_nested'])[0]:+.2f}")
    for lo, hi in [(0, 15), (15, 60), (60, 300), (300, 10 ** 6)]:
        b = R[(R["nonleaf"] >= lo) & (R["nonleaf"] < hi)]
        print(f"  non-leaf states in [{lo}, {hi if hi < 10 ** 6 else 'inf'}): groups {len(b):>2}, macro tau_all {b['tau_all'].mean():+.3f}, macro rho of the count {b['rho_paper'].mean():+.3f}")
    top = R.sort_values("nonleaf", ascending=False).head(10)
    print(f"  10 largest groups: tau_all from {top['tau_all'].min():+.3f} to {top['tau_all'].max():+.3f}, macro rho {top['rho_paper'].mean():+.3f}")
    print("\nGroups where non-nested pairs alone are clearly positive (tau_other > 0.15) or negative (< -0.15):")
    print("  positive:", ", ".join(f"{g} ({t:+.2f})" for g, t in zip(R.group, R.tau_other) if t > 0.15) or "none")
    print("  negative:", ", ".join(f"{g} ({t:+.2f})" for g, t in zip(R.group, R.tau_other) if t < -0.15) or "none")
    print(f"\nGroups with tau_all > 0 (live count positive): {int((R.tau_all > 0).sum())} of {len(R)}; with positive tau_other: {int((R.tau_other > 0).sum())}")
    R.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "44_nesting_decomposition_groups.csv"), index=False)


if __name__ == "__main__":
    main()
