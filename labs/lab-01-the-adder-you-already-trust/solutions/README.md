# Lab 01 — reference solution

**Do not read this first.** Get your own `make check` to say `VERDICT: PASS`, then come
back and compare — the interesting part of this file is not the four changed lines, it is
the two decisions behind them.

```bash
cp solutions/test_adder.py test_solution.py
make check TB=test_solution
```

Measured, in the pinned container:

```
      ok  src/  the good adder           2 tests, all passed          1.4s
  caught  broken/  carry-in dropped      2 tests, 1 FAILED            1.4s
        t02_exhaustive
            AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1
------------------------------------------------------------------------
 VERDICT: PASS
```

## Two decisions worth arguing about

**1. `t01_the_obvious_six` is still in the file.** It is strictly weaker than
`t02_exhaustive` — every vector it drives, `t02` also drives — so an argument for deleting
it is easy to make. It stays because a test suite is read as often as it is run: six named
cases with a comment is documentation of what the module is for, and it is the row that goes
red first when somebody deletes the module. Keeping a redundant fast test is a defensible
choice; so is deleting it. Have the argument, do not skip it.

**2. Failures are collected, not raised.** `assert` on the first bad vector stops the test
at vector 256 of 512 and reports one wrong answer. Collecting them runs all 512 and reports
`256 of 512`, and that ratio is the diagnosis — half the input space failing means the fault
tracks a signal that is high in half the vectors, and there is exactly one such signal here.

The cost is real and you should know it: a collecting test keeps running after the design has
gone wrong, so on a *stateful* design (every lab from 02 onward) it can pile up thousands of
consequential failures behind one root cause, and the useful line scrolls off the top. The
rule that falls out: **collect on combinational tests, stop on the first failure once state
is involved.** SimProc's harness stops.

## What this lab is really claiming

Both testbenches in this lab pass on the good adder. One of them is worth committing and one
is not, and `make sim` cannot tell them apart — only `make check` can, because only `make
check` runs them against something that is wrong.

That is the whole course in a four-bit adder. Lab 02 does it again with a processor.
