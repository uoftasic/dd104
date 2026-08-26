# Lab 06 — reference capstone suite

**Do not read this first.** Get your own `make check-all` to say `13 of 13`.

```bash
cp solutions/test_capstone.py test_solution.py
make check-all TB=test_solution
```

Sixteen tests: ten from Lab 04, three from Lab 05, three new. On the golden core, 16 of 16 in
**2,118,170.02 ns**. `make check-all` takes about 4 min 35 s and reports `13 of 13 caught`.

That proportion — thirteen tests you already had, three that took the longest — is the honest
shape of a capstone.

## The three new ones

**`c01_ori_over_bits_already_set`** — three `ORI`s whose immediates overlap. `5 | 3 = 7`,
`5 + 3 = 8`; then `7 | 24 = 31`, `8 + 24 = 32`. OR and ADD agree on every pair of operands that
share no set bits, which is *every constant anybody builds on purpose*, including the one
`set_reg` builds. You have to OR a bit into a register that already has it.

**`c02_ori_writes_r0_and_only_r0`** — `ORI 5; SHL r0, 3; ORI 3`, then all four registers
checked. The `SHL` is load-bearing: it takes r0 out of the window where reset has made every
register equal. Inside that window a value landing in the wrong register is indistinguishable
from a value landing in the right one, and any program short enough to be readable runs
entirely inside it.

**`c03_baud_sweep`** — five bit periods, and at each one a `PING` *and* a byte that is not a
fixed pattern. `PING` alone is not a link test. `0xF0` already has bit 7 set and the reply
`0xAA` is a fixed pattern, so a receiver whose bit period is one clock too long gets both of
them exactly right while mangling every byte that carries data.

Which speeds work is the diagnosis, not just the result: a slow receiver walks further off
centre with every bit of a frame, so it fails at **short** bit periods first and is invisible
at long ones. Every other lab in this course runs at the default `clk_per_bit = 32`, where this
bug does not exist.

## Two things to argue about

**1. Two tests do a third of the work.** `t01_arithmetic` and `t08_against_the_golden_model`
catch six of the thirteen between them. Five bugs are caught by exactly one test each. Is that
a well-balanced suite or a suite with a long tail of special cases bolted on? Both readings are
defensible, and the answer changes what you would write next.

**2. Sixteen tests, and [`../common/test_reference.py`](../../common/test_reference.py) does
the same job in eleven.** Read it after you have your own. It merges several of these, uses
random programs where this one uses directed ones, and drops the redundant weak tests this
suite keeps. Every one of those is a choice with a cost. Find the three you disagree with.

## The thing to write down before you close the course

One sentence: the claim your suite now supports. Start it with *"This processor…"* and keep
going until the sentence is true.

Then put it next to the one the chip shipped with:

```python
assert dut.uo_out.value == 3
```

which supports the claim *"this processor is not running."*
