# Lab 05: reference solution

Get `make verdict` green on both bugs (there are only two) before you read this.

```bash
cp solutions/test_lab05.py test_solution.py
make verdict TB=test_solution      # grades the core already in core/; run `make new` first if you have none
```

The reference has four tests, and this is what they reported when we ran them against both bugs:

```
  caught  B08_store_drops_done               4 tests, 1 FAILED
            AssertionError: `done` pulsed 8 times for a 9-instruction program.
  caught  B13_store_falls_to_idle            4 tests, 2 FAILED
            AssertionError: `halt` was high on 1 of the 38 cycles the core spent running.
            AssertionError: the program took 38 clock cycles, expected 37.
```

`8`, `9`, `1`, `37` and `38` are all exact.

## Three tests, three non-architectural facts

These are the names in `test_lab05.py`. (Lab 06's reference suite renames the same three
`p01`–`p03`.)

| Test | Asserts | Correct value |
|---|---|---|
| `t02_the_scoreboard_that_stopped_scoring` | `done` pulses once per retired instruction | 9, for a 9-instruction program |
| `t03_halt_stays_low_while_running` | `halt` is never high while RUN is asserted | 0 |
| `t04_the_program_takes_exactly_37_cycles` | the program's exact clock count | 37 |

`t03` is the cheapest useful assertion in the course: one number, one expected value, no
arithmetic, and zero is the only right answer. `t04` costs one addition,
`4+5+4+4+4+4+5+4+3 = 37` from the documented instruction costs, and it turns "the answer is right
and arrived late" from something nobody notices into a red row with a number attached.

## The failure messages

This is what `t02` says when it fails:

> The shortfall is 1. Look at the instructions that appear exactly 1 time(s) in this program:
> one of them retired without pulsing `done`.

`8, expected 9` and "some pulses are missing" are very different amounts of help. The first tells
you the shortfall is one instruction, and only two instructions in the program appear once, one
`SHL` and one `STORE`. When a failure
message does that arithmetic for the reader, it can save them an hour of looking.

`t03` does the same: *"1 blip in a program with one STORE in it is a useful ratio — count the
instructions of each kind and see which count matches."*

## The decision to argue about

`test_architecture.py` in this package is Lab 04's suite with the cycle-count assertion removed
from `t04_a_loop`. We removed it on purpose, because a cycle count is a timing property and not
an architectural one. With it left in, Lab 04's suite catches `B13` by accident and the
`make blind` demonstration does not work.

That makes Lab 04's cycle assertion a protocol test living in an architectural suite. It is also a
good test, though, and it should stay in Lab 04. The categories help you think about what a test
checks; they do not decide which suite it belongs in.
