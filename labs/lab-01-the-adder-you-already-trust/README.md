# Lab 01 — The adder you already trust

Writeup: [`docs/labs/lab-01-the-adder-you-already-trust-overview.md`](../../docs/labs/lab-01-the-adder-you-already-trust-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-01-the-adder-you-already-trust>

The 4-bit ripple-carry adder you built in DD102, with a cocotb testbench around it, and a
second copy of the adder that is deliberately broken. The lab is four lines of work and one
uncomfortable realisation.

```bash
cd labs/lab-01-the-adder-you-already-trust
make
```

Inside the workbench container (`hpretl/iic-osic-tools:2026.04` — cocotb 2.0.1, Icarus
Verilog 14.0). No environment setup, no `pip install`, no paths to retype. About **5 seconds**,
and it ends on `VERDICT: FAIL`, which is correct.

## Targets

| | |
|---|---|
| `make` | `sim`, then `check` — and a verdict |
| `make sim` | your testbench against `src/`, the good adder |
| `make broken` | your testbench against `broken/`, the one that drops its carry-in |
| `make check` | the verdict: must PASS on `src/`, must FAIL on `broken/` |
| `make clean` | remove `build/` |

`make check TB=test_mine` runs a different module. `TB` names a Python module, not a file:
`TB=test_mine`, not `TB=test_mine.py`.

## Files

| | |
|---|---|
| `test_adder.py` | **the file you edit.** Two tests, both passing, one TODO. |
| `src/ripple4.sv`, `src/fulladder.sv` | the adder, correct. Same source as DD103 Lab 01. |
| `broken/ripple4.sv` | the same adder with the carry-in dropped. **Not hidden** — its own header says what is wrong with it. Lab 01 is not a bug hunt; the hunt starts in Lab 04. |
| `check.py` | the verdict. About 150 lines, and worth reading — every later lab uses a bigger version of it. |
| `coverage/` | an add-on that asks a different question about the same stimulus. Its own `README.md`, its own `make`. |
| `solutions/` | a reference solution. Do not open it before your own verdict says PASS. |

## What it prints, and what is deterministic

`make sim` on the shipped file, against `src/`:

```
** test_adder.t01_the_obvious_six       PASS           6.00           0.00       7609.87  **
** test_adder.t02_every_a_and_every_b   PASS         256.00           0.01      20845.71  **
** TESTS=2 PASS=2 FAIL=0 SKIP=0                      262.00           0.01      17915.68  **
```

**262.00 ns and `checked 256 of the 512 possible input vectors` are golden** — they are
simulated time and a vector count, they do not vary, and if yours differ something has changed.
The `REAL TIME` and `RATIO` columns are wall clock and will not match.

`make check` on the shipped file:

```
      ok  src/  the good adder           2 tests, all passed          1.5s
  MISSED  broken/  carry-in dropped      2 tests, all passed          2.1s
------------------------------------------------------------------------
 VERDICT: FAIL -- your testbench passes the broken adder too.
```

and, with the TODO done:

```
  caught  broken/  carry-in dropped      2 tests, 1 FAILED            1.4s
        t02_exhaustive
            AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1
------------------------------------------------------------------------
 VERDICT: PASS
```

**256 of 512 is golden.** It is also the diagnosis: exactly half the input space failing means
the fault tracks a signal that is high in exactly half the vectors, and this module has one
such signal.

## Three things `make check` will not call a PASS

**Half the TODO.** The TODO is two changes and doing only the first one — sweeping `cin`,
keeping the `assert` inside the loop — turns `broken/` red for the wrong reason. The run stops
at the first wrong vector, so the failure is an anecdote instead of the count Step 4 is entirely
about. `check.py` measures how many vectors each run actually drove and says which half is
missing:

```
 VERDICT: FAIL -- the second half of the TODO is not done.
   You swept cin: on the good adder you drove all 512 vectors.
   On the broken adder you drove 263 and then stopped, because you are
   still asserting on the first vector that is wrong instead of collecting
   them.
```

**A test that blew up.** `NameError` is not a caught bug — Python stopped before the comparison
happened, so the run says nothing about either adder:

```
  BROKEN  broken/  carry-in dropped      2 tests, 1 BLEW UP           1.3s
        t02_every_a_and_every_b   <- this test BLEW UP; it checked nothing
            NameError: name 'summary' is not defined
------------------------------------------------------------------------
 VERDICT: FAIL -- 1 of your tests did not run to the end.
```

This is the one worth understanding, because a testbench that is correct right up until it
finds something — and then crashes in the code that builds the failure message — passes the
good adder and crashes on the broken one, which looks exactly like a catch. It is not one.
[`../common/verdict.py`](../common/verdict.py) is where the two are told apart.

**A test that never ran.** Every test skipped is not "all tests passed".

## `make: *** [Makefile:49: check] Error 1` is not a broken Makefile

A failed verdict exits non-zero on purpose, so `make` prints an error line under it. That line
is the verdict talking. It disappears when the verdict passes.

## Definition of done

`make check` says `VERDICT: PASS` — which now requires all 512 vectors on both adders, and a
failure on `broken/` that is a *count*, not the first bad vector.
