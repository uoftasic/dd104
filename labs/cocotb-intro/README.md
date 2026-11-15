# `labs/cocotb-intro`: cocotb on a counter

Writeup: [`docs/labs/cocotb-intro-overview.md`](../../docs/labs/cocotb-intro-overview.md)
· live: <https://uoftasic.com/dd104/labs/cocotb-intro-overview.html>

This package holds every file the cocotb guide pages talk about, complete and runnable, all built
around an 8-bit counter. Where a guide page shows an excerpt, it names the file here that it came
from.

```bash
cd labs/cocotb-intro
make
```

It runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) without any environment setup. `make` runs four testbenches, nineteen tests in all, and
prints a verdict. That takes 8–14 s of wall clock, of which only 0.3 s is simulation.

## Targets

| Target | What it runs |
|---|---|
| `make` | `hello`, `triggers`, `sim` and `broken`, then a verdict |
| `make hello` | `test_01_hello.py`: one test, the minimum that does anything |
| `make triggers` | `test_02_triggers.py`: six tests on simulated time |
| `make sim` | `test_03_checking.py` on the good counter; must PASS |
| `make broken` | the same file on the broken counter; must FAIL |
| `make waves` | `test_04_waves.py`, writing `counter.fst` and `counter.vcd` |
| `make oldapi` | four cocotb 1.x forms, and what each does under 2.0.1 |
| `make nothing` | a green run that tested nothing |
| `make clean` | remove `build/`, the waveform files and caches |

You can add `SIM=verilator` to any of them to use Verilator instead of Icarus.
`make sim SIM=verilator` gives the same result as Icarus, 6 tests and 6 PASS, and the counter lints clean.

`make sim` and `make broken` always run `test_03_checking`, so passing `TB=` to them has no
effect. To run your own copy of the testbench, call `sim.mk` directly and give each run its own
`SIM_BUILD`. cocotb relinks only when the sources are newer than the last build, so a second run
with a different `RTL=` in the same `SIM_BUILD` would quietly re-run the first design:

```bash
cp test_03_checking.py test_mine.py
make -f sim.mk sim TB=test_mine SIM_BUILD=build/mine
make -f sim.mk sim TB=test_mine RTL=rtl/counter_broken.sv SIM_BUILD=build/mine-broken
```

`make broken` exits 0 when the testbench fails on the broken counter, because that failure is
what it is checking for. If the testbench can't see the bug, it prints
`test_03_checking.py PASSED on the broken counter` and exits non-zero. On the shipped files, `make`, `make sim` and
`make broken` all exit 0.

## Files

| File | What it is |
|---|---|
| `rtl/counter.sv` | the design: 8-bit up-counter, active-low synchronous reset, `load` beats `en`, `tc = en & (q == 8'hFF)` |
| `rtl/counter_broken.sv` | the same file with `en &` deleted from `tc`; every value of `q` is still correct |
| `test_01_hello.py` | clock, reset, one assertion |
| `test_02_triggers.py` | `Clock`, `start_soon`, `RisingEdge`, `FallingEdge`, `ClockCycles`, `Timer`, `First`, `with_timeout` |
| `test_03_checking.py` | six tests whose failure messages are the diagnosis |
| `test_04_waves.py` | a run meant for looking at in a viewer |
| `oldapi/test_1x_units.py` | `units=`: still works, warns and passes |
| `oldapi/test_1x_fork.py` | `cocotb.fork`: gone, `AttributeError` |
| `oldapi/test_1x_assign.py` | `dut.sig <= 1`: gone, `TypeError` |
| `oldapi/test_1x_imports.py` | `cocotb.binary`, `cocotb.result`: fail before any test runs |
| `sim.mk` | the thirteen lines that point cocotb at a Verilog file |
| `counter.gtkw` | a GTKWave save file for the counter's signals |
