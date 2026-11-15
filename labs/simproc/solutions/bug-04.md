# bug-04 — ALU write-back uses the `rB` field

Catalogue B04. Tier 2, Lab 04 (decode and the register file).

```diff
--- a/src/simproc_system.sv     line 648, CYCLE_4, the ADD/SUB/NAND/SHIFT write-back
-                    rf_reg_w_in     = instr_reg_out[7:6];
+                    rf_reg_w_in     = instr_reg_out[5:4];
```

The instruction word is `AA BB oooo`: `instr[7:6]` is rA, `instr[5:4]` is rB.
Every ALU result lands in the *source* register instead of the destination.

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | passes |
| Suite | 3/10 — caught by T01, T02, T03, T05, T06, T08, T10 |
| Symptom demo | R1 should be 7; it is 0, and never changes |

## Why it hides

It is completely invisible whenever `rA == rB`, and this machine's idioms are
full of that: `SUB rX,rX` to clear, `NAND rX,rX` to invert, `ADD rX,rX` to double.
A program written entirely from those runs correctly on this core.

Only the ALU write-back is patched. The `LOAD` write-back three clauses down
(line 662) is left correct, so `LOAD` puts values exactly where it is told,
which sends a student who has noticed "registers get the wrong values" straight
past the actual code.

## What it teaches

There are two nearly identical code paths, and one of them is wrong. This is the
most common real-world RTL bug in the whole catalogue: a block was copied, the copy
was edited, and the original was not (or the other way round). Finding it means
noticing that `LOAD` and `ADD` disagree about something they should agree about.

Three suite tests pass on it. Ask students to work out which three and why
*before* they read the source; the answer is "the three that never write a
register they later read from a different name", and that reasoning finds the bug.

## The fix

Restore `rf_reg_w_in = instr_reg_out[7:6];`.
