# The golden model

This page answers: *the input space is too big to walk. What do I compare against instead?*

In [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) you drove all 393,216 legal
vectors through SimProc's ALU in about twenty seconds, and afterwards there was no unexplored
corner left for a bug. That is the best position verification ever puts you in, and you should
take it whenever a block is small enough.

Now count the processor: [554 bits of architectural state](guide/simproc-in-one-page.md), and a
program is 64 bytes, so the space of programs alone is $256^{64}$. Exhaustive testing is not
just impractical here; it is out of the question.

So you stop checking every input and start checking every instruction, against a second opinion.

## What a golden model is

A **golden model**, or reference model, is a second implementation of the same specification,
written in a language where you can see what it does. You run the design and the model on the
same stimulus and compare them after every step. When they disagree, one of them is wrong.

DD104's is [`labs/common/golden.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/golden.py):
about 120 lines of plain Python, no imports, no simulator. You ran it on its own in
[Lab 02, Part 4](labs/lab-02-the-only-test-this-chip-has-overview.md#part-4-the-golden-model-on-its-own):

```
16 instructions in memory, 28 executed, 109 clock cycles
registers: r0=32 r1=15 r2=1 r3=32
mem[0x20] = 15   (all 28 instructions executed)
```

That is a whole SimProc program running with no Verilog anywhere. It takes no measurable time, you
can read it, and you can put a `print` in it.

The interface is deliberately small:

```python
def snapshot(self):
    """(regs, pc, N, Z) — the same shape `SimProc.snapshot()` returns, so
    the two can be compared with `==` and nothing else."""
    return (tuple(self.regs), self.pc, self.n, self.z)
```

Both sides return the same tuple, so the comparison is `==`. There is no field-by-field checking
and no list of things to remember to look at, and that is why the model checks the registers you
were not thinking about.

> Write the model from the ISA, not from the Verilog. A model written by reading the RTL agrees
> with the design about everything, including its bugs. It passes forever and proves nothing.
> This is the most common way a verification effort wastes six months, and it is easy to do by
> accident, so it is worth writing at the top of the file.
>
> `golden.py` is written from [the instruction set](reference/simproc-instruction-set.md). Where
> the ISA was ambiguous, somebody had to decide; see the end of this page.

## Using it in four lines

```python
await sp.load(prog)
model = Golden(prog + [PARK])
steps, problem = await trace(sp, len(prog), model=model)
assert problem is None, f"{problem}\n\n{listing(prog)}"
```

`trace()` single-steps the real design, steps the model alongside it, and compares the full
snapshot after every instruction. Four lines check all four registers, the PC and both flags,
twenty-nine times over, including everything you did not think to check.

When it passes it says so and nothing more:

```
29 instructions, every register / PC / flag / byte of memory agreed with golden.py
```

When it fails, you get this. It is `test_example.t06` on the core whose `SUB` computes `B - A`:

```
AssertionError: instruction 19, at address 19 (0x66 = SUB   r1, r2), left the machine in a different state:
        model: r=(48, 195, 29, 48) PC=20 N=1 Z=0
          DUT: r=(48, 61, 29, 48) PC=20 N=0 Z=0

the program:
  00: 06   SUB   r0, r0
  01: C7   ORI   24
  ...
  12: 64   ADD   r1, r2
  13: 66   SUB   r1, r2
```

Every part of that message came for free:

- which instruction: the nineteenth, not "somewhere in the program";
- where it lives: address 19;
- what it was: `0x66`, disassembled to `SUB r1, r2`, so you are not decoding hex;
- the whole machine on both sides, and $195 + 61 = 256$, the signature of a negated result, which
  tells you the operands went in backwards before you open anything;
- the flag too: `N=1` against `N=0`, caught by the same comparison, with no extra assertion.

## What a model gives you that a hand-written expectation can't

Directed assertions are not wrong. `assert sp.reg(1) == 5` is fine and you should write plenty of
them. But a model gives you three things a hand-written expected value cannot.

### 1. It checks the registers you were not looking at

A directed test asserts on the register the instruction names. It says nothing about the other
three, and "the answer is correct" and "nothing else moved" are different claims.

On the same broken core, the directed test in the same file reports:

```
AssertionError: r1 is 199, expected 247.
```

That is true and useful, and it points at `r1`, where the answer was supposed to go. One bug in
the catalogue writes the right value into the wrong register, and against that one a directed
assertion on the destination reports a symptom in a register that was never the problem. The
model comparison notices immediately, because a bystander register that changed fails `==` just as
loudly as a destination register that did not.

> Check the state that should not have changed. It costs nothing when you compare snapshots, and
> it is almost impossible to remember when you don't.

### 2. It names the first disagreement, not the last

Once a processor's state has diverged, everything downstream is wrong too. A test that checks
state at the end of a program hands you the symptom (a wrong byte, forty instructions later, in a
register nobody cared about) and leaves you to walk it back by hand.

`trace()` stops at instruction 19 of 29, while the machine is one instruction away from correct.
Everything before it is known good, so you start debugging at instruction 19 instead of walking
back from the end.

### 3. It lets you run stimulus you can't work out by hand

You cannot write down the expected final register file for thirty random instructions. The model
can. That opens up a whole category of test, and its limits are the subject of
[Directed and random tests](guide/directed-random-and-the-gap.md).

## What a model cannot see

Write this down next to the model rather than discovering it at midnight. A model only checks what
it models. `golden.py` models architectural state: four registers, the PC, two flags, 64 bytes of
RAM. It has no concept of:

| | |
|---|---|
| `done` | The one-cycle retire pulse |
| `halt` | The pin that says the core is in `IDLE` |
| Cycle counts | It publishes them, but nothing compares them by default |
| The UART | Baud rate, framing, the debug protocol |
| `X` | A model has no undefined value |

A core that computes every answer correctly and gets its handshake wrong passes a model comparison,
because those are different kinds of property. Two bugs in the catalogue are exactly that, and
they are [Lab 05](labs/lab-05-every-answer-is-right-overview.md). More vectors don't help; a
different kind of check does.

## When the model is the one that's wrong

Everyone gets this wrong the first time, so here is a real example from this repository.

The unimplemented opcodes take four cycles, and `golden.py` used to say three. Opcodes `0xC`,
`0xD` and `0xE` are easy to describe: the PC advances, nothing else changes, and `done` never
pulses. The model said they cost three cycles, like every branch and `STORE`, which is what the RTL
looks like it should do. Measured on four filler bytes:

| | |
|---|---|
| Clock cycles | 16: four each |
| `done` pulses | 0 |
| Cycles with `halt` high | 4 |

They match no clause in `CYCLE_3`, so the FSM takes its default exit to `IDLE`, spends a cycle
there, and is sent back to `CYCLE_1` by `run`, which is still asserted. That is four cycles, with
one cycle of `halt` in the middle of a running program.

Three lessons from that:

1. The model was the wrong one. It is a second implementation written by a person, not an oracle.
   "The DUT disagrees with the model" is a statement about a pair, and the next question is always
   which one is wrong. Answer it from the specification, or, when the specification is silent, by
   measuring the hardware and writing down what it does.
2. The model was right about what it was mostly used for. Its architectural state was correct all
   along; the number it got wrong was a timing figure it also happened to publish. A model can be
   trustworthy in one dimension and wrong in another, so know exactly which dimensions yours covers.
3. It was found by measuring a case nobody tests. `0x0C` is filler, and no program runs it on
   purpose. It is exactly the kind of "obviously nothing happens here" behaviour that never gets an
   assertion, which is the subject of [Where bugs hide](guide/where-bugs-hide.md), applied to the
   testbench instead of the design.

### When the specification has not decided

SimProc's `ORI` has no register field (all five spare bits are the immediate), so the register it
accumulates into is implicit in the hardware. The RTL carried a comment for a year saying it might
be the other register.

Four variants were built and simulated to settle it. `r0` and `r1` turn out to be exactly
isomorphic in this machine: a register index never leaves the instruction word, `r0` is not
hardwired to zero, and no flag, addressing mode, reset value or debug command treats either one
specially. The same program with `r0` and `r1` swapped produces the same memory and mirrored
registers.

The hardware cannot break the tie, so no measurement can. Somebody has to decide, write it down,
and make the model match, and then the decision becomes part of the specification rather than an
accident of the RTL. DD104 specifies `r0`.

What is not a matter of taste is that the two lines implementing the decision must change
together. Applying it to only one gives "OR the immediate into one register, write the answer to a
different one", an instruction nobody specified. That is one of the two hardest bugs in the
catalogue, because after a reset both candidate registers hold zero and the first `ORI` of any
program looks correct.

## When the model and the design disagree

1. Read the failing instruction, not the final state. `trace()` has already told you which one.
2. Decide which side is wrong from the specification, not from whichever one you wrote.
3. If the specification is silent, measure the hardware, write down what it does, and say in the
   model that this records behaviour rather than a requirement.
4. If the specification is ambiguous rather than silent, that ambiguity is a hazard in itself.
   Decide it, document it, and check that everything implementing the decision changed together.
5. Then ask what a model comparison could not have seen on this design, and write that test
   separately.

> Compare snapshots, not values. If both sides can produce the same tuple, compare the tuples:
> it is less code than a hand-written expectation, it checks state you were not thinking about,
> and it fails with a location instead of a symptom.
>
> Keep the model's blind spots written down next to it. A model that everyone trusts and nobody
> has bounded is worse than no model, because it turns "we did not check that" into "it passed".

## Check yourself

1. A `trace()` failure says the model has `r2 = 10` and the DUT has `r2 = 10`, but `r3` differs.
   The instruction was `ADD r2, r1`. What kind of bug do you suspect?
2. Name two things a SimProc core can get wrong that `golden.py` will never notice.

Next: [Where bugs hide](guide/where-bugs-hide.md).
