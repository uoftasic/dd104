# bug-08 — `STORE` never pulses `done`

Catalogue **B08**. Tier 4, Lab 05 (protocol, not data).

```diff
--- a/src/simproc_system.sv     line 602, CYCLE_3, the STORE clause
-                    done            = 1;
+                    done            = 0;
```

## Measured

| | |
|---|---|
| Boilerplate `test/test.py` | **passes** |
| Suite | 9/10 — caught by **T09, and nothing else** |
| Symptom demo | 14 instructions retired, **11** `done` pulses; every value correct |

T01–T08 and T10 all pass. Registers, memory, flags and the PC are correct on
every program tried, including 20 random ones.

## Why it hides

Because nothing is wrong with the answers. The core executes the `STORE`, writes
the right byte to the right address, and moves on in the right number of cycles.
The only thing missing is the one-cycle announcement on `uo_out[2]`.

## What it teaches

The handshake is part of the contract. A pin that says "an instruction just
retired" is as much a specified output as the data, and a testbench that never
checks it has left a whole output unverified.

And then the part that is worth saying out loud, because it inverts what students
expect a bug to do:

> If your scoreboard triggers on `done`, this bug does not make your test fail.
> It makes your test *stop scoring* — silently — and a test that has stopped
> scoring looks exactly like a test that is passing.

T09 is the shape of the test that catches it: count retired instructions
independently of `done`, then assert the two counts are equal. It never looks at
a single data value.

## The fix

Restore `done = 1;` in the `STORE` clause.
