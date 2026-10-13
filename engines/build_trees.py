"""Turns each engines/runs/<Program>/coastal_runs.csv (one row per concrete COASTAL execution) into a
state-tree CSV with the same columns the JPF analysis code reads, under engines/data/<COASTAL_OUTNAME>/<category>/<Program>.csv.

Tree definition (matches how a symbolic-execution tree is drawn for JPF's choice-generator states):
  * a node is a distinct PREFIX of branch decisions; the root is the empty prefix (program start)
  * a child extends its parent by one decision (branch identity = conjunct string + '#' + alternative taken,
    as logged by the patched SymbolicState)
  * a node is a leaf when a run ends exactly there (isEndStateAtEntry = True)
  * stateId = order in which a node is FIRST reached while replaying the runs in execution order, root to leaf
    (the analogue of JPF's visitation order)

Work definitions (instructions = instrumented bytecode instructions executed by the concrete run):
  * actualSubtreeWork(v) = sum over runs r through v of (total_r - cumInstr_r at v's deciding branch); for the
    root that is total_r. This is the work done from the moment v is entered to the end of each run through it,
    the counterpart of JPF's entry/exit counter delta (prefix re-execution NOT counted).
  * actualFullRunWork(v) = sum over runs through v of total_r (re-executed prefix counted), reported as an
    alternative, since a concolic engine really does re-execute the prefix in every run.
"""
import os
import sys
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RUNROOT = os.environ.get("COASTAL_RUNROOT", "runs")
OUTNAME = os.environ.get("COASTAL_OUTNAME", "data_coastal")
CATS = ["synthetic", "real-world", "sv-comp"]


def run_status(prog):
    """clean / unimplemented-instruction / other-problem, from COASTAL's own console output."""
    out = os.path.join(ROOT, "engines", RUNROOT, prog, "out.txt")
    if not os.path.exists(out):
        return "no-output"
    txt = open(out, encoding="utf-8", errors="replace").read()
    if "UNIMPLEMENTED INSTRUCTION" in txt:
        m = [l for l in txt.splitlines() if "UNIMPLEMENTED INSTRUCTION" in l][0]
        return "unimplemented:" + m.split("(")[-1].split(")")[0].replace("opcode: ", "op")
    if "COASTAL DONE" not in txt:
        return "not-finished"
    if "aborted: 0" not in txt:
        return "aborted-runs"
    return "clean"


def parse_run(line):
    run_id, total, rest = line.rstrip("\n").split(",", 2)
    branches = []
    for tok in rest.split("\t"):
        if not tok:
            continue
        parts = tok.rsplit("@", 2)
        if len(parts) == 3 and parts[1].lstrip("-").isdigit() and parts[2].lstrip("-").isdigit():
            ident, cum, ins = parts[0], int(parts[1]), int(parts[2])
        else:
            ident, cum = tok.rsplit("@", 1)
            cum, ins = int(cum), -1
        branches.append((ident, cum, ins))
    return int(run_id), int(total), branches


def compress(df):
    """Collapse forced (single-feasible-child) decisions so a node is a genuine choice outcome, like a JPF
    choice-generator state: kept nodes = root + every child of a node with >=2 children. A kept node's
    compressed parent is the kept node whose unary chain contains the branching node it hangs from. Work columns
    are those of the kept node itself (its own deciding branch), unchanged."""
    kids = {}
    for r in df.itertuples():
        kids.setdefault(r.parentId, []).append(r.stateId)
    row = {r.stateId: r for r in df.itertuples()}
    keep = {0}
    def chain_pc(nid):
        cur = nid
        while True:
            ks = kids.get(cur, [])
            if len(ks) == 0:
                return -1
            if len(ks) >= 2:
                return int(row[cur].childInstr)
            cur = ks[0]
    for nid, ks in kids.items():
        if nid != -1 and len(ks) >= 2:
            keep.update(ks)
    head = {0: 0}
    for r in df.itertuples():  # parents always have smaller stateId, so one pass suffices
        if r.stateId == 0:
            continue
        head[r.stateId] = r.stateId if r.stateId in keep else head[r.parentId]
    order = sorted(keep)
    new_id = {nid: i for i, nid in enumerate(order)}
    ckids = {}
    out = []
    for nid in order:
        r = row[nid]
        cp = -1 if nid == 0 else new_id[head[r.parentId]]
        out.append({"stateId": new_id[nid], "parentId": cp, "actualSubtreeWork": r.actualSubtreeWork,
                    "actualFullRunWork": r.actualFullRunWork, "pathConditionSize": r.depth,
                    "pcInstrNext": int(r.childInstr) if kids.get(nid) else -1, "pcInstrChain": chain_pc(nid)})
        ckids.setdefault(cp, []).append(new_id[nid])
    res = pd.DataFrame(out)
    dep = {}
    for r in res.itertuples():
        dep[r.stateId] = 0 if r.parentId == -1 else dep[r.parentId] + 1
    res["depth"] = res.stateId.map(dep)
    # leaf = kept node whose unary chain ends in a run end, i.e. it has no compressed children
    res["isEndStateAtEntry"] = res.stateId.map(lambda s: s not in ckids)
    return res[["stateId", "parentId", "depth", "actualSubtreeWork", "actualFullRunWork", "pathConditionSize",
                "pcInstrNext", "pcInstrChain", "isEndStateAtEntry"]]


