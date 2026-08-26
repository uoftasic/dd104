# `labs/common` — the harness, the assembler, and the verdict

This is the shared infrastructure every DD104 lab imports. You do not have to read all of it
before Lab 1, but everything here is written to be read: the harness is the worked example for
the code the labs ask you to write.

```bash
cd labs/common
make            # the example testbench on the good core, then on a broken one
```

Everything runs in the workbench container (`hpretl/iic-osic-tools:2026.04` — cocotb 2.0.1,
Icarus Verilog 14.0, Verilator 5.046). **No environment setup, no arguments, no paths to
retype.** If `make` works, you are ready.

---

## The one idea

Here is a testbench:

```python
@cocotb.test()
async def it_works(dut):
    pass
```

It passes. It also passes on a processor whose `SUB` computes `B - A`, on one that writes every
result into the wrong register, and on one that never finishes an instruction. It passes on
everything, so it distinguishes nothing, so it is worth nothing.

That is not a strawman. SimProc shipped with exactly one test, `test/test.py`, and what it does
is set `ui_in = 1`, wait 100 clock cycles, and assert `uo_out == 3`. Decoded against the pin
map, `3` is `uart_tx = 1` (an idle serial line), `halt = 1` (the core sitting in `IDLE`) and
`done = 0` — **it asserts that the processor is not running.** Run it yourself:

```bash
make shuttle
```

```
 THE TEST THIS CHIP SHIPPED WITH
------------------------------------------------------------------------
    PASS  the golden core                               2.8s
    PASS  B01_sub_operands_swapped                      1.3s
    PASS  B02_nand_is_nor                               1.2s
    ...
    PASS  B12_uart_rx_bit_period                        1.4s
------------------------------------------------------------------------
 13 of 13 deliberately broken processors pass the
 only test this chip has.
```

So **"my tests pass" is not a result.** The result is two-sided, and `make check` is what
measures it:

| | must | because |
|---|---|---|
| on the golden core | **PASS** | otherwise you are testing the wrong thing |
| on a broken core | **FAIL** | otherwise you are not testing anything |

```
========================================================================
 CHECK   testbench: test_example      simulator: icarus
========================================================================
      ok  the golden core                    6 tests, all passed          7.1s
  caught  B01_sub_operands_swapped           6 tests, 4 FAILED            7.6s
        t03_arithmetic_on_different_values
            AssertionError: r1 is 199, expected 247.
        t04_flags_are_state
            AssertionError: after r1 = 255 the flags are N=0 Z=0, expected N=1 Z=0
        t05_a_loop_and_its_cycle_count
            TimeoutError: the program did not reach its parking loop at address 16 within 20000 clock
        t06_against_the_golden_model
            AssertionError: instruction 19, at address 19 (0x66 = SUB   r1, r2), left the machine in a
------------------------------------------------------------------------
 VERDICT: PASS
   Your testbench passes the good core and catches B01_sub_operands_swapped.
   That bug teaches: the number is the diagnostic: 65,024 of 65,536 vectors wrong has a shape
========================================================================
```

> The seconds are wall clock and will not match yours to the digit — they are
> the only numbers in this README that vary. Everything else here is exact.

And the other outcome, which is the one worth reading carefully:

```
      ok  the golden core                    6 tests, all passed          5.9s
  MISSED  B08_store_drops_done               6 tests, all passed          5.9s
------------------------------------------------------------------------
 VERDICT: FAIL — your testbench passes B08_store_drops_done too.
   A test that passes on a broken core is not testing that core.
   That bug hides behind: checking values instead of the handshake
   Write a test whose stimulus does not do that.
========================================================================

  The verdict above is FAIL, so this target exits non-zero and make
  prints an error line under this one. That is the verdict talking,
  not a broken Makefile.
make: *** [lab.mk:66: check] Error 1
```

`make: *** Error 1` after a FAIL verdict is correct and expected. `make` reports a non-zero
exit from anything it runs, and a failed verdict is a non-zero exit on purpose — so this is
usable from a script or a CI job without anyone having to grep the text.

---

## "It FAILED" and "it blew up" are different sentences

There is a third row this verdict can print, and it is the one that matters most:

```
      ok  the golden core                    6 tests, all passed          7.1s
  BROKEN  B01_sub_operands_swapped           6 tests, 1 BLEW UP           7.4s
        t03_arithmetic_on_different_values   <- this test BLEW UP; it checked nothing
            NameError: name 'diagnosis' is not defined
------------------------------------------------------------------------
 VERDICT: FAIL -- 1 of your tests did not run to the end.
   On B01_sub_operands_swapped, it raised NameError before any comparison
   happened.
```

