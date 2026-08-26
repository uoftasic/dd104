# Where bugs hide

**Question this page answers:** *The bugs I am hunting are one line each. Why can I not just
read the file?*

Because a one-line bug is not a typo. It is a line that is *correct-looking*, in the right
style, in the right place, doing something the surrounding code also does — and it is wrong
only on inputs you would not naturally write.

That sentence is the whole course. This page is the evidence for it, and then the taxonomy that
turns it into a way of working.

> **What this page deliberately does not tell you.** DD104 ships thirteen broken cores and
> [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md) deals you one without saying which. Every
> catalogue name below, and everything each one *hides behind*, is already printed by
> `make bugs`. **No line numbers and no RTL appear here.** Finding a bug in a design you cannot
> diff against a known-good copy is the skill; handing you the diff would delete it.

## Start with the number that should be impossible

`B01_sub_operands_swapped` makes the ALU compute `B - A` instead of `A - B`. Drive every legal
vector through the ALU — [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) does
exactly this, in about twenty seconds — and it is wrong on

```
65024 of 393216 vectors have the wrong value: {'SUB': 65024}.
  First one: SUB(0x00, 0x01) = 0x01, expected 0xFF.
```

**65,024 of the 65,536 `SUB` vectors. 99.2 % of them.** A processor that gets subtraction wrong
ninety-nine times out of a hundred.

And it passed code review. And it passed the only test the chip ever shipped with. And on
DD104's own six-test example suite it takes four separate assertions to bring it down.

That combination is not a paradox, and understanding why it is not a paradox is the single most
useful idea in verification.

## A bug is a disagreement set

Stop thinking of a bug as a broken line. Think of it as **the set of inputs on which the wrong
implementation and the right one produce different answers.**

- If that set is *everything*, you find the bug by looking at it. The design never works, the
  first person to run it notices, and it never reaches a shuttle.
- If that set is *empty*, there is no bug. The two implementations are the same machine, and
  which one you shipped is a matter of taste. (This is not hypothetical here: `ORI` could
  accumulate in `r0` or in `r1` and the two machines are exactly isomorphic. DD104 had to
  *decide*, because measurement could not.)
- **Every bug that survives to silicon lives in between**, and it survives precisely because
  its disagreement set excludes the inputs people actually write.

So for `B01`, the question is not "how did nobody see 99.2 % wrong?" It is: **what are the 512
survivors?**

`A - B == B - A` exactly when $2(A-B) \equiv 0 \pmod{256}$ — that is, when $A \equiv B$ or
$A - B \equiv 128$. Two hundred and fifty-six solutions each, 512 in total, and $65{,}536 - 512 =
65{,}024$, which is the number the sweep printed.

Now look at what is in that set. SimProc has four registers, no `MOV` and no `CLR`, so
**`SUB rX, rX` is how you zero a register**, and it is in nearly every program on this machine.
It is one of the 512. The bug is invisible on the single most common way anybody writes the
instruction it breaks.

That is not luck. **A bug survives review exactly when its disagreement set misses the idioms**,
and the idioms are what a reviewer's eye is trained on.

## Six places a disagreement set hides

Every bug in the DD104 catalogue is one of these six shapes, and so is most of what you will
find in industry. Each one comes with a habit, and the habit is the transferable part.

### 1. Aliasing — the two things are the same thing

An instruction with two register fields has a case where both fields name the same register. In
that case there is no wrong field to pick.

| | |
|---|---|
| catalogue | `B01`, `B02`, `B04`, `B07` |
| measured | `B02` disagrees on 65,280 of 65,536 `NAND` vectors — the 256 survivors are exactly `A == B` |
| why it survives | this machine has no `NOT`, so `NAND rX, rX` **is** how you invert, and `SUB rX, rX` is how you clear |

`B07` is the set piece, and its history is the best argument in the course. The first
`LOAD`/`STORE` test written for this core used `LOAD r1, r1` — load through a pointer into the
register that held the pointer, which is a real idiom you write when you are done with the
address. That test passed on a core that takes the address from the wrong register field,
because when both fields name the same register there is no wrong one. Nobody noticed until the
bug was deliberately injected and the suite did not move.

> **The habit:** make every operand distinct **on purpose**, and check the register that should
> *not* have moved as well as the one that should.

### 2. The identity element — and reset hands you one for free

`x | 0 == x + 0`, and `0 | imm == 0 + imm`. Operators that differ in general agree on their
identity elements — and **a reset sets every register in the machine to the identity element of
almost everything.**

