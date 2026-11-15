# Bug report: `B01_sub_operands_swapped`

A worked example of [`BUG-REPORT-template.md`](BUG-REPORT-template.md), filled in end to end.

`B01` is not in this lab's pool (`B10`, `B11`, `B12`), so nothing here gives your capstone
away. It is here because it is the clearest case in the catalogue of a report whose numbers make
the argument. Read it for the shape, then write yours.

---

## 1. The smallest program that reproduces it

The program is two `set_reg` calls (twelve instructions of setup) and one `SUB`. It ships complete as test `t01` in
[`../common/test_b01_repro.py`](../common/test_b01_repro.py):

```python
    sp = SimProc(dut)
    await sp.start()

    await sp.run(set_reg(1, 200) + set_reg(2, 100) + [SUB(1, 2)])
    got = sp.reg(1)

    assert got == 100, (
        f"SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = {got}.\n"
        f"  expected  200 - 100 = 100\n"
        f"  got       {got}\n"
        f"  note      (100 - 200) mod 256 = {(100 - 200) & 0xFF}, which is what a "
        f"core computing rB - rA would give\n"
        f"  {sp.describe()}")
```

How to run it:

```bash
cd labs/common
make sim   TB=test_b01_repro              # 3 tests, all pass on the golden core
make check TB=test_b01_repro BUG=B01      # t01 fails on the broken one
```

```
      ok  the golden core                    3 tests, all passed              3.4s
  caught  B01_sub_operands_swapped           3 tests, 1 FAILED                3.5s
        t01_sub_with_two_distinct_operands
            AssertionError: SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = 156.
```

It is minimised: there is no loop, no branch, no memory, no UART traffic beyond what the harness
needs, and no model. Both operands are constants, and they are different constants (see part 4).

## 2. Expected against actual, as numbers, with the arithmetic shown

| | |
|---|---|
| expected | `r1 = 100` |
| actual | `r1 = 156` |
| why the expected value is what it is | `SUB rA, rB` is specified as `rA - rB`. `200 - 100 = 100`. |
| why the actual value is what it is | `156 = (100 - 200) mod 256`, which is `rB - rA`. |

The two values differ in sign rather than by an offset or a single bit: `100` and `156` are
negatives of each other in eight bits, and that is the most useful sentence in this report.

## 3. The shape

Exhaustive on the ALU alone, 393,216 vectors, about 19 seconds
([Lab 03](../lab-03-three-blocks-before-the-processor/)):

```
ALU vectors=393216
ALU ADD  value_mismatch=     0 flag_mismatch=     0
ALU SUB  value_mismatch= 65024 flag_mismatch= 65024
ALU OR   value_mismatch=     0 flag_mismatch=     0
ALU NAND value_mismatch=     0 flag_mismatch=     0
ALU SHL  value_mismatch=     0 flag_mismatch=     0
ALU SHR  value_mismatch=     0 flag_mismatch=     0
```

65,024 of the 65,536 `SUB` operand pairs are wrong, and every other operation is perfect.

The 512 pairs that survive are what give you the diagnosis. `A - B == B - A (mod 256)` exactly when `2(A - B) == 0
(mod 256)`, that is when `A - B` is `0` or `128`:

| survivors | how many |
|---|---|
| `A == B` | 256 |
| `\|A - B\| == 128` | 256 |
| | 512 |

`65,536 - 512 = 65,024` exactly. When a count factors into a sentence about the design, you have
a hypothesis. This one says that the subtractor's operands are the wrong way round, and no other
fault leaves exactly 512 survivors.

The flag column matches the value column exactly (`65024` and `65024`), and that gives you a
second finding at no extra cost. `N` and `Z` are computed from `ALUout`, so they are wrong exactly
when it is, and the flag logic itself is not implicated.

## 4. Where it is not

- Every other ALU operation. `ADD`, `OR`, `NAND`, `SHL`, `SHR`: zero mismatches out of 65,536
  each.
- `SUB rX, rX`. `A - A` is the same subtraction either way round. This is the idiom for clearing
  a register on this machine, it appears in almost every program in the course, and it is why the
  bug survives so much stimulus. `t02_the_idiom_that_hides_it` passes on the broken core and is in
  the file to say so.
- The 512 pairs above. `t03_the_512_survivors` drives five of them in hardware, and they agree on
  both cores.
- The flags, decode, the register file, memory, the UART and cycle counts. `SUB` still takes four
  cycles and still writes the register the instruction names.
- Reset. It neither hides the bug nor helps, because the bug is combinational and involves no
  state.
- Register aliasing. The bug depends on the operand values being different, not on the operands
  being different registers.

That list is what turns "the ALU is broken" into "line 811 of `simproc_system.sv`".

## 5. The habit the suite gained

> Reflex: *never test a binary operation with `op(x, x)`. Aliased operands make a swapped,
> mirrored or wrong-source implementation indistinguishable from a correct one, and the aliases
> you write by habit (`SUB rX, rX` for clear, `NAND rX, rX` for not, `LOAD rX, rX` for a
> pointer dereference in place) are exactly the ones you will never suspect.*
>
> Enforced by: `t01_sub_with_two_distinct_operands` in
> [`../common/test_b01_repro.py`](../common/test_b01_repro.py), which fails on this core and
> passes on the golden one.

---

## The same thing in `make verdict`

`make verdict` turns parts 1 and 5 into a grade. Here is what it prints when you have been dealt
this core and have written the test but not yet applied a fix:

```
      ok  1. the golden core          must PASS      3 tests, all passed        4.2s
  caught  2. the core you were dealt  must FAIL      3 tests, 1 FAILED          3.4s
        t01_sub_with_two_distinct_operands
            AssertionError: SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = 156.
    FAIL  3. core/ as it stands now   must PASS      3 tests, 1 FAILED          3.4s
------------------------------------------------------------------------
 VERDICT: FAIL -- row 3. You have a test that catches the bug, which
   is the hard half and it is done.
```

And here it is after you change `ALUout = B - A;` back to `ALUout = A - B;` in
`core/simproc_system.sv`:

```
      ok  1. the golden core          must PASS      3 tests, all passed        4.2s
  caught  2. the core you were dealt  must FAIL      3 tests, 1 FAILED          3.4s
      ok  3. core/ as it stands now   must PASS      3 tests, all passed        3.5s
------------------------------------------------------------------------
 VERDICT: PASS
   Row 2 is the part worth keeping. Commit that test.
```

Row 2 does not change when you fix the design, because it is rebuilt from the catalogue every
time rather than read from `core/`. That is why the report is built around a reproducer. The
patch is something one person did once, and the test is what stops the bug coming back a year
later, in a rewrite by someone who has never heard of you.
