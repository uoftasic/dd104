# Lab 05 — Every answer is right

Full runnable package: [`labs/lab-05-every-answer-is-right/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-05-every-answer-is-right).

Two broken processors. Every register, every flag, every PC value and every byte of memory they
produce is correct, for every program you can write. The golden model agrees with them
completely. Your Lab 04 suite passes on both.

They are still broken, and on real silicon both of them would be found by a customer rather than
by you.

This is the shortest lab in the course and the sharpest.

## Prerequisites

- [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md) complete — you have a suite you trust
- Read [The handshake is part of the contract](guide/the-handshake-is-the-contract.md) *(not yet written)*
- [The SimProc harness](reference/the-harness-api.md) *(not yet written)* open in another tab

## Objectives

- Watch an architecturally complete testbench miss two bugs, and be able to say why it must
- Check the three things about this processor that are not architectural state: `done`, `halt`, and the clock
- Understand the failure mode where a missing trigger makes a test **stop scoring** instead of fail
- Assert an exact cycle count derived by hand from documented instruction costs
- Stop using "functionally equivalent" as a synonym for "correct"

## Theory (short)

**The prior this lab overwrites:** *if every value is right, the design is right.*

A processor's contract has more in it than its results. SimProc's has three parts that
`golden.py` says nothing about, because a model of an instruction set has nothing to say about
a handshake:

| | what it is | correct behaviour |
|---|---|---|
| `done` | one-cycle pulse as an instruction retires | exactly one pulse per retired instruction |
| `halt` | high while the core sits in `IDLE` | never high while `RUN` is asserted |
| the clock | `sp.run()` returns an exact count | `ORI` 5, `ADD`/`SUB`/`NAND`/`SHL`/`SHR`/`LOAD` 4, `STORE` and every branch 3 |

Anything *outside* the core that wants to know "has an instruction finished" watches `done` — a
debugger, a performance counter, a scoreboard in a testbench. Anything that wants to know
"is the processor running" watches `halt`. And a design that produces every right answer one
cycle late is a design that missed its timing budget.

### The failure mode this lab exists for

A **scoreboard** is the standard shape for checking a processor: something watches for "an
instruction finished" and, each time it sees one, compares the machine against a model. It is a
good design and almost every professional verification environment is built this way.

Now suppose the pin it triggers on stops pulsing for one instruction.

The scoreboard does not report an error. It has nothing to report — it was never woken up. It
runs, it compares everything it was asked to compare, it finds zero mismatches, and it reports
zero mismatches **truthfully**, having made one comparison fewer than there were instructions.

**A missing trigger does not fail your test. It silently stops your test from testing.** That is
strictly worse than a failure, because a failure is visible.

## Procedure

```bash
mod dd104
cd labs/lab-05-every-answer-is-right
make blind
```

### Step 1 — Prove the negative first

- **Try this:** `make blind`, before anything else. About **41 seconds**.
- **What you should see:**

  ```
  ============================================================
   BLIND SPOT   test_architecture.py -- ten architecturally complete
                tests -- against both cores in this lab's pool.
  ============================================================
        ok  the golden core                            10 tests, all passed      13.4s
    MISSED  B08                                        10 tests, all passed      13.5s
    MISSED  B13                                        10 tests, all passed      13.4s
  ------------------------------------------------------------------------
   Three identical green rows. Every architectural result on all three
   of those processors is correct, and two of them are broken.

   What test_architecture.py never reads: the `done` pin, the `halt`
   pin, and the number of clock cycles anything took. Those are the
   three things this lab is about.
  ```

- **Why an engineer cares:** `test_architecture.py` is Lab 04's finished suite. Ten tests: all
  four registers, the PC, both flags and every byte of memory compared against the golden model
  after every instruction of a mixed program; every shift amount in both directions; all sixteen
  branch displacements; a compare followed by two branches; `LOAD` and `STORE` through pointers
  in a different register from the data. It catches **every** bug in Labs 03 and 04.

  There is nothing wrong with it. It is not lazy and it is not incomplete. It reads
  architectural state, and neither of these bugs is in architectural state. **More of the same
  does not reach them** — not more vectors, not more programs, not more assertions on registers.
  A different *kind* of check does.

### Step 2 — Count the pulses

- **Try this:** `make sim`, which runs the shipped `test_lab05.py` against the golden core.
- **What you should see:**

  ```
  the program ran in 37 clock cycles
  a done-triggered scoreboard would have made 9 comparisons for a 9-instruction program
  ```

  **`37` and `9` are GOLDEN.**

- **Why an engineer cares:** the program every test in this lab uses is nine instructions, one
  of them a `STORE`, and its cost is **arithmetic rather than measurement**:

  ```
  SUB 4 + ORI 5 + SHL 4 + SUB 4 + ADD 4 + SUB 4 + ORI 5 + ADD 4 + STORE 3 = 37
  ```

  Write that sum down. You are about to assert it.

  The shipped `t02` reports the pulse count and then asserts almost nothing about it — only
  that at least one instruction retired. That is deliberate, and `make check BUG=B08` is about
  to show you what it costs.

### Step 3 — Read a green run that scored eight things out of nine

- **Try this:** `make check BUG=B08`.
- **What you should see:** `MISSED`. The shipped file passes. Now look at the log line from the
  broken run: **`8 comparisons for a 9-instruction program`**.
- **Why an engineer cares:** nothing went red. No assertion failed. A done-triggered scoreboard
  running against this core would have compared eight machine states against the model, found
  all eight correct — because they *are* all correct — and reported a clean run.

  The ninth instruction executed. It wrote the right byte to the right address. It simply never
  said it was finished, and so nothing outside the core noticed it at all.

  **Nine instructions retired. Eight pulses.** That is the entire observable defect.

### Step 4 — Assert the number

- **Try this:** do the first TODO. Replace `assert pulses > 0` with the exact count, and put the
  count in the message.
- **What you should see:**

  ```
    caught  B08_store_drops_done               4 tests, 1 FAILED            3.5s
          AssertionError: `done` pulsed 8 times for a 9-instruction program.
  ```

  and the message goes on to say:

  > The shortfall is 1. There is exactly one instruction in this program that appears exactly
  > 1 time(s), and that is where to look.

- **Why an engineer cares:** `8, expected 9` and "some pulses are missing" are very different
  amounts of help. The first one tells you the shortfall is one instruction, and there is
  exactly one `STORE` in the program. A failure message that does the arithmetic for the reader
  saves an hour, and writing it costs one line.

### Step 5 — Watch a pin that should never move

- **Try this:** write the second TODO — `await sp.count_halt_cycles(n)`, which runs the loaded
  program for `n` cycles of execution and returns how many of them had `halt` high. Then
  `make check BUG=B13`.
- **What you should see:**

  ```
    caught  B13_store_falls_to_idle            4 tests, 2 FAILED            3.6s
          AssertionError: `halt` was high on 1 of the 38 cycles the core spent running.
          AssertionError: the program took 38 clock cycles, expected 37.
  ```

  **`1`, `38` and `37` are GOLDEN.**

- **Why an engineer cares:** this is the cheapest useful assertion in the course. One number,
  one expected value, no arithmetic, and **zero is the only correct answer** — while `RUN` is
  asserted the core is not supposed to visit `IDLE` at all.

  What `B13` does is drop the core into `IDLE` for a single cycle after every `STORE` and then
  immediately restart it, because `RUN` is still asserted. Every value it produces is correct,
  in the right order, in the right place. Its only symptoms are one wasted cycle and a
  one-cycle blip on a pin.

  On a real chip that is a **performance bug** — one store in a tight loop, running a million
  times, is a million wasted cycles — and a **debugger-visible glitch**, because anything
  watching `halt` to decide whether the processor is running sees it stop and start.

  "Functionally equivalent" is not "correct". It is a claim about outputs, made by somebody who
  has decided which outputs count.

### Step 6 — Assert the clock

- **Try this:** the third TODO. Assert `cycles == 37`, and put the sum in the failure message.
- **What you should see:** the second red row above, `the program took 38 clock cycles, expected
  37`, with the arithmetic in the message and the hint to divide the difference by the number of
  instructions of each kind.
- **Why an engineer cares:** $38 - 37 = 1$, and the program has exactly one `STORE`. One extra
  cycle, once per store. If the number had been 42 with five stores, the same division would
  have pointed at the same instruction.

  This is the check that turns "the answer is right and it arrived late" from a thing nobody
  notices into a red row with a number attached. It costs one addition, done once, from the
  instruction costs in [the ISA reference](reference/simproc-instruction-set.md).

### Step 7 — Hunt them properly

- **Try this:** `make new`, `make hunt`, `make verdict`. There are only two bugs in the pool, so
  do both.
- **Why an engineer cares:** the three-row grade is the same as
  [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md)'s, and row 2 is still the deliverable. What has
  changed is that `make hunt` on an architectural suite will now say `quiet` no matter how much
  stimulus you add, and the way out is a different kind of check rather than a bigger one.

## Expected results

The complete difference between a working processor and these two:

| | golden | `B08` | `B13` |
|---|---|---|---|
| `done` pulses over the program | **9** | **8** | 9 |
| `halt` high, of the running cycles | **0** | 0 | **1** |
| clock cycles, `sp.run()` | **37** | 37 | **38** |
| every register, flag, byte of memory, PC | correct | correct | correct |

**All twelve figures are GOLDEN.** Three of them are wrong and nine of them are not.

| Check | Expected | |
|---|---|---|
| `make blind` | `ok`, `MISSED`, `MISSED` | **GOLDEN** |
| `make blind` wall clock | about 41 s | BALLPARK |
| `make sim`, shipped file | `TESTS=2 PASS=2`, `88810.00` ns | **GOLDEN** |
| `make verdict` when done | three green rows, on both bugs | |

## Going further

### The category question worth arguing about

`test_architecture.py` in this package is Lab 04's suite with **one assertion removed**: the
exact cycle count in `t04_a_loop`. Without that removal, Lab 04's suite catches `B13` by
accident and the `make blind` demonstration does not work.

So was Lab 04's cycle assertion a *protocol* test that happened to be living in an architectural
suite? Yes. It is also a good test and it should stay in Lab 04.

Categories are for thinking with, not for filing. "Architectural" and "protocol" are useful
because they tell you what *kinds* of check you are missing — not because every test belongs in
exactly one box.

### What this means for a real scoreboard

If you take one habit out of this lab, take this one: **a scoreboard must assert how many times
it fired.** Not just that every comparison it made agreed — that it made the number of
comparisons it should have. Two lines, one counter, and it converts the worst failure mode in
verification into an ordinary red row.

## Links

- [Lab package](https://github.com/uoftasic/dd104/tree/main/labs/lab-05-every-answer-is-right)
- [The handshake is part of the contract](guide/the-handshake-is-the-contract.md)
- [The SimProc harness](reference/the-harness-api.md) — `count_done_pulses`, `count_halt_cycles`, and what `run()` actually returns
- Next lab: [Lab 06 — Capstone: three that hide](labs/lab-06-capstone-overview.md), where a reset hides one of them and the default baud rate hides another
