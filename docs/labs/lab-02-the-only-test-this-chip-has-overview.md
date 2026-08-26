# Lab 02 — The only test this chip has

Full runnable package: [`labs/lab-02-the-only-test-this-chip-has/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-02-the-only-test-this-chip-has).

SimProc is a real 8-bit processor. Four registers, 64 bytes of memory, sixteen opcodes, a UART
you can talk to, 1,178 lines of SystemVerilog. A student team on this course's own team
designed it and taped it out.

It shipped with one test. In the first five minutes of this lab you are going to run that test
against thirteen deliberately broken versions of the chip, and all thirteen are going to pass.

## Prerequisites

- [Lab 01](labs/lab-01-the-adder-you-already-trust-overview.md) complete — `make check` said `VERDICT: PASS`
- Read [SimProc in one page](guide/simproc-in-one-page.md) *(not yet written)* and
  [Driving and checking a design](guide/driving-and-checking.md)
- Skim [Two simulators, two jobs](guide/two-simulators-two-jobs.md) *(not yet written)* — you will meet Verilator properly in Lab 03
- `cocotb-config --version` says **`2.0.1`**

> **This lab includes `../common/lab.mk`.** You need the whole repository checked out, not just
> the lab directory. Every lab from here on does the same.

## Objectives

- Produce, yourself, the number this course is built on: **13 of 13**
- Decode a chip's output pins from its pin map, and say what an assertion on them actually claims
- Drive a real processor from Python: PING it, poke memory, run a program, read a register
- Write one test that passes on the golden core and **fails on a named broken one**
- Open a waveform of a whole processor while it is still small enough to read
- Recognise Icarus's 28 `sorry:` notes on sight, for the rest of the course

## Theory (short)

**The prior this lab overwrites:** *I will know a broken chip when I see it.* Everyone who
worked on SimProc saw this chip. It shipped.

Here is the entire test SimProc came with — `test/test.py` in the upstream repository, which is
the TinyTapeout template with the module name changed:

```python
dut.ui_in.value  = 1
dut.uio_in.value = 0
await ClockCycles(dut.clk, 100)
assert dut.uo_out.value == 3
```

The `3` is the interesting part. Decode it against the pin map:

| pin | | value in `3` |
|---|---|---|
| `uo_out[0]` | `uart_tx` | `1` — the serial line, idle high |
| `uo_out[1]` | `halt` | `1` — the core is sitting in `IDLE` |
| `uo_out[2]` | `done` | `0` — no instruction retired this cycle |
| `uo_out[7:3]` | unused | `0` |

$3 = 0b00000011$. **The test asserts that the processor is not running.** It sends no command,
loads no program, executes no instruction, and never sets `run`.

That is not a strawman written for this course. It is the file that shipped, and DD104 keeps a
byte-identical copy of it at `labs/common/test_shuttle.py`.

The rest of the theory is in [SimProc in one page](guide/simproc-in-one-page.md) — the register
set, the instruction encoding, the five-state FSM and the UART command protocol. Read it once
now; you will come back to it in every later lab.

## Procedure

```bash
mod dd104
cd labs/lab-02-the-only-test-this-chip-has
make shuttle     # start here
```

### Step 1 — The opening argument, produced by you

- **Try this:** `make shuttle`. About **24 seconds** — it builds and runs fourteen processors.
- **What you should see:**

  ```
  ========================================================================
   THE TEST THIS CHIP SHIPPED WITH
  ========================================================================
   test/test.py, from the SimProc repository, untouched. It sets
   ui_in = 1, waits 100 clock cycles, and asserts uo_out == 3.
   Decoded: uart_tx = 1 (idle), halt = 1 (IDLE), done = 0.
   It asserts that the processor is NOT RUNNING.
  ------------------------------------------------------------------------
      PASS  the golden core                              1.4s
      PASS  B01_sub_operands_swapped                     1.4s
      PASS  B02_nand_is_nor                              1.4s
      PASS  B03_zero_flag_low_nibble                     1.4s
      PASS  B04_alu_writeback_reg_field                  1.3s
      PASS  B06_shift_amount_one_bit                     1.6s
      PASS  B07_load_address_from_ra                     1.5s
      PASS  B05_branch_offset_zero_extended              1.8s
      PASS  B09_branch_clobbers_flags                    2.6s
      PASS  B08_store_drops_done                         1.6s
      PASS  B13_store_falls_to_idle                      2.1s
      PASS  B10_ori_adds_instead_of_ors                  1.7s
      PASS  B11_ori_writes_r1_reads_r0                   2.3s
      PASS  B12_uart_rx_bit_period                       1.6s
  ------------------------------------------------------------------------
   13 of 13 deliberately broken processors pass the
   only test this chip has.
  ========================================================================
  ```

  **`13 of 13` is GOLDEN.** The names are golden. The seconds are wall clock and will not match.

- **Why an engineer cares:** every one of those thirteen is a **single-line edit** to
  `simproc_system.sv`. One of them makes `SUB` compute `B - A`. One writes every arithmetic
  result into the wrong register. One never finishes a `STORE`. The chip's own test suite has
  nothing to say about any of them, because it never asks the chip to do anything.

  **The only test this chip has, passes on a processor whose `SUB` is backwards.** Everything in
  the rest of this course follows from that sentence.

`make bugs` prints the catalogue — thirteen names, five tiers, and one line each about what the
bug *teaches*. It does not print what any of them changes, and neither does this page.

> **Expect a wall of `sorry:` before your first result.** Icarus prints **28** of these on
> every single compile, from now until the end of the course:
>
> ```
> rtl/simproc_system.sv:552: sorry: constant selects in always_* processes are not fully
> supported (the process will be sensitive to all bits in 'instr_reg_out[7:0]').
> ```
>
> They are **notes**, not errors. Icarus is telling you it will make a process sensitive to a
> whole vector instead of a slice of it — more sensitivity, not less, so the simulation is
> correct. Exit code 0. A real Icarus failure starts a line with `error:` and stops. The full
> catalogue of scary-but-normal output is
> [Output that is not an error](reference/output-that-is-not-an-error.md).

### Step 2 — Make the chip do something

- **Try this:** `make sim`. This runs `test_lab02.py`, which ships working.
- **What you should see:**

  ```
  ** test_lab02.t01_the_test_this_chip_shipped_with      PASS        1150.00 **
  ** test_lab02.t02_what_that_number_meant               PASS        1160.00 **
  ** test_lab02.t03_one_instruction_that_actually_runs   PASS       33300.00 **
  ** TESTS=3 PASS=3 FAIL=0 SKIP=0                                   35610.00 **
  ```

  and in the log:

  ```
  PING -> 0xAA, and the core is IDLE
  halt=1 done=0 state=IDLE — this is a processor doing nothing, and t01 asserted exactly that
  one ORI, 5 clock cycles, r0 = 5
  ```

  **All four simulated-time figures and the `5 clock cycles` are GOLDEN.**

- **Why an engineer cares:** this is where SimProc stops being 1,178 intimidating lines and
  becomes a thing with knobs on it. Three lines of Python and it is executing instructions:

  ```python
  sp = SimProc(dut)
  await sp.start()                 # clock, reset, RAM blanked
  await sp.run([ORI(5)])           # load a program, run it to its parking loop
  assert sp.reg(0) == 5
  ```

  `t01` and `t02` are worth comparing carefully. They assert the same thing at the same instant
  on the same chip, and both are exactly as weak as the shipped test — both pass on all
  thirteen broken cores. `t02` is a better *sentence*, not a better test: when it fails, the
  message names the pin instead of handing you an integer to decode at 2 a.m. Assert on the
  decoded meaning, not on the bus value. It costs nothing.

The whole harness API is in
[The SimProc harness](reference/the-harness-api.md); the two-page version is in the docstring
at the top of `test_lab02.py`.

### Step 3 — Open a waveform, while it is still small

- **Try this:** `make waves`, then `surfer waves.vcd` (or `gtkwave waves.vcd`).
- **What you should see:** about **2 seconds**, and `waves.vcd` at **337,999 bytes** — GOLDEN,
  because it is a dump of a deterministic simulation.
- **Why an engineer cares:** a whole processor is a great many signals and a waveform viewer
  will happily show you all of them at once, which is useless. Do this now, on a
  three-instruction run, and learn the navigation while the trace is 35,610 ns long instead of
  two million.

  Start with `clk` and `uo_out`. Then open `tb` → the `tt_um_ieeeuoftasic_simproc` instance →
  `U1` → `CPU1` and add `curr_state`. That one signal is the five-state FSM, and watching it
  walk `IDLE → CYCLE_1 → … → IDLE` next to `done` is the fastest way to understand how this
  machine actually executes anything.

  More on when a waveform is the right tool and when it is procrastination:
  [Waveforms, when the assertion is not enough](guide/waveforms.md).

### Step 4 — Predict, then be wrong

- **Try this:** before running `make check`, decide whether `t03` — which loads `ORI 5`, runs
  it, and asserts `r0 == 5` — would catch a processor whose subtractor has its operands
  backwards.
- **What you should see:**

  ```
        ok  the golden core                    3 tests, all passed          1.9s
    MISSED  B01_sub_operands_swapped           3 tests, all passed          2.0s
  ------------------------------------------------------------------------
   VERDICT: FAIL — your testbench passes B01_sub_operands_swapped too.
     A test that passes on a broken core is not testing that core.
     That bug hides behind: SUB rX, rX — the idiom for 'clear a register'
     Write a test whose stimulus does not do that.
  ========================================================================
  ```

- **Why an engineer cares:** of course it does not catch it — `t03` never subtracts. The
  interesting part is the hint. `SUB rX, rX` is the idiom for clearing a register, it appears in
  nearly every program on this machine, and it is one of the operand pairs where `A - B` and
  `B - A` are the same number. So is every pair where `A == B`, and so is every pair whose
  difference is 128, because 128 is its own negation in eight bits.

  That is $256 + 256 = 512$ of the 65,536 possible operand pairs — **0.78 % of the input
  space** — and the single most natural subtraction test you could write lands inside it.

> **`make: *** [../common/lab.mk:64: check] Error 1`** appears under every failed verdict. It
> is the verdict talking: a `FAIL` exits non-zero on purpose so that a script or a CI job can
> read the result without grepping text. Not a broken Makefile.

### Step 5 — Write the test

- **Try this:** do the TODO in `t03`. Add a test that subtracts two registers holding
  **different** values and checks the result. `set_reg(1, 200) + set_reg(2, 60) + [SUB(1, 2)]`
  leaves r1 at $200 - 60 = 140$ on a correct core. Work out what a swapped subtractor gives
  before you run it.
- **What you should see:**

  ```
        ok  the golden core                    4 tests, all passed          3.6s
    caught  B01_sub_operands_swapped           4 tests, 1 FAILED            3.2s
          t04_subtract_two_different_numbers
              AssertionError: r1 is 116, expected 140 (200 - 60).
  ------------------------------------------------------------------------
   VERDICT: PASS
  ```

  **`140` and `116` are GOLDEN.** $60 - 200 = -140$, and $-140$ in eight bits is $116$.

- **Why an engineer cares:** you have just written a better test than the one a real chip taped
  out with, in about six lines, and you can prove it — not by arguing, but by running it against
  something that is wrong.

  If you also asserted the flags, check your prediction of `N`. $140 = 0b10001100$, so bit 7 is
  set and `N` is **1**. The machine has no opinion about whether that byte means 140 or -116;
  `N` is literally bit 7 of the result. Getting this wrong makes row 1 of the verdict go red,
  which is the correct order for it to go wrong in — a testbench that fails on the golden core
  is telling you about itself. See [Flags are architectural state](guide/flags-are-state.md).

## Expected results

| Check | Expected | |
|---|---|---|
| `make shuttle` final count | `13 of 13` | **GOLDEN** |
| `make shuttle` wall clock | about 24 s | BALLPARK |
| `make sim` total sim time, shipped file | `35610.00` ns | **GOLDEN** |
| the `ORI` cycle count in the log | `5 clock cycles` | **GOLDEN** |
| `make waves` output file | `waves.vcd`, `337999` bytes | **GOLDEN** |
| Icarus `sorry:` notes per compile | `28` | **GOLDEN** |
| `make check` on the shipped file | `VERDICT: FAIL`, `MISSED` | **GOLDEN** |
| `make check` when you are done | `VERDICT: PASS`, `caught` | |

Wall-clock seconds are the only figures allowed to differ.

## Going further

`make check-all` runs your testbench against all thirteen broken cores — about **22 seconds** —
and prints, for each one you missed, a single line about what it hides behind. Run it now and
keep the output. It is the scoreboard for the rest of the course, and by
[Lab 06](labs/lab-06-capstone-overview.md) the goal is `13 of 13 caught`.

On the shipped file it says **`1 of 13 caught`**, and the one it catches is worth a moment:

```
  caught  tier 5  B11_ori_writes_r1_reads_r0         t03_one_instruction_th   2.3s
```

`t03` runs a single `ORI 5` and checks r0, and that alone is enough to catch a tier-5 bug — one
of the three the reference suite needed a purpose-built test for. `ORI` is the only way to get a
constant into this machine, so a bug on that path is a bug on the critical path of every
program anybody writes.

Which is a useful early lesson about tiers: **the tier is how hard a bug is to think of, not how
hard it is to trip over.** You will meet `B11` again in
[Lab 06](labs/lab-06-capstone-overview.md), where its interest turns out to be its provenance rather than
its difficulty.

Expect the other twelve to stay missed. Three tests should not catch thirteen bugs, and if they
did, the bugs would not be worth having.

## Links

- [Lab package](https://github.com/uoftasic/dd104/tree/main/labs/lab-02-the-only-test-this-chip-has)
- [The harness](https://github.com/uoftasic/dd104/tree/main/labs/common) — the shared infrastructure every lab from here imports
- [SimProc in one page](guide/simproc-in-one-page.md) · [The SimProc instruction set](reference/simproc-instruction-set.md)
- [Output that is not an error](reference/output-that-is-not-an-error.md) — the `sorry:` notes, and everything else that looks like a crash and is not
- Next lab: [Lab 03 — Three blocks before the processor](labs/lab-03-three-blocks-before-the-processor-overview.md), where 1,178 lines become 16, 31 and 34
