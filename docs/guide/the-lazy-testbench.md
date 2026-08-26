# The lazy testbench

**Question this page answers:** *How careful do I actually have to be? My tests look
reasonable.*

They probably do. That is the problem, and the cheapest way to see it is on a circuit you
already understand completely.

You wrote a 4-bit ripple-carry adder in DD102 and you measured it in DD103. It is nine lines.
You know exactly what it does, and this is the last time in this course you will be able to
say that about the design under test. It ships as
[`labs/lab-01-the-adder-you-already-trust/src/ripple4.sv`](https://github.com/uoftasic/dd104/blob/main/labs/lab-01-the-adder-you-already-trust/src/ripple4.sv):

```systemverilog
module ripple4 (
    input  logic [3:0] a, b,
    input  logic       cin,
    output logic [3:0] sum,
    output logic       cout
);
    logic [4:0] c;
    assign c[0] = cin;
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : slice
            fulladder fa (.a(a[i]), .b(b[i]), .cin(c[i]),
                          .sum(sum[i]), .cout(c[i+1]));
        end
    endgenerate
    assign cout = c[4];
endmodule
```

The package also ships `broken/ripple4.sv`, which is that file with one line changed:

```systemverilog
    assign c[0] = 1'b0;              // <-- was: assign c[0] = cin;
```

The carry-in never reaches the bottom slice. **You are allowed to read that file** — it says
so at the top, and nothing on this page is a hunt. The question here is not *where is the
bug*, it is *what kind of testbench notices*.

That single line is a real bug of a real kind. A port tied off during bring-up and never
reconnected is one of the most common defects in industrial RTL, and it survives review
precisely because the line looks deliberate.

## The testbench a reasonable person writes

Not a careless one. `test_adder.py` ships with two tests already written, and the first one
was written by someone thinking about addition:

```python
    cases = [
        # a,  b,  cin
        (0,  0,  0),
        (1,  1,  0),
        (2,  3,  0),
        (7,  8,  0),
        (15, 0,  0),
        (15, 1,  0),
    ]
```

Zero, one, a middling pair, a carry that walks between slices, the top of the range, and the
wrap. That is a defensible list, and it is what most people produce when asked for "a few
good test cases".

The second test is the upgrade you would reach for next, and this is the interesting one:

```python
@cocotb.test()
async def t02_every_a_and_every_b(dut):
    """Every value of a against every value of b.  256 vectors."""
```

**Every value of `a`, against every value of `b`.** Not a sample — the complete cross
product. Sixteen times sixteen. If you were asked whether that testbench was thorough, you
would say yes, and you would use the word *exhaustive*, and you would be wrong in a way
that is going to be worth remembering.

Excerpt only; the complete file is
[`labs/lab-01-the-adder-you-already-trust/test_adder.py`](https://github.com/uoftasic/dd104/blob/main/labs/lab-01-the-adder-you-already-trust/test_adder.py),
and it ships working.

## Predict first

Before you run anything, commit to two answers.

1. Those two tests, against `broken/ripple4.sv`: **do they catch it?**
2. If you ran *every* input the adder has, **how many would be wrong?** A number, not a
   feeling.

Most people say yes to the first. Write yours down anyway — being wrong on purpose is the
cheapest lesson in this course, and it only works if you committed.

## Run it

```bash
cd labs/lab-01-the-adder-you-already-trust
make
```

About four and a half seconds. The first half is green:

```
============================================================
 SIM   test_adder   against src/  (the good adder)
============================================================
     6.00ns INFO     cocotb.ripple4                     6 hand-picked vectors, all correct
   262.00ns INFO     cocotb.ripple4                     checked 256 of the 512 possible input vectors
   ** test_adder.t01_the_obvious_six       PASS           6.00           0.00       8762.47  **
   ** test_adder.t02_every_a_and_every_b   PASS         256.00           0.01      21111.30  **
   ** TESTS=2 PASS=2 FAIL=0 SKIP=0                      262.00           0.01      18538.90  **

   Green. That is half a verdict. 'make check' is the other half.
```

And then the other half:

```
========================================================================
 CHECK   testbench: test_adder      simulator: icarus
========================================================================
      ok  src/  the good adder           2 tests, all passed          1.2s
  MISSED  broken/  carry-in dropped      2 tests, all passed          1.2s
------------------------------------------------------------------------
 VERDICT: FAIL -- your testbench passes the broken adder too.
   broken/ripple4.sv drops the carry-in on the way into slice 0, so
   every vector with cin = 1 comes out one too small. Every vector
   with cin = 0 is perfectly correct.
   Look at the third column of your stimulus. If cin is 0 in every
   row, this bug is not reachable by anything you drove.
========================================================================

  The verdict above is FAIL, so this target exits non-zero and make
  prints an error line under this one. That is the verdict talking,
  not a broken Makefile.
make: *** [Makefile:49: check] Error 1
```

> **`make: *** Error 1` here is correct.** The verdict exits non-zero on purpose so it is
> usable from a script or a CI job without anyone having to grep the text, and `make` reports
> that. The package tells you so in the two lines above it. Every DD104 lab does this.

**`MISSED`.** Two hundred and sixty-two nanoseconds of simulation, 262 vectors, every one
green, on an adder that is broken.

## "Exhaustive" is a claim about a space you named

Look again at the line the run printed:

```
checked 256 of the 512 possible input vectors
```

The testbench itself says it. Four bits of `a`, four bits of `b`, **and one bit of `cin`** is
$4 + 4 + 1 = 9$ bits of input. $2^9 = 512$. The cross product of `a` and `b` is complete and
it is *half the design*.

This is not carelessness. It is what happens when you enumerate the inputs you were thinking
about. The person who wrote `t02` was thinking "an adder takes two numbers" — which is what
an adder *is*, in every context except the one where you are testing it. `cin` is not a
number. `cin` is plumbing: the port you use when you chain two adders together, invisible
unless you are chaining.

> **The prior this page is overwriting:** you believe that if you loop over your inputs, you
> have been thorough. What you have actually been is thorough *over the input list you
> wrote down*, and that list came from the same mental model that has the same blind spots as
> the one that wrote the design. **"Exhaustive" is not a property of a testbench. It is a
> claim about a space, and the claim is only as good as the space.**

Fix the space — add `cin` to the sweep — and the count arrives:

```
      ok  src/  the good adder           2 tests, all passed          2.1s
  caught  broken/  carry-in dropped      2 tests, 1 FAILED            1.2s
        t02_exhaustive
            AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1=1 (want
------------------------------------------------------------------------
 VERDICT: PASS
   Your testbench passes the good adder and catches the broken one.
   That is a test worth committing: it will still catch this bug in
   a year, on a rewrite, done by somebody who has never met you.
```

Doing that is [Lab 01](labs/lab-01-the-adder-you-already-trust-overview.md), and it is four lines.

## The count is the diagnostic

This is the part to take with you.

The fixed test does not stop at the first disagreement. It walks all 512, counts every one,
and reports the total — and the total is **exactly half**.

Half is not a plausible number for a random mistake. A genuinely scrambled carry chain, or a
bad XOR, would give you some awkward fraction. Getting exactly 256 out of 512 says the
failures track a signal that is high exactly half the time, and in a space of
$16 \times 16 \times 2$ there is only one input with that shape: **`cin`**.

And the failure message says it out loud, because it was written to:

```
Every wrong vector above has cin=1 and every one is short by exactly 1.
```

Zero wrong with `cin = 0`. Every single one wrong with `cin = 1`, each short by one. That is
not a bug report, it is a diagnosis, and you have it **before reading a line of RTL**.

### Shapes worth recognising

| the count | what it usually means |
|---|---|
| **exactly half** | the failure tracks one input that is high half the time |
| **exactly one quarter** | two inputs, both wrong together |
| **exactly one** | an edge — the maximum, the wrap, a single decoded value |
| **all but a handful** | the operation is fundamentally wrong; the survivors are the cases where right and wrong happen to agree |
| **an odd, un-round number** | probably a real functional bug rather than a wiring mistake — start reading |

That fourth row is worth holding on to, because you meet it almost immediately. One of the
bugs waiting for you in SimProc swaps the operands of `SUB`, and against all 65,536 `(A, B)`
pairs it gets **65,024 wrong**. The 512 survivors are not random either: `A - B` and `B - A`
agree exactly when `A == B` (256 pairs) or when the difference is 128 (256 more). And `SUB
rX, rX` — the standard idiom for clearing a register — is *always* in that surviving 512.
**The most common way to use the instruction is the one way that hides the bug.**

## But you cannot walk everything

Nine lines and two operands is 512 vectors: 512 ns of simulated time, and about a hundredth
of a second of real time. That is the happy case, and when you are in it you should take it.

> **If the input space is small enough to walk, walk it.** Do not hand-pick cases for a
> combinational block with fewer than about $2^{20}$ input combinations. You are not better at
> choosing than a `for` loop is at not choosing.

SimProc's ALU is still in that world: 6 operations × 256 × 256 = **393,216 vectors**, which
is [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md), where three bugs fall out
by brute force.

The processor around it is not. Four registers, 64 bytes of memory, a program counter, two
flags and a UART — the state space is astronomically beyond walking, and it has *sequences*,
so enumerating states would not be enough either. From
[Lab 04](labs/lab-04-your-first-bug-hunt-overview.md) onward, exhaustive stops being an option and
you need the two things that replace it:

- **a reference model** to compare against instruction by instruction — [The golden
  model](guide/the-golden-model.md);
- **a way to ask what your stimulus actually reached**, which is not the same as counting how
  many tests you wrote — [Coverage as a question](guide/coverage-is-a-question.md), next.

## The reflex

Two, and they are both one line.

> **Sweep the field, do not sample it — and count the field first.** Add up the input bits,
> raise two to that power, and make your testbench print how many of them it checked. `256 of
> the 512 possible input vectors` is a sentence that catches this bug on its own.

> **Read the count before you read the values.** Exactly half, exactly one, exactly $2^k$ —
> the shape of a failure names the signal it tracks, and it does it faster than the waveform
> will.

Next: [Coverage as a question, not a metric](guide/coverage-is-a-question.md) — where a real
coverage tool is pointed at these same two stimulus sets and finds the blind spot without
being told anything about adders.
