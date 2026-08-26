# Lab 06 — Capstone

Writeup: [`docs/labs/lab-06-capstone-overview.md`](../../docs/labs/lab-06-capstone-overview.md)
· live: <https://uoftasic.com/dd104/#/labs/lab-06-capstone>

Three bugs that the reference suite needed a purpose-built test for, and one deliverable: a
test suite of your own that catches all thirteen.

```bash
cd labs/lab-06-capstone
make new           # one of the hard three
make hunt
make verdict
make check-all     # the thing that graduates you
```

Inside the workbench container (`hpretl/iic-osic-tools:2026.04` — cocotb 2.0.1, Icarus
Verilog 14.0). No environment setup. Includes `../common/lab.mk`, so you need the repository.

## The deliverable

```
------------------------------------------------------------------------
 13 of 13 caught.
 Every bug in the catalogue. Nothing in this course hides from
 this testbench any more.
========================================================================
```

Plus a written bug report for one of the three, using
[`BUG-REPORT-template.md`](BUG-REPORT-template.md).

`make check-all` takes about **4 min 35 s** on the reference suite — fourteen full builds and
simulations. That is BALLPARK; the `13 of 13` is not.

## Targets

| | |
|---|---|
| `make new` | deal one of `B10`, `B11`, `B12` into `core/` |
| `make hunt` | your suite against `core/`, no grade |
| `make verdict` | the three-row grade (see [Lab 04's README](../lab-04-your-first-bug-hunt/README.md)) |
| `make reveal` | give up |
| `make check-all` | **the capstone deliverable**: your suite against all thirteen |
| `make sim` | your suite against the golden core |
| `make check BUG=B11` | one named bug |
| `make bugs` | the catalogue: names and tiers only |
| `make clean` | remove `build/`; leaves `core/` alone |

## Files

| | |
|---|---|
| `test_capstone.py` | **the file you edit.** One test, a description of the three bugs that gives none of them away, and a coverage list. Start by bringing your Lab 04 and Lab 05 tests in here. |
| `BUG-REPORT-template.md` | the five parts of a report a designer can act on. |
| `hunt.py` | the dealer and grader, with a three-bug pool. |
| `solutions/` | a sixteen-test suite that catches all thirteen. Not before your own `13 of 13`. |

## The three, and what each one survives

Named without being given away — the point of this lab is that knowing a bug exists does not
tell you how to reach it.

| | survives |
|---|---|
| `B10_ori_adds_instead_of_ors` | a wrong operator that agrees with the right one on every value you would naturally pick. `0 \| imm == 0 + imm`, so the first `ORI` after reset is always right — and so is every constant built by ORing in disjoint groups of bits, because OR and ADD agree exactly when the operands share no set bits. |
| `B11_ori_writes_r1_reads_r0` | reset. Two registers hold zero after a reset, and while that is true a value landing in the wrong one is indistinguishable from a value landing in the right one. The first `ORI` of any program is correct. Divergence starts at the second. |
| `B12_uart_rx_bit_period` | the default parameter. Measured: at `clk_per_bit >= 32` this core is behaviourally identical to a clean one; at 16, **`PING` still answers `0xAA`** and data transfers fail; at `<= 8` nothing works. Every lab in this course runs at the default `uio_in = 8`, i.e. `clk_per_bit = 32`. |

`B12` is the one worth stopping on. `PING -> 0xAA` passes over a link that cannot carry a byte,
because `0xF0` already has its top bit set and `0xAA` is a fixed pattern — so mis-sampling
bit 7 as the stop bit changes neither of them. A link test that passes over a broken link is
worse than no link test.

## The reference suite's shape

Sixteen tests: ten from Lab 04, three from Lab 05, three new. Total simulated time on the
golden core: **2,118,170.02 ns**, 16 of 16 passing. Which test catches which bug:

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

Note how much work the two general tests do — `t01_arithmetic` and `t08_against_the_golden_model`
between them catch six — and note that five bugs are caught by exactly one test each. Both
facts are worth arguing about, and
[`../common/test_reference.py`](../common/test_reference.py) does the same job in eleven tests
by making different choices.

## Definition of done

`make check-all` says `13 of 13 caught`, and `BUG-REPORT.md` exists and has all five parts.
