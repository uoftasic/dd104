# Where bugs hide

This page answers: *the bugs I am hunting are one line each. Why can't I just read the file?*

Because a one-line bug is not a typo. It is a line that looks correct, in the right style and the
right place, doing something the surrounding code also does, and it is wrong only on inputs you
would not naturally write. This page gives the evidence for that, and then a taxonomy that turns it
into a way of working.

> This page does not tell you where any bug is. DD104 ships thirteen broken cores, and
> [Lab 04](../labs/lab-04-your-first-bug-hunt-overview.md) deals you one without saying which. Every
> catalogue name below, and what each one hides behind, is already printed by `make bugs`. No
> line numbers or RTL appear here. Finding a bug in a design you cannot diff against a known-good
> copy is the skill, and a diff would skip it.

## The 99.2 % case

`B01_sub_operands_swapped` makes the ALU compute `B - A` instead of `A - B`. Drive every legal
vector through the ALU, as [Lab 03](../labs/lab-03-three-blocks-before-the-processor-overview.md)
does in about twenty seconds, and it is wrong on

```
65024 of 393216 vectors have the wrong value: {'SUB': 65024}.
  First one: SUB(0x00, 0x01) = 0x01, expected 0xFF.
```

That is 65,024 of the 65,536 `SUB` vectors, 99.2 % of them: a processor that gets subtraction
wrong ninety-nine times in a hundred.

It passed code review. It passed the only test the chip ever shipped with. On DD104's own six-test
example suite it takes four separate assertions to catch it.

Those facts fit together, and seeing why is the single most useful idea in verification.

## Disagreement sets

Think of a bug not as a broken line but as the set of inputs on which the wrong implementation and
the right one give different answers.

- If that set is everything, you find the bug by looking. The design never works, the first person
  to run it notices, and it never reaches a shuttle.
- If that set is empty, there is no bug. The two implementations are the same machine, and which
  one you shipped is a matter of taste. (This happens here: `ORI` could accumulate in `r0` or in
  `r1`, and the two machines are exactly isomorphic. DD104 had to decide, because measurement
  could not.)
- Every bug that survives to silicon is in between, and it survives because its disagreement set
  excludes the inputs people actually write.

So for `B01` the question is not how nobody saw 99.2 % wrong. It is: what are the 512 survivors?

`A - B == B - A` exactly when $2(A-B) \equiv 0 \pmod{256}$, that is, when $A \equiv B$ or
$A - B \equiv 128$. Each has 256 solutions, 512 in total, and $65{,}536 - 512 = 65{,}024$, which is
the number the sweep printed.

Now look at what is in that set. SimProc has four registers and no `MOV` or `CLR`, so `SUB rX, rX`
is how you zero a register, and it is in nearly every program on this machine. It is one of
the 512. The bug is invisible on the most common way anyone writes the instruction it breaks.

That is the pattern. A bug survives review when its disagreement set misses the idioms, and the
idioms are what a reviewer's eye is trained on.

## Six places a disagreement set hides

Every bug in the DD104 catalogue has one of these six shapes, and so does most of what you will
find in industry. Each comes with a habit, and the habit is the part that transfers.

### 1. Aliasing

An instruction with two register fields has a case where both fields name the same register, and
in that case there is no wrong field to pick.

| | |
|---|---|
| Catalogue | `B01`, `B02`, `B04`, `B07` |
| Measured | `B02` disagrees on 65,280 of 65,536 `NAND` vectors; the 256 survivors are exactly `A == B` |
| Why it survives | The machine has no `NOT`, so `NAND rX, rX` is how you invert, and `SUB rX, rX` is how you clear |

`B07` has the best history in the course. The first `LOAD`/`STORE` test written for this core used
`LOAD r1, r1`: load through a pointer into the register that held the pointer, a real idiom you
use when you are done with the address. That test passed on a core that takes the address from the
wrong register field, because when both fields name the same register there is no wrong one.
Nobody noticed until the bug was injected on purpose and the suite stayed green.

> The habit: make every operand distinct on purpose, and check the register that should not have
> moved as well as the one that should.

### 2. Identity elements and reset

`x | 0 == x + 0`, and `0 | imm == 0 + imm`. Operators that differ in general agree on their
identity elements, and a reset sets every register in the machine to the identity element of
almost everything.

