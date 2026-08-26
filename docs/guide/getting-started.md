# Getting started

**Question this page answers:** *How do I get from a browser tab to a prompt where a
processor runs inside a Python test?*

You already did the hard part in [IC101](https://uoftasic.com/ic101/) and you have been
living in this container since [DD102](https://uoftasic.com/dd102/). This page is four
commands, a version check, and one four-second run that is also the whole argument of the
course.

**DD104 is the lightest course in the digital track to set up.** No PDK, no liberty file, no
`STD_CELL_LIBRARY`, no LibreLane. Nothing here is ever mapped to silicon. Simulation is the
entire tool story: a simulator, Python, and a waveform viewer.

## 1. Start the desktop

On your own machine, in your `workspace` clone:

```bash
cd workspace
./scripts/start_vnc.sh          # Windows: scripts\start_vnc.bat
```

Then open **http://localhost/** and open a terminal on that desktop. Every command from here
down is typed *inside* that terminal, not on your laptop.

Ports, passwords, resolution, and what to do when the page is blank: [IC101 — Launch the
noVNC desktop](https://uoftasic.com/ic101/#/guide/launch-novnc).

## 2. Load the environment

```bash
. /foss/designs/common/.designinit
```

```
ASIC-EDU: PDK=sky130A  PDK_ROOT=/foss/pdks  designs=/foss/designs
          run 'mod' to list course modules, or 'mod <name>' to enter one.
```

That leading `.` is the shell's `source` command — it runs the file *in your current shell*,
which is the only way a script can change your environment. You must do this in **every new
terminal**; it does not stick.

**In DD104 this line does exactly one thing for you: it defines `mod`.** DD103 needed it to
point the tools at the right process technology, and getting that wrong silently cost you a
whole run. Here there is no process technology to get wrong. If `mod` already works in your
terminal, you can skip this step entirely, and every lab in this course will still run.

> **Every DD104 lab runs with `make` alone, in a bare container, with no environment setup.**
> That is a design rule for this course, not a happy accident. If some setup step fails at 2
> a.m., type `make` anyway — the labs pin their own paths and will tell you what they found.

## 3. Get the course files

```bash
mod add dd104      # first time only — clones github.com/uoftasic/dd104
mod dd104          # every time after that
```

```
Cloning https://github.com/uoftasic/dd104.git
     into /foss/designs/modules/dd104
Cloning into '/foss/designs/modules/dd104'...
OK  module ready: /foss/designs/modules/dd104
    run: mod dd104
cwd: /foss/designs/modules/dd104
```

Everything lands under `/foss/designs/modules/`, which is your `workspace` folder
bind-mounted into the container. **Your files are on your disk.** Deleting the container does
not delete your work.

### Four errors you will see at least once

| What you see | What it means |
|---|---|
| `bash: /foss/designs/common/.designinit: No such file or directory` | The workspace is not mounted. `ls /foss/designs/` should list `common/` and `modules/`; if it is empty, relaunch `start_vnc.sh` from your `workspace` clone — see [IC101](https://uoftasic.com/ic101/). **You have not broken DD104, and you can still run every lab: `make` alone needs none of this.** |
| `bash: mod: command not found` | You did not run step 2 *in this terminal*. Every new tab starts clean. |
| `mod: no such module: dd104` | You ran `mod dd104` before `mod add dd104`. |
| `fatal: could not read Username for 'https://github.com'` | git is being asked to log in, which means it could not read the repo anonymously. Check the spelling first; if it is right, ask in [Discord](https://discord.gg/hrJnP5UsGz) — do not type your password. |

## 4. Check your versions

This course is pinned to `hpretl/iic-osic-tools:2026.04`. Four tools matter, and the two that
matter most are Icarus and cocotb:

```bash
iverilog -V | head -1
verilator --version
cocotb-config --version
surfer --version
```

```
Icarus Verilog version 14.0 (devel) (s20251012-145-g9b0d46b4-dirty)
Verilator 5.046 2026-02-28 rev v5.046
2.0.1
surfer 0.6.0 (git: v0.6.0)
```

**`2.0.1` is the number that will save you the most time.** Read the next box before you
search the internet for anything.

> ### ⚠ cocotb 2.x breaks every cocotb tutorial you will find online
>
> cocotb 2.0 renamed things that appear in the first five lines of every 1.x example, and
> most of what a search engine returns is 1.x. Two renames account for nearly all of it:
>
> | 1.x — what you will find online | 2.x — what runs here |
> |---|---|
> | `Timer(1, units="ns")` | `Timer(1, unit="ns")` |
> | `MODULE = test_thing` in the Makefile | `COCOTB_TEST_MODULES = test_thing` |
>
> The first one does not stop you. It warns, and the warning is easy to scroll past:
>
> ```
> DeprecationWarning: The 'units' argument has been renamed to 'unit'.
> ```
>
> The second one *does* stop you, and the failure is silent in the worst way: cocotb runs, the
> simulator runs, and no tests are found. And some 1.x code dies with an error that never
> mentions cocotb versions at all:
>
> ```
> AttributeError: module 'cocotb' has no attribute 'fork'
> ```
>
> (`cocotb.fork` became `cocotb.start_soon`.) When a tutorial disagrees with this course, this
> course is describing the cocotb actually sitting on your disk. The full list is in
> [cocotb 2.x vs every tutorial you will find](guide/cocotb-2x-vs-every-tutorial.md).

`gtkwave --version` is the one version check that will fail on you for an uninteresting
reason:

```
Could not initialize GTK!  Is DISPLAY env var/xhost set?
```

GTKWave will not even tell you its version without a display attached. That is not a broken
install. Run it from a terminal **on the noVNC desktop** and it works.

## 5. Your first run, which is also the point of the course

```bash
cd labs/lab-01-the-adder-you-already-trust
make
```

About **four and a half seconds**, against the same 4-bit adder you wrote in DD102. Two
tests pass, and then the verdict tells you they were not worth much:

```
   ** test_adder.t01_the_obvious_six       PASS           6.00           0.00       8762.47  **
   ** test_adder.t02_every_a_and_every_b   PASS         256.00           0.01      21111.30  **
   ** TESTS=2 PASS=2 FAIL=0 SKIP=0                      262.00           0.01      18538.90  **

   Green. That is half a verdict. 'make check' is the other half.
========================================================================
 CHECK   testbench: test_adder      simulator: icarus
========================================================================
      ok  src/  the good adder           2 tests, all passed          1.2s
  MISSED  broken/  carry-in dropped      2 tests, all passed          1.2s
------------------------------------------------------------------------
 VERDICT: FAIL -- your testbench passes the broken adder too.
========================================================================
```

If you got that, your toolchain is correct and you are ready. What `MISSED` means — and why
a testbench that checks all 256 combinations of `a` and `b` still misses a broken adder — is
[The lazy testbench](guide/the-lazy-testbench.md), the third page of the guide.

> ### ⚠ The `FAIL` is supposed to be there, and so is the `make` error under it
>
> ```
> make: *** [Makefile:49: check] Error 1
> ```
>
> **That is the verdict talking, not a broken Makefile.** Every DD104 lab's verdict exits
> non-zero when it fails, on purpose, so it can be used from a script or a CI job without
> anyone having to grep the text — and `make` faithfully reports the non-zero exit. The lab
> prints two lines saying exactly this immediately above it. You will see it a lot, and the
> day it goes away is the day you have finished the lab.

## Three things that look like they run a cocotb test and do not

This costs everybody an hour once. A cocotb test is **not** a Python program and **not** a
pytest test. It needs a simulator underneath it, and the only thing that starts one is `make`.

```bash
python3 -m pytest test_adder.py
```

```
collected 0 items

============================ no tests ran in 0.06s =============================
```

Exit code **5**. It is the most obvious command in the world, it is not an error message, and
it ran nothing.

```bash
python3 test_adder.py
```

**No output at all. Exit code 0.** Zero bytes on stdout, zero on stderr. The file imported
cleanly, defined a function decorated with `@cocotb.test()`, and ended.

And the third: **any cocotb 1.x tutorial**, per the box in step 4.

## Reading waveforms

DD104 gives you a waveform when you ask for one:

```bash
make waves          # in any SimProc lab package
surfer waves.vcd    # or: gtkwave waves.vcd
```

**Launch waveform viewers by typing their name in a terminal, never from a desktop icon.**
Both of them write their real complaints to the terminal they were started from. Started from
a menu, that terminal does not exist, and a viewer that cannot open your file just sits there
looking normal.

A whole processor is a lot of signals, and the default view of one is not useful. Start with
`clk`, `uo_out`, and the core's state register — each lab writeup names the exact signals
worth adding first.

## What the machine actually needs

The image is the same **~19 GB on disk** you already pulled for IC101. DD104 adds nothing to
it.

What DD104 asks of your CPU is small, and worth knowing in advance because it changes how you
work. Measured in the pinned container:

| Job | Wall time |
|---|---|
| Lab 01 end to end — two tests, run against two adders | **4.6 s** |
| The shipped example testbench against the SimProc core (Icarus) | **7.8 s** |
| The same six tests under Verilator, including its build | **22.6 s** |
| The shipped chip test against the good core and all 13 broken ones | **21.0 s** |
| Verilator toggle coverage on the Lab 01 adder, both stimulus sets | **10.8 s** |

Nothing in this course ties up your laptop. The consequence is that **you can afford to run
your tests every time you change one line**, which is the working rhythm the whole course
assumes.

## You are ready when

```bash
. /foss/designs/common/.designinit    # (only needed to define `mod`)
mod dd104
cocotb-config --version               # 2.0.1
cd labs/lab-01-the-adder-you-already-trust && make    # ends on VERDICT: FAIL, on purpose
```

Next: **["It works" is not a result](guide/it-works-is-not-a-result.md)** — where you find out that
the processor you are about to verify shipped with exactly one test, and that thirteen
deliberately broken versions of it all pass that test.

## Getting help

This course is self-paced, which is not the same as alone.

- **Ask in the [team Discord](https://discord.gg/hrJnP5UsGz).** There is no such thing as a
  question too basic. Most of what looks like your mistake in a verification course is the
  tool being unhelpful — and quite a lot of it, in this course specifically, is a design that
  is *supposed* to be broken.
- **Quote the exact error, and say which core you were running against.** "My test fails" and
  "my test fails on `B07` and passes on the golden core" are different questions with
  different answers. The first line of a Python traceback is the real one; everything above it
  is cocotb's machinery.
- **Paste the verdict block, not a screenshot of one line.** Every DD104 lab ends with a
  verdict that says which core, which testbench, and which tests fired. That block is the
  whole diagnosis.
- **If a command on these pages does not do what the page says it does, that is a bug in the
  course.** Report it. Every command here was run before it was written, so a mismatch means
  something drifted and we want to know.

### One thing not to ask for

`labs/common/bugs.py` contains all thirteen answers, in order, with line numbers. It is in
your clone right now and nobody is going to stop you reading it. It is also the one file that
can make this course worthless to you — the skill DD104 teaches is *finding* a bug you cannot
see, and you only get to practise that on a bug you have not been told.

If you are stuck, ask in Discord for **a better question to ask the design**, not for the
answer. That is the request the course is built to answer.