A test that raises `NameError` has not caught a bug. Python stopped *before* the comparison, so
the run says nothing at all about that core — and it would say the same nothing about a
perfectly correct one. cocotb writes both outcomes into `results.xml` as `<failure>`, which is
why this needs saying: a checker that reads them the same way counts a testbench that crashed
as a testbench that caught something, and prints `caught`.

DD104 shipped exactly that bug. A student was told **`3 of 3 ALU bugs caught`** by a testbench
whose exhaustive test raised `NameError` on every core it was pointed at. The three catches
were three crashes.

[`verdict.py`](verdict.py) is the one place the two are told apart, and every `check.py` and
`hunt.py` in the course reads it from there rather than deciding for itself:

| in `results.xml` | means | counts as |
|---|---|---|
| nothing inside `<testcase>` | passed | a pass |
| `error_type="AssertionError"` | your `assert` fired | **caught** |
| `error_type="TimeoutError"`, `"SimTimeoutError"`, `"ValueError"` | the harness proved the design misbehaved — a hang, a reply that never came, an X on a pin | **caught** |
| `error_type="NameError"`, `"TypeError"`, `"AttributeError"`, … | the testbench blew up | **neither** — `BROKEN` |
| `<failure>` with no `error_type` | cocotb could not even start the test | **neither** |
| `<skipped/>` | never ran | not a pass |

The list is a whitelist, not a blacklist, on purpose. Being wrong the other way round means
printing PASS.

```bash
make selftest            # the classifier and a source audit. Under a second.
make selftest FULL=1     # ... and every checker in the course, for real.
```

`selftest/` holds testbenches that are deliberately broken in specific ways, each with the
verdict it must provoke written in its own docstring. See [`selftest/README.md`](selftest/README.md).

---

## What is in here

| file | what it is |
|---|---|
| `simproc.py` | **the harness.** Clock, reset, load a program, run it, read registers / memory / flags / pins, and a bit-banged UART. Read this one. |
| `simproc_asm.py` | **the assembler.** Write `ADD(1, 0)` or a block of text with labels instead of `0x44`. Imports nothing; runs at a plain Python prompt. |
| `golden.py` | **the reference model.** SimProc's instruction set in about 120 lines of Python, to compare the real thing against. Also imports nothing. |
| `test_example.py` | **six worked tests.** Copy this file and change it — that is the intended workflow. |
| `test_reference.py` | **eleven tests that catch all thirteen bugs.** Read it *after* you have written your own. |
| `test_shuttle.py` | the test the chip actually shipped with, untouched. |
| `check.py` | the verdict: your testbench against the good core and a broken one. |
| `verdict.py` | **how a results file is read.** The one place that tells *the assertion fired* apart from *the test blew up*. Every checker in the course imports it. |
| `selftest/` | **does the grader actually grade?** Deliberately broken testbenches, and the verdict each one must provoke. `make selftest`. |
| `bugs.py` | the bug catalogue — thirteen one-line edits, with what each one teaches. |
| `gap.py` | **what the random generator covers, and what it cannot.** Nine bug-shaped windows, counted over the seeds `R10` runs and over a thousand more. No simulator. |
| `inject.py` | builds a broken core from the catalogue. Refuses if the RTL has drifted. |
| `rtl/` | the processor. Provenance and the four comment lines DD104 changed: [`rtl/README.md`](rtl/README.md). |
| `Makefile`, `lab.mk`, `sim.mk` | the targets. `lab.mk` is what a lab includes; `sim.mk` is the only place a simulator is ever launched. |

---

## Targets

| target | what it does | wall clock |
|---|---|---|
| `make` | `sim`, then `check` | 20 s |
| `make sim` | your testbench against the golden core | 7.2 s cold, 6.7 s after |
| `make waves` | the same run, dumping `waves.vcd` | 6.1 s, `waves.vcd` = 3,007,592 bytes |
| `make check` | the verdict: pass on the good core, FAIL on `BUG` | 13.3 s |
| `make check-all` | your testbench against all thirteen broken cores | 68.8 s |
| `make bugs` | the catalogue: names, tiers, and what each one teaches | instant |
| `make model` | run `golden.py` alone — no simulator involved | instant |
| `make gap` | what the random generator covers, and what it cannot | 0.9 s |
| `make selftest` | does the grader actually grade? classifier + source audit | 0.3 s |
| `make selftest FULL=1` | ... and every checker in the course, end to end | minutes |
| `make verify` | confirm every catalogue anchor still matches `rtl/` | instant |
| `make shuttle` | the shipped test, against everything | 18.5 s |
| `make clean` | remove `build/`, `waves.vcd`, `__pycache__` | |

Wall-clock figures are from the pinned container on a warm image; they move by a second or two
between runs. The simulated-time numbers further down do not move at all.

Variables, all overridable on the command line:

