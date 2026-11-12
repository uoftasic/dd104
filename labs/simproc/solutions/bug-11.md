# bug-11 — `ORI` reads R0 and writes R1

Catalogue B11. Tier 5, Lab 06. This one has history — read it before using it.

```diff
--- a/src/simproc_system.sv     line 689, CYCLE_5, the ORI write-back
-                    rf_reg_w_in     = 2'b0;
+                    rf_reg_w_in     = 2'b1;
```

Line 635 still reads `RF[0]`. So the instruction becomes `RF[1] <- RF[0] | imm`,
which is not an instruction anybody specified.

## Where it came from

Upstream, both of those lines carried the comment
`// change this to 1, to match SimProc`. This bug is that comment applied to
one of its two sites. The DD104 fork deletes both comments (see
`../FORKED-FROM` and `../../../ORI-DECISION.md`) — with them in place the source
would tell a student that the bug is the fix, which is precisely backwards for a
course whose premise is "there are hidden bugs in this file."

Four variants of those two lines were built and simulated to settle it: R0 and R1
are exactly isomorphic in this machine — a register index never leaves the
instruction word, and R0 is not hardwired to zero — so the hardware cannot break
the tie. What the hardware *can* say is that the two lines must move together,
and that is what makes the half-applied edit a real bug rather than a preference.

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | passes |
| Suite | 3/10 — caught by T01, T02, T03, T05, T06, T08, T10 |
| Symptom demo | `ORI 5 ; ORI 3` leaves R0 = 0; it should be 7 |
| One `ORI` from reset | R0 = 0 instead of 5 — and R1 = 5 |

## Why it hides

After a reset every register holds 0. `RF[1] <- RF[0] | imm` and
`RF[0] <- RF[0] | imm` therefore put the same value into the machine on the
first `ORI` — just under a different name. Divergence starts at the second one,
because the second `ORI` reads R0, which the first one never updated.

A bug that a reset hides is a genuinely hard class: the shortest test you would
write to check `ORI` — reset, one `ORI`, look at the value — is the one test that
cannot see it, unless you look at the *whole* register file rather than the
register you expected.

## What it teaches

Check the state you did not change. A scoreboard that compares all four registers
after every instruction catches this immediately; one that checks "the register
the instruction names" never does.

And: when a spec is ambiguous, the ambiguity itself is a hazard. Two lines
implementing one decision must be edited together, and the way to find out
whether they were is to test the second instruction, not the first.

## The fix

Restore `rf_reg_w_in = 2'b0;` — matching the read at line 635.
