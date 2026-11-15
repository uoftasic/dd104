# Lab 04: reference solution

Don't read this until `make verdict` shows three green rows on the core you were dealt.

```bash
cp solutions/test_lab04.py test_solution.py
make sim TB=test_solution
make verdict TB=test_solution
```

The suite has ten tests, takes `1319890.01` ns of simulated time on the golden core, and catches
all five bugs in this lab's pool. These are the measured results:

| Bug | Tests that fail |
|---|---|
| `B04_alu_writeback_reg_field` | 8 of 10 |
| `B05_branch_offset_zero_extended` | 2 of 10 |
| `B06_shift_amount_one_bit` | 8 of 10 |
| `B07_load_address_from_ra` | 1 of 10 |
| `B09_branch_clobbers_flags` | 1 of 10 |

## `t07`

The shipped `test_lab04.py` tests `LOAD` as `LOAD r1, r1`, loading through a pointer into itself.
That is a real idiom, used when you are walking a list and no longer need the address. A core that
reads the address from the wrong register field also gets it right, because on that instruction
both fields name the same register.

We had to write `t07` specifically to catch `B07`, after `t01` to `t06` and `t08` had all passed
on it, `t08` being a golden-model comparison over 27 instructions. Nothing about `LOAD r1, r1`
warns you that it is too weak a test.

The habit this lab is meant to build is to make every operand distinct on purpose, and to check
the register that should not have moved as well as the one that should.

## Two things that cost time writing this file

In both cases the harness is behaving as documented, and both mistakes make the test fail on the
golden core, which is why the golden core is the verdict's first row.

- `set_reg` clobbers `r0`. Every constant on this machine is built in `r0` and then copied,
  because `ORI` is the only way to get a literal in and `ORI` only writes `r0`. So
  `set_reg(0, x) + set_reg(1, y)` sets `r0` and then immediately overwrites it. Always set `r0`
  last.
- `sp.regs()` returns a tuple, and `(16, 35, 3, 64) == [16, 35, 3, 64]` is `False`, so comparing
  it with a list fails with an assertion message that prints two things that look identical.

## The decision to argue about

`t08_against_the_golden_model` is four lines and checks every register, the PC and both flags
after every instruction, which makes it by far the most coverage per line in the file. Elsewhere
in the course it catches `B03` and `B10`. It is blind to `B08` and `B13`, because `golden.py`
models the instruction set, and a model of an instruction set has nothing to say about a
handshake.

The model is doing its job there, and the gap is the reason a suite needs more than one kind of
test, which is the subject of Lab 05.
