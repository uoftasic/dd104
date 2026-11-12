# Lab 01: The adder you already trust

You'll set up the course, then take the 4-bit ripple-carry adder from DD102, a copy of it with
one line changed, and a testbench that cannot tell them apart. You'll fix the testbench so it
catches the broken adder and reports how many vectors are wrong, then ask a coverage tool the
same question.

This lab takes about 90 minutes.

Package: [`labs/lab-01-the-adder-you-already-trust/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust)

## Before you start

- Read [Getting started](guide/getting-started.md), [What a passing test proves](guide/it-works-is-not-a-result.md),
  [What a testbench is](guide/what-a-testbench-is.md),
  [Your first cocotb test](guide/your-first-cocotb-test.md),
  [The lazy testbench](guide/the-lazy-testbench.md) and
  [Coverage as a question](guide/coverage-is-a-question.md).
- You need [IC101](https://uoftasic.com/ic101/) done (the noVNC desktop opens and you can get a
  terminal) and [DD102](https://uoftasic.com/dd102/) done (you have written a `ripple4.sv`).
- `broken/ripple4.sv` is not hidden, and its header says what is wrong with it. This lab is not a
  bug hunt; that starts in [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md). You may read the
  changed line.

## Part 1: Set up

1. On your own machine, in your `workspace` clone, start the desktop:

   ```bash
   cd workspace
   ./scripts/start_vnc.sh          # Windows: scripts\start_vnc.bat
   ```

   Open <http://localhost/> and open a terminal on that desktop. Type every command from here on
   in that terminal, not on your laptop. If the page is blank or asks for a password you don't
   have, see [IC101: Launch the noVNC desktop](https://uoftasic.com/ic101/#/guide/launch-novnc).

2. Load the environment. The leading `.` is the shell's `source` command: it runs the file in
   your current shell, which is the only way a script can change your environment. Do this in
   every new terminal.

   ```bash
   . /foss/designs/common/.designinit
   ```

   You should see:

   ```
   ASIC-EDU: PDK=sky130A  PDK_ROOT=/foss/pdks  designs=/foss/designs
             run 'mod' to list course modules, or 'mod <name>' to enter one.
   ```

   In DD104 this line only defines `mod`. There is no process technology to get wrong here, so if
   `mod` already works in your terminal you can skip this step.

3. Get the course files:

   ```bash
   mod add dd104      # first time only: clones github.com/uoftasic/dd104
   mod dd104          # every time after that
   ```

   Between them, the two commands print:

   ```
   Cloning https://github.com/uoftasic/dd104.git
        into /foss/designs/modules/dd104
   Cloning into '/foss/designs/modules/dd104'...
   OK  module ready: /foss/designs/modules/dd104
       run: mod dd104
   cwd: /foss/designs/modules/dd104
   ```

   If something goes wrong:

   | What you see | What it means |
   |---|---|
   | `bash: /foss/designs/common/.designinit: No such file or directory` | The workspace is not mounted. `ls /foss/designs/` should list `common/` and `modules/`. If it is empty, relaunch `start_vnc.sh` from your `workspace` clone (see [IC101](https://uoftasic.com/ic101/)). You can still run every lab from any clone of this repo, because `make` alone needs none of this. |
   | `bash: mod: command not found` | You did not run step 2 in this terminal. Every new tab starts clean. |
   | `mod: no such module: dd104` | You ran `mod dd104` before `mod add dd104`. |
   | `fatal: could not read Username for 'https://github.com'` | git could not read the repo anonymously and is asking you to log in. Check that you typed `dd104`. If you did, ask in [Discord](https://discord.gg/hrJnP5UsGz). Do not type your password. |

4. Check your tool versions:

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

   If `cocotb-config --version` prints anything starting with `1.`, you are not in the workbench.

   Don't use `gtkwave --version` as a check. Without a display attached (in a terminal that is not
   on the noVNC desktop) it fails with
   `Could not initialize GTK!  Is DISPLAY env var/xhost set?`, which does not mean the install is
   broken. Run GTKWave from a terminal on the noVNC desktop and it works.

Check: `cocotb-config --version` prints `2.0.1` and you are in `/foss/designs/modules/dd104`.

## Part 2: Run the shipped testbench

1. Before you run anything, write down two answers. First: will the two shipped tests in
   `test_adder.py` (in the lab folder you `cd` into in step 2) catch `broken/ripple4.sv`? Second: if you ran every input the adder has, how
   many would come out wrong? Give a number. Committing to a prediction is what makes being wrong
   useful.

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
   256. The output is followed by `make: *** [Makefile:49: check] Error 1`. That error line is the verdict exiting
   non-zero on purpose ([Getting started](guide/getting-started.md#reading-a-labs-output)
   explains why). It disappears when the verdict passes.

5. Compare with your prediction. `t02` drives every value of `a` and every value of `b`, so it is
   exhaustive over two of the three inputs. The module has $4 + 4 + 1 = 9$ bits of input, and
   $2^9 = 512$, not 256.

Check: the verdict says `MISSED` on `broken/` and `VERDICT: FAIL`.

## Part 3: Fix the testbench

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
   `make check` truncates long messages to fit its table.

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
is where DD104 tells the two kinds of red apart.

Check: `make check` ends on `VERDICT: PASS`, and the failure on `broken/` says `256 of 512 vectors
are wrong`.

## Part 4: Read the count

1. Look at the count in your failure message: 256 of 512, exactly half.

2. Answer this before reading on: which signal in the port list is high in exactly half of all
   input vectors?

   A failure count of exactly half means the fault tracks a signal that is high in half the
   vectors. This module has one such input, and it is in the port list. You have narrowed the
   bug to one wire without opening the RTL.

3. Compare with the first-bad-vector version from Part 3. Asserting on the first bad vector stops
   the run at the first wrong one (index 256, the first vector with `cin = 1`) and reports one wrong
   answer. Collecting reports `256 of 512`. Only the
   second is a diagnosis.

The count is data on every design, not just adders. You'll meet these in Lab 03:

| Count | What it says |
|---|---|
| Exactly half | Tracks a signal that is high half the time |
| 65,024 of 65,536 | 512 survivors, and 512 has a description |
| 0 values wrong, 25,726 flags wrong | The arithmetic is fine; look at the flag logic |

Check: you can name the signal the 256 failures track.

## Part 5: Ask a coverage tool

1. Run the coverage add-on, a small package in the lab's `coverage/` folder:

   ```bash
   cd coverage
   make
   ```

   It takes about twelve seconds because it builds the design twice with Verilator. Both runs use
   the correct adder in `../src/` and the add-on's own stimulus files, `cov_six.sv` (the six
   hand-picked cases) and `cov_all.sv` (all 512), not your `test_adder.py`.

2. In the six-case block, you should see `design toggle points : 48`, `never toggled : 5` and
   these five points:

   ```
       ripple4.sv:3  b[2]:1->0
       ripple4.sv:4  cin:0->1
       ripple4.sv:4  cin:1->0
       ripple4.sv:8  c[0]:0->1
       ripple4.sv:8  c[0]:1->0
   ```

   The tool has no idea what an adder is and never checked an answer, and it named `cin` anyway.

3. In the all-512 block, you should see `never toggled : 1`, the point `a[3]:1->0`. The loops end
   with `a` at 15, so `a[3]` rises and the test finishes before it can fall. That is an artefact of
   loop order, not a gap in your stimulus.

4. Note `design line points : 0` in both runs. The design is continuous assignments, and line
   coverage has nothing in it to count. A report claiming "100 % line coverage" on this adder would
   be true and empty.

The add-on has its own
[`README.md`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust/coverage).

Check: six cases leave 5 points cold, including both `cin` transitions; all 512 leave 1.

## Finishing

You are done when `make check` says `VERDICT: PASS` and you have read the coverage report in
Part 5. There is nothing to submit.

| Check | Expected | |
|---|---|---|
| `make check` final line | `VERDICT: PASS` | exact |
| `make sim` total simulated time | `518.00` ns | exact |
| The log line in your sweep | `checked 512 of the 512 possible input vectors` | exact |
| The failure on `broken/` | `256 of 512 vectors are wrong` | exact |
| `make` wall clock | about 5 s | ballpark |
| `coverage/`, six cases | 48 toggle points, 5 never toggled, 0 line points | exact |
| `coverage/`, all 512 | 48 toggle points, 1 never toggled, 0 line points | exact |

One question to argue with yourself before you open
[`solutions/README.md`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust/solutions):
the reference solution keeps `t01_the_obvious_six`, even though your sweep drives every vector it
drives and 506 more. Would you delete it? The solutions README gives the case for keeping it, and
one more decision worth disagreeing with.

Next: read [Clocks, resets and triggers](guide/clocks-resets-and-triggers.md), then do
[cocotb on a counter](labs/cocotb-intro-overview.md).
