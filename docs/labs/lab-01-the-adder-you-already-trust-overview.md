# Lab 01: The adder you already trust

You'll load the course, then take the 4-bit ripple-carry adder from DD102, a copy of it with
one line changed, and a testbench that cannot tell them apart. You'll fix the testbench so it
catches the broken adder and reports how many vectors are wrong, then see which parts of the
adder a coverage tool says your stimulus never moved.

This lab takes about 90 minutes.

Package: [`labs/lab-01-the-adder-you-already-trust/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust)

## Before you start

- Read [Getting started](guide/getting-started.md), [What a passing test proves](guide/it-works-is-not-a-result.md),
  [What a testbench is](guide/what-a-testbench-is.md),
  [Your first cocotb test](guide/your-first-cocotb-test.md),
  [The lazy testbench](guide/the-lazy-testbench.md) and
  [Coverage as a question](guide/coverage-is-a-question.md).
- You need [IC101](https://uoftasic.com/ic101/) done (the noVNC desktop opens and you can get a
  terminal) and [DD102](https://uoftasic.com/dd102/) done (you have written a `ripple4.sv`; the lab
  ships its own copy in `src/`).
- `broken/ripple4.sv` is not hidden, and its header says what is wrong with it. This lab is not a
  bug hunt; that starts in [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md). You may read the
  changed line.

## Part 1: Load the course

Can you reach DD104's files, on the tool versions this course's outputs were recorded with?
If you haven't set up the workbench yet, do
[IC101 Lab 03](https://uoftasic.com/ic101/#/labs/lab-03-launch-the-workbench-overview) first.

1. From your `workspace` clone, start the desktop (`./scripts/start_vnc.sh`, or
   `scripts\start_vnc.bat` on Windows), open <http://localhost/> and open a terminal on the
   desktop. Type every command from here on in that terminal.

2. Load the environment and get the course files:

   ```bash
   . /foss/designs/common/.designinit   # in every new terminal
   mod add dd104                        # first time only: clones github.com/uoftasic/dd104
   mod dd104                            # every time after that
   ```

   You should see the `ASIC-EDU: PDK=sky130A ...` banner, then
   `OK  module ready: /foss/designs/modules/dd104`, then `cwd: /foss/designs/modules/dd104`.
   DD104 uses no PDK; here `.designinit` does one thing for you, which is to define `mod`.

3. Check the versions that every exact number in this course depends on:

   ```bash
   iverilog -V | head -1
   verilator --version
   cocotb-config --version
   surfer --version
   ```

   You should see:

   ```
   Icarus Verilog version 14.0 (devel) (s20260301-391-g64f13540-dirty)
   Verilator 5.050 2026-07-01 rev v5.050
   2.0.1
   surfer 0.6.0 (git: v0.6.0)
   ```

   Two `Unable to get version from ...` lines after the Icarus line are harmless; they appear
   because `head` stops reading early. If `cocotb-config` prints a version starting with `1.`, you
   are not in the workbench. Don't use `gtkwave --version` as a check: outside the noVNC desktop it
   fails with `Could not initialize GTK!  Is DISPLAY env var/xhost set?`, which doesn't mean
   GTKWave is broken.

| If you see | Do this |
|---|---|
| `bash: /foss/designs/common/.designinit: No such file or directory` | The workspace isn't mounted: relaunch `start_vnc` from your `workspace` clone. Every lab also runs from a plain clone of this repo inside the workbench image, because `make` needs none of this setup. |
| `mod: no such module: dd104` | You ran `mod dd104` before `mod add dd104`. |
| `fatal: could not read Username for 'https://github.com'` | git couldn't read the repo anonymously and is asking you to log in. Check that you typed `dd104`; if you did, ask in [Discord](https://discord.gg/hrJnP5UsGz). Don't type your password. |

For anything else, see IC101's [Troubleshooting](https://uoftasic.com/ic101/#/reference/troubleshooting) page.

Check: `cocotb-config --version` prints `2.0.1` and you are in `/foss/designs/modules/dd104`.

## Part 2: Run the shipped testbench

Does the shipped testbench catch the broken adder?

1. Before you run anything, write down two answers. You may read the lab's `test_adder.py` first.
   First: will its two shipped tests catch `broken/ripple4.sv`? Second: if you ran every input the
   adder has, how many would come out wrong? Give a number, even a guess; you'll check it in
   Part 3.

2. Run the package:

   ```bash
   cd labs/lab-01-the-adder-you-already-trust
   make
   ```

   This takes about five seconds. `make` runs `make sim` (your testbench against the good adder in
   `src/`) and then `make check` (against both adders).

3. Read the `make sim` half. You should see this summary table:

   ```
   ** TEST                                STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
   ********************************************************************************************
   ** test_adder.t01_the_obvious_six       PASS           6.00           0.00       7527.92  **
   ** test_adder.t02_every_a_and_every_b   PASS         256.00           0.01      21811.16  **
   ********************************************************************************************
   ** TESTS=2 PASS=2 FAIL=0 SKIP=0                      262.00           0.01      19078.99  **
   ```

   and, in the log above it, `checked 256 of the 512 possible input vectors`. The simulated times
   (`6.00`, `256.00`, `262.00`) and the vector count are exact. The `REAL TIME` and `RATIO`
   columns are wall clock and will differ.

4. Read the `make check` half. You should see:

   ```
   ========================================================================
    CHECK   testbench: test_adder      simulator: icarus
   ========================================================================
         ok  src/  the good adder           2 tests, all passed              1.9s
     MISSED  broken/  carry-in dropped      2 tests, all passed              1.9s
   ------------------------------------------------------------------------
    VERDICT: FAIL -- your testbench passes the broken adder too.
      broken/ripple4.sv drops the carry-in on the way into slice 0, so
      every vector with cin = 1 comes out one too small. Every vector
      with cin = 0 is perfectly correct.
      Look at the third column of your stimulus. If cin is 0 in every
      row, this bug is not reachable by anything you drove -- and you
      drove 262 of the 512 vectors this module has.
   ========================================================================
   ```

   The `262` counts `t01`'s six vectors as well as `t02`'s 256; the six are repeated inside the
   256. The output is followed by `make: *** [Makefile:49: check] Error 1`. That error line is the
   verdict exiting non-zero on purpose ([Getting started](guide/getting-started.md#reading-a-labs-output)
   explains why). It disappears when the verdict passes.

5. Compare with your first prediction. `t02` is called "every a and every b". Why does it check
   only 256 of the 512 vectors?

   <details>
   <summary>Answer</summary>

   `t02` drives every value of `a` and every value of `b`, so it is exhaustive over two of the
   three inputs. The module has $4 + 4 + 1 = 9$ bits of input, and $2^9 = 512$, not 256. `cin`
   stays at 0.

   </details>

Check: the verdict says `MISSED` on `broken/` and `VERDICT: FAIL`.

## Part 3: Fix the testbench

Can you make the testbench catch the broken adder and report how many vectors are wrong?

1. Open `test_adder.py` and find the TODO in `t02`. It asks for two changes.

2. Sweep `cin` as well. The shape you want is:

   ```python
   for cin in range(2):
       for a in range(16):
           for b in range(16):
               ...
   ```

3. Stop asserting on the first bad vector. Collect the bad ones in a list, run all 512, and
   assert once at the end with `len(bad)` in the message. Part 4 is about why. Do both changes
   before you run: `make check` will not pass with only the first one.

4. Run `make sim`. You should see `checked 512 of the 512 possible input vectors` in the log and
   `518.00` ns total simulated time (6 for `t01` plus 512 for `t02`).

5. Run `make check`. You should see:

   ```
         ok  src/  the good adder           2 tests, all passed              1.9s
     caught  broken/  carry-in dropped      2 tests, 1 FAILED                1.9s
           t02_exhaustive
               AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1=1 (want
   ------------------------------------------------------------------------
    VERDICT: PASS
   ```

   The test name in that block is whatever you called your test; the reference solution in
   `solutions/` renames `t02` to `t02_exhaustive`. The `AssertionError` line is cut off on purpose:
   `make check` truncates long messages to fit its table. Compare `256` with your second
   prediction from Part 2.

If the verdict is still FAIL, read its message. `check.py` measures how many vectors each run
drove and tells you which half of the TODO is missing. Doing only the sweep makes `broken/` fail,
but the run stops at the first wrong vector, so the failure is one anecdote instead of a count:

```
 VERDICT: FAIL -- the second half of the TODO is not done.
   You swept cin: on the good adder you drove all 512 vectors.
   On the broken adder you drove 263 and then stopped, because you are
   still asserting on the first vector that is wrong instead of collecting
   them.
```

With the loop order from step 2, the 263 is `t01`'s six vectors plus the 257 that `t02` drives up
to and including the first one with `cin = 1`.

There is one more verdict `check.py` can print. A misspelled variable in the code that builds
your failure message only runs once something is wrong, so the test passes the good adder,
crashes on the broken one, and looks like a catch:

```
  BROKEN  broken/  carry-in dropped      2 tests, 1 BLEW UP           1.3s
        t02_every_a_and_every_b   <- this test BLEW UP; it checked nothing
            NameError: name 'summary' is not defined
------------------------------------------------------------------------
 VERDICT: FAIL -- 1 of your tests did not run to the end.
```

Python stopped before the comparison, so the run says nothing about either adder. Fix the name
and rerun. [`labs/common/verdict.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/verdict.py)
is where DD104 tells a test that failed an assertion from a test that crashed.

Check: `make check` ends on `VERDICT: PASS`, and the failure on `broken/` says `256 of 512 vectors
are wrong`.

## Part 4: Read the count

What does `256 of 512` tell you about the bug before you open the RTL?

1. Look at the count in your failure message: 256 of 512, exactly half. Which input in the port
   list is high in exactly half of all input vectors? Write it down.

   <details>
   <summary>Answer</summary>

   `cin`. A failure count of exactly half means the fault tracks a signal that is high in half the
   vectors, and in a space of $16 \times 16 \times 2$ only `cin` has that shape. You have narrowed
   the bug to one wire without opening the RTL.

   </details>

2. Compare with the first-bad-vector verdict quoted in Part 3. What does each style of test
   report on the broken adder?

   <details>
   <summary>Answer</summary>

   Asserting on the first bad vector stops the run at the first wrong one (index 256, the first
   vector with `cin = 1`) and reports one wrong answer. Collecting reports `256 of 512`. Only the
   second is a diagnosis.

   </details>

The count is data on every design, not just adders. You'll meet these in Lab 03:

| Count | What it says |
|---|---|
| Exactly half | Tracks a signal that is high half the time |
| 65,024 of 65,536 | 512 survivors, and 512 has a description |
| 0 values wrong, 25,726 flags wrong | The arithmetic is fine; look at the flag logic |

Check: you can name the signal the 256 failures track.

## Part 5: Ask a coverage tool

Which parts of the adder did the six hand-picked cases never move?

1. Before you run it, write down which input you expect six hand-picked cases never to toggle.

2. Run the coverage add-on, a small package in the lab's `coverage/` folder:

   ```bash
   cd coverage
   make
   ```

   It takes about twelve seconds because it builds the design twice with Verilator. Both runs use
   the correct adder in `../src/` and the add-on's own stimulus files, `cov_six.sv` (the six
   hand-picked cases) and `cov_all.sv` (all 512), not your `test_adder.py`.