| | |
|---|---|
| Catalogue | `B10`, `B11` |
| Measured | `ORI 5 ; ORI 3` gives 8 on a core whose `ORI` adds; it should give 7. `ORI 8 ; ORI 3` gives 11 on both |
| Why it survives | The first `ORI` after reset is `0 \| imm`, which is correct under both bugs. Building a constant from disjoint bit groups, the natural way to assemble a value from a 5-bit immediate, never overlaps, so it never diverges |

`B11` is the sharper one. It writes the right value to the wrong register, and after a reset the
right and wrong registers hold the same thing, so the first `ORI` of any program leaves a machine
state that is correct under a different name. Divergence starts at the second `ORI`.

> The habit: never test an operation only from a reset state, and never test it only once. Two of
> anything (two `ORI`s, two branches off one compare, two writes to the same register) is where
> state stops being a coincidence.

### 3. Parameters left at their default

A parameter only ever driven at its default has been tested at one point of a range that silicon
will be used across.

| | |
|---|---|
| Catalogue | `B12`, and `B06` in spirit |
| Measured | `B12` scores 10/10 on the full systematic suite at `clk_per_bit = 32`, indistinguishable from a correct core, and 0/10 at `clk_per_bit = 8` |
| Why it survives | `clk_per_bit` is set by eight external pins, every lab uses one value, and at that value the receiver's drift still lands inside the bit |

There is a second trap on top of the first. At `clk_per_bit = 16`, `PING` still answers `0xAA`
over a link that cannot carry data. `PING` sends `0xF0`, whose top bit is already 1; a receiver
sampling one bit-time late reads the stop bit, which is also 1, and the command decodes perfectly.
A link test can pass over a broken link.

`B06` is the same shape one level down: the shift-amount field is two bits wide, amounts 0 and 1
are correct, and 1 is what everybody writes.

> The habit: sweep the field instead of sampling it. Four shift amounts, sixteen branch
> displacements, five baud rates: these are small enough to walk, and testing all of them is just
> finishing the job.

### 4. One half of a signed range

| | |
|---|---|
| Catalogue | `B05` |
| Measured | All eight forward displacements, `+0` to `+7`, land exactly right; every backward one lands 16 too far forward |
| Why it survives | "Skip the next instruction" is the first branch anybody writes, and it works. The first thing to break is the first loop, because a loop is the only reason to branch backwards |

Half the number line is correct, and it is the half you test first, so the bug survives every test
that only branches forwards.

> The habit: when a field is signed, the sweep must cross zero.

### 5. Outputs that are not values

Every value is correct. Something that is not a value is wrong.

| | |
|---|---|
| Catalogue | `B03` (flags), `B08` (`done`), `B13` (`halt` and one cycle) |
| Measured | The exhaustive ALU sweep on `B03` reports 0 value mismatches and 25,726 flag mismatches out of 393,216 |
| Why it survives | A testbench that reads registers and memory is testing a smaller machine than the one on the die |

`B03` is the one to think about. A value-only testbench does not usually miss it; it cannot see it,
ever, however many vectors you add. More stimulus is not what is missing; a different kind of check
is. That is [Flags as architectural state](../guide/flags-are-state.md).

`B08` does the opposite of what you expect a bug to do. If your scoreboard triggers on `done` and
one instruction stops pulsing it, the scoreboard does not report an error: it was never woken up.
It compares everything it was asked to compare, finds no mismatches, and reports that truthfully,
having made one comparison fewer than there were instructions. A missing trigger does not fail
your test. It quietly stops your test from testing, which is worse, because a failure is visible.

> The habit: list the design's outputs. Every one you never assert on is unverified, and the list
> is shorter than you think. Here it is `done`, `halt`, `uart_tx` and the clock.

### 6. Using state twice

State that is correct when you use it once can be destroyed before you use it twice.

| | |
|---|---|
| Catalogue | `B09`, and `B11` again |
| Measured | One branch after a compare works every time. A second branch off the same compare reads garbage |
| Why it survives | Most programs compare once and branch once, and this machine's flags are read combinationally in the same cycle the branch decides, so the first branch always sees the right value |

In a machine whose `SUB` doubles as its compare, how long the flags stay valid matters, and the
source does not show it. "The comparison is still valid" is an assumption, and assumptions need
tests.

> The habit: use each piece of state twice, and assert that the second use sees what the first did.

## The evidence

