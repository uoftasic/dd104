# bug-07 — `LOAD` addresses memory with `rA`

Catalogue B07. Tier 2, Lab 04. The set piece of the whole catalogue.

```diff
--- a/src/simproc_system.sv     line 589, CYCLE_3, the LOAD clause
-                    mem_addr        = reg_b_out;
+                    mem_addr        = reg_a_out;
```

`LOAD rA, rB` should read `mem[rB]` into `rA`. This one reads through the
destination register instead of the pointer register. The `STORE` clause seven
lines below has its own `mem_addr = reg_b_out;` and is untouched, so `STORE` is
exact.

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | passes |
| Suite | 9/10 — caught by T10, and nothing else |
| Symptom demo | `LOAD r0,r1` with R1 = 40 and `mem[40] = 90` gives R0 = 6 |

6 is the byte at address 0: the first instruction of the program, read as data,
because R0 held 0.

## Why it hides

It is invisible whenever `rA == rB`. And `LOAD rX, rX` (load through a pointer
into the register that held the pointer) is not a contrived case. It is a real
idiom: you have finished with the address and you want the value.

## Ship the story, not just the bug

The first `LOAD`/`STORE` test written for this core, T06, used `LOAD r1,r1`. It
passes on this variant. The bug was found by injecting it and discovering that
the test suite did not move, and T10 was written specifically to catch it:
"LOAD and STORE where the pointer register and the data register differ."

That is a better lesson than the bug. The person writing the testbench had a
blind spot, wrote a test that shared it, and only found out because someone
deliberately broke the thing the test was supposed to be watching. T08's 600
random instructions also miss it.

Tell students that story before Lab 04 and again after. It is the argument for
fault injection, made from inside the course's own history rather than from a
textbook.

## What it teaches

Aliasing hides bugs. When two operands can be the same register, a test that
lets them be the same register is testing half the instruction. Make every
operand distinct on purpose, and write down why.

## The fix

Restore `mem_addr = reg_b_out;` in the `LOAD` clause.
