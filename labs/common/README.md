# `labs/common`: the harness, the assembler and the verdict

This directory holds the shared infrastructure that every SimProc lab (Labs 02–06) uses: the cocotb
harness, the assembler, the golden model, the bug catalogue and the verdict machinery.

The reference page [The SimProc harness](https://uoftasic.com/dd104/reference/the-harness-api.html)
documents every call, with output from `test_api_tour.py`. The labs that use this directory directly are
[Lab 02](https://uoftasic.com/dd104/labs/lab-02-the-only-test-this-chip-has-overview.html) (Parts 3–5 and Going further),
[Lab 03](https://uoftasic.com/dd104/labs/lab-03-three-blocks-before-the-processor-overview.html) (Part 5),
[Lab 04](https://uoftasic.com/dd104/labs/lab-04-your-first-bug-hunt-overview.html) (Part 6),
[Lab 05](https://uoftasic.com/dd104/labs/lab-05-every-answer-is-right-overview.html) (Part 7) and
[Lab 06](https://uoftasic.com/dd104/labs/lab-06-capstone-overview.html) (Parts 2 and 7).

```bash
cd labs/common
make            # the example testbench on the good core, then on a broken one
```

It runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0, Verilator 5.050) and needs no environment setup and no arguments.

## Targets

| Target | What it does | Wall clock |
|---|---|---|
| `make` | `sim`, then `check` | 20 s |
| `make sim` | your testbench against the golden core | 7.2 s cold, 6.7 s after |
| `make waves` | the same run, dumping `waves.vcd` | 6.1 s, `waves.vcd` = 3,007,592 bytes |
| `make check` | the verdict: PASS on the good core, FAIL on `BUG` | 13.3 s |
| `make check-all` | your testbench against all thirteen broken cores | 68.8 s |
| `make bugs` | the catalogue: names, tiers, and what each one teaches | instant |
| `make model` | `golden.py` alone, no simulator | instant |
| `make gap` | what the random generator covers, and what it cannot | 0.9 s |
| `make selftest` | does the grader grade? Classifier and source audit | 0.3 s |
| `make selftest FULL=1` | the same, plus every checker in the course end to end | minutes |
| `make verify` | confirm every catalogue anchor still matches `rtl/` | instant |
| `make shuttle` | the shipped test, against the golden core and all thirteen | 18.5 s |
| `make clean` | remove `build/`, `waves.vcd`, `__pycache__` | |

The wall-clock figures were measured in the pinned container on a warm image, and they move by a
second or two. You can override these variables on the command line:

```bash
make sim   TB=test_mine          # your own module instead of test_example
make check BUG=B07               # which broken core to check against
make sim   SIM=verilator         # the other simulator
```

`TB` names a Python module on the path, not a file: `TB=test_mine`, not `TB=test_mine.py`. To start
your own testbench, copy `test_example.py`.

## Files

| File | What it is |
|---|---|
| `simproc.py` | the harness: clock, reset, load and run a program, read registers, memory, flags and pins, and a bit-banged UART |
| `simproc_asm.py` | the assembler: write `ADD(1, 0)` or labelled text instead of `0x44`; imports nothing |
| `golden.py` | the reference model: SimProc's instruction set in about 120 lines of Python; imports nothing |
| `test_example.py` | six worked tests; copy this file to start your own |
| `test_reference.py` | eleven tests that catch all thirteen bugs; read it after writing your own |
| `test_shuttle.py` | the test the chip shipped with, unchanged |
| `test_api_tour.py` | every entry point in this directory once, with its answer printed; nine tests, 535,650 ns, about 5 s; the source for the harness reference page |
| `test_values_only.py` | a thorough testbench that never reads a flag, and so cannot catch `B03` |
| `test_handshake_timing.py` | how long the chip's UART receiver is busy, and what a BFM that ignores it does to the next byte |
| `test_two_simulators.py` | one read past the end of RAM, giving different answers on Icarus and Verilator with identical simulated time |
| `test_b01_repro.py` | a minimal reproducer as a bug report should ship one: three tests, one fails on `B01`, two pass on purpose |
| `check.py` | the verdict: your testbench against the good core and a broken one |
| `verdict.py` | how a results file is read; the one place that tells "the assertion fired" from "the test blew up" |
| `selftest/` | deliberately broken testbenches and the verdict each must provoke; see [`selftest/README.md`](selftest/README.md) |
| `bugs.py` | the bug catalogue: thirteen one-line edits, with what each teaches. Reading it gives the course away |
| `gap.py` | nine bug-shaped windows, counted over the seeds `R10` runs and a thousand more; no simulator |
| `inject.py` | builds a broken core from the catalogue, and refuses if the RTL has drifted |
| `rtl/` | the processor; provenance and the four comment lines DD104 changed are in [`rtl/README.md`](rtl/README.md) |
| `Makefile`, `lab.mk`, `sim.mk` | the targets. A lab includes `lab.mk`; `sim.mk` is the only place a simulator is launched |

## How `verdict.py` reads a result

cocotb writes an assertion that fired and a test that crashed into `results.xml` the same way, as a
`<failure>` element, and only the `error_type` attribute tells them apart. A checker that reads
them alike therefore counts a crashed testbench as a catch. DD104 shipped exactly that bug: a student was told `3 of 3 ALU bugs
caught` by a testbench whose exhaustive test raised `NameError` on every core.

Every `check.py` and `hunt.py` in the course imports `verdict.py` instead of deciding for itself:

| In `results.xml` | Means | Counts as |
|---|---|---|
| Nothing inside `<testcase>` | Passed | A pass |
| `error_type="AssertionError"` | Your `assert` fired | Caught |
| `error_type="TimeoutError"`, `"SimTimeoutError"`, `"ValueError"` | The harness showed the design misbehaved: a hang, a reply that never came, an X on a pin | Caught |
| `error_type="NameError"`, `"TypeError"`, `"AttributeError"`, … | The testbench blew up | Neither: `BROKEN` |
| `<failure>` with no `error_type` | cocotb could not start the test | Neither |
| `<skipped/>` | Never ran | Not a pass |

The list of "caught" types is a whitelist on purpose, because a type wrongly counted as caught
turns a crashed testbench into a PASS. Before you change a checker, run `make selftest` (and `make selftest FULL=1`).

## Reference numbers

Measured in the pinned container. Simulated time does not vary between runs or simulators.

`make sim` (the example testbench) totals 512,010.01 ns across six tests. `make sim TB=test_reference`
runs 11 tests, all passing, in 1,905,380.01 ns and about 21 s.

| | `test_example` | `test_reference` |
|---|---|---|
| Bugs caught | 10 of 13 | 13 of 13 |
| `make check-all` | 68.8 s | about 4 min |

More tests of the same kind would not find the three bugs that `test_example` misses; each needs a
different kind of test:

| Bug | What finds it in `test_reference` | Why nothing else does |
|---|---|---|
| `B08_store_drops_done` | `R08`, counting `done` pulses | every register, flag and byte of memory is correct; 10 of the 11 reference tests pass on it |
| `B10_ori_adds_instead_of_ors` | `R02`, ORing in a bit that was already set | `0 \| imm == 0 + imm`, so the first `ORI` after reset is always right |
| `B12_uart_rx_bit_period` | `R11`, sweeping `clk_per_bit` | invisible at the default speed; `PING` still answers `0xAA` where it breaks |

`B13_store_falls_to_idle` is caught by `R08` and `R09` and nothing else. `B08` is caught by `R08`
alone.

## Using this from a lab

A SimProc lab's `Makefile` is three lines, for example Lab 02's:

```make
COMMON := ../common
TB     ?= test_lab02
include $(COMMON)/lab.mk
```

That gives the lab every target above, with its own `build/` directory, against the same golden RTL
and bug catalogue.

## If you change the RTL

`inject.py` checks the exact text of every line before it patches it. If someone edits
`rtl/simproc_system.sv` and the line numbers move, you get this error rather than a grader that is silently wrong:

```
B01_sub_operands_swapped: rtl/simproc_system.sv line 811 has drifted.
  the catalogue expects: '            SUB:        ALUout = A - B;'
  the file actually has: ...
Refusing to inject — patching the wrong line would produce a 'broken' core that is not
broken, and every check against it would be meaningless.
```

`make verify` runs that check on all thirteen without building anything.
