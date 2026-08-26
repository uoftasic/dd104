# Coverage as a question, not a metric

**Question this page answers:** *How do I know when I have tested enough?*

You do not, and no number will tell you. That is the honest answer, and everything useful
about coverage follows from taking it seriously rather than looking for a way around it.

Coverage is not a score you are trying to raise. **Coverage is a machine that generates
questions about your stimulus**, and each question is worth exactly as much as the answer you
give it. The number attached to it is a side effect.

The fastest way to believe that is to point a real coverage tool at the two testbenches from
[The lazy testbench](guide/the-lazy-testbench.md) and watch it find the blind spot without being
told anything about adders.

## Run it

```bash
cd labs/lab-01-the-adder-you-already-trust/coverage
make
```

This one takes about **twelve seconds**, because it builds the design twice with Verilator —
Icarus has no coverage instrumentation, so this is the one place in the early course where
the strict simulator is the only one that can answer.

```
==================================================================
 COVERAGE   what did the stimulus actually reach?
==================================================================

------------------------------------------------------------------
 six hand-picked cases
------------------------------------------------------------------
cov_six.dat
  design toggle points : 48
  never toggled        : 5
  design line points   : 0
  the ones that never moved:
    ripple4.sv:3  b[2]:1->0
    ripple4.sv:4  cin:0->1
    ripple4.sv:4  cin:1->0
    ripple4.sv:8  c[0]:0->1
    ripple4.sv:8  c[0]:1->0

        // 4-bit ripple-carry adder built from four full adders.
        module ripple4 (
%000002     input  logic [3:0] a, b,
%000000     input  logic       cin,
%000002     output logic [3:0] sum,
%000001     output logic       cout
        );
%000002     logic [4:0] c;
            assign c[0] = cin;

------------------------------------------------------------------
 all 512
------------------------------------------------------------------
cov_all.dat
  design toggle points : 48
  never toggled        : 1
  design line points   : 0
  the ones that never moved:
    ripple4.sv:3  a[3]:1->0

==================================================================
 Coverage did not say whether the adder is right.  It said which
 parts of it your stimulus never moved.  Different question.
==================================================================
```

Note that this run used `../src/ripple4.sv` — the **correct** adder. There is no bug here at
all. Coverage is not looking for one, and that is the first thing to understand about it.

## What it just told you

`%000000` on the `cin` line.

`verilator_coverage --annotate` rewrites your source with a count in the left margin and a
flag character for anything it considers under-covered — `%` when a point falls below
`--annotate-min` (10 by default). You do not need the full legend; you need the two facts on
that one line. The flag is `%`, and the count is `000000`.

The explicit list above it says the same thing without ambiguity: of the forty-eight toggle
points in this design, five never fired, and two of them are `cin:0->1` and `cin:1->0`. **The
carry-in never moved, in either direction, in the entire run** — and the tool wrote that on
the exact line of source where it lives.

It did that without knowing what an adder is, without a reference model, without an
assertion, and without anyone telling it that `cin` was the interesting input. It asked one
mechanical question of every bit in the design — *did this go 0→1, and did it go 1→0?* — and
five of the answers were no.

That is the whole value proposition. **Coverage does not know what is correct. It knows what
you never touched, and "what you never touched" is where bugs are.**

The other three cold points are the same finding wearing different hats: `c[0]` is the wire
`cin` is assigned to, so of course it never moved either. `b[2]:1->0` is real but incidental
— none of the six cases happens to lower that particular bit.

## Three traps, all visible in that one output

### 1. `design line points : 0`

Line coverage — the metric almost everybody means when they say "coverage", and the one your
software friends live by — found **zero** points inside `ripple4.sv` and `fulladder.sv`. Not
zero *covered*. Zero *points*. There is nothing there to count: the design is continuous
assignments, and a continuous assignment is not a statement that executes.

So a report saying **"100 % line coverage"** on this design would be perfectly true and
completely empty. It would also be true of the six-case run and the exhaustive run equally,
which means it cannot distinguish them, which means it is worth nothing here.

> **Name the metric, or the number means nothing.** "We have 92 % coverage" is not a
> sentence. "We have 92 % *statement* coverage and we have never measured functional
> coverage" is.

### 2. The stimulus files check nothing at all

