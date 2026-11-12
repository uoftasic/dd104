# Directed and random tests

This page answers: *should I write tests by hand or generate them?*

Both, and neither is enough on its own:

> Directed tests find what you thought of. Random tests find what you did not think of, from the
> distribution you chose. Neither finds what neither covers, and that third category is where the
> expensive bugs live.

DD104 ships the tools to measure all three parts of that, so this page is mostly measurements.

## Directed tests

A directed test drives stimulus you chose and asserts an answer you worked out. Nine of the eleven
tests in the reference suite are directed, and none of them is clever: each is a short program, a
run and a comparison. What makes them work is the choice of stimulus.

Directed testing fails in one way: your test shares your blind spot. You choose the stimulus, so
an input class you never thought of is missing from both the testing and your idea of what needs
testing.

This repository's history shows it. The first `LOAD`/`STORE` test written for this core used
`LOAD r1, r1`: load through a pointer into the register that held the pointer, a real idiom. It
passes on a core that takes the address from the wrong register field, because when both fields
name the same register there is no wrong one. Nobody found out until the bug was injected on
purpose and the suite stayed green.

[Where bugs hide](guide/where-bugs-hide.md) has the habit that prevents it. The point here is that
the fix was another directed test, written on purpose after somebody named the input class. You
cannot generate your way out of a blind spot you have not named.

## Random tests

`R10_random_programs` generates eight twenty-instruction programs, runs each on the chip, and
compares the final register file with [the golden model](guide/the-golden-model.md). It is about
forty lines including the generator, and you could not work out a single one of its expected
answers by hand.

It works. Measured one bug at a time against the catalogue:

| Bug | Random programs that disagreed with the model |
|---|---|
| `B01_sub_operands_swapped` | 4 of 8 |
| `B10_ori_adds_instead_of_ors` | 5 of 8 |
| `B05_branch_offset_zero_extended` | 7 of 8 |

Three of the thirteen bugs, found by stimulus nobody wrote and checked against a model nobody had
to work out by hand. That is a good return on forty lines. Random testing is not a substitute for
thinking, and it is not worthless either.

Now measure what it did not do.

## What the generator reaches

The generator is designed around **windows**: input conditions a bug needs before it can be seen at
all. `SUB rX, rY` with `rX != rY` is the window for a swapped subtract; outside it, a backwards
`SUB` gives the right answer.

