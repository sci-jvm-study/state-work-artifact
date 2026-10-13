package gov.nasa.jpf.symbc;

import gov.nasa.jpf.jvm.bytecode.ATHROW;
import gov.nasa.jpf.jvm.bytecode.ANEWARRAY;
import gov.nasa.jpf.jvm.bytecode.GOTO;
import gov.nasa.jpf.jvm.bytecode.GOTO_W;
import gov.nasa.jpf.jvm.bytecode.IfInstruction;
import gov.nasa.jpf.jvm.bytecode.INVOKEINTERFACE;
import gov.nasa.jpf.jvm.bytecode.INVOKEVIRTUAL;
import gov.nasa.jpf.jvm.bytecode.JVMReturnInstruction;
import gov.nasa.jpf.jvm.bytecode.MULTIANEWARRAY;
import gov.nasa.jpf.jvm.bytecode.NEW;
import gov.nasa.jpf.jvm.bytecode.NEWARRAY;
import gov.nasa.jpf.jvm.bytecode.SwitchInstruction;
import gov.nasa.jpf.vm.Instruction;
import gov.nasa.jpf.vm.MethodInfo;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.BitSet;
import java.util.Deque;
import java.util.List;

/**
 * Group A: static lookahead features (see the paper's feature definitions section).
 *
 * SCOPE: INTRAPROCEDURAL only -- a control-flow reachability
 * analysis over the CURRENT method's bytecode, from the current program
 * counter forward. Interprocedural reachability (call-graph depth,
 * methods reachable through calls) is NOT implemented -- it requires
 * resolving call targets including virtual dispatch, which is not
 * statically fixed.
 *
 * METHOD: the features are computed on the CONTROL-FLOW GRAPH of the current method. Basic blocks are built, edges are added between
 * them (fallthrough and explicit jump targets), and a forward search starts from the block that contains the current PC. Only the
 * instructions in blocks that are reachable this way are counted, so code of a branch that is no longer reachable (for example the
 * `a<=0` branch after `a>0` was taken) is not counted although it appears later in the instruction order of the method.
 *
 * APIs used below:
 *   - MethodInfo.getInstructions() / getInstructionAt(int position)
 *   - Instruction.getInstructionIndex() / isBackJump()
 *   - IfInstruction.getTarget() / GOTO.getTarget() -- resolved Instruction
 *   - SwitchInstruction.getTarget() (default, raw position) and
 *     getTargets() (case targets, raw positions int[]) -- resolved via
 *     MethodInfo.getInstructionAt(...)
 *   - JVMReturnInstruction -- common superclass of IRETURN/ARETURN/
 *     LRETURN/DRETURN/FRETURN/RETURN, used to detect "no fallthrough"
 **/

public class StaticLookahead {

    public static class Features {
        public final int remainingBytecodesInMethod;
        public final int reachableBranchCount;
        public final int reachableLoopBackEdgeCount;
        public final int reachableVirtualCallCount;
        public final int reachableAllocSiteCount;
        public final int reachableAthrowCount;

        Features(int remainingBytecodesInMethod, int reachableBranchCount,
                 int reachableLoopBackEdgeCount, int reachableVirtualCallCount,
                 int reachableAllocSiteCount, int reachableAthrowCount) {
            this.remainingBytecodesInMethod = remainingBytecodesInMethod;
            this.reachableBranchCount = reachableBranchCount;
            this.reachableLoopBackEdgeCount = reachableLoopBackEdgeCount;
            this.reachableVirtualCallCount = reachableVirtualCallCount;
            this.reachableAllocSiteCount = reachableAllocSiteCount;
            this.reachableAthrowCount = reachableAthrowCount;
        }

        /** Sentinel used when there is no current instruction to analyze (e.g. root/-1 state, or a terminated thread). */
        static Features none() {
            return new Features(-1, -1, -1, -1, -1, -1);
        }
    }

    // ---------------- basic block model ----------------

    private static class Block {
        final int startIdx; // inclusive, index into the method's instruction array
        int endIdx;         // inclusive
        final List<Integer> successorBlockStarts = new ArrayList<>();

        Block(int startIdx) {
            this.startIdx = startIdx;
            this.endIdx = startIdx;
        }
    }

    /** True if this instruction does NOT fall through to the next instruction in program order. */
    private static boolean endsBlockUnconditionally(Instruction insn) {
        return insn instanceof GOTO
                || insn instanceof GOTO_W
                || insn instanceof JVMReturnInstruction
                || insn instanceof ATHROW
                || insn instanceof SwitchInstruction;
    }

