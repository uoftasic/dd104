# The golden model

**Question this page answers:** *The input space is too big to walk. What do I compare against
instead?*

In [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) you drove **393,216
vectors** through SimProc's ALU — every legal input the module can be given — in about twenty
seconds, and afterwards there was no unexplored corner left for a bug to sit in. That is the
best position verification ever puts you in, and you should take it whenever a block is small
enough.

Now count the processor. [554 bits of architectural state](guide/simproc-in-one-page.md), and a
program is 64 bytes, so the space of programs alone is $256^{64}$. Exhaustive is not merely
impractical here; it is over.

So you stop trying to check *every input* and start checking *every instruction* — against a
second opinion.

## What a golden model is

A **golden model** (or reference model) is a second implementation of the same specification,
written in a language where you can see what it does. You run the design and the model on the
same stimulus and compare them after every step. When they disagree, one of them is wrong.

DD104's is
[`labs/common/golden.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/golden.py):
about 120 lines of plain Python, no imports, no simulator. Run it on its own:

```bash
cd labs/common
make model
```

```
16 instructions in memory, 28 executed, 109 clock cycles
registers: r0=32 r1=15 r2=1 r3=32
mem[0x20] = 15   (all 28 instructions executed)
```

That is a whole SimProc program executing with no Verilog anywhere in the process. It takes no
measurable time, and you can read it, and — most usefully — you can put a `print` in it.

The shape is deliberately small:

```python
def snapshot(self):
    """(regs, pc, N, Z) — the same shape `SimProc.snapshot()` returns, so
    the two can be compared with `==` and nothing else."""
    return (tuple(self.regs), self.pc, self.n, self.z)
```

**Both sides return the same tuple, so the comparison is `==`.** No field-by-field checking, no
list of things to remember to look at, nothing to forget. That is not a stylistic choice; it is
the reason the model checks the registers you were not thinking about.

> ### Write the model from the ISA, not from the Verilog
>
> If you write your reference model by reading the RTL, you have built something that agrees
> with the design about everything — including its bugs. It will pass, forever, and prove
> nothing. This is the single most common way a verification effort wastes six months, and it is
> so easy to do by accident that it is worth writing at the top of the file.
>
> `golden.py` is written from [the instruction set](reference/simproc-instruction-set.md). Where
> the ISA was genuinely ambiguous, somebody had to *decide* — see the bottom of this page.

## Using it: four lines

```python
await sp.load(prog)
model = Golden(prog + [PARK])
steps, problem = await trace(sp, len(prog), model=model)
assert problem is None, f"{problem}\n\n{listing(prog)}"
```

`trace()` single-steps the real design, steps the model alongside it, and compares the full
snapshot after **every instruction**. Four lines, and it checks all four registers, the PC and
both flags, twenty-nine times over — including everything you did not think to check.

When it passes it says so and nothing more:

```
29 instructions, every register / PC / flag / byte of memory agreed with golden.py
```

When it fails, this is what you get. This is `test_example.t06` on the core whose `SUB` computes
`B - A`:

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

Read what that message contains, because every part of it was free:

- **which instruction** — the nineteenth, not "somewhere in the program"
- **where it lives** — address 19
- **what it was** — `0x66`, disassembled to `SUB r1, r2`, so you are not decoding hex at 1 a.m.
- **the whole machine, both sides** — and $195 + 61 = 256$, which is the signature of a negated
  result and tells you the operands went in backwards before you have opened anything
- **the flag too** — `N=1` against `N=0`, caught in the same comparison as the value, with no
  extra assertion written by anyone

## Why this beats writing the expected value by hand

Directed assertions are not wrong. `assert sp.reg(1) == 5` is a fine thing to write and you
should write a lot of them. But a model gives you three things a hand-written expectation
structurally cannot.

### 1. It checks the registers you were not looking at

A directed test asserts on the register the instruction names. It says nothing about the other
three, and "the answer is correct" and "nothing else moved" are different claims.

On the same broken core, the directed test in the same file reports:

```
AssertionError: r1 is 199, expected 247.
```

True, useful, and it points at `r1` — which is where the answer was *supposed* to go. There
exists a bug in this catalogue that writes the right value into the wrong register, and against
that one a directed assertion on the destination register reports a symptom in a register that
was never the problem. The model comparison notices immediately, because a **bystander register
that changed** fails `==` exactly as loudly as a destination register that did not.

> **The habit this builds:** check the state that should *not* have changed. It costs nothing
> when you compare snapshots and it is nearly impossible to remember when you do not.

### 2. It names the *first* disagreement, not the last

Once a processor's state has diverged, everything downstream of the divergence is also wrong. A
test that checks state at the end of a program hands you the **symptom** — a wrong byte, forty
instructions later, in a register nobody was interested in — and you get to walk it backwards
by hand.

`trace()` stops at instruction 19 of 29, while the machine is still one instruction from
correct. Everything before it is known good. That is not a nicer error message; it is a
different amount of work.

### 3. It lets you run stimulus you cannot hand-compute

You cannot write down the expected final register file for thirty random instructions. The model
can. That unlocks a whole category of test — and its limits are the subject of
[Directed, random, and the gap](guide/directed-random-and-the-gap.md).

## What a model cannot see

This is the part to write down next to the model rather than discover at midnight.

**A model only checks what it models.** `golden.py` models architectural state: four registers,
the PC, two flags, 64 bytes of RAM. It has no concept of:

| | |
|---|---|
| `done` | the one-cycle retire pulse |
| `halt` | the pin that says the core is in `IDLE` |
| cycle counts | it publishes them, but nothing compares them by default |
| the UART | baud rate, framing, the debug protocol |
| `X` | a model has no undefined value |

A core that computes every answer correctly and gets its handshake wrong sails straight through a
model comparison, because those are not the same *kind* of property. Two bugs in this catalogue
are exactly that, and they are
[Lab 05](labs/lab-05-every-answer-is-right-overview.md). Adding vectors does not help; a
different kind of check does.

## When they disagree, it is not always the hardware

This is the part everybody gets wrong the first time, so here is a real example from this
repository rather than a hypothetical one.

**The unimplemented opcodes take four cycles. `golden.py` said three.**

Opcodes `0xC`, `0xD` and `0xE` are not implemented. Everything about them is easy to state: the
PC advances, nothing else changes, `done` never pulses. The model said they cost three clock
cycles, which is what every branch and `STORE` costs, and which is what the RTL looks like it
should do.

Measured, on four filler bytes:

| | |
|---|---|
| clock cycles | **16** — four each |
| `done` pulses | **0** |
| cycles with `halt` high | **4** |

They match no clause in `CYCLE_3`, so the FSM takes its **default exit to `IDLE`**, spends a
cycle there, and is sent back to `CYCLE_1` by the still-asserted `run`. Four cycles, and one
cycle of `halt` in the middle of a free-running program.

Three things worth taking from that.

1. **The model was the wrong one of the two.** It is a second implementation written by a
   person; it is not an oracle. "The DUT disagrees with the model" is a statement about a
   *pair*, and the next question is always *which one*, answered by going back to the
   specification — or, when the specification is silent, by measuring the hardware and writing
   down what it does.
2. **The model was right about the part it was mostly used for.** Its architectural state was
   correct all along; the number it got wrong was a timing figure it also happened to publish.
   A model can be trustworthy in one dimension and wrong in another, which is an argument for
   knowing exactly which dimensions yours covers.
3. **It was found by measuring a case nobody tests.** `0x0C` is filler. No program executes it
   on purpose. It is precisely the sort of "obviously nothing happens here" behaviour that never
   gets an assertion — which is the whole subject of
   [Where bugs hide](guide/where-bugs-hide.md), applied to the testbench instead of the design.

### And sometimes neither is wrong, because the spec has not decided

SimProc's `ORI` has no register field — all five spare bits are the immediate — so its
accumulator is implicit in the hardware, and the RTL carried a comment for a year saying it
might be the other register.

Four variants were built and simulated to settle it. The answer is that `r0` and `r1` are
**exactly isomorphic** in this machine: a register index never leaves the instruction word, `r0`
is not hardwired to zero, and no flag, addressing mode, reset value or debug command treats
either specially. The same program with `r0` and `r1` swapped produces the same memory and
mirrored registers, exactly.

**The hardware cannot break the tie, so no measurement can.** Somebody has to decide, write it
down, and make the model match — and that decision then becomes part of the specification rather
than an accident of the RTL. DD104 specifies `r0`.

What is *not* a matter of taste is that the two lines implementing that decision must move
together. Half-applying it produces "OR the immediate into one register, write the answer to a
different one", which is an instruction nobody specified — and it is one of the two hardest bugs
in the catalogue, because after a reset both candidate registers hold zero and the first `ORI`
of any program looks correct.

## The checklist

When the model and the design disagree:

1. **Read the failing instruction, not the final state.** `trace()` already told you which one.
2. **Decide which side is wrong**, from the specification — not from whichever one you wrote.
3. If the specification is silent, **measure the hardware, then write down what it does** and
   say in the model that this is a record of behaviour rather than a requirement.
4. If the specification is *ambiguous* rather than silent, that ambiguity is itself a hazard.
   Decide it, document it, and check that everything implementing the decision moved together.
5. **Then ask what a model comparison could not have seen** on this design, and go write that
   test separately.

## The reflex

> **Compare snapshots, not values.** If both sides can produce the same tuple, compare the
> tuples — it is fewer characters than a hand-written expectation, it checks the state you were
> not thinking about, and it fails with a location instead of a symptom.
>
> And keep the model's blind spots written down next to it. A model that everybody trusts and
> nobody has bounded is worse than no model, because it converts "we did not check that" into
> "it passed".

Next: [Directed, random, and the gap](guide/directed-random-and-the-gap.md), where the model
earns its keep on stimulus nobody wrote by hand — and then does not.