```bash
make sim   TB=test_mine          # run your own module instead of test_example
make check BUG=B07               # pick which broken core to check against
make sim   SIM=verilator         # the strict simulator
```

`TB` names a Python module on the path, not a file — `TB=test_mine`, not `TB=test_mine.py`.

---

## Reference numbers

Everything below was measured in the pinned container. If your numbers differ, something has
changed and it is worth finding out what.

**`make sim` — the example testbench, Icarus**

```
** TEST                                             STATUS  SIM TIME (ns) **
** test_example.t01_the_chip_answers                 PASS       13680.00 **
** test_example.t02_one_instruction                  PASS       11220.00 **
** test_example.t03_arithmetic_on_different_values   PASS       33370.00 **
** test_example.t04_flags_are_state                  PASS       99580.00 **
** test_example.t05_a_loop_and_its_cycle_count       PASS       33820.00 **
** test_example.t06_against_the_golden_model         PASS      320340.00 **
** TESTS=6 PASS=6 FAIL=0 SKIP=0                                512010.01 **
```

The simulated-time column is deterministic: **512,010.01 ns** total, every run, on both
simulators. Wall clock is about 7 s.

**`make sim TB=test_reference`** — 11 tests, all pass, **1,905,380.01 ns**, about 21 s.

**Which testbench catches which bug**

| | `test_example` | `test_reference` |
|---|---|---|
| bugs caught | **10 of 13** | **13 of 13** |
| `make check-all` | 68.8 s | about 4 min |

The three that hide from `test_example` are the three that need a *different kind* of test, not
a bigger one:

| bug | what finds it | why nothing else does |
|---|---|---|
| `B08_store_drops_done` | `R08`, counting `done` pulses | every register, flag and byte of memory is correct — 10 of the 11 reference tests pass on it |
| `B10_ori_adds_instead_of_ors` | `R02`, ORing in a bit that was already set | `0 \| imm == 0 + imm`, so the first ORI after reset is always right |
| `B12_uart_rx_bit_period` | `R11`, sweeping `clk_per_bit` | invisible at the default speed; `PING` still answers `0xAA` even where it breaks |

And one worth knowing about: `B13_store_falls_to_idle` is caught by `R08` **and** `R09` and by
nothing else. `B08` is caught by `R08` alone.

**The chip's own timing** (all measured, at the default `clk_per_bit = 32`)

| | cycles |
|---|---|
| one 3-byte UART command | 1,104 |
| a command with a reply (`PING`) | 1,353 |
| loading a 64-byte program over the wire | 70,656 |
| the same program through the memory backdoor | 2 |
| the RUN command's head start — the core is already executing this long before `uart_cmd` returns | 57 |

Instruction timing, which you can add up by hand:

| instruction | cycles |
|---|---|
| `ORI` | 5 |
| `ADD` `SUB` `NAND` `SHL` `SHR` `LOAD` | 4 |
| `STORE` `JMP` `BZ` `BNZ` `BPZ` | 3 |
| an unimplemented opcode (`0xC`, `0xD`, `0xE`) | 4, no `done` pulse, and one cycle of `halt` |

`make model` runs the sum-of-1-to-5 program through `golden.py`:

```
16 instructions in memory, 28 executed, 109 clock cycles
registers: r0=32 r1=15 r2=1 r3=32
mem[0x20] = 15   (all 28 instructions executed)
```

and `t05_a_loop_and_its_cycle_count` gets the same 109 out of the actual silicon model. That
is the check worth internalising: `30 + (4+4+3)×5 + 24 = 109`, and if the hardware says 114
then something takes one extra cycle five times, which is once per loop iteration.

**Icarus vs Verilator**, same six tests, same result:

| | wall clock | of which simulating |
|---|---|---|
| Icarus | 7.2 s | 4.4 s |
| Verilator | 17.3 s | 2.0 s |

Verilator simulates more than twice as fast and takes fifteen seconds to build first. For a
test you are running every ninety seconds while you debug, Icarus wins on the number that
matters. Icarus is the default here for that reason, not because it is better.

---

## Two walls of output that are not errors

**Icarus prints 28 lines saying `sorry:`.**

```
rtl/simproc_system.sv:552: sorry: constant selects in always_* processes are not fully
supported (the process will be sensitive to all bits in 'instr_reg_out[7:0]').
```

Twenty-eight of them, at 22 distinct places, every single time you compile. They are **notes**.
Icarus is saying it will make the process sensitive to the whole vector instead of just the
selected bits — more sensitivity, not less. **Exit code 0, simulation correct.** A real Icarus
failure starts a line with `error:` and stops.

**Verilator refuses to build the design at all.**

```
%Error: Exiting due to 12 warning(s)
```

