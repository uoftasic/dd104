# bug-13 — `STORE` drops to IDLE for one cycle

Catalogue B13. Tier 4, Lab 05.

```diff
--- a/src/simproc_system.sv     line 603, CYCLE_3, the STORE clause
-                    if (run)
+                    if (0)
```

The `STORE` path stops asking whether the core is still running and always goes
to IDLE. Because `run_reg` is still set, the next cycle sends it straight back to
CYCLE_1 — so the program continues, one cycle later, with a one-cycle blip on the
`halt` pin.

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | passes |
| Suite | 9/10 — caught by T07, and nothing else |
| Symptom demo | identical R0, R1, R2, `mem[32]`, and 14 of 14 `done` pulses |
| | 3 clocks with `halt` high while `run` was asserted (correct: 0) |

Three `STORE`s in the program, three blips. Every architectural result matches a
correct core exactly.

## Why it hides

Because it is, in every sense a data-comparing testbench can measure, correct.
Same values, same addresses, same flags, same `done` count, same instruction
count. Only the timing and one status pin differ.

## What it teaches

Functional equivalence is not correctness. On a real chip this is two things
at once:

- a performance bug — one wasted cycle on every `STORE`, forever;
- a debug-visibility bug — anyone watching `halt` to see whether the core is
  running sees it stop, repeatedly, for no reason in the program.

Only a protocol assertion sees it: *`halt` must stay low for as long as `run` is
asserted*. That is a property, not a value comparison, and writing it is the
lesson.

Pair with bug-08 in the same lab. Both leave every number correct; one drops a
handshake pulse, the other adds a state that should not exist. Between them they
make the case that a testbench needs to check the *protocol* and not only the
data — which is the whole reason assertions exist.

## The fix

Restore `if (run)`.
