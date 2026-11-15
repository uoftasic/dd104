# bug-03 — the `Z` flag only sees the low nibble

Catalogue **B03**. Tier 1, Lab 03.

```diff
--- a/src/simproc_system.sv     line 822, the ALU's flag logic
-    assign Z = ~(|ALUout);
+    assign Z = ~(|ALUout[3:0]);
```

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | passes |
| Suite | 7/10 — caught by T03, T06, T10 |
| ALU sweep | 0 value mismatches. 25,726 flag mismatches. |

Per operation, from the sweep:

| op | value mismatches | flag mismatches |
|---|---|---|
| ADD | 0 | 3,840 |
| SUB | 0 | 3,840 |
| OR | 0 | 255 |
| NAND | 0 | 255 |
| SHL | 0 | 14,400 |
| SHR | 0 | 3,136 |

Every one is derivable by hand. ADD: there are 15 nonzero 8-bit results whose low
nibble is zero (0x10, 0x20 … 0xF0), and each is reachable by 256 operand pairs:
15 × 256 = 3,840. OR: the low nibble of `A | B` is zero only when both operands
have a zero low nibble, which is 16 × 16 = 256 pairs, minus the one genuinely-zero
case: 255.

## Why it hides

Every arithmetic result this core produces is correct. Only the flag is wrong,
and only for results that are nonzero but end in four zero bits. A test that
compares values and never compares flags passes completely.

T08 misses it: its 20 random programs, 600 random instructions in all, every one
passes. That is the most useful single fact in this variant. Random stimulus with
no coverage model does not find a flag bug, because flags are only observable through a
*subsequent* branch, and a random program rarely puts the right branch after the
right result.

## What it teaches

Flags are architectural state. They are as much a part of the answer as the eight
bits in the register, and they need to be in the scoreboard.

This is also the bug that shows what "coverage" means before anyone has said the
word: 600 random instructions is a lot of stimulus, and it gives zero coverage of
the thing that is broken.

## The fix

Restore `assign Z = ~(|ALUout);`.
