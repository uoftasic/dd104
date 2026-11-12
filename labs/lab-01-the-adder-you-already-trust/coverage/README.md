# `coverage/`: toggle coverage on the Lab 01 stimulus

The lab one directory up asks whether the adder is right. This add-on asks which parts of it your
stimulus never moved, and answers without knowing what an adder is.

Writeup: [Lab 01, Part 5](https://uoftasic.com/dd104/#/labs/lab-01-the-adder-you-already-trust-overview?id=part-5-ask-a-coverage-tool).
Background: [Coverage as a question](https://uoftasic.com/dd104/#/guide/coverage-is-a-question).

```bash
cd labs/lab-01-the-adder-you-already-trust/coverage
make
```

It takes about 11 seconds because it builds the design twice with Verilator. Icarus has no
coverage instrumentation, so this is the one place early in the course where only Verilator can
answer. Both runs use `../src/ripple4.sv`, the correct adder; there is no bug here.

## Files

| File | What it is |
|---|---|
| `cov_six.sv` | the lab's six hand-picked cases in plain SystemVerilog. It checks nothing, on purpose: coverage instruments the design, so it measures what the stimulus reached and cannot tell whether anyone looked at the answer. |
| `cov_all.sv` | all 512 vectors, with `cin` in the innermost loop on purpose. Toggle coverage counts transitions, not values, so loop order is part of the stimulus. |
| `covcount.py` | counts the coverage points that belong to the design. `verilator_coverage` prints one merged percentage over everything it compiled, testbench included, which is not the number you want. |

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

The counts are exact and do not move between runs; the wall-clock time does. `design line points
: 0` is not a bug in the script. The design is continuous assignments, and a continuous assignment
is not a statement that executes, so line coverage has nothing here to count.
