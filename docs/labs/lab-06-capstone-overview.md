# Lab 06: Capstone

You'll bring your work from Labs 04 and 05 into one suite, find the three tier-5 bugs, the hardest
in the catalogue to think of, and finish with a suite that catches all thirteen and a written bug
report for one of the three. None of the three is subtle in the RTL. All three are subtle in the
stimulus.

This lab takes about 3 hours 30 minutes.

Package: [`labs/lab-06-capstone/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-06-capstone)

## Before you start

- Finish [Lab 05](labs/lab-05-every-answer-is-right-overview.md): you have protocol tests as well
  as architectural ones.
- Read [Writing the bug report](guide/writing-the-bug-report.md), and reread
  [Directed and random tests](guide/directed-random-and-the-gap.md).
- Have your Lab 04 and Lab 05 test files at hand to bring forward.

The three bugs in this lab's pool, and why each survives:

| | Survives because |
|---|---|
| `B10_ori_adds_instead_of_ors` | `0 \| imm` equals `0 + imm`, so the first `ORI` after reset is always right, and OR and ADD agree exactly when the operands share no set bits, which is every constant anyone builds on purpose |
| `B11_ori_writes_r1_reads_r0` | The value it produces is correct; only its destination is wrong, and after a reset the two candidate destinations hold the same thing |
| `B12_uart_rx_bit_period` | It does not exist at the default parameter value, and the link test everybody starts with passes over the broken link |

Use this coverage list as questions about your own suite. Each has an answer you can measure:

| | Ask |
|---|---|
| Instructions | Which of the sixteen opcodes has my suite never executed, including the three unimplemented ones? |
| Operands | For each instruction, have I run it with `rA == rB` and with `rA != rB`? |
| Fields | Every shift amount (4), every branch displacement (16), every `ORI` immediate that overlaps bits already set |
| Registers | Has each of the four been a source, a destination, a pointer, and a bystander that must not move? |
| Flags | Asserted after every flag-setting instruction, and asserted not to move after the ones that leave them alone? |
| Memory | Address 0, address 63, an address above 63 |
| Protocol | `done` counted, `halt` counted, cycle counts asserted |
| Parameters | `clk_per_bit` swept, not sampled at its default |
| State | Does anything in my suite run long enough to leave the window where reset has made everything equal? |

The last two rows are `B12` and `B11`, and the fields row is `B10`.

```bash
mod dd104     # in a new terminal, load .designinit first (Lab 01, Part 1)
cd labs/lab-06-capstone
```

## Part 1: Get a baseline

How many of the thirteen does the suite you already have catch?

1. Copy your Lab 04 and Lab 05 tests into `test_capstone.py`. `make check-all` scores whatever
   that module contains, and there is no credit for retyping work.

2. Score it against all thirteen:

   ```bash
   make check-all
   ```

   It takes about four minutes: fourteen full builds and simulations. You should see a scoreboard,
   and for each bug you missed, one line about what it hides behind:

   ```
     caught  tier 1  B01_sub_operands_swapped           t01_arithmetic          20.9s
     ...
     MISSED  tier 5  B12_uart_rx_bit_period
   ------------------------------------------------------------------------
    10 of 13 caught.
    Still hiding from this testbench:
      B12_uart_rx_bit_period
         hides behind: the default baud rate, where it is invisible
   ```

   Your count and list will depend on what you brought in.

This is the only place in the course where you get a hint after failing. Use the list as a work
queue.

Check: you have a baseline count.

## Part 2: B10, the wrong operator

Why does a good testbench miss an `ORI` that adds instead of ORs?

1. Before you run, predict whether the six-test example testbench catches `B10`. Then, in
   `labs/common`:

   ```bash
   cd ../common
   make check TB=test_example BUG=B10
   cd ../lab-06-capstone
   ```

   You should see `MISSED  B10_ori_adds_instead_of_ors` and the hint
   `ORing in bits that were not already set — ADD agrees`. Six tests and a 29-instruction model
   comparison, and none of those instructions ORed in a bit that was already set.

2. The hint says when `ADD` agrees with `OR`. Before writing a test, work out why that makes this
   bug hard to catch: try `5 | 3` against `5 + 3`, then think about how a program on this machine
   builds a constant, and how often it ORs a bit into a register that already has it.

   <details>
   <summary>Answer</summary>

   `5 | 3 = 7` but `5 + 3 = 8`; then `7 | 24 = 31` but `8 + 24 = 32`. OR and ADD give the same
   answer on every pair of operands that share no set bits. That is how you build a constant on
   this machine, and it is what `set_reg` does:

   ```
   SUB r0, r0     # clear
   ORI 0x16       # the top five bits
   SHL r0, 3      # shove them up
   ORI 0x07       # the bottom three -- disjoint from what is already there
   ```

   Every one of those `ORI`s is correct on a core whose `ORI` adds. And the first `ORI` after a
   reset is `0 | imm`, which is `0 + imm`, so even an overlapping immediate is right the first
   time.

   </details>

3. Write a test that ORs a bit into a register that already has it:

   ```python
   await sp.run([ORI(5), ORI(3), ORI(24)])
   assert sp.reg(0) == 31
   ```

4. Run `make check BUG=B10`. You should see `caught`: `31` on a correct core, `32` on `B10`.

Against the eleven-test reference suite, `B10` is caught by 2 of 11 tests.

Check: `make check BUG=B10` says `caught`.

## Part 3: B11, the wrong destination register

Why can a value be right and still be wrong?

1. See how the reference suite does against it:

   ```bash
   make check TB=test_reference BUG=B11
   ```

   You should see:

   ```
     caught  B11_ori_writes_r1_reads_r0         11 tests, 7 FAILED              14.2s
           R01_alu_asymmetric_operands
           R02_ori_overlapping_immediates
           R03_shift_amount_sweep
           R05_flags_survive_a_branch
   ```

   Seven of eleven is exact, and by some distance the highest number in this pool.

2. Compare a five-instruction constant builder on the two cores (both rows exact):

   | | `r0` | `r1` |
   |---|---|---|
   | Golden | 20 | 0 |
   | `B11` | 0 | 4 |

   `ORI` reads `r0` and writes `r1`, so the shift in the middle of the builder shifts a register
   that never received anything.

3. Make sure your suite catches it with `make check BUG=B11`.

4. Why is `B11` easy to catch in this design, and why would a short test that only checks the
   value miss it?

   <details>
   <summary>Answer</summary>

   It is easy to catch here because `ORI` is the only way to get a constant into the machine, so
   every `set_reg` in every test goes through it; not every design is that obliging. But the value
   is right and the destination is wrong. Right after a reset `r0` and `r1` hold the same thing, so
   a machine that reads one and writes the other produces a number that is correct in every respect
   except where it is. Reset is a state in which several things are temporarily indistinguishable,
   and a test that stays inside that window cannot tell them apart. Your programs are short because
   short programs are readable.

   </details>

`B11` is also upstream's own to-do, applied to one of its two sites. The SimProc source shipped
with a comment suggesting exactly this change. DD104's fork removed the comment on purpose,
because in a course whose premise is "there are hidden bugs in this file" it reads as a planted
clue pointing at correct code. [`ORI-DECISION.md`](https://github.com/uoftasic/dd104/blob/main/ORI-DECISION.md)
has the full reasoning, including why the shipped behaviour is the specified one. A source comment
is not a specification, and neither is a to-do, and `B11` shows what happens when one is
half-applied.

Check: your suite catches `B11`.

## Part 4: B12, the baud rate

Does the UART work at every speed, or only at the default?

`clk_per_bit` is `uio_in × 4`. Every lab so far has run at the default `uio_in = 8`, so
`clk_per_bit = 32`.

1. Write a test that sweeps it, and at each speed does a `PING` and moves a byte that is not a
   fixed pattern:

   ```python
   for uio in (4, 8, 16, 32, 64):
       await sp.set_baud(uio)
       reply = await sp.uart_ping()
       await sp.uart_write(0x3F, 0x5A)
       got = await sp.uart_read(0x3F)
   ```

2. `B12` adds one clock to every received bit. Before you run, predict whether it fails at short
   bit periods or long ones first. Then run it with `make sim`, then `make check BUG=B12`. On the
   golden core every speed works. On `B12` you should see this pattern (every row exact):

   | `clk_per_bit` | `PING` | A data byte (`0x5A`, written then read back) |
   |---|---|---|
   | 8 | `TimeoutError`, no reply at all | |
   | 16 | `0xAA` | `ValueError`: the reply is X bits |
   | 24 | `0xAA` | `0x5A` |
   | 32 (the labs' default) | `0xAA` | `0x5A` |
   | 64, 128, 256 | `0xAA` | `0x5A` |

3. At 16, `PING` answers `0xAA` perfectly over a link that cannot carry a byte. Why?

   <details>
   <summary>Answer</summary>

   Because of the bytes involved: `0xF0` already has its top bit set and the reply `0xAA` is a
   fixed pattern, so a receiver that mis-samples bit 7 as the stop bit gets both right. A link test
   that passes over a broken link is worse than none, because you believe it.

   </details>

4. Why does `B12` fail at short bit periods first, and look correct at 24 and above?

   <details>
   <summary>Answer</summary>

   The extra clock per received bit makes the sample point drift further off centre with each bit
   of a frame, and a long bit period has room to absorb it. At the default this core behaves like
   a correct one, and the rest of your suite scores the same on it, so which speeds work is the
   diagnosis. Against the reference suite, `B12` is caught by 1 of 11 tests, the only one that
   sweeps. When a design has a parameter, test it at more than one value.

   </details>

Check: `make check BUG=B12` says `caught`.

## Part 5: Hunt one properly

Can you find which of the three your dealt core has?

1. Deal one of the three and hunt it:

   ```bash
   make new
   make hunt
   make verdict
   ```

   The grade is the same three rows as [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md); row
   2 is still the deliverable. `make probe` is here too, showing every `print()` and `dut._log`
   line live, and so are `make hunt VERBOSE=1` and `make verdict VERBOSE=1`.

Knowing three bugs exist and knowing which one you have are different things. The pool description
in `test_capstone.py` describes all three without naming the line any of them touches, which is
about the information a bug report gives you in real life.

Check: `make verdict` says `VERDICT: PASS`.

## Part 6: The suite

Does your suite catch all thirteen, and which tests do the catching?

1. Run `make check-all` until it says:

   ```
   ------------------------------------------------------------------------
    13 of 13 caught.
    Every bug in the catalogue. Nothing in this course hides from
    this testbench any more.
   ========================================================================
   ```

2. Look at which test catches what. In the reference capstone suite:

   ```
     caught  tier 1  B01_sub_operands_swapped           t01_arithmetic
     caught  tier 1  B02_nand_is_nor                    t01_arithmetic
     caught  tier 1  B03_zero_flag_low_nibble           t08_against_the_golden
     caught  tier 2  B04_alu_writeback_reg_field        t01_arithmetic
     caught  tier 2  B06_shift_amount_one_bit           t01_arithmetic
     caught  tier 2  B07_load_address_from_ra           t07_load_through_a_sep
     caught  tier 3  B05_branch_offset_zero_extended    t04_a_loop
     caught  tier 3  B09_branch_clobbers_flags          t10_a_compare_survives
     caught  tier 4  B08_store_drops_done               p01_done_pulses_once_p
     caught  tier 4  B13_store_falls_to_idle            t04_a_loop
     caught  tier 5  B10_ori_adds_instead_of_ors        t08_against_the_golden
     caught  tier 5  B11_ori_writes_r1_reads_r0         t01_arithmetic
     caught  tier 5  B12_uart_rx_bit_period             c03_baud_sweep
   ```

   The reference suite is sixteen tests: ten from Lab 04, three from Lab 05 and three new. Most of
   the work was already done, and the last three took the longest.

3. Two general tests, `t01_arithmetic` and `t08_against_the_golden_model`, catch six of the
   thirteen between them, and five bugs are caught by exactly one test each. Is that a
   well-balanced suite, or one with a long tail of special cases bolted on? Write down your answer
   and what you would write next. Both readings are defensible.

Check: `13 of 13 caught`.

## Part 7: Practise the report on B01

Can you take a bug you already know through the whole report loop?

1. Run the worked reproducer in `labs/common`:

   ```bash
   cd ../common
   make check TB=test_b01_repro BUG=B01
   ```

   You should see `ok` on the golden core and `caught  B01_sub_operands_swapped  3 tests, 1 FAILED`,
   with `SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = 156.`

2. Deal `B01` in the Lab 04 package and grade the reproducer against it. `make new` deletes the
   `core/` already in `labs/lab-04-your-first-bug-hunt`, so finish anything you still want from
   your Lab 04 core first.

   ```bash
   cd ../lab-04-your-first-bug-hunt
   make new BUGPICK=B01
   make verdict TB=test_b01_repro
   ```

   The `make new` banner still lists Lab 04's five-bug pool; the core it wrote is `B01`. You should
   see rows 1 and 2 green and row 3 `FAIL`: the test exists and the design is still broken.

   ```
         ok  1. the golden core          must PASS      3 tests, all passed        7.8s
     caught  2. the core you were dealt  must FAIL      3 tests, 1 FAILED          4.2s
           t01_sub_with_two_distinct_operands
               AssertionError: SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = 156.
       FAIL  3. core/ as it stands now   must PASS      3 tests, 1 FAILED          4.1s
   ```

3. Fix line 811 of `core/simproc_system.sv`:

   ```systemverilog
               SUB:        ALUout = B - A;     ->     SUB:        ALUout = A - B;
   ```

4. Grade it again, with the full failure message shown:

   ```bash
   make verdict TB=test_b01_repro VERBOSE=1
   ```

   You should see `VERDICT: PASS` with row 2 unchanged, and the whole assertion message from
   [Writing the bug report](guide/writing-the-bug-report.md),
   including `note      (100 - 200) mod 256 = 156`.

5. Go back to the capstone package:

   ```bash
   cd ../lab-06-capstone
   ```

Check: row 2 stayed `caught` after the fix.

## Part 8: Write the report

Can someone act on your bug without redoing your work?

1. Copy the template:

   ```bash
   cp BUG-REPORT-template.md BUG-REPORT.md
   ```

2. Fill it in for one of `B10`, `B11` and `B12`, using
   [`BUG-REPORT-EXAMPLE.md`](https://github.com/uoftasic/dd104/blob/main/labs/lab-06-capstone/BUG-REPORT-EXAMPLE.md)
   as a model. Five parts:

   1. The smallest program that reproduces it. Cut instructions until it stops failing, then put
      the last one back.
   2. Expected against actual, as numbers, with the arithmetic shown.
   3. The shape: how many vectors or cycles are wrong, out of how many, and what the count implies
      before anyone opens the RTL.
   4. Where it is not: what still works.
   5. The habit the suite gained, in one line, and the test that enforces it, by name.

A red test is where the report starts. The report is what someone can act on without redoing your
week. Part 4 is the one people skip and the one designers read first: "every `ORI`
whose immediate is disjoint from `r0` is correct, all 393,216 ALU vectors are correct, and both
branches and all memory accesses are unaffected" turns a report into a map. The report is finished
when a test in the suite fails before the fix and passes after, which is what `make verdict`
checks.

Check: `BUG-REPORT.md` exists and has all five parts.

## Part 9: Close the course

What claim does your suite now support?

1. Write down, in one sentence, the claim your suite now supports. Start it with "This
   processor…" and keep going until the sentence is true.

2. Put it next to the claim the chip shipped with:

   ```python
   assert dut.uo_out.value == 3
   ```

   which supports "this processor is not running". How long is yours, and why?

   <details>
   <summary>Answer</summary>

   It should be uncomfortably long. It will have clauses about operands that are not equal to each
   other, about every value of a two-bit field and both halves of a four-bit signed one, about
   flags that move and flags that must not, about a pin that pulses once per instruction and a pin
   that never rises, about an exact number of clock cycles, and about a serial link at five
   different speeds. Each clause is there because a bug got past you first. A test suite is a way
   to make a long, specific, checkable claim, and you write one because nobody, including you next
   year, can hold a claim that long in their head.

   The part of this course you will use everywhere is the question to ask of any green test,
   including your own: what would this have caught?

   </details>

Check: you have your sentence written next to the shipped claim.

## Expected results

| Check | Expected | |
|---|---|---|
| `make check-all` | `13 of 13 caught` | exact |
| `make check-all` wall clock | about 4 min 35 s | ballpark |
| Reference suite on golden | 16 of 16, `2118170.02` ns | exact |
| Tests failing, reference 11-test suite: `B10` / `B11` / `B12` | 2 / 7 / 1 | exact |
| `B10`: `ORI 5, ORI 3, ORI 24` | golden `31`, broken `32` | exact |
| `B11`: five-instruction constant builder | golden `r0 = 20`; broken `r0 = 0, r1 = 4` | exact |
| `B12` at `clk_per_bit = 16` | `PING` returns `0xAA`; a data byte does not survive | exact |
| `B12` at `clk_per_bit >= 24` | indistinguishable from a correct core | exact |
| `BUG-REPORT.md` | exists, five parts | |

## Finishing

You're done when `make check-all` on your `test_capstone.py` says `13 of 13 caught` and your
`BUG-REPORT.md` has all five parts.

Submit: `test_capstone.py` and `BUG-REPORT.md`.

## Going further (optional)

Read [`labs/common/test_reference.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_reference.py),
which catches all thirteen in eleven tests, and find the three choices you disagree with.

Next on the Course path: this is the last lab. The digital track continues with DD201 (High-Level
Synthesis) and DD202 (Computer Architecture).
