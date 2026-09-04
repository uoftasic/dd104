# Lab 04 — Your first bug hunt

Writeup: [`docs/labs/lab-04-your-first-bug-hunt-overview.md`](../../docs/labs/lab-04-your-first-bug-hunt-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-04-your-first-bug-hunt>

You get a processor with one line changed and you are not told which line. You write tests
until one of them goes red, you fix it, and you prove the fix with a test that fails on the old
core and passes on the new one.

**The deliverable is the failing test, not the fix.**

```bash
cd labs/lab-04-your-first-bug-hunt
make new         # deal a mystery core into core/
make hunt        # your testbench against it -- the loop you live in
make probe       # the same run, showing everything the simulator prints
make verdict     # the grade
```

Inside the workbench container (`hpretl/iic-osic-tools:2026.08` — cocotb 2.0.1, Icarus
Verilog 14.0). No environment setup. Includes `../common/lab.mk`, so you need the repository,
not just this directory.

## The grade has three rows

```
      ok  1. the golden core          must PASS      10 tests, all passed       9.4s
  caught  2. the core you were dealt  must FAIL      10 tests, 1 FAILED         9.3s
      ok  3. core/ as it stands now   must PASS      10 tests, all passed       9.3s
------------------------------------------------------------------------
 VERDICT: PASS
   The bug was B07_load_address_from_ra.
   It hides behind: LOAD rX, rX — loading through a pointer into itself
   It teaches: aliasing hides bugs — make every operand distinct on purpose

   Row 2 is the part worth keeping. Commit that test.
```

Row 2 is rebuilt **fresh from the catalogue** every time, never read from `core/`. You cannot
get a green row 2 by editing the file the test runs against. A patch is a thing one person did
once; a test that fails on the old core is what stops the bug coming back in a year, in a
rewrite, done by somebody who has never heard of you.

## Targets

| | |
|---|---|
| `make new` | deal a mystery core into `core/` — **this deletes any `core/` you have** |
| `make hunt` | your testbench against `core/`, with no grade attached — **summary only** |
| `make probe` | the same run, **showing the simulator's own output**: every `print()`, every `dut._log` line, live |
| `make verdict` | the three rows above |
| `make reveal` | give up. It tells you the name and what it hides behind, not the line. |
| `make sim` | your testbench against the golden core |
| `make check BUG=B05` | the two-sided check against a **named** bug, no mystery |
| `make check-all` | your testbench against all thirteen |
| `make waves` | the same run, dumping `waves.vcd` |
| `make bugs` | the catalogue: names and tiers only |
| `make clean` | remove `build/`. **It leaves `core/` alone**, so a `clean` cannot lose your hunt. |

`make new BUGPICK=B06` deals a specific one, for when you want to practise a shape rather than
be surprised.

## Seeing your own output — `make probe`

`make hunt` and `make verdict` capture the simulator's stdout and print a summary of it, so the
verdict stays a readable table. That is deliberate, and it is wrong for exactly one job: running
a small probe program and reading what it prints. Under `hunt`, a testbench full of
`print(sp.regs())` gives you this and nothing else:

```
   quiet  core/  the mystery                         1 tests, all passed        2.4s
```

**`make probe` is the escape hatch.** Same run, same core, nothing swallowed:

```console
$ make probe TB=test_probe
========================================================================
 PROBE  testbench: test_probe   target: core/
========================================================================
 Showing everything the simulator says. Your print() and dut._log
 lines are in here, in the order they happened.
------------------------------------------------------------------------
  $ cd /work/labs/lab-04-your-first-bug-hunt && \
    make -f /work/labs/common/sim.mk sim \
      COMMON=/work/labs/common \
      TB=test_probe \
      SIM=icarus \
      RTL_DIR=/work/labs/lab-04-your-first-bug-hunt/core \
      SIM_BUILD=/work/labs/lab-04-your-first-bug-hunt/build/hunt/sim \
      COCOTB_RESULTS_FILE=/work/labs/lab-04-your-first-bug-hunt/build/hunt/results.xml
------------------------------------------------------------------------
     0.00ns INFO     cocotb.regression   running test_probe.t_probe (1/1)
PROBE-PRINT regs = (60, 4, 60, 0)
 33290.00ns INFO     cocotb.tb           PROBE-LOG regs = (60, 4, 60, 0)
 33290.00ns INFO     cocotb.regression   test_probe.t_probe passed
------------------------------------------------------------------------
   quiet  core/  the mystery                         1 tests, all passed        2.5s
```

It streams as the simulation runs, so a testbench that hangs shows you *where* it hung, and it
prints the underlying `make -f sim.mk` command so you can run it by hand without reverse
engineering `hunt.py`.

| | |
|---|---|
| `make probe` | probe `test_lab04.py` |
| `make probe TB=test_probe` | probe a scratch file — **do this**; `test_probe.py` ships as a starting point |
| `make hunt VERBOSE=1` | identical to `make probe` |
| `make verdict VERBOSE=1` | all three rows of the grade, with full output for each |

Keep probes in `test_probe.py` and keep `test_lab04.py` a suite. The grade only ever runs
`TB=test_lab04`, so scaffolding in the probe file costs you nothing.

## The pool

Five bugs: `B04`, `B05`, `B06`, `B07`, `B09`. Three are in the decode path or the register
file, two are in the branch path. None of them is in the ALU — Lab 03 finished the ALU, and
every vector it can be given is already known to be right. That is not flavour text; it is a
region of the design you can stop suspecting, and narrowing the search is most of what
verification is.

## Files

| | |
|---|---|
| `test_lab04.py` | **the file you edit.** Four tests, all passing, and a TODO list of shapes. |
| `test_probe.py` | scratch space for probe programs. `make probe TB=test_probe`. Never graded. |
| `hunt.py` | deals a core, seals which one it was, and runs the three-row grade. |
| `core/` | created by `make new`. The RTL you edit. Gitignored. |
| `solutions/` | a ten-test suite that catches all five. Not before your own verdict. |

`core/.sealed` holds the answer, base64'd. Decoding it costs you the lab; `make reveal` does it
for you and says so on the way past. It is an honour system and it is stated as one.

## Golden numbers

The shipped `test_lab04.py` against the golden core:

```
** test_lab04.t01_arithmetic       PASS       33360.00 **
** test_lab04.t02_shifts           PASS       66440.00 **
** test_lab04.t03_load_and_store   PASS       66440.00 **
** test_lab04.t04_a_loop           PASS       33820.00 **
** TESTS=4 PASS=4 FAIL=0 SKIP=0              200060.00 **
```

The reference solution: 10 tests, `1319890.01` ns, and this scoreboard —

| bug | tests that fail |
|---|---|
| `B04_alu_writeback_reg_field` | 8 of 10 |
| `B05_branch_offset_zero_extended` | 2 of 10 |
| `B06_shift_amount_one_bit` | 8 of 10 |
| `B07_load_address_from_ra` | **1** of 10 |
| `B09_branch_clobbers_flags` | **1** of 10 |

Two of the five are caught by exactly one test each, and in both cases it is a test that had to
be written on purpose to catch them. That ratio is the lab.

## Scary output that is not an error

Icarus's 28 `sorry:` notes on every compile, and `make: *** [...] Error 1` under a `VERDICT:
FAIL`. Both are covered in [Lab 02's README](../lab-02-the-only-test-this-chip-has/README.md).

## Definition of done

`make verdict` says `VERDICT: PASS` — three green rows — on the core you were dealt.
