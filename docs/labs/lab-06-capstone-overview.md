# Lab 06 — Capstone: three that hide

Full runnable package: [`labs/lab-06-capstone/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-06-capstone).

Three bugs that the reference suite needed a purpose-built test for. No hand-holding on
stimulus: you have the harness, the golden model and a coverage list, and this lab supplies
framing and a verdict.

The deliverable is not a fix. It is **a test suite that catches all thirteen**, and a written
bug report for one of the three.

## Prerequisites

- [Lab 05](labs/lab-05-every-answer-is-right-overview.md) complete — you have protocol tests as well as architectural ones
- Every guide page. Particularly
  [Directed, random, and the gap](guide/directed-random-and-the-gap.md) *(not yet written)* and
  [Writing the bug report](guide/writing-the-bug-report.md) *(not yet written)*
- Your Lab 04 and Lab 05 test files, to bring forward

## Objectives

- Assemble your own work from five labs into one suite and score it against all thirteen bugs
- Find a bug where the wrong operator agrees with the right one on every input you would naturally choose
- Find a bug that a **reset** conceals, and one that the **default value of a parameter** conceals
- Sweep a parameter instead of sampling it, and understand why `PING → 0xAA` is not a link test
- Write a bug report somebody can act on without re-deriving your week
- Write down the one-line claim your suite supports, and compare it with the claim the chip shipped with

## Theory (short)

**The prior this lab overwrites:** *the hard bugs are the deep ones.* None of these three is
subtle in the RTL. All three are subtle in the **stimulus**, and that is a different skill.

### Where each one lives

| | survives, because |
|---|---|
| `B10_ori_adds_instead_of_ors` | `0 \| imm` equals `0 + imm`, so the first `ORI` after reset is always right — and OR and ADD agree **exactly when the operands share no set bits**, which is every constant anybody builds on purpose |
| `B11_ori_writes_r1_reads_r0` | the value it produces is correct; only its destination is wrong, and after a reset the two candidate destinations hold the same thing |
| `B12_uart_rx_bit_period` | it does not exist at the default parameter value, and the link test everybody starts with passes over the broken link |

### The coverage list

Not a checklist to tick. A list of questions about your own suite, each of which has an answer
you can go and measure.

| | ask |
|---|---|
| instructions | Which of the sixteen opcodes has my suite never executed? Including the three unimplemented ones. |
| operands | For each instruction, have I run it with `rA == rB` **and** with `rA != rB`? |
| fields | Every shift amount (4). Every branch displacement (16). Every `ORI` immediate that **overlaps bits already set**. |
| registers | Has each of the four been a source, a destination, a pointer, and a bystander that must not move? |
| flags | Asserted after every flag-setting instruction — and asserted **not to move** after the ones that leave them alone? |
| memory | Address 0. Address 63. An address above 63. |
| protocol | `done` counted. `halt` counted. Cycle counts asserted. |
| parameters | `clk_per_bit`, **swept** — not sampled at its default. |
| state | Does anything in my suite run long enough to leave the window where reset has made everything equal? |

The last two rows are `B12` and `B11`, and the "fields" row is `B10`.

## Procedure

```bash
mod dd104
cd labs/lab-06-capstone
```

Start by bringing your Lab 04 and Lab 05 tests into `test_capstone.py`. `make check-all` scores
whatever that module contains, and there is no credit for retyping work you have already done.

### Step 1 — Get a baseline

- **Try this:** `make check-all` on what you have. About **4 minutes** — fourteen full builds
  and simulations.
- **What you should see:** a scoreboard, and for each bug you missed, one line about what it
  hides behind:

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

- **Why an engineer cares:** this is the only place in the course where you are handed a hint
  after failing, and by now you have earned it. Use the list as a work queue.

### Step 2 — `B10`: the wrong operator that agrees with the right one

- **Try this:** run `ORI` three times with immediates that **overlap**.

  ```python
  await sp.run([ORI(5), ORI(3), ORI(24)])
  assert sp.reg(0) == 31
  ```

- **What you should see:** `31` on a correct core, `32` on `B10`.
- **Why an engineer cares:** work out why this is hard before you decide it was easy.

  `5 | 3 = 7` but `5 + 3 = 8`; then `7 | 24 = 31` but `8 + 24 = 32`. OR and ADD produce the same
  answer on **every pair of operands that share no set bits**. That is not an obscure corner —
  it is exactly how you build a constant on this machine, and it is what `set_reg` in the
  assembler does:

  ```
  SUB r0, r0     # clear
  ORI 0x16       # the top five bits
  SHL r0, 3      # shove them up
  ORI 0x07       # the bottom three -- disjoint from what is already there
  ```

  Every one of those `ORI`s is correct on a core whose `ORI` adds. And the very first `ORI`
  after a reset is `0 | imm`, which is `0 + imm`, so even an overlapping immediate is right the
  first time.

  You have to OR a bit into a register that already has it. Measured against the eleven-test
  reference suite, `B10` is caught by **2 of 11** tests.

### Step 3 — `B11`: the one that looks hardest and is not

- **Try this:** `make check TB=test_reference BUG=B11`.
- **What you should see:**

  ```
    caught  B11_ori_writes_r1_reads_r0         11 tests, 7 FAILED          13.5s
          R01_alu_asymmetric_operands
          R02_ori_overlapping_immediates
          R03_shift_amount_sweep
          R05_flags_survive_a_branch
  ```

  **7 of 11** — GOLDEN, and by some distance the highest number in this pool. Compare a
  five-instruction constant builder on the two cores:

  | | `r0` | `r1` |
  |---|---|---|
  | golden | **20** | 0 |
  | `B11` | **0** | 4 |

  Both GOLDEN. `ORI` reads `r0` and writes `r1`, so the shift in the middle of the builder
  shifts a register that never received anything.

- **Why an engineer cares:** three things, and the last one is the reason this bug is in the
  capstone.

  **First**, it is easy to catch *here* because `ORI` is the only way to get a constant into
  this machine, so every `set_reg` in every test goes through it. A bug on the sole path to
  every literal is a bug on the critical path of your whole suite. Not every design is so
  obliging.

  **Second**, the thing that is right and the thing that is wrong come apart cleanly: the
  *value* is correct and the *destination* is not. Right after a reset, `r0` and `r1` hold the
  same thing, so a machine reading one and writing the other produces a number that is correct
  in every respect except where it is. That is the shape to remember — **reset is a state in
  which several things are temporarily indistinguishable, and a test that lives inside that
  window cannot tell them apart.** Your programs are short because short programs are readable.

  **Third, and this is the point:** `B11` is upstream's own to-do, applied to one of its two
  sites. The SimProc source shipped with a comment suggesting exactly this change. DD104's fork
  removed it, on purpose, because in a course whose premise is *"there are hidden bugs in this
  file"* a comment like that reads as a planted clue pointing at correct code. The full
  reasoning — including why the shipped behaviour is the specified one and what it would cost to
  reverse that decision — is in
  [`ORI-DECISION.md`](https://github.com/uoftasic/dd104/blob/main/ORI-DECISION.md).

  **A source comment is not a specification.** Neither is a to-do. Both are somebody's opinion
  from a Tuesday, and this is what it looks like when one of them is half-applied.

### Step 4 — `B12`: sweep the parameter

- **Try this:** `clk_per_bit` is `uio_in × 4`. Every lab in this course has run at the default
  `uio_in = 8`, so `clk_per_bit = 32`. Sweep it, and at each speed do a `PING` **and** move a
  byte that is not a fixed pattern:

  ```python
  for uio in (4, 8, 16, 32, 64):
      await sp.set_baud(uio)
      reply = await sp.uart_ping()
      await sp.uart_write(0x3F, 0x5A)
      got = await sp.uart_read(0x3F)
  ```

- **What you should see:** on the golden core, every speed works. On `B12`:

  | `clk_per_bit` | `PING` | a data byte (`0x5A`, written then read back) |
  |---|---|---|
  | 8 | `TimeoutError` — no reply at all | — |
  | **16** | **`0xAA`** | `ValueError` — the reply is X bits |
  | 24 | `0xAA` | `0x5A` |
  | 32 *(the labs' default)* | `0xAA` | `0x5A` |
  | 64, 128, 256 | `0xAA` | `0x5A` |

  **Every row is GOLDEN.**

- **Why an engineer cares:** two lessons, and both of them are in that table.

  **The row at 16 is the one to stare at.** `PING` answers `0xAA`, perfectly, over a link that
  cannot carry a byte. It does that because of the specific bytes involved: `0xF0` already has
  its top bit set, and the reply `0xAA` is a fixed pattern, so a receiver that mis-samples bit 7
  as the stop bit gets both of them exactly right. **A link test that passes over a broken link
  is worse than no link test, because you believe it.**

  **And the rows at 24 and above are why sampling is not sweeping.** At the default this core is
  behaviourally indistinguishable from a correct one — the entire rest of your suite scores
  exactly the same on it. The bug is one extra clock per received bit, so the sample point walks
  further off centre with every bit of a frame, and a long bit period simply has room to absorb
  it. It fails at **short** bit periods first.

  Which speeds work is therefore the diagnosis, not just the result. Measured against the
  reference suite, `B12` is caught by **1 of 11** tests, and it is the only one that sweeps.

  **A parametric design tested at one parameter value has been tested once.**

### Step 5 — Hunt one properly

- **Try this:** `make new`, `make hunt`, `make verdict`. Same three-row grade as
  [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md); row 2 is still the deliverable.
- **Why an engineer cares:** knowing that three bugs exist and knowing which one you have are
  different states. The pool description in `test_capstone.py` describes all three without
  naming which line any of them touches, which is roughly the information a bug report gives you
  in real life.

### Step 6 — The suite

- **Try this:** `make check-all` until it says `13 of 13`.
- **What you should see:**

  ```
  ------------------------------------------------------------------------
   13 of 13 caught.
   Every bug in the catalogue. Nothing in this course hides from
   this testbench any more.
  ========================================================================
  ```

- **Why an engineer cares:** the reference suite that does this is **sixteen tests** — ten from
  Lab 04, three from Lab 05, three new. That proportion is the honest shape of a capstone: most
  of the work was already done, and the last three took the longest.

  Look at which test catches what, and notice two things:

  ```
    caught  tier 1  B01_sub_operands_swapped           t01_arithmetic
    caught  tier 1  B03_zero_flag_low_nibble           t08_against_the_golden
    caught  tier 2  B07_load_address_from_ra           t07_load_through_a_sep
    caught  tier 4  B08_store_drops_done               p01_done_pulses_once_p
    caught  tier 5  B12_uart_rx_bit_period             c03_baud_sweep
  ```

  Two general tests — `t01_arithmetic` and `t08_against_the_golden_model` — catch six of the
  thirteen between them. And five bugs are caught by exactly one test each. Is that a
  well-balanced suite, or a suite with a long tail of special cases bolted on? Both readings are
  defensible and the answer changes what you would write next.

### Step 7 — Write the report

- **Try this:** copy `BUG-REPORT-template.md` to `BUG-REPORT.md` and fill it in for one of the
  three. Five parts:

  1. **The smallest program that reproduces it.** Minimise — cut instructions until it stops
     failing, then put the last one back.
  2. **Expected versus actual, as numbers, with the arithmetic shown.**
  3. **The shape** — how many vectors or cycles are wrong, out of how many, and what the count
     implies before anybody opens the RTL.
  4. **Where it is *not*.** What still works. This is what makes a report credible and it is
     what localises the fix.
  5. **The reflex the suite gained** — one line, and the test that enforces it, by name.

- **Why an engineer cares:** the deliverable of verification is not a red test. It is a report
  somebody can act on without re-deriving your week. Part 4 is the one people skip and the one
  designers read first: *"every `ORI` whose immediate is disjoint from `r0` is correct, all
  393,216 ALU vectors are correct, and both branches and all memory accesses are unaffected"*
  turns a bug report into a map.

  The report is finished when there is a test in the suite that fails before the fix and passes
  after. `make verdict` is that, mechanised. Full worked example:
  [Writing the bug report](guide/writing-the-bug-report.md).

## Expected results

| Check | Expected | |
|---|---|---|
| `make check-all` | `13 of 13 caught` | **GOLDEN** |
| `make check-all` wall clock | about 4 min 35 s | BALLPARK |
| reference suite on golden | 16 of 16, `2118170.02` ns | **GOLDEN** |
| tests failing, reference 11-test suite: `B10` / `B11` / `B12` | 2 / 7 / 1 | **GOLDEN** |
| `B10`: `ORI 5, ORI 3, ORI 24` | golden `31`, broken `32` | **GOLDEN** |
| `B11`: five-instruction constant builder | golden `r0 = 20`; broken `r0 = 0, r1 = 4` | **GOLDEN** |
| `B12` at `clk_per_bit = 16` | `PING` returns `0xAA`; a data byte does not survive | **GOLDEN** |
| `B12` at `clk_per_bit >= 24` | indistinguishable from a correct core | **GOLDEN** |
| `BUG-REPORT.md` | exists, five parts | |

## Closing the course

Write down, in one sentence, the claim your suite now supports. Start it with *"This
processor…"* and keep going until the sentence is true.

Then put it next to the claim the chip actually shipped with:

```python
assert dut.uo_out.value == 3
```

which supports the claim *"this processor is not running."*

Your sentence should be uncomfortably long. It will have clauses about operands that are not
equal to each other, about every value of a two-bit field and both halves of a four-bit signed
one, about flags that move and flags that must not, about a pin that pulses once per instruction
and a pin that never rises, about an exact number of clock cycles, and about a serial link at
five different speeds. Every one of those clauses exists because something walked past you
first.

**That length is the whole point.** A test suite is a machine for making a long, specific,
checkable claim — and the reason to write one is that nobody can hold a claim that long in their
head, including you, including next year.

The transferable skill is not cocotb. It is the question you should now ask reflexively, of any
green test, anywhere, including your own: **what would this have caught?**

## Links

- [Lab package](https://github.com/uoftasic/dd104/tree/main/labs/lab-06-capstone)
- [Writing the bug report](guide/writing-the-bug-report.md)
- [`ORI-DECISION.md`](https://github.com/uoftasic/dd104/blob/main/ORI-DECISION.md) — why `ORI` is specified the way it is, and what `B11` is a half-application of
- [`labs/common/test_reference.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_reference.py) — all thirteen in eleven tests. Read it now, and find the three choices you disagree with.
- Next: **DD201 — High-Level Synthesis** and **DD202 — Computer Architecture**
