# Lab 05: Every answer is right

You'll meet two broken processors on which every register, flag, PC value and byte of memory is
correct for every program you can write. The golden model agrees with them completely and your
Lab 04 suite passes on both. You'll write three short checks that catch them, measure the UART
receiver's turnaround time, and hunt both bugs.

This lab takes about 75 minutes.

Package: [`labs/lab-05-every-answer-is-right/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-05-every-answer-is-right)

## Before you start

- Finish [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md): you have a suite you trust.
- Read [Handshakes and timing](guide/the-handshake-is-the-contract.md).
- Keep [The SimProc harness](reference/the-harness-api.md) open in another tab, for
  `count_done_pulses`, `count_halt_cycles`, and what `run()` returns.

SimProc's contract has three parts that `golden.py` says nothing about:

| | What it is | Correct behaviour |
|---|---|---|
| `done` | One-cycle pulse as an instruction retires | Exactly one pulse per retired instruction |
| `halt` | High while the core sits in `IDLE` | Never high while `RUN` is asserted |
| The clock | `sp.run()` returns an exact count | `ORI` 5; `ADD`/`SUB`/`NAND`/`SHL`/`SHR`/`LOAD` 4; `STORE` and every branch 3 |

Anything outside the core that wants to know whether an instruction finished (a debugger, a
performance counter, a testbench scoreboard) watches `done`. Anything that wants to know whether the
processor is running watches `halt`. A design that produces every right answer one cycle late has
missed its timing budget.

```bash
mod dd104
cd labs/lab-05-every-answer-is-right
```

## Part 1: Prove the negative first

1. Run Lab 04's finished suite against both cores in this lab's pool:

   ```bash
   make blind
   ```

   It takes about 41 seconds. You should see:

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

`test_architecture.py` is Lab 04's finished suite: ten tests that compare all four registers, the
PC, both flags and every byte of memory with the golden model after every instruction of a mixed
program, plus every shift amount in both directions, all sixteen branch displacements, a compare
followed by two branches, and `LOAD` and `STORE` through pointers in a different register from the
data. It catches every bug in Labs 03 and 04. Nothing is wrong with it; it reads architectural
state, and neither of these bugs is in architectural state. More vectors, programs or register
assertions will not reach them. A different kind of check will.

Check: three green rows, two of them on broken cores.

## Part 2: Count the pulses

1. Run the shipped `test_lab05.py` against the golden core:

   ```bash
   make sim
   ```

   You should see `TESTS=2 PASS=2` and `88810.00` ns, and in the log:

   ```
   the program ran in 37 clock cycles
   a done-triggered scoreboard would have made 9 comparisons for a 9-instruction program
   ```

   `37` and `9` are exact.

2. Work out the 37 yourself. Every test in this lab uses the same nine-instruction program, one of
   them a `STORE`, and its cost is arithmetic:

   ```
   SUB 4 + ORI 5 + SHL 4 + SUB 4 + ADD 4 + SUB 4 + ORI 5 + ADD 4 + STORE 3 = 37
   ```

   Write that sum down; you will assert it in Part 6.

The shipped `t02` reports the pulse count and asserts almost nothing about it, only that at least
one instruction retired. That is deliberate, as the next part shows.

Check: `37 clock cycles` and `9 comparisons` in the log.

## Part 3: A green run that scored eight out of nine

1. Run the shipped file against `B08`:

   ```bash
   make check BUG=B08
   ```

   You should see `MISSED`: the shipped file passes.

2. Find the same log line from the broken run. It says `8 comparisons for a 9-instruction program`.

Nothing went red and no assertion failed. A scoreboard triggered by `done` would have compared
eight machine states with the model, found all eight correct (they are), and reported a clean run.
The ninth instruction executed and wrote the right byte to the right address. It never signalled
that it had finished, so nothing outside the core noticed it. Nine instructions retired with eight
pulses, and that is the entire observable defect.

A missing trigger does not fail your test. It quietly stops your test from testing, which is worse
than a failure, because a failure is visible.

Check: the broken run says 8 comparisons.

## Part 4: Assert the number

1. Do the first TODO in `test_lab05.py`: replace `assert pulses > 0` with the exact count, and put
   the count in the message.

2. Run `make check BUG=B08` again. You should see:

   ```
     caught  B08_store_drops_done               4 tests, 1 FAILED            3.5s
           AssertionError: `done` pulsed 8 times for a 9-instruction program.
   ```

   The reference message continues:

   > The shortfall is 1. There is exactly one instruction in this program that appears exactly
   > 1 time(s), and that is where to look.

`8, expected 9` and "some pulses are missing" are very different amounts of help. The first says
the shortfall is one instruction, and the program has exactly one `STORE`. A failure message that
does the arithmetic for the reader saves an hour, and costs one line.

Check: `caught` on `B08`.

## Part 5: Watch a pin that should never move

1. Write the second TODO: use `await sp.count_halt_cycles(n)`, which runs the loaded program for
   `n` cycles of execution and returns how many of them had `halt` high. Assert that it is zero.

2. Run it against `B13`:

   ```bash
   make check BUG=B13
   ```

   You should see:

   ```
     caught  B13_store_falls_to_idle            4 tests, 2 FAILED            3.6s
           AssertionError: `halt` was high on 1 of the 38 cycles the core spent running.
           AssertionError: the program took 38 clock cycles, expected 37.
   ```

   The second line appears once you have done Part 6 too. `1`, `38` and `37` are exact.

This is the cheapest useful assertion in the course: one number, one expected value, no arithmetic,
and zero is the only correct answer, because while `RUN` is asserted the core is not supposed to
visit `IDLE` at all.

`B13` drops the core into `IDLE` for one cycle after every `STORE` and then restarts it at once,
because `RUN` is still asserted. Every value it produces is correct, in the right order and the
right place. Its only symptoms are one wasted cycle and a one-cycle blip on a pin. On a real chip
that is a performance bug (one store in a tight loop, run a million times, is a million wasted
cycles) and a glitch any debugger can see, because anything watching `halt` sees the processor stop
and start. "Functionally equivalent" is not the same as "correct". It is a claim about outputs, made
by someone who has decided which outputs count.

Check: `caught` on `B13`, with `halt` high on 1 cycle.

## Part 6: Assert the clock

1. Do the third TODO: assert `cycles == 37`, with the sum from Part 2 in the failure message.

2. Run `make check BUG=B13` again. You should see the second failure from Part 5,
   `the program took 38 clock cycles, expected 37.`

$38 - 37 = 1$, and the program has exactly one `STORE`: one extra cycle, once per store. Had the
number been 42 with five stores, the same division would point at the same instruction. This check
turns "the answer is right and arrived late" into a red row with a number attached, and it costs one
addition done once from the instruction costs in [the ISA reference](reference/simproc-instruction-set.md).

Check: both `B13` failures appear.

## Part 7: The UART receiver's busy time

1. In `labs/common`, run the handshake-timing tests:

   ```bash
   cd ../common
   make sim TB=test_handshake_timing
   ```

   You should see `TESTS=4 PASS=4` and `90910.00` ns, with these lines in the log:

   ```
   clk_per_bit = 32; receiver states: START=16  RECEIVE=288  DONE=32
   sent    : 0x99 0x0C 0x00
   received: 0x99 0x86 0x80
   with the inter-frame gap: PC = 12.  Without it: PC = 134.
   gapless PING answered 0xAA -- a green light on a link that just corrupted two of its three bytes
   one 3-byte command costs 1104 clock cycles = 3 x 11 x 32 (frame + gap) + 32 + 16 = 1104
   the core fetched its first instruction 57 clock cycles BEFORE uart_cmd(RUN) returned
   ```

2. Explain `0x86` from `0x0C` using one rule. [Handshakes and timing](guide/the-handshake-is-the-contract.md#a-bfm-without-the-gap-corrupts-the-next-byte)
   has the answer.

3. Change the command bytes and run it again:

   ```bash
   sed 's/^COMMAND = (CMD_SET_PC, 12, 0)/COMMAND = (CMD_SET_PC, 0x34, 0x12)/' \
       test_handshake_timing.py > test_gap_mine.py
   make sim TB=test_gap_mine
   ```

   You should see:

   ```
   sent    : 0x99 0x34 0x12
   received: 0x99 0x9A 0x89
   with the inter-frame gap: PC = 52.  Without it: PC = 154.
   if every frame after the first were sampled ONE BIT PERIOD LATE, they would arrive as: 0x99 0x9A 0x89
   ```

   The prediction and the measurement agree.

4. Repeat step 3 with `0x0F, 0x33` and with `0x55, 0xFF` in place of `0x34, 0x12`. Compare your
   results with the table in [Other bytes](guide/the-handshake-is-the-contract.md#other-bytes). Which
   one does not follow the one-bit-period rule, and why does `0x55, 0xFF` deliver only two bytes?

5. Delete your copy and go back to the lab directory:

   ```bash
   rm test_gap_mine.py
   cd ../lab-05-every-answer-is-right
   ```

Check: you can explain the received bytes for at least the first two commands.

## Part 8: Hunt them properly

1. Hunt both bugs in the pool, one at a time:

   ```bash
   make new
   make hunt
   make verdict
   ```

   The three-row grade is the same as [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md)'s,
   and row 2 is still the deliverable. Bring in your checks from Parts 4–6. `make hunt` with an
   architectural suite alone will say `quiet` however much stimulus you add; the way out is a
   different kind of check.

2. As in Lab 04, `make probe` shows everything the simulator printed, including a probe program's
   `print()` output. `make hunt VERBOSE=1` and `make verdict VERBOSE=1` do the same.

3. Run `make new` again until you have dealt and fixed both.

Check: `make verdict` passes on both bugs.

## Finishing

You are done when `make verdict` says `VERDICT: PASS` on the core you were dealt, and ideally on
both, since there are only two. There is nothing to submit; keep `test_lab05.py` for Lab 06.

The complete difference between a working processor and these two:

| | Golden | `B08` | `B13` |
|---|---|---|---|
| `done` pulses over the program | 9 | 8 | 9 |
| `halt` high, of the running cycles | 0 | 0 | 1 |
| Clock cycles, `sp.run()` | 37 | 37 | 38 |
| Every register, flag, byte of memory, PC | Correct | Correct | Correct |

All twelve figures are exact. Three of them are wrong and nine are not.

| Check | Expected | |
|---|---|---|
| `make blind` | `ok`, `MISSED`, `MISSED` | exact |
| `make blind` wall clock | about 41 s | ballpark |
| `make sim`, shipped file | `TESTS=2 PASS=2`, `88810.00` ns | exact |
| `make sim TB=test_handshake_timing` in `labs/common` | `TESTS=4 PASS=4`, `90910.00` ns | exact |
| `make verdict`, when done | three green rows, on both bugs | |

Two questions to settle before Lab 06:

- `test_architecture.py` is Lab 04's suite with one assertion removed: the exact cycle count in
  `t04_a_loop`. With it left in, Lab 04's suite catches `B13` by accident and `make blind` does not
  work. So was Lab 04's cycle assertion a protocol test living in an architectural suite? It was,
  and it is a good test that belongs in Lab 04. "Architectural" and "protocol" are useful because
  they tell you what kinds of check you are missing, not because every test fits in exactly one box.
- If you take one habit from this lab: a scoreboard must assert how many times it fired, not just
  that every comparison it made agreed. One counter and two lines turn the worst failure mode in
  verification into an ordinary red row.

Next: read [Writing the bug report](guide/writing-the-bug-report.md), then do
[Lab 06](labs/lab-06-capstone-overview.md).
