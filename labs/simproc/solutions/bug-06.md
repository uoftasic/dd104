# bug-06 — the shift amount loses a bit

Catalogue **B06**. Tier 2, Lab 2.

```diff
--- a/src/simproc_system.sv     line 579, CYCLE_3, the SHIFT operand
-                    alu_in_b        = {6'b0, instr_reg_out[4:3]};
+                    alu_in_b        = {7'b0, instr_reg_out[3]};
```

The SHIFT encoding is `AA D SS 011`, and `instr[4:3]` is the two-bit amount. Only
its low bit reaches the ALU, so 2 collapses to 0 and 3 collapses to 1.

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | **passes** |
| Suite | 8/10 — caught by **T03**, **T08** |
| **ALU sweep** | **0 mismatches — the ALU is completely clean** |
| Symptom demo | `1 << 3` gives 2, `1 << 2` gives 1, `64 >> 3` gives 32 |

## Why it hides

Shift by 0 and shift by 1 are both correct — and shift by 1 is what almost
everyone writes. Only amounts 2 and 3 are wrong, in both directions.

## What it teaches

Two things, and the second one is worth more.

**Sweep the field, do not sample it.** There are four encodable amounts and two
directions: eight cases, and testing all eight is not thorough, it is just
finishing.

**The unit test that cannot find it.** Put this variant next to bug-01, bug-02
and bug-03 in the same course. Those three are found by the ALU sweep in 19
seconds. This one is *not* — the ALU sweep is 0/393,216 clean, because the ALU
shifts perfectly well by whatever amount it is handed, and the wrong amount is
being handed to it from outside. That is the boundary between a unit test and an
integration test, drawn by measurement instead of by definition, and it is the
best answer this course has to "why do we need both?"

## The fix

Restore `alu_in_b = {6'b0, instr_reg_out[4:3]};`.