| | |
|---|---|
| catalogue | `B10`, `B11` |
| measured | `ORI 5 ; ORI 3` gives 8 on a core whose `ORI` adds; it should give 7. `ORI 8 ; ORI 3` gives 11 on **both** |
| why it survives | the *first* `ORI` after reset is `0 \| imm`, which is correct under both bugs. And building a constant out of disjoint bit groups — the natural way to assemble a value from a 5-bit immediate — never overlaps, so it never diverges |

`B11` is the sharper one. It writes the right value to the wrong register — and after a reset
the right and wrong registers hold the same thing, so the first `ORI` of any program produces a
machine state that is correct *under a different name*. Divergence starts at the second `ORI`.

> **The habit:** never test an operation only from a reset state, and never test it only once.
> Two of anything — two `ORI`s, two branches off one compare, two writes to the same
> register — is where state stops being a coincidence.

### 3. The default value of a parameter

A parameter that is only ever driven at its default has been tested at one point of a range that
silicon will be used across.

| | |
|---|---|
| catalogue | `B12`, and `B06` in spirit |
| measured | `B12` scores **10/10 on the full systematic suite at `clk_per_bit = 32`** — indistinguishable from a correct core — and **0/10 at `clk_per_bit = 8`** |
| why it survives | `clk_per_bit` is set by eight external pins, every lab uses one value, and at that value the receiver's drift is still inside the bit |

There is a second trap layered on the first, and it is worth carrying out of this course:
at `clk_per_bit = 16`, `PING` still answers `0xAA` **over a link that cannot carry data.**
`PING` sends `0xF0`, whose top bit is already 1; a receiver sampling one bit-time late reads the
stop bit, which is also 1, and the command decodes perfectly. **A link test can pass over a
broken link.**

`B06` is the same shape one level down: the shift-amount field is two bits wide, amounts 0 and 1
are correct, and 1 is what everybody writes.

> **The habit:** sweep the field, do not sample it. Four shift amounts, sixteen branch
> displacements, five baud rates — these are small enough to walk exhaustively, and testing all
> of them is not thorough, it is just finishing.

### 4. One half of a signed range

| | |
|---|---|
| catalogue | `B05` |
| measured | all eight forward displacements `+0 … +7` land exactly right; every backward one lands **16 too far forward** |
| why it survives | "skip the next instruction" is the first branch anybody writes, and it works. The first thing that breaks is the first loop — because a loop is the only reason to branch backwards |

Half the number line is correct, and it is the half you test first.

> **The habit:** when a field is signed, the test that sweeps it must **cross zero**.

### 5. The right answer, delivered through the wrong channel

The values are correct. All of them. Something that is not a value is wrong.

| | |
|---|---|
| catalogue | `B03` (flags), `B08` (`done`), `B13` (`halt` and one cycle) |
| measured | the exhaustive ALU sweep on `B03` reports **0 value mismatches and 25,726 flag mismatches** out of 393,216 |
| why it survives | a testbench that reads registers and memory is testing a strictly smaller machine than the one on the die |

`B03` is the one to sit with. It is not that a value-only testbench *usually* misses it — it
**cannot** see it, ever, no matter how many vectors you add. More stimulus is not the missing
ingredient; a different *kind* of check is. That is
[Flags are architectural state](guide/flags-are-state.md).

`B08` inverts what you expect a bug to do. If your scoreboard triggers on `done` and one
instruction stops pulsing it, the scoreboard does not report an error — it was never woken up.
It compares everything it was asked to compare, finds zero mismatches, and reports zero
mismatches **truthfully**, having made one comparison fewer than there were instructions.
**A missing trigger does not fail your test. It silently stops your test from testing**, which
is strictly worse, because a failure is visible.

> **The habit:** list the design's outputs. Every one you never assert on is unverified, and the
> list is shorter than you think — here it is `done`, `halt`, `uart_tx`, and the clock.

### 6. The second use of a piece of state

State that is correct when you use it once can be destroyed before you use it twice.

| | |
|---|---|
| catalogue | `B09`, and `B11` again |
| measured | one branch after a compare works perfectly, every time. The second branch off the same compare reads garbage |
| why it survives | most programs compare once and branch once, and this machine's flags are read combinationally in the same cycle the branch decides — so the *first* branch always sees the right thing |

In a machine whose `SUB` doubles as its compare, the **lifetime of the flags is load-bearing and
completely invisible in the source.** "The comparison is still valid" is an assumption, and
assumptions get tests.

> **The habit:** use each piece of state twice, and assert that the second use sees what the
> first one did.

## The evidence that this is not a story

