"""Static lookahead features for COASTAL trees: a faithful Python port of jpf-symbc's StaticLookahead.compute()
(intraprocedural CFG reachability from a program counter), working on `javap -c -p` disassembly.

Instruction numbering: COASTAL's `instr` is a 1-based global counter over the instrumented classes' instructions in
class-file order, main class first, then any nested classes (checked on BranchTree4 against javap: branches at 5,7,9,11).

Deliberate, documented deviation: JPF's IfInstruction.isBackJump() is `conditionValue && targetPosition <= position`,
where conditionValue is RUNTIME state of the instruction object (direction taken the last time it executed), so JPF's
"reachable loop back-edge count" is history dependent for conditional back-jumps. This port offers two variants:
  back_if=False : count only GOTO/GOTO_W back-jumps (the deterministic part of JPF's definition)
  back_if=True  : also count conditional back-jumps statically
engines/validate_static.py measures which one agrees better with JPF's logged values.
"""
import os
import re
import shutil
import subprocess

# javap of the JDK on PATH; set the environment variable JAVAP to use another one
JAVAP = os.environ.get("JAVAP") or shutil.which("javap") or "javap"
IFS = {"ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle", "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpge", "if_icmpgt",
       "if_icmple", "if_acmpeq", "if_acmpne", "ifnull", "ifnonnull"}
GOTOS = {"goto", "goto_w"}
SWITCH = {"tableswitch", "lookupswitch"}
RETURNS = {"ireturn", "lreturn", "freturn", "dreturn", "areturn", "return"}
VIRT = {"invokevirtual", "invokeinterface"}
ALLOC = {"new", "newarray", "anewarray", "multianewarray"}

_INSN = re.compile(r"^\s+(\d+):\s+([a-z_0-9]+)(.*)$")
_CASE = re.compile(r"^\s+(default|-?\d+):\s+(\d+)\s*$")


def parse_class(bin_dir, cls):
    out = subprocess.run([JAVAP, "-c", "-p", "-cp", bin_dir, cls], capture_output=True, text=True).stdout
    methods, cur, in_switch, sw_targets = [], None, False, []
    for line in out.splitlines():
        if line.strip() == "Code:":
            cur = []
            methods.append(cur)
            continue
        if cur is None:
            continue
        if in_switch:
            if line.strip() == "}":
                cur[-1]["targets"] = sw_targets
                in_switch = False
                continue
            m = _CASE.match(line)
            if m:
                sw_targets.append(int(m.group(2)))
            continue
        m = _INSN.match(line)
        if not m:
            continue
        off, op, rest = int(m.group(1)), m.group(2), m.group(3)
        rec = {"off": off, "op": op, "targets": []}
        if op in IFS or op in GOTOS:
            rec["targets"] = [int(rest.split("//")[0].split()[0])]
        elif op in SWITCH:
            in_switch, sw_targets = True, []
        cur.append(rec)
    return methods


class ProgramStatics:
    def __init__(self, bin_dir, main_class):
        classes = [main_class] + sorted(
            f[:-6] for f in os.listdir(bin_dir) if f.endswith(".class") and f[:-6] != main_class)
        self.methods, self.index_of = [], {}
        counter = 0
        for c in classes:
            for insns in parse_class(bin_dir, c):
                m_id = len(self.methods)
                self.methods.append(insns)
                for i in range(len(insns)):
                    counter += 1
                    self.index_of[counter] = (m_id, i)
        self._cache = {}

    def features(self, instr, back_if=False):
        """(remaining, branches, backEdges, virtualCalls, allocSites, athrows) at global instruction `instr`;
        all -1 when instr < 0 (no program counter, e.g. a leaf) or unknown."""
        if instr is None or instr < 0 or instr not in self.index_of:
            return (-1,) * 6
        key = (instr, back_if)
        if key in self._cache:
            return self._cache[key]
        m_id, start = self.index_of[instr]
        res = self._compute(self.methods[m_id], start, back_if)
        self._cache[key] = res
        return res

    @staticmethod
    def _compute(insns, start, back_if):
        n = len(insns)
        idx_of_off = {r["off"]: i for i, r in enumerate(insns)}

        def targets(i):
            return [idx_of_off[o] for o in insns[i]["targets"] if o in idx_of_off]

        def ends_uncond(r):
            return r["op"] in GOTOS or r["op"] in RETURNS or r["op"] == "athrow" or r["op"] in SWITCH

        starts = {0}
        for i, r in enumerate(insns):
            starts.update(targets(i))
            if ends_uncond(r) or r["op"] in IFS:
                if i + 1 < n:
                    starts.add(i + 1)
        blocks, block_of = [], [0] * n
        for i in range(n):
            if i in starts:
                blocks.append([i, i, []])
            blocks[-1][1] = i
            block_of[i] = len(blocks) - 1
        for b in blocks:
            last = insns[b[1]]
            if not ends_uncond(last) and b[1] + 1 < n:
                b[2].append(block_of[b[1] + 1])
            for t in targets(b[1]):
                b[2].append(block_of[t])
        seen, queue = {block_of[start]}, [block_of[start]]
        while queue:
            for s in blocks[queue.pop()][2]:
                if s not in seen:
                    seen.add(s)
                    queue.append(s)
        rem = br = be = vc = al = at = 0
        for bi in sorted(seen):
            for i in range(blocks[bi][0], blocks[bi][1] + 1):
                if bi == block_of[start] and i < start:
                    continue
                r = insns[i]
                rem += 1
                if r["op"] in IFS or r["op"] in GOTOS or r["op"] in SWITCH:
                    br += 1
                if r["op"] in GOTOS and r["targets"] and r["targets"][0] <= r["off"]:
                    be += 1
                elif back_if and r["op"] in IFS and r["targets"] and r["targets"][0] <= r["off"]:
                    be += 1
                if r["op"] in VIRT:
                    vc += 1
                if r["op"] in ALLOC:
                    al += 1
                if r["op"] == "athrow":
                    at += 1
        return (rem, br, be, vc, al, at)
