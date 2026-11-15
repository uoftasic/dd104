# Coverage as a question

This page answers: *how do I know when I have tested enough?*

You don't, and no number will tell you. Everything useful about coverage follows from accepting
that rather than looking for a way around it.

Treat coverage as a tool that generates questions about your stimulus rather than as a score to
raise. Each question is worth as much as the answer you give it, and the percentage attached is a
side effect.

The quickest way to see this is to point a real coverage tool at the two stimulus sets from
[The lazy testbench](../guide/the-lazy-testbench.md) and watch it find the blind spot without being
told anything about adders.

## What the coverage run prints

The Lab 01 package has a `coverage/` add-on that runs Verilator's toggle coverage on the six
hand-picked cases and on all 512 vectors. Icarus has no coverage instrumentation, so this is the
one place early in the course where only the stricter simulator can answer. You'll run it in
[Lab 01, Part 5](../labs/lab-01-the-adder-you-already-trust-overview.md#part-5-ask-a-coverage-tool),
and this is what it prints:

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

Both runs use `../src/ripple4.sv`, the correct adder. There is no bug here at all. Coverage is not
looking for one, and that is the first thing to understand about it.

## What it found

Look at `%000000` on the `cin` line.

`verilator_coverage --annotate` rewrites your source with a count in the left margin and a flag
for anything it considers under-covered: `%` when a point falls below `--annotate-min` (10 by
default). You don't need the full legend, only the two facts on that line: the flag is `%`, and
the count is `000000`.

The list above it says the same thing more plainly. Of the 48 toggle points in the design, five
never fired, and two of them are `cin:0->1` and `cin:1->0`. The carry-in never moved in either
direction during the whole run, and the tool reported it on the line of source where `cin` lives.

It did that without knowing what an adder is, without a reference model, without an assertion,
and without being told `cin` was interesting. It asked one mechanical question of every bit in
the design, *did this go 0→1, and did it go 1→0?*, and five of the answers were no.

That is the value of coverage. It does not know what is correct. It knows what you never touched,
and the places you never touched are where bugs survive.

The other three cold points follow from the first two or are incidental. `c[0]` is the wire `cin`
is assigned to, so it never moved either. `b[2]:1->0` is real but incidental: none of the six
cases happens to lower that bit.

## Three traps in that one output

### 1. `design line points : 0`

Line coverage is what most people mean by "coverage", and it is what software teams track. It
found zero points inside `ripple4.sv` and `fulladder.sv`: not zero covered, zero points. The
design is continuous assignments, and a continuous assignment is not a statement that executes,
so there is nothing to count.

A report saying "100 % line coverage" on this design would be true and empty. It would also be
true of the six-case run and the exhaustive run alike, so it cannot tell them apart.

> Name the metric, or the number means nothing. "We have 92 % coverage" is not a useful sentence.
> "We have 92 % statement coverage and have never measured functional coverage" is.

### 2. The stimulus files check nothing

Open [`cov_six.sv`](https://github.com/uoftasic/dd104/blob/main/labs/lab-01-the-adder-you-already-trust/coverage/cov_six.sv).
It has no assertions. It drives six values and prints them, and that is the whole file.

It scores exactly what a fully checking version would score. Coverage instruments the design, so
it can only measure what your stimulus reached; it cannot know whether you looked at the answer.
A testbench that drives every input, toggles every bit and asserts nothing is 100 % covered and
useless. That is not hypothetical: it is what a large, old, unmaintained regression suite tends to
drift into.

| | Asserts nothing | Asserts properly |
|---|---|---|
| Poor coverage | Useless, and it looks it | Useless, and it looks fine |
| Good coverage | Useless, and it looks excellent | The only useful combination |

The dangerous cell is bottom-left, because it is the one with a good number on it.

### 3. Even the exhaustive run has a hole

In the second block, all 512 vectors ran and one point still never moved: `a[3]:1->0`.

Nothing is untested; every input combination was applied. The sweep ends with `a = 15` and stops,
so the top bit of `a` goes up several times and never comes back down. Toggle coverage counts
transitions, not values, so loop order is part of your stimulus.

The same package has a sharper version of this. `cov_all.sv` puts `cin` in the innermost loop on
purpose. Write the same sweep with `cin` outermost, 256 vectors at `cin = 0` and then 256 at
`cin = 1`, and you visit every value of `cin` while toggling it only once, so `cin:1->0` stays cold
in a test that really is exhaustive.

> A coverage hole is a question, not a verdict. Uncovered does not mean untested, and covered
> does not mean correct. Find out which one you are looking at.

Some holes are real gaps: `cin` in the six-case run, so fix your stimulus. Some are artefacts of
how the metric is defined: `a[3]:1->0`, so note it and move on. Some are unreachable by
construction, and those are the most valuable: a point your design cannot reach is either dead
logic to delete or a part of your understanding that is wrong. Chasing a number would have you
paper over all three the same way.

## Functional coverage on a processor

Toggle coverage on a nine-line adder is a good teacher because you can hold the whole design in
your head. On SimProc it is nearly useless: almost any program toggles nearly every bit, and you
would sit at 99 % with `SUB` backwards.

What you need there is **functional coverage**: coverage of things you named yourself because
they matter to the design's specification rather than its wiring. You write the list. For SimProc
it starts like this:

| The question | Why it is on the list |
|---|---|
| Have I executed every opcode? | Eleven exist; three encodings are unimplemented on purpose |
| Have I executed `SUB` with two different operands? | `SUB rX, rX` is symmetric and hides an operand swap |
| Have I executed `NAND` with two different operands? | `NAND rX, rX` is how you write NOT, the one case where NAND and NOR agree |
| Have I used all four shift amounts, in both directions? | Shifting by 1 is what everybody writes |
| Have I taken a backward branch? | Forward displacements are correct under one sign-extension bug |
| Have I taken and not taken every branch? | A branch never taken has never been tested |
| Have I run two branches off one compare? | Flags are supposed to survive a branch |
| Have I checked for one `done` pulse per retired instruction? | Two bugs disturb nothing else |
| Have I run the UART at more than one baud rate? | One bug is invisible at the default |

You could answer each of those today with a `for` loop and a set, without any tool. Functional
coverage is a list you maintain. Writing the list is the engineering; counting is clerical.

Read the table again and you'll see it is organised around the ways an operation can be symmetric,
defaulted or one-sided, rather than around the design's structure. Those are the places where a
wrong implementation and a right one agree. That is where the thirteen SimProc bugs live.
[Where bugs hide](../guide/where-bugs-hide.md) is the full taxonomy, and every entry in it is a hole
this kind of list is designed to notice.

> Never quote a coverage number without naming the metric and the assertions behind it. When you
> find a hole, ask it a question instead of closing it. "Why did nothing ever set `cin`?" finds
> the bug. "How do I get this to 100 %?" hides it.

## Before Lab 01

You now have the four ideas the rest of DD104 builds on:

1. A green tick is a claim exactly as large as the stimulus behind it.
2. A testbench drives, observes and decides, and it is only a testbench once you have seen it
   fail.
3. If you can walk the input space, walk it. When you can't, the shape of a failure still tells
   you where to look.
4. Coverage asks where you have not been. It never tells you whether you were right.

## Check yourself

1. A colleague reports "100 % line coverage" on a design made entirely of `assign` statements.
   What has been measured?
2. Why can a testbench with no assertions score full toggle coverage?

Next: [Lab 01: The adder you already trust](../labs/lab-01-the-adder-you-already-trust-overview.md).
