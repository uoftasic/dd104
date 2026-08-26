# Lab 05 — reference solution

**Do not read this first.** Get `make verdict` green on both bugs — there are only two.

```bash
cp solutions/test_lab05.py test_solution.py
make verdict TB=test_solution      # grades the core already in core/; run `make new` first if you have none
```

Four tests. Measured:

```
  caught  B08_store_drops_done               4 tests, 1 FAILED
            AssertionError: `done` pulsed 8 times for a 9-instruction program.
  caught  B13_store_falls_to_idle            4 tests, 2 FAILED
            AssertionError: `halt` was high on 1 of the 38 cycles the core spent running.
            AssertionError: the program took 38 clock cycles, expected 37.
```

`8`, `9`, `1`, `37` and `38` are all golden.

## Three of the four tests, and three non-architectural facts

The names below are the ones in `test_lab05.py`. (Lab 06's reference suite renames the same
three `p01`–`p03`.)

| test | asserts | correct value |
|---|---|---|
| `t02_the_scoreboard_that_stopped_scoring` | `done` pulses once per retired instruction | 9, for a 9-instruction program |
| `t03_halt_stays_low_while_running` | `halt` is never high while RUN is asserted | 0 |
| `t04_the_program_takes_exactly_37_cycles` | the program's exact clock count | 37 |

`t03` is the cheapest useful assertion in the course: one number, one expected value, no
arithmetic, and zero is the only right answer. `t04` costs one addition —
`4+5+4+4+4+4+5+4+3 = 37` from the documented instruction costs — and it is what turns "the
answer is right and it arrived late" from a thing nobody notices into a red row with a number
attached.

## The failure messages do most of the teaching

Look at what `t02` says when it fails, and why:

> The shortfall is 1. There is exactly one instruction in this program that appears exactly
> 1 time(s), and that is where to look.

`8, expected 9` and "some pulses are missing" are very different amounts of help. The first one
tells you the shortfall is one instruction, and the program has exactly one `STORE` in it. A
failure message that does arithmetic for the reader is a failure message that saves an hour.

Same for `t03`: *"1 blip in a program with one STORE in it is a useful ratio — count the
instructions of each kind and see which count matches."*

## The decision to argue about

`test_architecture.py` in this package is Lab 04's suite with **the cycle-count assertion
removed from `t04_a_loop`**. That is deliberate: a cycle count is a timing property, not an
architectural one, and with it left in, Lab 04's suite catches `B13` by accident and the
`make blind` demonstration does not work.

Which raises the real question: was Lab 04's cycle assertion a *protocol* test that happened to
be living in an architectural suite? It was. It is also a good test and it should stay in
Lab 04. Categories are for thinking with, not for filing.
