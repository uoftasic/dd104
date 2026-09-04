# Lab 02 — The only test this chip has

Writeup: [`docs/labs/lab-02-the-only-test-this-chip-has-overview.md`](../../docs/labs/lab-02-the-only-test-this-chip-has-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-02-the-only-test-this-chip-has>

Meet SimProc — a real 8-bit processor a student team designed and taped out — and the single
test it shipped with. Run that test against thirteen deliberately broken versions of the chip.
All thirteen pass.

```bash
cd labs/lab-02-the-only-test-this-chip-has
make shuttle     # start here
make             # then this: sim, check, and a verdict
```

Inside the workbench container (`hpretl/iic-osic-tools:2026.08` — cocotb 2.0.1, Icarus
Verilog 14.0). No environment setup. This lab includes `../common/lab.mk`, so you need the
repository, not just this directory.

## Targets

Everything here comes from [`../common/lab.mk`](../common/lab.mk), which every DD104 lab
includes.

| | | wall clock |
|---|---|---|
| `make shuttle` | the shipped test, against the golden core and all thirteen broken ones | ~24 s |
| `make` | `sim`, then `check` | ~8 s |
| `make sim` | your testbench against the golden core | ~4 s |
| `make check` | the verdict: PASS on golden, FAIL on `BUG` (default `B01`) | ~4 s |
| `make check BUG=B06` | pick a different broken core | |
| `make check-all` | your testbench against all thirteen | ~22 s |
| `make waves` | the same run, dumping `waves.vcd` | ~2 s |
| `make bugs` | the catalogue: names, tiers, and what each one teaches | instant |
| `make model` | run the golden model with no simulator involved | instant |
| `make clean` | remove `build/`, `waves.vcd`, `__pycache__` | |

Wall-clock figures are BALLPARK and move by a second or two. Everything else on this page is
exact.

## Files

| | |
|---|---|
| `test_lab02.py` | **the file you edit.** Three tests, all passing, one TODO. |
| `solutions/` | a reference solution. Do not open it before your own verdict says PASS. |

The harness, the assembler, the golden model, the bug catalogue and the RTL all live in
[`../common/`](../common/README.md). Read that README when you want the full API; the
docstrings in `test_lab02.py` carry what this lab needs.

## The number this lab exists for

```
------------------------------------------------------------------------
 13 of 13 deliberately broken processors pass the
 only test this chip has.
========================================================================
```

`13 of 13` is golden. `test/test.py` from the SimProc repository sets `ui_in = 1`, waits 100
clock cycles, and asserts `uo_out == 3`. Decoded through the pin map that is `uart_tx = 1`
(idle line), `halt = 1` (core in IDLE), `done = 0` — **it asserts that the processor is not
running.**

## What `make sim` prints on the shipped file

```
** test_lab02.t01_the_test_this_chip_shipped_with      PASS        1150.00 **
** test_lab02.t02_what_that_number_meant               PASS        1160.00 **
** test_lab02.t03_one_instruction_that_actually_runs   PASS       33300.00 **
** TESTS=3 PASS=3 FAIL=0 SKIP=0                                   35610.00 **
```

All four simulated-time figures are **golden**. So is `one ORI, 5 clock cycles, r0 = 5` in the
log: `ORI` costs five cycles on this machine, always.

Then `make check` says:

```
      ok  the golden core                    3 tests, all passed          1.9s
  MISSED  B01_sub_operands_swapped           3 tests, all passed          2.0s
------------------------------------------------------------------------
 VERDICT: FAIL — your testbench passes B01_sub_operands_swapped too.
```

## Two things that look like errors and are not

**Icarus prints 28 lines saying `sorry:`,** on every compile, from here to the end of the
course:

```
rtl/simproc_system.sv:552: sorry: constant selects in always_* processes are not fully
supported (the process will be sensitive to all bits in 'instr_reg_out[7:0]').
```

They are notes. Icarus is telling you it will make a process sensitive to a whole vector
instead of a slice of it — more sensitivity, not less. Exit code 0, simulation correct. A real
Icarus failure starts a line with `error:` and stops.

**`make: *** [../common/lab.mk:66: check] Error 1`** under a `VERDICT: FAIL`. A failed verdict
exits non-zero on purpose. That line is the verdict talking, not a broken Makefile.

## Definition of done

`make check` says `VERDICT: PASS` — your testbench passes the golden core and fails on a named
broken one.
