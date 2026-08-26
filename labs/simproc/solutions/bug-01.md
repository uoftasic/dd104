# bug-01 — `SUB` computes `B - A`

Catalogue **B01**. Tier 1, Lab 03 (the ALU, on its own).

```diff
--- a/src/simproc_system.sv     line 811, inside the ALU
-            SUB:        ALUout = A - B;
+            SUB:        ALUout = B - A;
```

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | **passes** |
| Suite | 8/10 — caught by **T01**, **T08** |
| ALU sweep | **65,024** of 65,536 `SUB` vectors wrong, values and flags both |

## Why it hides

`A - B == B - A` exactly when `A == B`, or when `A - B == 128` (because −128 and
+128 are the same bit pattern in eight bits). That is 256 + 256 = **512**
vectors, and 65,536 − 512 = 65,024 — which is the number the sweep prints. The
count and the explanation close on each other, by hand, to the digit.

The 256 `A == B` vectors are the trap. This machine has four registers and no
"clear" instruction, so `SUB rX,rX` **is** how you zero a register, and it is
everywhere in every program. It is correct under this bug. A student who writes
`SUB r0,r0` to set up a test and then checks the result has tested the one input
class the bug survives.

## What it teaches

That the number is the diagnostic. "65,024 wrong" is not a scarier version of
"it's broken" — it is a *shape*. 512 exceptions out of 65,536 is a specific,
namable set, and naming that set names the bug. Get students to predict the count
before they run the sweep.

## The fix

Restore `ALUout = A - B;`.
