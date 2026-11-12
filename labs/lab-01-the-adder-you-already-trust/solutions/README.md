# Lab 01: reference solution

Get your own `make check` to say `VERDICT: PASS` before you read this, then compare. The four
changed lines matter less than the two decisions behind them.

```bash
cp solutions/test_adder.py test_solution.py
make check TB=test_solution
```

Measured in the pinned container:

```
      ok  src/  the good adder           2 tests, all passed          1.4s
  caught  broken/  carry-in dropped      2 tests, 1 FAILED            1.4s
        t02_exhaustive
            AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1
------------------------------------------------------------------------
 VERDICT: PASS
```

## Two decisions worth arguing about

1. `t01_the_obvious_six` is still in the file. It is strictly weaker than `t02_exhaustive`, since
   every vector it drives `t02` also drives, so deleting it is easy to argue for. It stays because
   a test suite is read as often as it is run: six named cases with a comment document what the
   module is for, and they are the first row to go red when somebody deletes the module. Keeping a
   redundant fast test is defensible, and so is deleting it. Have the argument rather than
   skipping it.

2. Failures are collected, not raised. Asserting on the first bad vector stops the test at vector
   256 of 512 and reports one wrong answer. Collecting runs all 512 and reports `256 of 512`, and
   that ratio is the diagnosis: half the input space failing means the fault tracks a signal that
   is high in half the vectors, and this module has exactly one.

   The cost is real. A collecting test keeps running after the design has gone wrong, so on a
   stateful design (every lab from 02 on) it can pile up thousands of consequential failures
   behind one root cause, and the useful line scrolls off the top. The rule: collect on
   combinational tests, and stop on the first failure once state is involved. SimProc's harness
   stops.

## What the lab shows

Both testbenches pass on the good adder. One is worth committing and one is not, and `make sim`
cannot tell them apart. Only `make check` can, because only `make check` runs them against
something that is wrong. Lab 02 makes the same point with a processor.
