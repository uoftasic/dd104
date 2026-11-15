# The lazy testbench

This page answers: *how careful do I actually have to be? My tests look reasonable.*

They probably do, and that is the problem. The cheapest place to see it is a circuit you already
understand completely.

You wrote a 4-bit ripple-carry adder in DD102 and measured it in DD103. It is nine lines and you
know exactly what it does. It is also the last design under test in this course you will be able
to say that about. It ships as
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

The Lab 01 package also ships `broken/ripple4.sv`, which is that file with one line changed:

```systemverilog
    assign c[0] = 1'b0;              // <-- was: assign c[0] = cin;
```

The carry-in never reaches the bottom slice. From Lab 04 on you will be asked not to read the
broken designs, but you may read this one: it says so at the top, and Lab 01 is not a bug hunt. The question here is not where the bug is but what kind of
testbench notices it.

It is a real bug of a real kind. A port tied off during bring-up and never reconnected is one of
the most common defects in industrial RTL, and it survives review because the line looks
deliberate.

## The shipped testbench

`test_adder.py` ships with two tests, and the first was written by someone thinking about
addition:

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
wrap. That is a defensible list, and it is what most people produce when asked for "a few good
test cases".

The second test is the upgrade you would reach for next:

```python
@cocotb.test()
async def t02_every_a_and_every_b(dut):
    """Every value of a against every value of b.  256 vectors."""
```

Every value of `a` against every value of `b`: the complete cross product, sixteen by sixteen.
Asked whether that testbench was thorough, you would say yes, and you would probably call it
exhaustive. That would be wrong in a way worth remembering.

