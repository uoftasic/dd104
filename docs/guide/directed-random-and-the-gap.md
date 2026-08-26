# Directed, random, and the gap between them

**Question this page answers:** *Should I write tests by hand or generate them?*

Both, and the answer that matters is neither of them:

> **Directed tests find what you thought of. Random tests find what you did not think of, from
> the distribution you chose. Neither finds what neither covers — and that third category is
> where the expensive bugs live.**

DD104 ships the machinery to measure all three of those sentences, so this page is
measurements rather than opinion.

## Directed: the tests you wrote on purpose

A directed test drives stimulus you chose and asserts an answer you worked out. Nine of the
eleven tests in the reference suite are directed, and none of them is clever — each is a short
program, a run, and a comparison. What makes them work is entirely the *choice* of stimulus.

Its failure mode has one shape, and it is worth naming before you meet it: **your test shares
your blind spot.** You choose the stimulus, so the input class you never thought of is
missing from both the design's testing and your model of what needs testing.

That is not a warning; it is the history of this repository. The first `LOAD`/`STORE` test
written for this core used `LOAD r1, r1` — load through a pointer into the register that held
the pointer, a perfectly real idiom. It passes on a core that takes the address from the wrong
register field, because when both fields name the same register there is no wrong one. Nobody
found out until the bug was deliberately injected and the suite did not move.

The habit that closes it is on [Where bugs hide](guide/where-bugs-hide.md). The point here is
that the fix was **another directed test**, written on purpose, after somebody named the input
class. You cannot generate your way out of a blind spot you have not named.

## Random: the stimulus nobody chose

`R10_random_programs` generates eight twenty-instruction programs, runs each on the chip, and
compares the final register file against [the golden model](guide/the-golden-model.md). It is
about forty lines including the generator, and you could not hand-compute a single one of its
expected answers.

**It works.** Measured, one bug at a time, against the shipped catalogue:

| bug | random programs that disagreed with the model |
|---|---|
| `B01_sub_operands_swapped` | **4 of 8** |
| `B10_ori_adds_instead_of_ors` | **5 of 8** |
| `B05_branch_offset_zero_extended` | **7 of 8** |

Three of the thirteen bugs, found by stimulus nobody wrote, checked against a model nobody had
to hand-compute. That is a genuinely good return on forty lines, and anybody who tells you
random testing is a substitute for thinking has still not earned the right to be smug about it,
because anybody who tells you it is worthless is also wrong.

Now measure what it did **not** do.

## `make gap` — what the generator covers, and what it cannot

The generator is designed around a **window**: an input condition a bug needs before it can be
seen at all. `SUB rX, rY` with `rX != rY` is the window for a swapped subtract; outside it, a
backwards `SUB` gives the right answer.

`gap.py` runs the same generator `R10` uses — imported from the same file, so there is one copy
of it and not two — through `golden.py`, and counts how often each of nine windows is entered.
No simulator is involved and it takes about a second:

```bash
cd labs/common
make gap
```

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

**Every number on that page is GOLDEN** — the generator is seeded, so it produces the same 160
instructions on every machine that runs it.

Three different things are going on in that table, and telling them apart is the skill.

### Windows it enters constantly

`B06`'s window — a shift by 2 or 3 — is entered thirteen times, in **8 of 8** programs. `B10`'s
is entered fifteen times. Random stimulus really does cover these, and it covers them without
anybody having thought about shift amounts at all. This is the case for random testing, and it
is a strong one: it is *cheap*, and it does not care what you failed to imagine.

### Windows it enters rarely — and one it enters and still misses

`B03`'s window is a flag-setting result that is non-zero with a zero low nibble. Entered
**twice** in 160 instructions. Run a thousand programs and it is entered 338 times in 20,000
instructions — about 1.7 % of them.

And yet:

```bash
make check TB=test_reference BUG=B03
```

```
      ok  the golden core                    11 tests, all passed        19.2s
  caught  B03_zero_flag_low_nibble           11 tests, 1 FAILED          16.2s
        R07_zero_and_negative_flags
            AssertionError: after r1 = 16 (0b00010000) the Z flag is 1.
```

**One test of eleven, and it is not the random one** — even though the random one entered the
window twice.

The reason is the most useful sentence on this page. `R10` compares
`model.snapshot()[0] != sp.regs()` — **the registers, and nothing else.** The flags are right
there in the snapshot and it does not look at them. A wrong `Z` can only reach a register at
all if a later branch consumes it and changes the control flow, and across those eight programs
none of them did.

> **Coverage of your stimulus and coverage of your checks are two different questions, and you
> have to ask both.** A generator can walk into the window and walk back out again, and if
> nothing in the checker can observe the difference, the run is not a test — it is exercise.

### Windows it can never enter

Two rows are marked `*` and both are **zero after a thousand programs and twenty thousand
instructions.** That is not bad luck, and no seed count will change it. The reason is in the
generator's own docstring:

```python
def random_program(seed, n=20):
    """Arithmetic, shifts, ORI, and forward branches that cannot loop.

    No LOAD or STORE: a random register value is a random address, and half of
    them are outside the 64-byte RAM. No backward branches: a random loop is an
    infinite loop. Both of those are worth testing — with stimulus you designed
    rather than stimulus you rolled."""
```

