# `labs/cocotb-intro` — learning cocotb on something small

Every file the cocotb guide pages talk about is here, complete and runnable. Nothing on those
pages is a fragment you have to assemble; where a page shows an excerpt it names the file it
came from.

```bash
cd labs/cocotb-intro
make
```

That is the whole setup. In the workbench container (`hpretl/iic-osic-tools:2026.04` — cocotb
2.0.1, Icarus Verilog 14.0), `make` alone runs four testbenches, nineteen tests, and prints a
verdict. Measured wall clock: **8–14 s**, depending on how busy the machine is; the simulation
itself is 0.3 s of that. No environment variables, no `pip install`, no paths to retype.

## The design under test

`rtl/counter.sv` — an 8-bit up-counter. Sixteen lines of logic:

| pin | |
|---|---|
| `clk` | |
| `rst_n` | **active low**, **synchronous** — clears `q` to 0 on a rising edge |
| `en` | count enable |
| `load`, `d[7:0]` | parallel load; **beats `en`** |
| `q[7:0]` | the count |
| `tc` | `en & (q == 8'hFF)` — high on the cycle before the count wraps |

It is small enough to hold in your head, and its pin conventions (active-low reset,
synchronous reset) are SimProc's, so nothing you learn here has to be unlearned when
you meet SimProc in Lab 02.

`rtl/counter_broken.sv` is the same file with `en &` deleted from `tc`, and nothing else.
**Every value of `q` is still correct on every cycle.** Only the flag is wrong, and only while
`en` is low. That is the shape of most real bugs, and it is why `make broken` exists.

## Targets

| | |
|---|---|
| `make` | everything below, then a verdict |
| `make hello` | `test_01_hello.py` — one test, the minimum that does anything |
| `make triggers` | `test_02_triggers.py` — six tests, one per thing about simulated time |
| `make sim` | `test_03_checking.py` on the good counter — **must PASS** |
| `make broken` | the same file on the broken counter — **must FAIL** |
| `make waves` | `test_04_waves.py`, and a `counter.fst` / `counter.vcd` to open |
| `make oldapi` | four cocotb **1.x** forms, and exactly what each one does under 2.0.1 |
| `make nothing` | a green run that tested nothing — read this one twice |
| `make clean` | |

Add `SIM=verilator` to any of them. Verified: `make sim SIM=verilator` is 6 tests, 6 PASS, same
as Icarus — the counter, unlike SimProc, lints clean.

## The files

| file | what it teaches |
|---|---|
| `test_01_hello.py` | clock, reset, one assertion |
| `test_02_triggers.py` | `Clock`, `start_soon`, `RisingEdge`, `FallingEdge`, `ClockCycles`, `Timer`, `First`, `with_timeout` |
| `test_03_checking.py` | six tests shaped so that their **failure messages** are the diagnosis |
| `test_04_waves.py` | a run shaped for looking at rather than asserting on |
| `oldapi/test_1x_units.py` | `units=` — **still works**, warns, passes. The dangerous one. |
| `oldapi/test_1x_fork.py` | `cocotb.fork` — gone, `AttributeError` |
| `oldapi/test_1x_assign.py` | `dut.sig <= 1` — gone, `TypeError` |
| `oldapi/test_1x_imports.py` | `cocotb.binary`, `cocotb.result` — fail before any test runs |
| `sim.mk` | the twelve lines that point cocotb at a Verilog file |
| `counter.gtkw` | a GTKWave save file, so you stop re-adding the same seven signals |

## Copy and change

That is the intended workflow. `make sim TB=whatever` runs whatever module you name, so:

```bash
cp test_03_checking.py test_mine.py
make sim    TB=test_mine
make broken TB=test_mine        # can it FAIL? that is the other half
```

## Two lines that look like failures and are not

**`make waves` prints its dump message after the results table**, out of order:

```
** TESTS=1 PASS=1 FAIL=0 SKIP=0                         231.00           0.01      42872.88  **
FST info: dumpfile /work/labs/cocotb-intro/build/waves/counter.fst opened for output.
```

Icarus closes the dump file at the end of the run, and the message comes from Icarus, not from
cocotb. The test already passed.

**`make broken` prints a FAIL table and then exits 0.** That is deliberate and it is the right
way round: the target's job is to check that your testbench *can* fail, so a FAIL there is the
success condition. It is `make broken` **passing** that exits non-zero, with

```
   *** test_03_checking.py PASSED on the broken counter. ***
   That is the failure. The testbench cannot see the bug.
```

Verified: `make`, `make sim` and `make broken` all exit `0` on the shipped files.
