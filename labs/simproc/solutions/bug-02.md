# bug-02 — `NAND` is wired as `NOR`

Catalogue B02. Tier 1, Lab 03.

```diff
--- a/src/simproc_system.sv     line 813, inside the ALU
-            NAND:       ALUout = ~(A & B);
+            NAND:       ALUout = ~(A | B);
```

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | passes |
| Suite | 8/10 — caught by T01, T08 |
| ALU sweep | 65,280 of 65,536 `NAND` vectors wrong; 34,954 flag pairs wrong |

## Why it hides

`~(A & B) == ~(A | B)` exactly when `A == B` — 256 vectors. 65,536 − 256 = 65,280,
which is what the sweep prints.

And those 256 vectors are, again, the ones everybody uses. SimProc has no `NOT`
instruction. `NAND rX,rX` is how you invert a register, and it is the single most
common way `NAND` appears in a real SimProc program. It is correct under this bug.

## What it teaches

"I tested NAND" and "I tested NAND on two different operands" are different
sentences, and only the second one is a test. This is the cleanest example in the
set of a bug that lives exactly where the idiom lives — the operand pattern a
programmer reaches for first is the operand pattern that hides it.

Pair it with bug-01 in the same lab. Both are one line in the same `case`
statement, both are found by the same 19-second sweep, and the two exception
counts (512 and 256) are different in a way students can explain.

## The fix

Restore `ALUout = ~(A & B);`.