Two commands, in the shipped package, that make the whole argument without any prose.

**All thirteen pass the only test this chip has.**

```bash
cd labs/common
make shuttle
```

```
 13 of 13 deliberately broken processors pass the
 only test this chip has.
```

**And a real testbench, on a real bug, is not obviously enough either.** `test_example.py` is
six worked tests — arithmetic on distinct operands, flags, a loop with a hand-checked cycle
count, and a full golden-model comparison over 29 instructions. Point it at `B10`:

```bash
make check TB=test_example BUG=B10
```

```
      ok  the golden core                    6 tests, all passed          6.6s
  MISSED  B10_ori_adds_instead_of_ors        6 tests, all passed          5.7s
------------------------------------------------------------------------
 VERDICT: FAIL — your testbench passes B10_ori_adds_instead_of_ors too.
   A test that passes on a broken core is not testing that core.
   That bug hides behind: ORing in bits that were not already set — ADD agrees
   Write a test whose stimulus does not do that.
```

Six good tests. Twenty-nine instructions checked against a reference model, register by
register. **`MISSED`**, because not one of those instructions happened to OR a bit that was
already set.

The test that catches it is three lines long, and the only thing special about it is the
stimulus:

```python
await sp.run([ORI(5), ORI(3), ORI(24)])
assert sp.reg(0) == 31          # 5 | 3 = 7, 7 | 24 = 31.  Added: 5 + 3 + 24 = 32.
```

> **Verification is mostly taste about inputs.** Not machinery, not assertion count, not
> framework. The reference suite that catches all thirteen bugs is eleven ordinary tests — a
> short program, a run, and a comparison — and what makes them work is entirely the *choice* of
> stimulus: not subtracting a number from itself, not shifting by one, not branching only
> forwards, not ORing in bits that were already set.

## So what is reading the file for?

Not nothing. Reading tells you **where to look**. It cannot tell you that you are finished, and
on a design you did not write it cannot even tell you which of two plausible lines is the wrong
one — because the wrong line is usually the correct line from four clauses further down.

Three reasons the read-it-carefully instinct fails on exactly this class of bug:

1. **You do not have the good version to diff against.** That is the normal case in industry
   and it is the case [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md) is built around. With
   a diff, all thirteen of these take four seconds and teach nothing.
2. **A one-line bug is written in the file's own dialect.** One of the thirteen *adds* a
   line, in the right style, in the right place, that looks like it belongs. Injected bugs do
   not have to be typos.
3. **Reading scales with the file; testing scales with the machine.** The file is 1,178 lines.
   The machine is [554 bits of state and eleven instructions](guide/simproc-in-one-page.md). One
   of those two numbers is going to grow on your next project and one of them is not.

## The question list

The taxonomy above, turned into something you can run down while a core is in front of you. Each
question either narrows the search or eliminates a region of the design.

| | Question | What a "yes" rules in | Shape |
|---|---|---|---|
| 1 | Which **instruction classes** are wrong — arithmetic, shift, load/store, branch? | the decode path for that class | |
| 2 | Is it wrong for **all operands**, or only some? | a data-dependent path — the ALU, or a width | |
| 3 | Does it depend on **rA and rB being different**? | a register-select field, read or write | 1 |
| 4 | Which **register** ends up wrong — the destination, a source, a bystander? | the write-back address | 1 |
| 5 | Does it survive a **reset**? Is the first one right and the second not? | somewhere reset makes two things equal | 2 |
| 6 | Are the **values** right and something else wrong? | flags, `done`, `halt`, the cycle count | 5 |
| 7 | Does a **field value you have only driven at one setting** change it? | a shift amount, a displacement, a baud divider | 3, 4 |

Run them in order. Each answer is one small program, and the difference between a five-minute
debug and a two-hour one is almost never insight — it is whether you spent the first ten
minutes narrowing or the first ten minutes reading.

## The reflex

> **Before you write a test, name the input class it will not reach.**
>
> Not "what does this test check" — you already know that. *Which operand pattern, which field
> value, which half of which range, which output pin does this stimulus never touch?* Write the
> answer in the docstring. That sentence is the most valuable line in most testbenches, and it
> is the one nobody writes.

And the corollary, which is what `make check` mechanises: **a test you have never seen fail is
a claim you have never checked.** Deliberately break the thing your test is supposed to be
watching, and find out whether it notices. That is how `B07` was found, in this repository, by
the person who had written the test that missed it.

Next: [Directed, random, and the gap](guide/directed-random-and-the-gap.md) — because the obvious
reply to this page is "so generate more stimulus", and it is half right.
