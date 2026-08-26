# Lab 02 — reference solution

**Do not read this first.** Get your own `make check` to say `VERDICT: PASS`, then compare.

```bash
cp solutions/test_lab02.py test_solution.py
make check TB=test_solution
```

Measured, in the pinned container:

```
      ok  the golden core                    4 tests, all passed          3.6s
  caught  B01_sub_operands_swapped           4 tests, 1 FAILED            3.2s
        t04_subtract_two_different_numbers
            AssertionError: r1 is 116, expected 140 (200 - 60).
------------------------------------------------------------------------
 VERDICT: PASS
```

`140` and `116` are golden. `116` is `60 - 200 = -140` in eight bits.

## Two decisions worth arguing about

**1. The operands are 200 and 60, and the choice is the entire test.** `A - B` and `B - A` are
the same number when `A == B`, and also when the difference is 128 (128 is its own negation in
eight bits). That is 512 of the 65,536 possible operand pairs — 0.78 % of the input space — and
`SUB rX, rX`, the idiom for clearing a register, is one of them. Almost everyone's first
subtraction test lands in that 0.78 %.

**2. The flag assertion says `N=1`, and the first draft said `N=0`.** 200 - 60 = 140, which is
`0b10001100`, so bit 7 is set and `N` is 1. The machine has no opinion about whether that byte
is 140 or -116; `N` is literally bit 7 of the result. Getting this wrong is instructive and the
verdict catches it immediately — a testbench that fails on the golden core is telling you about
itself, which is why row 1 comes first.

## What is deliberately *not* here

t01 and t02 are unchanged. They are exactly as weak as the shipped test — both pass on all
thirteen broken cores — and they stay in the file, because when a processor is genuinely dead
they are the two rows that go red first and the cheapest thing in the suite to read.