Open [`cov_six.sv`](https://github.com/uoftasic/dd104/blob/main/labs/lab-01-the-adder-you-already-trust/coverage/cov_six.sv).
There is not one assertion in it. It drives six values and prints them, and that is the whole
file.

It scores exactly what a fully-checking version would score. **Coverage instruments the
design, so it can only ever measure what your stimulus reached — it has no way to know
whether you looked at the answer.** A testbench that drives every input, exercises every
line, toggles every bit, and asserts nothing is 100 % covered and 0 % useful. That
combination is not hypothetical; it is what a large, old, unmaintained regression suite drifts
into.

Which gives you the pairing to hold on to:

| | asserts nothing | asserts properly |
|---|---|---|
| **poor coverage** | worthless, and it looks it | worthless, and it looks fine |
| **good coverage** | **worthless, and it looks excellent** | the only useful square |

The dangerous cell is the bottom-left, because it is the one with a good number on it.

### 3. Even the exhaustive run has a hole

Look at the second block. All 512 vectors, and **one point still never moved**: `a[3]:1->0`.

Nothing is untested. Every input combination was applied. What happened is that the sweep
ends with `a = 15` and then stops, so the top bit of `a` goes up several times and never comes
back down. **Toggle coverage counts transitions, not values**, and the loop order is part of
your stimulus.

There is a second, sharper version of this in the same package. `cov_all.sv` puts `cin` in the
*innermost* loop on purpose. Write the same sweep with `cin` outermost — 256 vectors at
`cin = 0`, then 256 at `cin = 1` — and you visit every value of `cin` while toggling it
exactly once, so `cin:1->0` stays cold in a test that is genuinely exhaustive.

This is the lesson that stops you treating coverage as a scoreboard:

> **A coverage hole is a question, not a verdict.** Uncovered does not mean untested, and
> covered certainly does not mean correct. Go and find out which one you are looking at.

Some holes are real gaps (`cin` in the six-case run — go fix your stimulus). Some are
artefacts of how the metric is defined (`a[3]:1->0` — write it down and move on). Some are
**unreachable by construction**, and those are the most valuable of all: a point your design
genuinely cannot reach is either dead logic you should delete, or a piece of your
understanding that is wrong. Chasing a number would have you paper over all three
identically.

## The kind of coverage that actually helps on a processor

Toggle coverage on a nine-line adder is a good teacher because you can hold the whole thing
in your head. On SimProc it is nearly useless: a processor running almost any program will
toggle nearly every bit, and you will sit at 99 % with `SUB` backwards.

What you need there is **functional coverage** — coverage of things you named yourself,
because they are meaningful to the design's *specification* rather than its wiring. You write
the list. On SimProc it starts like this:

| the question | why it is on the list |
|---|---|
| have I executed every opcode? | eleven exist; three encodings are unimplemented on purpose |
| have I executed `SUB` with **two different** operands? | `SUB rX, rX` is symmetric and hides an operand swap |
| have I executed `NAND` with two different operands? | `NAND rX, rX` is how you write NOT — the one case where NAND and NOR agree |
| have I used **all four** shift amounts, in both directions? | shifting by 1 is what everybody writes |
| have I taken a **backward** branch? | forward displacements are correct under one sign-extension bug and one only |
| have I taken **and** not-taken every branch? | a branch never taken has never been tested |
| have I run two branches off **one** compare? | flags are supposed to survive a branch |
| have I checked a `done` pulse per retired instruction? | two bugs disturb nothing else |
| have I run the UART at more than one baud rate? | one bug is invisible at the default |

Every line in that table is a question about stimulus that you could answer today, with a
`for` loop and a set. None of them requires a tool. **Functional coverage is a list you
maintain, and the list is the engineering** — the counting is clerical.

And you will notice something about that table if you read it twice: it is not organised
around the design's structure at all. It is organised around **the ways an operation can be
symmetric, or default, or one-sided** — the places where a wrong implementation and a right
one agree. That is where the thirteen SimProc bugs live, and it is not an accident:
[Where bugs hide](guide/where-bugs-hide.md) is the taxonomy, and every entry in it is a hole this
kind of list is designed to notice.

## The reflex

> **Never quote a coverage number without naming the metric and the assertion behind it.**
> And when you find a hole, do not close it — *ask it*. "Why did nothing ever set `cin`?" is
> the question that finds the bug. "How do I get this to 100 %?" is the question that hides
> it.

## Where this goes

You now have the four ideas the rest of DD104 runs on:

1. A green tick is a claim exactly as large as the stimulus behind it.
2. A testbench drives, observes and decides — and it is only a testbench once you have seen
   it fail.
3. If you can walk the input space, walk it; when you cannot, the shape of a failure still
   tells you where to look.
4. Coverage asks where you have not been. It never tells you whether you were right.

Next: [Your first cocotb test](guide/your-first-cocotb-test.md), where you stop borrowing a
harness and start writing one — and then [Lab 01](labs/lab-01-the-adder-you-already-trust.md), which
is four lines of work and the first `VERDICT: PASS` in this course.