(Excerpts only. The complete file is
[`labs/lab-01-the-adder-you-already-trust/test_adder.py`](https://github.com/uoftasic/dd104/blob/main/labs/lab-01-the-adder-you-already-trust/test_adder.py),
and it ships working.)

## What the two tests report

Against the good adder both tests pass, and the log says how much they covered:

```
   262.00ns INFO     cocotb.ripple4                     checked 256 of the 512 possible input vectors
```

Against `broken/`, they pass too. `make check` runs the testbench on both adders and passes only
if the testbench passes the good one (`ok`) and fails the broken one (`caught`); a testbench that
passes both gets `MISSED` and `VERDICT: FAIL`. This is what it prints, which you'll see for
yourself in [Lab 01, Part 2](../labs/lab-01-the-adder-you-already-trust-overview.md#part-2-run-the-shipped-testbench):

```
========================================================================
 CHECK   testbench: test_adder      simulator: icarus
========================================================================
      ok  src/  the good adder           2 tests, all passed              1.9s
  MISSED  broken/  carry-in dropped      2 tests, all passed              1.9s
------------------------------------------------------------------------
 VERDICT: FAIL -- your testbench passes the broken adder too.
   broken/ripple4.sv drops the carry-in on the way into slice 0, so
   every vector with cin = 1 comes out one too small. Every vector
   with cin = 0 is perfectly correct.
   Look at the third column of your stimulus. If cin is 0 in every
   row, this bug is not reachable by anything you drove -- and you
   drove 262 of the 512 vectors this module has.
========================================================================
```

`MISSED` means every vector driven was green on an adder that is broken. The verdict counts 262
vectors driven: 6 from `t01` and 256 from `t02`, with the six repeated inside the 256.

## What "exhaustive" covers

Look again at the line the run printed: `checked 256 of the 512 possible input vectors`. The
testbench says it itself. Four bits of `a`, four bits of `b` and one bit of `cin` make
$4 + 4 + 1 = 9$ bits of input, and $2^9 = 512$. The cross product of `a` and `b` is complete, and
it is half the design.

Careful people do this too. It happens whenever you list the inputs you were thinking about.
The author of `t02` was thinking "an adder takes two numbers", which is what an adder is in every
context except testing it. `cin` is not a number. It is plumbing: the port you use when you chain
adders, invisible unless you are chaining.

> If you loop over your inputs, you have been thorough over the input list you wrote down. That
> list came from the same mental model as the design, with the same blind spots. "Exhaustive" is
> not a property of a testbench. It is a claim about a space, and the claim is only as good as
> the space.

Add `cin` to the sweep and collect the failures instead of stopping at the first, and the count
appears. (The reference solution also renames `t02` to `t02_exhaustive`.) Now `t02` fails on the
broken adder, so the testbench can tell the two apart and the verdict is PASS:

```
  caught  broken/  carry-in dropped      2 tests, 1 FAILED                1.9s
        t02_exhaustive
            AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1=1 (want
------------------------------------------------------------------------
 VERDICT: PASS
   512 vectors on the good adder, all correct.
   512 vectors on the broken one, and the failure is a count, not
   an anecdote:
       t02_exhaustive: AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+
   That is a test worth committing: it will still catch this bug in
   a year, on a rewrite, done by somebody who has never met you.
```

Making that change is [Lab 01](../labs/lab-01-the-adder-you-already-trust-overview.md), and it is
four lines.

## Reading the count

The fixed test does not stop at the first disagreement. It walks all 512 vectors, counts every
wrong one and reports the total, and the total is exactly half.

Half is not a plausible number for a random mistake. A scrambled carry chain or a bad XOR would
give you some awkward fraction. Exactly 256 out of 512 says the failures track a signal that is
high exactly half the time, and in a space of $16 \times 16 \times 2$ only one input has that
shape: `cin`.

The reference solution's failure message lists the first few wrong vectors and then says so too,
because it was written to:

```
Every wrong vector above has cin=1 and every one is short by exactly 1.
```

None wrong with `cin = 0`, every one wrong with `cin = 1`, each short by one. That is a
diagnosis, and you have it before reading a line of RTL.

### Shapes worth recognising

| The count | What it usually means |
|---|---|
| Exactly half | The failure tracks one input that is high half the time |
| Exactly one quarter | Two such inputs, both high together |
| Exactly one | An edge: the maximum, the wrap, a single decoded value |
| All but a handful | The operation is fundamentally wrong; the survivors are cases where right and wrong happen to agree |
| An odd, un-round number | Probably a real functional bug rather than a wiring mistake; start reading |

You will meet the fourth row soon. One of the SimProc bugs swaps the operands of `SUB`, and
against all 65,536 `(A, B)` pairs it gets 65,024 wrong. The 512 survivors are not random: `A - B`
and `B - A` agree exactly when `A == B` (256 pairs) or when the difference is 128 (256 more). And
`SUB rX, rX`, the usual way to clear a register, is always among those 512. The most common use
of the instruction is the one use that hides the bug.

## When you can't walk everything

Nine input bits is 512 vectors: 512 ns of simulated time and about a hundredth of a
second of real time. When you are in that situation, take it.

> If the input space is small enough to walk, walk it. Do not hand-pick cases for a
> combinational block with fewer than about $2^{20}$ input combinations. You will not choose
> better than a `for` loop that tries everything.

SimProc's ALU is still small enough: 6 operations × 256 × 256 = 393,216 vectors. That is
[Lab 03](../labs/lab-03-three-blocks-before-the-processor-overview.md), where three bugs fall out by
brute force.

The processor around it is not. Four registers, 64 bytes of memory, a program counter, two flags
and a UART make a state space far too big to walk, and it has sequences, so enumerating states
would not be enough either. From [Lab 04](../labs/lab-04-your-first-bug-hunt-overview.md) on, you
need the two things that replace exhaustive testing:

- a reference model to compare against instruction by instruction:
  [The golden model](../guide/the-golden-model.md);
- a way to ask what your stimulus actually reached, which is not the same as counting how many
  tests you wrote: [Coverage as a question](../guide/coverage-is-a-question.md), next.

## Two habits

> Sweep the input space instead of sampling it, and count the space first. Add up the input bits,
> raise two to that power, and make your testbench print how many of them it checked. `256 of
> the 512 possible input vectors` is a sentence that catches this bug on its own.

> Read the count before you read the values. Exactly half, exactly one, exactly $2^k$: the shape
> of a failure names the signal it tracks, and it does it faster than a waveform will.

## Check yourself

1. A module has an 8-bit input, a 3-bit select and an enable. How many input vectors does it
   have?
2. A sweep of that module reports exactly half of its vectors wrong. What kind of signal do you
   look for first?

Next: [Coverage as a question](../guide/coverage-is-a-question.md).
