# bug-05 — branch displacement is zero-extended

Catalogue **B05**. Tier 2, Lab 3 (control flow).

```diff
--- a/src/simproc_system.sv     line 621, the branch target calculation
-                    alu_in_b        = {{4{instr_reg_out[7]}}, instr_reg_out[7:4]};
+                    alu_in_b        = {4'b0, instr_reg_out[7:4]};
```

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | **passes** |
| Suite | 7/10 — caught by **T04**, **T07**, **T08** |
| Symptom demo | a 3-iteration countdown ends with R0 = **2**; the body ran once |

Sweeping all sixteen displacements from an instruction at address 20:

| displacement | correct target | this core |
|---|---|---|
| `+0` … `+7` | 21 … 28 | 21 … 28 — **all correct** |
| `-1` | 20 | 36 |
| `-2` | 19 | 35 |
| `-3` | 18 | 34 |
| `-8` | 13 | 29 |

Every backward branch lands exactly 16 too far forward, which is the whole of
what dropping a sign extension does.

## Why it hides

The forward half of the number line is correct, and the forward half is the half
that gets tested first. "Skip the next instruction" — `BZ +1`, `BNZ +1` — is the
first branch anybody writes, and it works. A test suite full of skip-the-next
passes completely.

The first thing that breaks is the first loop, because a loop is the only reason
to branch backwards.

## What it teaches

Sign extension is a silent half of the number line. More generally: when a field
is signed, the test that sweeps it must cross zero, and 16 values is a small
enough space to sweep exhaustively — T04 does exactly that and it is not a clever
test, it is the obvious one.

## The fix

Restore `alu_in_b = {{4{instr_reg_out[7]}}, instr_reg_out[7:4]};`.