Six `WIDTHTRUNC`, four `WIDTHEXPAND`, two `CASEINCOMPLETE` (19 with `-Wall`). That is why
`sim.mk` passes `-Wno-fatal` when `SIM=verilator`. Four of the twelve are the same real finding
at four lines:

```
%Warning-WIDTHTRUNC: rtl/simproc_system.sv:848:16: Bit extraction of array[63:0] requires
                     6 bit index, not 8 bits.
```

The RAM has 64 entries and the address bus is 8 bits wide. Verilator finds that by reading the
file in 0.4 seconds. Icarus finds it when you read address 100 at run time and eight X bits
come out of the chip's TX pin. Both are right; only one told you before you ran anything.

---

## Three things that look like they run a cocotb test and do not

1. **`python3 -m pytest test_example.py`** → `collected 0 items`, `no tests ran in 0.10s`,
   **exit 0**. It looks like the obvious command. It is green. It ran nothing.
2. **`python3 test_example.py`** → no output at all, **exit 0**. Same.
3. **A cocotb 1.x tutorial.** Most of what you find online is 1.x. Some of it still runs here
   with a deprecation warning (`units=` instead of `unit=`, `MODULE=` instead of
   `COCOTB_TEST_MODULES=`), and some of it stops dead with an error that never mentions cocotb
   (`cocotb.fork` → `AttributeError: module 'cocotb' has no attribute 'fork'`). The full
   measured list is at the top of `simproc.py`.

A cocotb test is not a Python program and not a pytest test. It needs a simulator underneath
it, and the only thing that starts one here is `make`.

---

## Writing your own testbench

Copy `test_example.py`, rename it, and run it:

```bash
cp test_example.py test_mine.py
make sim   TB=test_mine
make check TB=test_mine BUG=B01
```

The shortest complete test:

```python
import cocotb
from simproc import SimProc
from simproc_asm import ORI, ADD

@cocotb.test()
async def r1_gets_five(dut):
    sp = SimProc(dut)
    await sp.start()                              # clock, reset, blank memory
    cycles = await sp.run([ORI(5), ADD(1, 0)])    # r0 = 5 ; r1 = r1 + r0
    assert sp.reg(1) == 5, f"r1 is {sp.reg(1)}, expected 5"
    assert cycles == 9, f"took {cycles} cycles, expected 5 + 4"
```

The harness in one screen:

| | |
|---|---|
| `SimProc(dut)` · `await sp.start()` | clock, reset, RAM blanked to `0x0C` filler |
| `await sp.run(prog)` → cycles | load, run to the end, return an exact cycle count |
| `await sp.step(n)` | execute exactly `n` instructions, one at a time |
| `await sp.run_cycles(n)` | free-run for `n` cycles of execution |
| `sp.reg(i)` `sp.regs()` `sp.pc()` `sp.flags()` `sp.fsm()` | read the machine |
| `sp.peek(a)` `sp.poke(a, v)` | the memory backdoor |
| `sp.halt` `sp.done` | the pins, as `'0'` / `'1'` / `'x'` |
| `sp.describe()` | one line of everything, for failure messages |
| `await sp.count_done_pulses(n)` · `count_halt_cycles(n)` | protocol checks |
| `await sp.uart_ping()` `uart_read(a)` `uart_write(a, v)` `set_baud(u)` | the real wire |
| `await trace(sp, n, model=g)` | step and compare against `golden.py`, naming the first disagreement |

Two things about the harness that are not obvious and will cost you an hour if you meet them
the hard way:

- **`load()` writes a `JMP -1` after your program.** There is no way to stop this processor
  after exactly N instructions — `HALT` arrives over the UART and takes 1,104 cycles, and the
  core runs the whole time. So programs park themselves, the way real bare-metal test code
  does, and `run()` watches for the parking address.
- **A reset clears the registers and not the RAM.** `dp_ram` has no reset. That is what lets
  you load a program, reset the core, and start from a known state — and it is why
  `test_reference.py`'s random-program test calls `sp.reset()` between programs and the
  memory-comparison still works.

---

## Using this from a lab

A DD104 lab's `Makefile` is three lines:

```make
COMMON := ../common
TB     ?= test_lab01
include $(COMMON)/lab.mk
```

That gives the lab every target above, with its own `build/` directory, running against the
same golden RTL and the same bug catalogue.

---

## If you change the RTL

`inject.py` checks the exact text of every line it is about to patch before it patches it. If
someone edits `rtl/simproc_system.sv` and the line numbers move, you get this instead of a
silently-wrong grader:

```
B01_sub_operands_swapped: rtl/simproc_system.sv line 811 has drifted.
  the catalogue expects: '            SUB:        ALUout = A - B;'
  the file actually has: ...
Refusing to inject — patching the wrong line would produce a 'broken' core that is not
broken, and every check against it would be meaningless.
```

`make verify` runs that check on all thirteen without building anything.