`gap.py` runs the same generator `R10` uses (imported from the same file, so there is one copy)
through `golden.py`, and counts how often each of nine windows is entered. No simulator is involved
and it takes about a second. You'll run it as `make gap` in
[Lab 04, Part 6](labs/lab-04-your-first-bug-hunt-overview.md#part-6-what-random-stimulus-reaches):

```
the eight seeds R10 actually runs
------------------------------------------------------------------------
window                                                entered   programs
  B01  SUB, operands differ by neither 0 nor 128            6      5 of 8
  B02  NAND with two different operands                    11      5 of 8
  B06  shift by 2 or 3                                     13      8 of 8
 *B05  branch with a negative displacement                  0      0 of 8
  B09  two branches off one comparison                      7      5 of 8
 *B07  any LOAD or STORE                                    0      0 of 8
  B03  non-zero result whose low nibble is zero             2      2 of 8
  B10  ORI that sets a bit r0 already had                  15      5 of 8
  B11  ORI executed while r0 is non-zero                   19      6 of 8
------------------------------------------------------------------------
8 programs, 160 instructions written, 2 of 9 windows never entered
```

Every number in that table is exact: the generator is seeded, so it writes the same 160
instructions on every machine.

Three different things are going on in that table.

### Windows it enters constantly

`B06`'s window, a shift by 2 or 3, is entered thirteen times, in 8 of 8 programs. `B10`'s is
entered fifteen times. Random stimulus does cover these, without anyone having thought about shift
amounts at all. That is the case for random testing, and it is a strong one: it is cheap, and it
does not depend on what you failed to imagine.

### Windows it enters rarely, and one it enters and still misses

`B03`'s window is a flag-setting result that is non-zero with a zero low nibble. It is entered
twice in 160 instructions. Over a thousand programs it is entered 338 times in 20,000 instructions,
about 1.7 % of them.

And yet this is the reference suite against `B03`:

```
      ok  the golden core                    11 tests, all passed        19.2s
  caught  B03_zero_flag_low_nibble           11 tests, 1 FAILED          16.2s
        R07_zero_and_negative_flags
            AssertionError: after r1 = 16 (0b00010000) the Z flag is 1.
```

One test of eleven catches it, and it is not the random one, even though the random one entered
the window twice.

The reason is the most useful point on this page. `R10` compares `model.snapshot()[0] != sp.regs()`:
the registers and nothing else. The flags are in the snapshot and it ignores them. A wrong `Z` can
only reach a register if a later branch uses it and changes the control flow, and none of those
eight programs did.

> Coverage of your stimulus and coverage of your checks are two different questions, and you have
> to ask both. A generator can walk into a window and back out again, and if nothing in the checker
> can see the difference, the run was exercise, not a test.

### Windows it can never enter

The two rows marked `*` are still zero after a thousand programs and twenty thousand instructions.
That is not bad luck, and no number of seeds will change it. The generator's docstring says why:

```python
def random_program(seed, n=20):
    """Arithmetic, shifts, ORI, and forward branches that cannot loop.

    No LOAD or STORE: a random register value is a random address, and half of
    them are outside the 64-byte RAM. No backward branches: a random loop is an
    infinite loop. Both of those are worth testing — with stimulus you designed
    rather than stimulus you rolled."""
```

Both exclusions are good engineering. A random 8-bit register value is an address outside the
64-byte RAM more often than not, and a randomly placed backward branch is an infinite loop that
turns your regression into a timeout. Nobody made a mistake.

But look at what the constraints did. `B07` lives in `LOAD`, and `B05` lives in backward branches.
The generator's necessary, sensible exclusions are exactly the directed tests you still have to
write, and the reference suite's `R06` and `R04` are those two tests.

> A constrained random generator's constraints describe what it will never find. Write them down as
> a to-do list, because that is what they are.

## A catch you must not take credit for

`R10` does fail on `B05`, and the table says the generator never emits a backward branch. Both are
true, and it is worth two minutes to see why.

The harness's `load()` appends a parking loop, one `JMP -1` (byte `0xF1`), after every program,
because this machine has no `HALT` instruction and a program has to stop itself. On a core whose
branch displacements are zero-extended instead of sign-extended, `JMP -1` is not a loop. It is
`JMP +15`.

So the program runs off its own end, through filler, wraps its 8-bit PC over the 64-byte RAM, and
executes itself a second time over its own results. Measured on a three-instruction program:

| | `r1` |
|---|---|
| Model | 10 |
| Chip | 20 |

The random test catches `B05` because the harness added one backward branch to every program and
the bug broke it. Nothing the generator chose had anything to do with it.

1. This is real coverage and a real catch. Take the failure; it is telling you the truth.
2. You cannot report it as evidence that your random testing covers backward branches, and you
   cannot rely on it. Change the parking idiom and the catch disappears while the bug stays.

Being able to say why a test failed, and not just that it did, is the difference between a
verification result and a lucky one.

## The gap

Put the three together:

| | Finds | Misses | Costs |
|---|---|---|---|
| Directed | Exactly what you named | Everything you did not name, including whatever your model of the design gets wrong | One test per input class, written by someone who understands the machine |
| Random | Things nobody named, inside the distribution you chose | Anything the constraints exclude; anything your checker cannot observe | A generator, a model, and honesty about what it did not reach |
| The gap | | What neither covers, which is where the bugs that reach silicon live | A written list |

The only thing that closes the gap is a list of questions you maintain by hand. That list is
functional coverage. It is not a tool, and [Coverage as a question](guide/coverage-is-a-question.md)
shows what it looks like. On this machine it starts:

| The question | Why it is on the list |
|---|---|
| Have I executed every opcode, including the three unimplemented ones? | |
| For every instruction, `rA == rB` and `rA != rB`? | Four bugs live here |
| All four shift amounts, both directions? | Shifting by 1 is what everybody writes |
| All sixteen branch displacements, taken and not taken? | Half the number line is a hiding place |
| Two branches off one comparison? | Flags are supposed to survive a branch |
| An `ORI` whose immediate overlaps bits `r0` already has? | `OR` and `ADD` agree until it does |
| A second `ORI`, once `r0` is no longer zero? | After reset, several wrong machines look right |
| `done` counted, `halt` counted, cycle counts asserted? | Three bugs disturb nothing else |
| `clk_per_bit` swept, not sampled? | One bug does not exist at the default |

You can answer every line today with a `for` loop and a set, without a tool. Writing the list is
the engineering; counting is clerical.

## Making the generator better

If you want to improve `R10` rather than replace it, there are three separate improvements, and
they are not interchangeable:

1. Constrain instead of exclude. `LOAD` and `STORE` are excluded because a random address is
   usually out of range. Force the pointer register into `0..63` before the access and they come
   back; that is what "constrained random" means, and it is where the `B07` window lives. Backward
   branches come back the same way, as a loop with a counter the generator sets up.
2. Widen the checker, not the stimulus. Compare the whole snapshot (registers, PC, `N` and `Z`)
   instead of the register tuple. That is a one-character change, and it makes every flag window
   the generator already enters count.
3. Report what you reached. `gap.py` is the smallest possible coverage model: a list of named
   windows, a counter for each, and a `*` on the ones that stayed cold. Without something like it,
   "we ran ten thousand random programs" says more about your CPU budget than about your design.

Do (2) first. It is the cheapest, and it turns stimulus you already have into checking you don't
have yet.

> After every random run, ask what it could not have reached, and write the answer next to the
> seed count. "Ten thousand programs, none of which contained a memory access" is a useful
> sentence. "Ten thousand programs" on its own is not a result, for the same reason
> [a green tick is not a result](guide/it-works-is-not-a-result.md).

## Check yourself

1. A random generator never emits `STORE`. Which bugs in the catalogue can it never reach
   directly, and what directed test would you write?
2. `R10` entered `B03`'s window twice and still passed. What one change to its checker fixes that?

Next: [Lab 04: Your first bug hunt](labs/lab-04-your-first-bug-hunt-overview.md).
