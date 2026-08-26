# Lab 04 — Your first bug hunt

Full runnable package: [`labs/lab-04-your-first-bug-hunt/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-04-your-first-bug-hunt).

You are dealt a processor with one line changed and you are not told which line. You write
tests until one of them goes red, you fix the line, and you prove the fix.

**The deliverable is the failing test, not the fix.** The package grades you on that
specifically, and it is worth understanding why before you start.

## Prerequisites

- [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) complete — `3 of 3 ALU bugs caught`
- Read [Where bugs hide](guide/where-bugs-hide.md) *(not yet written)*,
  [The golden model](guide/the-golden-model.md) *(not yet written)* and
  [Directed, random, and the gap](guide/directed-random-and-the-gap.md) *(not yet written)*
- [The SimProc instruction set](reference/simproc-instruction-set.md) *(not yet written)* and
  [The SimProc harness](reference/the-harness-api.md) *(not yet written)* open in other tabs

## Objectives

- Find a bug in a design you cannot diff against a known-good copy
- Bisect a machine instead of staring at it: narrow by instruction class, by register, by operand relationship
- Use the golden model to name the **first** disagreeing instruction rather than the last
- Write a test that fails on the broken core and passes on the fixed one, and understand why that is worth more than the patch
- Meet a bug that one carefully-written test catches and nine others do not

## Theory (short)

**The prior this lab overwrites:** *finding the bug is the work.* Finding it is the part you do
once. The test is the part that stays.

### The grade has three rows, in this order on purpose

```
      ok  1. the golden core          must PASS      10 tests, all passed       9.4s
  caught  2. the core you were dealt  must FAIL      10 tests, 1 FAILED         9.3s
      ok  3. core/ as it stands now   must PASS      10 tests, all passed       9.3s
```

Row 1 first, because a test that fails on a *correct* processor is telling you about itself and
nothing else is meaningful until it passes.

Row 3 is the fix, and it is the row everybody thinks is the point.

**Row 2 is the deliverable.** A patch is a thing one person did once. A test that fails on the
old core is what stops the bug coming back in a year, in a rewrite, done by somebody who has
never heard of you. Row 2 is rebuilt **fresh from the catalogue** on every run, never read from
`core/`, so you cannot get it green by editing the file the test runs against.

### The question list

From [Where bugs hide](guide/where-bugs-hide.md), as a working checklist rather than prose. Run
them in order; each one either narrows the search or removes a region of the design from
suspicion.

| | Question | What a "yes" rules in |
|---|---|---|
| 1 | Which **instruction classes** are wrong? Arithmetic, shift, load/store, branch? | the decode path for that class |
| 2 | Is it wrong for **all operands**, or only some? | a data-dependent path — the ALU, or a width |
| 3 | Does it depend on **rA and rB being different**? | a register-select field, read or write |
| 4 | Which **register** ends up wrong — the destination, a source, a bystander? | the write-back address |
| 5 | Does it survive a **reset**? Is the first one correct and the second not? | somewhere reset makes two things equal |
| 6 | Are the **values** right and something else wrong? | flags, `done`, `halt`, the cycle count |
| 7 | Does it change with a **field value** you have only ever driven at one setting? | a shift amount, a displacement, a baud divider |

Question 3 is the one this lab is built around, and question 5 is [Lab 06](labs/lab-06-capstone-overview.md).

> **Do not diff `core/` against `../common/rtl/`.** It works, it takes four seconds, and it
> skips the entire lab. The skill being built here is finding a bug in a design you cannot diff
> against a known-good one — which is every design you will ever be paid to verify.

## Procedure

```bash
mod dd104
cd labs/lab-04-your-first-bug-hunt
make new
```

### Step 1 — Take delivery

- **Try this:** `make new`.
- **What you should see:**

  ```
  ========================================================================
   A MYSTERY CORE
  ========================================================================
   Written to core/: the two RTL files and the testbench wrapper.
   Exactly one line of simproc_system.sv differs from the golden core.

   It is one of 5: B04, B05, B06, B07, B09.
   Three are in the decode path or the register file, between the
   instruction word and the register it writes. Two are in the branch
   path. None of them is in the ALU -- Lab 03 finished the ALU, and
   every vector it can be given is already known to be right.
  ```

- **Why an engineer cares:** that last sentence is not flavour text. Lab 03 drove all 393,216
  ALU vectors and checked values and flags on every one. The ALU is a region of the design you
  can **stop suspecting**, and narrowing the search is most of what verification is. You start
  this hunt with 34 lines already eliminated and a five-way multiple choice.

  `core/.sealed` holds which one it was, base64'd. Decoding it costs you the lab. It is an
  honour system and the file says so.

### Step 2 — Start from what you already have

- **Try this:** `make hunt`. It runs the shipped `test_lab04.py` — four ordinary tests, the kind
  a competent person writes in twenty minutes — against your mystery core.
- **What you should see:** either a red row, or this:

  ```
     quiet  core/  the mystery                         4 tests, all passed        3.4s
  ------------------------------------------------------------------------
   Nothing your testbench drives can tell this core from a correct
   one. The bug is real and it is in there; your stimulus has not
   reached it yet. Widen the stimulus, not the assertions.
  ```

- **Why an engineer cares:** "widen the stimulus, not the assertions" is the whole instruction.
  The shipped tests already assert the right things about the things they drive. What they do
  not do is drive a shift by 2, or a branch backwards, or an instruction where rA and rB are
  different registers.

  Read the three questions at the top of `test_lab04.py` and then read `t02` and `t03` against
  them. Both were written on purpose to have a blind spot, and both blind spots are ones you
  will produce by accident for the rest of your career.

  `hunt` is deliberately quiet — it summarises so that the loop stays a loop. The moment you
  want to *watch* a run instead of being told about it, that is **`make probe`** (Step 3).

### Step 3 — Bisect, do not stare

- **Try this:** work down the question list. Each answer is one small program.

  ```python
  # Q1 -- which classes are wrong?
  await sp.run(set_reg(1, 200) + set_reg(2, 60) + [ADD(1, 2)])   # arithmetic
  await sp.run(set_reg(1, 0x0C) + [SHL(1, 2)])                   # shift, amount != 1
  await sp.run(set_reg(2, 0x2A) + [LOAD(1, 2)])                  # load, rA != rB
  ```

  ```python
  # Q4 -- which register ends up wrong?
  print(sp.regs())          # all four at once. A tuple, not a list.
  ```

  Run those with **`make probe`**, not `make hunt`. `hunt` prints a one-line summary and
  throws the simulator's output away, so a probe program run under it tells you nothing:

  ```
     quiet  core/  the mystery                         1 tests, all passed        2.4s
  ```

  `make probe` is the same run with nothing swallowed — your `print()`, your `dut._log.info`,
  every Icarus line, live as it happens, plus the exact `make -f sim.mk …` command it used so
  you can run it by hand:

  ```
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
        ...
  ------------------------------------------------------------------------
  ...
       0.00ns INFO     cocotb.regression   running test_probe.t_probe (1/1)
  PROBE-PRINT regs = (60, 4, 60, 0)
   33290.00ns INFO     cocotb.tb           PROBE-LOG regs = (60, 4, 60, 0)
  ```

  Put your probes in their own file and point `probe` at it — `make probe TB=test_probe` — so
  the suite you are building in `test_lab04.py` stays a suite and does not fill up with
  scaffolding you will delete. `make hunt VERBOSE=1` is the same target under another name, and
  `make verdict VERBOSE=1` does it for all three rows of the grade.

- **What you should see:** a shrinking list. If arithmetic with `rA == rB` is right and
  arithmetic with `rA != rB` is wrong, questions 1, 3 and 4 have all been answered at once and
  you are looking at four lines of RTL.
- **Why an engineer cares:** the difference between a five-minute debug and a two-hour one is
  almost never insight. It is whether you spent the first ten minutes narrowing or the first ten
  minutes reading.

### Step 4 — Let the model find the first disagreement

- **Try this:** add the golden-model trace.

  ```python
  await sp.load(prog)
  model = Golden(prog + [PARK])
  steps, problem = await trace(sp, len(prog), model=model)
  assert problem is None, f"{problem}\n\n{listing(prog)}"
  ```

- **What you should see:** when it fails, a message naming the instruction number, its address,
  the disassembled instruction and the field that disagreed:

  ```
  instruction 19, at address 19 (0x66 = SUB   r1, r2), left the machine in a ...
  ```

- **Why an engineer cares:** it names the **first** disagreement, not the last. Once a
  processor's state has diverged, everything downstream of the divergence is also wrong, and a
  test that checks state only at the end of the program hands you the *symptom* — a wrong byte,
  forty instructions later, in a register that was never the problem.

  Four lines of setup, and it checks every register, the PC and both flags after every single
  instruction — including all the things you did not think to check. It is the highest-leverage
  test you can write on this machine, and it takes less code than the directed tests around it.

  Its limitation is worth writing down next to it rather than discovering: `golden.py` models
  architectural state and nothing else. It has no idea `done` or `halt` exist. A core that
  computes every answer correctly and gets its handshake wrong sails straight through. That is
  [Lab 05](labs/lab-05-every-answer-is-right-overview.md).

### Step 5 — The bug one test catches

- **Try this:** whatever you were dealt, before you finish, write these two tests and run
  `make check BUG=B07` and `make check BUG=B09`:

  - **`LOAD` with the pointer in a different register from the destination**, and the pointer
    checked afterwards to prove it was not eaten.
  - **One compare followed by two branches** — `BZ x; BNZ y` off a single comparison.

- **What you should see:** with the ten-test reference suite, this scoreboard —

  | bug | tests that fail, of 10 |
  |---|---|
  | `B04_alu_writeback_reg_field` | 8 |
  | `B05_branch_offset_zero_extended` | 2 |
  | `B06_shift_amount_one_bit` | 8 |
  | `B07_load_address_from_ra` | **1** |
  | `B09_branch_clobbers_flags` | **1** |

  **All five counts are GOLDEN.**

- **Why an engineer cares:** two of the five are caught by exactly one test each, and in both
  cases it is a test that had to be written *on purpose*, after everything else had already
  walked past.

  `B07` is the set piece. The shipped `t03` tests `LOAD` with `LOAD r1, r1` — load through a
  pointer into itself. That is a real idiom; it is what you write when you are walking a list and
  do not need the address afterwards. It is also **correct on a core that reads the address out
  of the wrong register field**, because on that one instruction the two fields name the same
  register. A golden-model comparison over 27 instructions missed it too.

  Nothing about `LOAD r1, r1` announces that it is insufficient. The habit that fixes it is
  cheap and general: **make every operand distinct on purpose, and check the register that
  should not have moved as well as the one that should.**

### Step 6 — Fix it, and get the third row

- **Try this:** edit the line in `core/simproc_system.sv`, then `make verdict`.
- **What you should see:**

  ```
        ok  1. the golden core          must PASS      10 tests, all passed        9.4s
    caught  2. the core you were dealt  must FAIL      10 tests, 1 FAILED          9.3s
          t07_load_through_a_separate_pointer
              LOAD r1, r2 with r2 = 0x2A gave r1 = 0x06, expected 0x77.
        ok  3. core/ as it stands now   must PASS      10 tests, all passed        9.3s
  ------------------------------------------------------------------------
   VERDICT: PASS
     The bug was B07_load_address_from_ra.
     It hides behind: LOAD rX, rX — loading through a pointer into itself
     It teaches: aliasing hides bugs — make every operand distinct on purpose

     Row 2 is the part worth keeping. Commit that test.
  ```

- **Why an engineer cares:** if you fix `core/` before you have a test that catches the bug,
  row 3 goes green and row 2 stays red, and the verdict still says FAIL:

  ```
   VERDICT: FAIL -- row 2. Your testbench cannot tell the dealt core
     from a correct one, so it is not testing whatever is wrong with it.
     This is the row that matters and it is the one still open.
  ```

  That is the lab refusing to accept a fix nobody can prove. It is also exactly what a code
  review should say to a patch with no test attached.

### Step 7 — Do it again

- **Try this:** `make new` deals another one. There are five in the pool and they take
  progressively less time. `make new BUGPICK=B05` picks a specific one when you want to practise
  a shape rather than be surprised.
- **Why an engineer cares:** the first hunt teaches you the harness. The third teaches you the
  question list, which is the transferable part.

## Expected results

| Check | Expected | |
|---|---|---|
| `make sim`, shipped file | `TESTS=4 PASS=4`, `200060.00` ns | **GOLDEN** |
| `make verdict` when done | three green rows, `VERDICT: PASS` | |
| tests failing on `B07`, ten-test suite | **1** | **GOLDEN** |
| tests failing on `B09`, ten-test suite | **1** | **GOLDEN** |
| tests failing on `B04` / `B06` / `B05` | 8 / 8 / 2 | **GOLDEN** |
| `make hunt` wall clock | 3–10 s depending on suite size | BALLPARK |
| `make probe TB=…`, testbench that `print()`s | the `print()` appears in the terminal | |

> The `sorry:` notes and `make: *** [...] Error 1` under a FAIL verdict are both still normal.
> [Output that is not an error](reference/output-that-is-not-an-error.md).

## Going further

### Random stimulus is not a safety net

`labs/common/test_reference.py` is a suite that catches all thirteen bugs in eleven tests, and
one of those eleven runs eight random programs and compares every register against the golden
model after each. It is genuinely useful and it finds things nobody thought of.

Measured, in this lab:

```
  caught  B03_zero_flag_low_nibble           11 tests, 1 FAILED
        R07_zero_and_negative_flags
  caught  B07_load_address_from_ra           11 tests, 1 FAILED
        R06_load_store_distinct_registers
```

Each of those bugs is caught by **exactly one** test, and in neither case is it the random one.
Random programs generate operands at random, so `rA == rB` happens often enough to look tested
and the specific pairing that exposes `B07` — a `LOAD` whose two register fields differ, with a
meaningful byte at the address in one of them — is not something an unguided generator reliably
produces. And a broken `Z` flag needs a non-zero result whose bottom nibble is zero, which eight
random programs can easily never produce at all.

**Random with no coverage model does not replace thinking about the input.** It samples.
[Directed, random, and the gap](guide/directed-random-and-the-gap.md) is the long version.

### `make reveal`, and when to use it

It exists. It tells you the bug's name and what it hides behind — not the line — and then still
requires you to write the test that catches it, because knowing the name of a bug and owning a
test for it are different things and only one of them survives you leaving the project.

**Using it after a genuine hour is a reasonable engineering decision, not a moral failure.** A
self-paced course with no escape hatch does not produce more persistent students; it produces
fewer students. Take the hint, write the test, and move on.

## Links

- [Lab package](https://github.com/uoftasic/dd104/tree/main/labs/lab-04-your-first-bug-hunt)
- [Where bugs hide](guide/where-bugs-hide.md) — the question list, with the reasoning behind each entry
- [The golden model](guide/the-golden-model.md) — what `trace()` compares, and what it cannot see
- [Directed, random, and the gap](guide/directed-random-and-the-gap.md)
- Next lab: [Lab 05 — Every answer is right](labs/lab-05-every-answer-is-right-overview.md), where the golden model agrees with a broken chip completely
