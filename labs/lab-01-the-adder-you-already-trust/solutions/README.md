# Lab 01: reference solution

Get your own `make check` to say `VERDICT: PASS` before you read this, and then compare. The four
lines we changed matter less than the two decisions behind them, which are written up below.
To run the reference testbench from the lab directory:

```bash
cp solutions/test_adder.py test_solution.py
make check TB=test_solution
```

This is what it printed in the pinned container:

```
      ok  src/  the good adder           2 tests, all passed          1.4s
  caught  broken/  carry-in dropped      2 tests, 1 FAILED            1.4s
        t02_exhaustive
            AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1
------------------------------------------------------------------------
 VERDICT: PASS
```

## Two decisions worth arguing about

1. `t01_the_obvious_six` is still in the file. It is strictly weaker than `t02_exhaustive`,
   since `t02` drives every vector that `t01` drives, so there's a good case for deleting it. We
   kept it because a test suite is read as often as it is run. Six named cases with a comment
   document what the module is for, and they are the first row to go red when somebody deletes
   the module. Keeping a redundant fast test is defensible, and so is deleting it, but make the
   choice on purpose.

2. The tests collect failures instead of raising on the first one. Asserting on the first bad
   vector stops the test at vector 256 of 512 and reports one wrong answer. Collecting runs all
   512 and reports `256 of 512`, and that ratio is the diagnosis: when half the input
   space fails, the fault follows a signal that is high in half the vectors, and this module has
   exactly one such signal.

   Collecting has a real cost. A collecting test keeps running after the design has gone wrong,
   so on a stateful design (every lab from 02 on) it can pile up thousands of follow-on failures
   behind one root cause, and the useful line scrolls off the top of the terminal. Our rule is to
   collect on combinational tests and to stop on the first failure once state is involved, which
   is why SimProc's harness stops.

## What the lab shows

The shipped testbench and this one both pass on the good adder, but only this one is worth
committing. `make sim` can't tell them apart, because it runs them only against the correct
adder. `make check` can, because it also runs them against one that is wrong. Lab 02 makes the
same point with a processor.
