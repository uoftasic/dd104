# bug-09 — a branch overwrites the flags

Catalogue **B09**. Tier 3, Lab 3.

```diff
--- a/src/simproc_system.sv     line 622, the branch clause
                     alu_op          = ALU_ADD;
+                    flag_wr         = 1;
                     pc_in           = alu_out;
```

The one variant that **adds** a line rather than changing one. Branches use the
ALU to compute `PC + 1 + offset`; this makes them latch the flags from that
address arithmetic, destroying whatever comparison the program was in the middle
of using.

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | **passes** |
| Suite | 8/10 — caught by **T05**, **T08** |
| Symptom demo | R0 should be 8 after `BZ` then `BNZ`; it is **0** |

## Why it hides

One branch after a compare works perfectly, every time. The flags are read
combinationally in the same cycle the branch decides, so the *first* branch sees
the correct flags and does the correct thing. It is only the *second* branch off
the same comparison that reads garbage.

`BZ … ; BNZ …` — one compare, two tests — is an idiom students write on day one,
and it is the only thing this bug breaks.

## What it teaches

That "the comparison is still valid" is an assumption, and assumptions get
tests. In a machine with no explicit compare instruction, where `SUB` doubles as
the comparison, the lifetime of the flags is load-bearing and completely
invisible in the source.

Also, as a code-review lesson: this is one added line, in the right style, in the
right place, that looks like it belongs. Injected bugs do not have to be typos.

## The fix

Delete the added `flag_wr = 1;` from the branch clause.
