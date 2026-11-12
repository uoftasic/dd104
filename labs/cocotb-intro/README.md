# `labs/cocotb-intro`: cocotb on a counter

Writeup: [`docs/labs/cocotb-intro-overview.md`](../../docs/labs/cocotb-intro-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/cocotb-intro-overview>

Every file the cocotb guide pages talk about, complete and runnable, on an 8-bit counter. Where a
guide page shows an excerpt, it names the file here that it came from.

```bash
cd labs/cocotb-intro
make
```

Runs in the workbench container (`hpretl/iic-osic-tools:2026.08`: cocotb 2.0.1, Icarus Verilog
14.0) with no environment setup. `make` runs four testbenches, nineteen tests, and prints a
verdict in 8–14 s of wall clock, of which 0.3 s is simulation.

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

Add `SIM=verilator` to any of them. `make sim SIM=verilator` gives 6 tests, 6 PASS, the same as
Icarus; the counter lints clean.

`make sim` and `make broken` always run `test_03_checking`; passing `TB=` to them has no effect.
To run your own copy, call `sim.mk` directly and give each run its own `SIM_BUILD`:

```bash
cp test_03_checking.py test_mine.py
make -f sim.mk sim TB=test_mine SIM_BUILD=build/mine
make -f sim.mk sim TB=test_mine RTL=rtl/counter_broken.sv SIM_BUILD=build/mine-broken
```

`make broken` exits 0 when the testbench fails on the broken counter, because that failure is
what it is checking for. It exits non-zero, printing `test_03_checking.py PASSED on the broken
counter`, if the testbench cannot see the bug. `make`, `make sim` and `make broken` all exit 0 on
the shipped files.

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
| `sim.mk` | the twelve lines that point cocotb at a Verilog file |
| `counter.gtkw` | a GTKWave save file for the counter's signals |