All thirteen broken cores pass the only test the chip has: you saw `13 of 13` in
[Lab 02, Part 1](../labs/lab-02-the-only-test-this-chip-has-overview.md#part-1-the-shipped-test).

A real testbench against a real bug is not obviously enough either. `test_example.py` has six
worked tests: arithmetic on distinct operands, flags, a loop with a hand-checked cycle count, and
a full golden-model comparison over 29 instructions. Against `B10`:

```
      ok  the golden core                    6 tests, all passed          6.6s
  MISSED  B10_ori_adds_instead_of_ors        6 tests, all passed          5.7s
------------------------------------------------------------------------
 VERDICT: FAIL — your testbench passes B10_ori_adds_instead_of_ors too.
   A test that passes on a broken core is not testing that core.
   That bug hides behind: ORing in bits that were not already set — ADD agrees
   Write a test whose stimulus does not do that.
```

Six good tests and twenty-nine instructions checked register by register against a reference
model, and it is `MISSED`, because none of those instructions happened to OR in a bit that was
already set. You'll run this in [Lab 06, Part 2](../labs/lab-06-capstone-overview.md#part-2-b10-the-wrong-operator).

The test that catches it is three lines, and what makes it work is the stimulus:

```python
await sp.run([ORI(5), ORI(3), ORI(24)])
assert sp.reg(0) == 31          # 5 | 3 = 7, 7 | 24 = 31.  Added: 5 + 3 + 24 = 32.
```

> Verification is mostly a matter of choosing inputs well, not of machinery, assertion count or
> framework. The reference suite that catches all thirteen bugs is eleven ordinary tests (a short
> program, a run, a comparison), and what makes them work is the choice of stimulus: not
> subtracting a number from itself, not shifting by one, not branching only forwards, not ORing in
> bits that were already set.

## Reading the file

Reading tells you where to look. It cannot tell you that you are finished, and on a design you did
not write it often cannot even tell you which of two plausible lines is wrong, because the wrong
line usually looks like a correct line from four clauses further down.

Three reasons the "read it carefully" instinct fails on this class of bug:

1. You don't have the good version to diff against. That is normal in industry, and it is what
   [Lab 04](../labs/lab-04-your-first-bug-hunt-overview.md) is built around. With a diff, all thirteen
   take four seconds and teach nothing.
2. A one-line bug is written in the file's own style. One of the thirteen adds a line, in the
   right style and the right place, that looks like it belongs. Injected bugs don't have to be
   typos.
3. Reading scales with the file; testing scales with the machine. The file is 1,178 lines. The
   machine is [554 bits of state and eleven instructions](../guide/simproc-in-one-page.md). On your
   next project one of those numbers will grow and the other won't.

## The question list

This is the taxonomy as something to work down while a core is in front of you. Each question
either narrows the search or rules out a region of the design.

| | Question | What a "yes" rules in | Shape |
|---|---|---|---|
| 1 | Which instruction classes are wrong: arithmetic, shift, load/store, branch? | The decode path for that class | |
| 2 | Is it wrong for all operands, or only some? | A data-dependent path: the ALU, or a width | |
| 3 | Does it depend on rA and rB being different? | A register-select field, read or write | 1 |
| 4 | Which register ends up wrong: the destination, a source, a bystander? | The write-back address | 1 |
| 5 | Does it survive a reset? Is the first one right and the second not? | Somewhere reset makes two things equal | 2 |
| 6 | Are the values right and something else wrong? | Flags, `done`, `halt`, the cycle count | 5 |
| 7 | Does a field you have only driven at one setting change it? | A shift amount, a displacement, a baud divider | 3, 4 |

Work through them in order. Each answer is one small program, and the difference between a
five-minute debug and a two-hour one is rarely insight. It is whether you spent the first ten
minutes narrowing or the first ten minutes reading.

> Before you write a test, name the input class it will not reach: which operand pattern, which
> field value, which half of which range, which output pin. Write the answer in the docstring. It
> is the most valuable line in most testbenches, and almost nobody writes it.

And the corollary, which `make check` mechanises: a test you have never seen fail is a claim you
have never checked. Break the thing your test is supposed to watch, and see whether it notices.
That is how `B07` was found in this repository, by the person who had written the test that
missed it.

## Check yourself

1. A broken `ADD` gives the right answer whenever one operand is zero. Which of the six shapes is
   that?
2. A suite tests every branch with displacement `+1`. Which bug in the catalogue can it never see?
3. For `NAND`, how many of the 65,536 operand pairs survive a NAND-is-NOR bug, and which ones?

Next: [Directed and random tests](../guide/directed-random-and-the-gap.md).
