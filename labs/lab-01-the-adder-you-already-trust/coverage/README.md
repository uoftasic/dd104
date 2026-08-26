# `coverage/` — the same stimulus, a different question

The lab one directory up asks *is the adder right?* This asks *which parts of it did my
stimulus never move?* — and it answers without knowing what an adder is.

Writeup: [Coverage as a question, not a metric](https://uoftasic.com/dd104/#/guide/coverage-is-a-question)

```bash
cd labs/lab-01-the-adder-you-already-trust/coverage
make
```

About **12 seconds**, because it builds the design twice with Verilator. Icarus has no
coverage instrumentation, so this is the one place in the early course where the strict
simulator is the only one that can answer.

Both runs use `../src/ripple4.sv` — **the correct adder**. There is no bug here at all.
Coverage is not looking for one.

| file | what it is |
|---|---|
| `cov_six.sv` | the lab's six hand-picked cases, in plain SystemVerilog. **It checks nothing.** That is the point — coverage instruments the design, so it measures what your stimulus reached and has no way to know whether you looked at the answer. |
| `cov_all.sv` | all 512, with `cin` in the **innermost** loop on purpose. Toggle coverage counts transitions, not values, so loop order is part of your stimulus. |
| `covcount.py` | counts coverage points belonging to the *design*. `verilator_coverage` prints one merged percentage over everything it compiled, testbench included, which is not the number you want. |

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

Those five numbers are golden — they do not move between runs. The twelve seconds is wall
clock and does.

`design line points : 0` is not a bug in the script. This design is continuous assignments,
and a continuous assignment is not a statement that executes, so **line coverage has nothing
here to count**. A report claiming "100 % line coverage" on this adder would be perfectly
true and completely empty.
