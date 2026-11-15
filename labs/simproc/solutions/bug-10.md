# bug-10 — `ORI` adds instead of ORing

Catalogue **B10**. Tier 5, Lab 06 (the hard end).

```diff
--- a/src/simproc_system.sv     line 678, CYCLE_4, the ORI clause
-                    alu_op          = ALU_OR;
+                    alu_op          = ALU_ADD;
```

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | passes |
| Suite | 7/10 — caught by T02, T03, T08 |
| Symptom demo | `ORI 5 ; ORI 3` gives 8; it should give 7 |
| Control | `ORI 8 ; ORI 3` gives 11 on this core *and* on a correct one |

## Why it hides

`OR` and `ADD` agree exactly when the operands share no set bits. That has two
consequences, and between them they cover almost everything a real program does:

1. The first `ORI` after a reset is always right. R0 is 0, and `0 | imm` is
   `0 + imm` for every immediate.
2. Building a constant out of disjoint bit groups is always right. `ORI 8`
   then `ORI 3`, the natural way to assemble a value in a machine with a 5-bit
   immediate, never overlaps, so it never diverges. Measured: 11 on both cores.

The bug only appears when an immediate sets a bit that R0 already has. T02 exists
to force exactly that.

## What it teaches

This is a wrong operator that agrees with the right one on every value you would
naturally pick. It is the hardest class of bug to find by inspection *and* by
random stimulus, because the disagreement set is a thin slice of the input space
and programmers avoid it without meaning to.

Getting a student to construct the failing case from the property ("when do OR
and ADD differ?") rather than by trial and error is the point of the exercise.

## The fix

Restore `alu_op = ALU_OR;`.
