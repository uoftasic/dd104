# Lab 04: reference solution

Get `make verdict` to three green rows on the core you were dealt before you read this.

```bash
cp solutions/test_lab04.py test_solution.py
make sim TB=test_solution
make verdict TB=test_solution
```

Ten tests, `1319890.01` ns of simulated time on the golden core, and it catches all five bugs in
this lab's pool. Measured:

| Bug | Tests that fail |
|---|---|
| `B04_alu_writeback_reg_field` | 8 of 10 |
| `B05_branch_offset_zero_extended` | 2 of 10 |
| `B06_shift_amount_one_bit` | 8 of 10 |
| `B07_load_address_from_ra` | 1 of 10 |
| `B09_branch_clobbers_flags` | 1 of 10 |

## `t07`

The shipped `test_lab04.py` tests `LOAD` as `LOAD r1, r1`, loading through a pointer into itself.
That is a real idiom, used when you are walking a list and no longer need the address. It is also
correct on a core that reads the address from the wrong register field, because on that
instruction both fields name the same register.

`t07` had to be written specifically to catch `B07`, after `t01` to `t06` and `t08`, including a
golden-model comparison over 27 instructions, had all passed it. Nothing about `LOAD r1, r1` says
it is insufficient.

That is the habit this lab is for: make every operand distinct on purpose, and check the register
that should not have moved as well as the one that should.

## Two things that cost time writing this file

Both are the harness behaving as documented, and both fail on the golden core, which is why row 1
of the verdict comes first.

- `set_reg` clobbers `r0`. Every constant on this machine is built in `r0` and then copied,
  because `ORI` is the only way to get a literal in and `ORI` only writes `r0`. So
  `set_reg(0, x) + set_reg(1, y)` sets `r0` and then immediately overwrites it. Set `r0` last.
- `sp.regs()` returns a tuple. `(16, 35, 3, 64) == [16, 35, 3, 64]` is `False`, and the assertion
  message prints two things that look identical.

## The decision to argue about

`t08_against_the_golden_model` is four lines and checks every register, the PC and both flags
after every instruction, by far the most coverage per line in the file. It catches `B03` and `B10`
elsewhere in the course. It is blind to `B08` and `B13`, because `golden.py` models the instruction
set, and a model of an instruction set has nothing to say about a handshake.

That is not a flaw in the model. It is why a suite needs more than one kind of test, which is
Lab 05.