def build(csv_path):
    runs = [parse_run(l) for l in open(csv_path, encoding="utf-8", errors="replace") if l.strip()]
    runs.sort(key=lambda r: r[0])
    node_id = {(): 0}
    parent = {0: -1}
    depth = {0: 0}
    sub_work = {0: 0}
    full_work = {0: 0}
    children = {0: set()}
    is_leaf_end = set()
    child_instr = {}
    for _, total, branches in runs:
        prefix = ()
        cums = [0] + [c for _, c, _ in branches]
        for k in range(len(branches) + 1):
            if k > 0:
                new = prefix + (branches[k - 1][0],)
                child_instr.setdefault(node_id[prefix], branches[k - 1][2])
                if new not in node_id:
                    nid = len(node_id)
                    node_id[new] = nid
                    parent[nid] = node_id[prefix]
                    depth[nid] = k
                    sub_work[nid] = 0
                    full_work[nid] = 0
                    children[nid] = set()
                children[node_id[prefix]].add(node_id[new])
                prefix = new
            nid = node_id[prefix]
            sub_work[nid] += total - cums[k]
            full_work[nid] += total
        is_leaf_end.add(node_id[prefix])
    rows = []
    for nid in range(len(node_id)):
        rows.append({
            "stateId": nid, "parentId": parent[nid], "depth": depth[nid],
            "actualSubtreeWork": sub_work[nid], "actualFullRunWork": full_work[nid],
            "isEndStateAtEntry": len(children[nid]) == 0,
            "childInstr": child_instr.get(nid, -1),
        })
    return pd.DataFrame(rows), len(runs)


if __name__ == "__main__":
    out_root = os.path.join(ROOT, "engines", "data", OUTNAME)
    summary = []
    for cat in CATS:
        for prog_csv in sorted(os.listdir(os.path.join(ROOT, "data", cat))):
            prog = prog_csv[:-4]
            run_csv = os.path.join(ROOT, "engines", RUNROOT, prog, "coastal_runs.csv")
            if not os.path.exists(run_csv) or os.path.getsize(run_csv) == 0:
                continue
            raw, nruns = build(run_csv)
            os.makedirs(os.path.join(out_root + "_raw", cat), exist_ok=True)
            raw.to_csv(os.path.join(out_root + "_raw", cat, prog + ".csv"), index=False)
            df = compress(raw)
            os.makedirs(os.path.join(out_root, cat), exist_ok=True)
            df.to_csv(os.path.join(out_root, cat, prog + ".csv"), index=False)
            jpf_rows = sum(1 for _ in open(os.path.join(ROOT, "data", cat, prog_csv))) - 1
            summary.append((cat, prog, nruns, len(df), int((~df.isEndStateAtEntry).sum()), jpf_rows, run_status(prog)))
    print(f"{'category':<11}{'program':<30}{'runs':>6}{'nodes':>7}{'nonleaf':>8}{'JPF_states':>11}  status")
    for s in summary:
        print(f"{s[0]:<11}{s[1]:<30}{s[2]:>6}{s[3]:>7}{s[4]:>8}{s[5]:>11}  {s[6]}")
    pd.DataFrame(summary, columns=["category", "program", "runs", "nodes", "nonleaf", "jpf_states", "status"]).to_csv(
        os.path.join(ROOT, "engines", "run_status_" + OUTNAME + ".csv"), index=False)
    print(len(summary), "programs written to", out_root)