Both exclusions are **correct engineering**. A random 8-bit register value is an address outside
the 64-byte RAM more often than not, and a randomly-placed backward branch is an infinite loop
that turns your regression into a timeout. Nobody made a mistake here.

But look at what the constraints did. `B07` lives in `LOAD`. `B05` lives in backward branches.
The generator's necessary, sensible, well-reasoned exclusions are **the exact shape of the
directed tests you still have to write** — and the reference suite's `R06` and `R04` are
precisely those two tests.

> **A constrained random generator's constraints are a specification of what it will never
> find.** Write them down as a to-do list, because that is what they are.

## The catch you must not take credit for

`R10` does fail on `B05`, and the table above says the generator never emits a backward branch.
Both are true, and reconciling them is worth the two minutes.

The harness's `load()` appends a **parking loop** — one `JMP -1`, byte `0xF1` — after every
program, because this machine has no `HALT` instruction and a program has to stop itself. On a
core whose branch displacements are zero-extended instead of sign-extended, `JMP -1` is not a
loop. It is `JMP +15`.

So the program runs off its own end, walks through filler, wraps its 8-bit PC over a 64-byte
RAM, and **executes itself a second time over its own results.** Measured, on a three-instruction
program:

| | `r1` |
|---|---|
| model | 10 |
| chip | **20** |

The random test catches `B05` because the *harness* contributed one backward branch to every
program and the bug destroyed it. Nothing the generator chose had anything to do with it.

Two lessons, and the second is the one that matters:

1. This is real coverage and it is a real catch. Take the failure; it is telling you the truth.
2. **You cannot report it as evidence that your random testing covers backward branches**, and
   you certainly cannot rely on it. Change the parking idiom and the catch evaporates while the
   bug does not.

Being able to say *why* a test failed — not just that it did — is the difference between a
verification result and a lucky one.

## The gap

Put the three together:

| | finds | misses | costs |
|---|---|---|---|
| **directed** | exactly what you named | everything you did not name — including whatever your model of the design is wrong about | one test per input class, written by a person who understands the machine |
| **random** | things nobody named, inside the distribution you chose | anything the constraints exclude; anything your checker cannot observe | a generator, a model, and honesty about what it did not reach |
| **the gap** | — | what neither covers, which is where the bugs that reach silicon live | a written list |

The only thing that closes the gap is a list of questions you maintain by hand. That list is
**functional coverage**, it is not a tool, and
[Coverage as a question](guide/coverage-is-a-question.md) is what it looks like. On this machine
it starts:

| the question | why it is on the list |
|---|---|
| have I executed every opcode, including the three unimplemented ones? | |
| for every instruction, `rA == rB` **and** `rA != rB`? | four bugs live here |
| all four shift amounts, both directions? | shifting by 1 is what everybody writes |
| all sixteen branch displacements, taken **and** not taken? | half the number line is a bug's hiding place |
| two branches off one comparison? | flags are supposed to survive a branch |
| an `ORI` whose immediate overlaps bits `r0` already has? | `OR` and `ADD` agree until it does |
| a second `ORI`, once `r0` is no longer zero? | after reset, several wrong machines look right |
| `done` counted, `halt` counted, cycle counts asserted? | three bugs disturb nothing else |
| `clk_per_bit` **swept**, not sampled? | one bug does not exist at the default |

Every line is a question you can answer today with a `for` loop and a set. None of them requires
a tool. **The list is the engineering; the counting is clerical.**

## What would actually make the generator better

If you want to improve `R10` rather than replace it, there are three separate improvements and
they are not interchangeable:

1. **Constrain rather than exclude.** `LOAD` and `STORE` are excluded because a random address
   is usually out of range. Force the pointer register into `0..63` before the access and they
   come back — that is what "constrained random" means, and it is where the `B07` window lives.
   Backward branches come back the same way: a loop with a counter the generator sets up.
2. **Widen the checker, not the stimulus.** Compare the whole snapshot — registers, PC, `N`
   and `Z` — instead of the register tuple. That is one character of code and it makes every
   flag window the generator already enters actually count for something.
3. **Report what you reached.** `gap.py` is the smallest possible version of a coverage model:
   a list of named windows, a counter each, and a `*` on the ones that stayed cold. Without
   something like it, "we ran ten thousand random programs" is a statement about your CPU
   budget rather than about your design.

Do (2) first. It is the cheapest and it is the one that converts stimulus you already have into
checking you do not have.

## The reflex

> **After every random run, ask what it could not have reached** — and write the answer down
> next to the seed count. "Ten thousand programs, none of which contained a memory access" is a
> useful sentence. "Ten thousand programs" on its own is not a result, in exactly the way that
> [a green tick is not a result](guide/it-works-is-not-a-result.md).

Next: [The handshake is part of the contract](guide/the-handshake-is-the-contract.md), which is
the third category made concrete — two processors on which every value, in every register, on
every program, is correct. And then
[Lab 06](labs/lab-06-capstone-overview.md), where the coverage list above stops being a table on
a page and becomes the thing you are graded on.