3. In the six-case block, you should see `design toggle points : 48`, `never toggled : 5` and
   these five points:

   ```
       ripple4.sv:3  b[2]:1->0
       ripple4.sv:4  cin:0->1
       ripple4.sv:4  cin:1->0
       ripple4.sv:8  c[0]:0->1
       ripple4.sv:8  c[0]:1->0
   ```

   `cin` never moved in either direction. Why is `c[0]` cold too?

   <details>
   <summary>Answer</summary>

   `c[0]` is the internal carry wire that `cin` drives (`assign c[0] = cin;` in `ripple4.sv`), so
   it is cold for the same reason. The tool has no idea what an adder is and never checked an
   answer, and it named `cin` anyway.

   </details>

4. In the all-512 block, you should see `never toggled : 1`, the point `a[3]:1->0`. Every input
   combination ran. Why does one point stay cold?

   <details>
   <summary>Answer</summary>

   The loops in `cov_all.sv` end with `a` at 15, so `a[3]` rises and the test finishes before it
   can fall. That is an artefact of loop order, not a gap in your stimulus.

   </details>

5. Note `design line points : 0` in both runs. What would a report of "100 % line coverage" on
   this adder tell you?

   <details>
   <summary>Answer</summary>

   Nothing. The design is continuous assignments, and line coverage has nothing in it to count. The
   claim would be true and empty, and true of the six-case run and the exhaustive run alike.

   </details>

