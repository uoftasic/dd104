# `coverage/`: toggle coverage on the Lab 01 stimulus

The lab one directory up asks whether the adder is right. This add-on asks a different question,
which parts of the adder your stimulus never moved, and the coverage tool answers it without
knowing anything about what an adder does.

Writeup: [Lab 01, Part 5](https://uoftasic.com/dd104/labs/lab-01-the-adder-you-already-trust-overview.html#part-5-ask-a-coverage-tool).
Background: [Coverage as a question](https://uoftasic.com/dd104/guide/coverage-is-a-question.html).

```bash
cd labs/lab-01-the-adder-you-already-trust/coverage
make
```

It takes about 11 seconds, because it builds the design twice with Verilator. Icarus has no
coverage instrumentation, so this is the one place early in the course where only Verilator can
answer. Both runs use `../src/ripple4.sv`, the correct adder, so there is no bug to find here.

## Files

| File | What it is |
|---|---|
| `cov_six.sv` | the lab's six hand-picked cases in plain SystemVerilog. It deliberately checks nothing. Coverage instruments the design, so it measures what the stimulus reached and has no way to tell whether anyone looked at the answer. |
| `cov_all.sv` | all 512 vectors, with `cin` deliberately in the innermost loop. Toggle coverage counts transitions rather than values, so the loop order is part of the stimulus. |
| `covcount.py` | counts only the coverage points that belong to the design. `verilator_coverage` prints one merged percentage over everything it compiled, testbench included, and that isn't the number you want. |

## What it prints

```
------------------------------------------------------------------
 six hand-picked cases
------------------------------------------------------------------
cov_six.dat
  design toggle points : 48
  never toggled        : 5
  design line points   : 0
  the ones that never moved:
    ripple4.sv:3  b[2]:1->0
    ripple4.sv:4  cin:0->1
    ripple4.sv:4  cin:1->0
    ripple4.sv:8  c[0]:0->1
    ripple4.sv:8  c[0]:1->0
```

The counts are exact and stay the same from run to run, though the wall-clock time varies. The
`design line points : 0` line isn't a bug in the script. The adder is
built from continuous assignments, and a continuous assignment isn't a statement that executes,
so line coverage has nothing in it to count.