    public static Features compute(Instruction currentPC) {
        if (currentPC == null) {
            return Features.none();
        }

        MethodInfo mi = currentPC.getMethodInfo();
        if (mi == null) {
            return Features.none();
        }

        Instruction[] all = mi.getInstructions();
        int startIdx = currentPC.getInstructionIndex();
        if (all == null || startIdx < 0 || startIdx >= all.length) {
            return Features.none();
        }

        // ---- 1. find every instruction index that is a jump target (a basic-block boundary) ----
        BitSet isBlockStart = new BitSet(all.length);
        isBlockStart.set(0);
        for (Instruction insn : all) {
            if (insn == null) continue;
            for (int targetIdx : jumpTargetIndices(insn, mi)) {
                if (targetIdx >= 0 && targetIdx < all.length) {
                    isBlockStart.set(targetIdx);
                }
            }
            if (endsBlockUnconditionally(insn) || insn instanceof IfInstruction) {
                int next = insn.getInstructionIndex() + 1;
                if (next < all.length) {
                    isBlockStart.set(next);
                }
            }
        }

        // ---- 2. carve the instruction array into blocks at those boundaries ----
        List<Block> blocks = new ArrayList<>();
        int[] blockOfIndex = new int[all.length]; // instruction index -> block list index
        Block current = null;
        for (int i = 0; i < all.length; i++) {
            if (isBlockStart.get(i)) {
                current = new Block(i);
                blocks.add(current);
            }
            current.endIdx = i;
            blockOfIndex[i] = blocks.size() - 1;
        }

        // ---- 3. wire up successor edges between blocks ----
        for (int b = 0; b < blocks.size(); b++) {
            Block block = blocks.get(b);
            Instruction last = all[block.endIdx];
            if (last == null) continue;

            boolean noFallthrough = endsBlockUnconditionally(last);
            if (!noFallthrough && block.endIdx + 1 < all.length) {
                block.successorBlockStarts.add(blockOfIndex[block.endIdx + 1]);
            }
            for (int targetIdx : jumpTargetIndices(last, mi)) {
                if (targetIdx >= 0 && targetIdx < all.length) {
                    block.successorBlockStarts.add(blockOfIndex[targetIdx]);
                }
            }
        }

        // ---- 4. forward BFS from the block containing the current PC ----
        BitSet reachableBlocks = new BitSet(blocks.size());
        Deque<Integer> queue = new ArrayDeque<>();
        int startBlock = blockOfIndex[startIdx];
        queue.add(startBlock);
        reachableBlocks.set(startBlock);
        while (!queue.isEmpty()) {
            Block b = blocks.get(queue.poll());
            for (int succ : b.successorBlockStarts) {
                if (!reachableBlocks.get(succ)) {
                    reachableBlocks.set(succ);
                    queue.add(succ);
                }
            }
        }

        // ---- 5. tally features over reachable instructions only ----
        int remaining = 0, branches = 0, backEdges = 0, virtualCalls = 0, allocSites = 0, athrows = 0;
        for (int b = reachableBlocks.nextSetBit(0); b >= 0; b = reachableBlocks.nextSetBit(b + 1)) {
            Block block = blocks.get(b);
            for (int i = block.startIdx; i <= block.endIdx; i++) {
                Instruction insn = all[i];
                if (insn == null) continue;

                // Within the START block, only instructions from startIdx onward count
                // (the block may contain earlier instructions before the current PC).
                if (b == startBlock && i < startIdx) continue;

                remaining++;

                if (insn instanceof IfInstruction || insn instanceof GOTO
                        || insn instanceof GOTO_W || insn instanceof SwitchInstruction) {
                    branches++;
                }
                if (insn.isBackJump()) {
                    backEdges++;
                }
                if (insn instanceof INVOKEVIRTUAL || insn instanceof INVOKEINTERFACE) {
                    virtualCalls++;
                }
                if (insn instanceof NEW || insn instanceof NEWARRAY
                        || insn instanceof ANEWARRAY || insn instanceof MULTIANEWARRAY) {
                    allocSites++;
                }
                if (insn instanceof ATHROW) {
                    athrows++;
                }
            }
        }

        return new Features(remaining, branches, backEdges, virtualCalls, allocSites, athrows);
    }

    /** Resolves every jump target of `insn`, as instruction-array indices, or an empty list if it has none. */
    private static List<Integer> jumpTargetIndices(Instruction insn, MethodInfo mi) {
        List<Integer> out = new ArrayList<>();
        if (insn instanceof IfInstruction) {
            Instruction t = ((IfInstruction) insn).getTarget();
            if (t != null) out.add(t.getInstructionIndex());
        } else if (insn instanceof GOTO) {
            Instruction t = ((GOTO) insn).getTarget();
            if (t != null) out.add(t.getInstructionIndex());
        } else if (insn instanceof GOTO_W) {
            Instruction t = ((GOTO_W) insn).getTarget();
            if (t != null) out.add(t.getInstructionIndex());
        } else if (insn instanceof SwitchInstruction) {
            SwitchInstruction sw = (SwitchInstruction) insn;
            addResolved(out, mi, sw.getTarget()); // default
            for (int pos : sw.getTargets()) {
                addResolved(out, mi, pos);
            }
        }
        return out;
    }

    private static void addResolved(List<Integer> out, MethodInfo mi, int rawPosition) {
        Instruction t = mi.getInstructionAt(rawPosition);
        if (t != null) {
            out.add(t.getInstructionIndex());
        }
    }
}