The add-on has its own
[`README.md`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust/coverage).

Check: six cases leave 5 points cold, including both `cin` transitions; all 512 leave 1.

## Expected results

| Check | Expected | |
|---|---|---|
| `make check` final line | `VERDICT: PASS` | exact |
| `make sim` total simulated time | `518.00` ns | exact |
| The log line in your sweep | `checked 512 of the 512 possible input vectors` | exact |
| The failure on `broken/` | `256 of 512 vectors are wrong` | exact |
| `make` wall clock | about 5 s | ballpark |
| `coverage/`, six cases | 48 toggle points, 5 never toggled, 0 line points | exact |
| `coverage/`, all 512 | 48 toggle points, 1 never toggled, 0 line points | exact |

## Finishing

You're done when `make check` on your `test_adder.py` ends on `VERDICT: PASS` and its failure on
`broken/` says `256 of 512 vectors are wrong`.

Questions:

1. The reference solution keeps `t01_the_obvious_six`, even though your sweep drives every vector
   it drives and 506 more. Would you delete it? Decide before you open the answer.

   <details>
   <summary>Answer</summary>

   Both choices are defensible. The reference keeps it because a test suite is read as often as it
   is run: six named cases with a comment document what the module is for, and they are the first
   row to go red when somebody deletes the module.
   [`solutions/README.md`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust/solutions)
   gives the full case, and one more decision worth disagreeing with.

   </details>

Submit: nothing for this lab.

Next on the Course path: read [Clocks, resets and triggers](guide/clocks-resets-and-triggers.md),
[cocotb 2.x and older tutorials](guide/cocotb-2x-vs-every-tutorial.md),
[Driving and checking a design](guide/driving-and-checking.md) and [Waveforms](guide/waveforms.md),
then do [Lab: cocotb on a counter](labs/cocotb-intro-overview.md).
