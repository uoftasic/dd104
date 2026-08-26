# Flags are architectural state

**Question this page answers:** *I checked the answer and it was right. What else is there to check?*

The flags.

SimProc has two of them. `N` is bit 7 of the last result. `Z` is "that result was zero". They
are written by `ADD`, `SUB`, `NAND`, `SHIFT` and `ORI`, and left alone by `LOAD`, `STORE` and
every branch. They are one bit each. And they are **architectural state** — as much a result of
an instruction as the byte that lands in a register, and the only thing every branch on this
machine can see.

> Here is the belief you probably brought with you, and it is the one this page is about to
> take away: *if the numbers are right, the machine is right.* On this processor you can get
> every number right, in every register, in every byte of memory, on every instruction, and
> still ship a chip that takes the wrong branch.

## A bug you can hold in one hand

`B03_zero_flag_low_nibble` is one character:

```systemverilog
good:    assign Z = ~(|ALUout);
broken:  assign Z = ~(|ALUout[3:0]);
```

The zero-detector looks at the bottom four bits of the result instead of all eight. So the
broken core says "that was zero" for 16, for 32, for 64, for 128, for 240 — for every byte
whose low nibble happens to be zero.

**Every value it computes is still correct.** `ALUout` is untouched. The register gets the
right byte, memory gets the right byte, the program counter is right, `N` is right. One bit is
wrong, sometimes.

## The exhaustive test that proves the shape

The ALU is 34 lines and its entire input space is 393,216 vectors, which Icarus walks in about
twenty seconds. [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md) is that
walk. Run it against the broken ALU:

```bash
cd labs/lab-03-three-blocks-before-the-processor
cp solutions/test_alu.py test_alu_solution.py
make check TB_ALU=test_alu_solution BUG=B03
```

**What you should see:**

```
      ok  the golden ALU                     3 tests, all passed             19.4s
  caught  B03_zero_flag_low_nibble           3 tests, 1 FAILED               18.6s
        t02_every_vector_the_alu_can_be_given
            AssertionError: Every value is correct, and 25726 of 393216 vectors have the wrong FLAGS
```

Read that sentence again, because it is the whole page: **`Every value is correct, and 25726 of
393216 vectors have the wrong FLAGS`.**

`make check` truncates the message to fit its table. The run itself prints the whole thing, and
the whole thing is a diagnosis rather than a score:

```
393216 vectors checked -- 0 value mismatches , 25726 flag mismatches
    {'ADD': 3840, 'SUB': 3840, 'OR': 255, 'NAND': 255, 'SHL': 14400, 'SHR': 3136}
  First one: ADD(0x00, 0x10) = 0x10 with N=0 Z=1, expected N=0 Z=0.
```

Three things to read off it before you open any RTL.

**The value column is zero for all six operations.** Not small — zero. The adder adds, the
subtractor subtracts, the shifter shifts.

**The flag column is non-zero for all six.** A fault that affects every operation and no value
is not *in* any operation. It is in something all six share and none of them computes, and
there are exactly two such things in this module: `N` and `Z`.

**The counts factor, and the factors describe the bug.** Every one of the six is exactly the
number of vectors whose *result* is non-zero with a zero low nibble — which is the only
prediction the hypothesis "`Z` is wired to `ALUout[3:0]`" makes:

| | count | = | why |
|---|---|---|---|
| ADD, SUB | 3,840 | 15 × 256 | 15 results `0x10`…`0xF0`, each reachable from 256 operand pairs |
| OR | 255 | 16 × 16 − 1 | `a\|b` ends in four zeros only if both do; drop the genuinely-zero case |
| NAND | 255 | 16 × 16 − 1 | mirror image: both operands must end in `0xF` |
| SHL | 14,400 | 960 + 1,920 + 3,840 + 7,680 | shift by 0, 1, 2, 3 — each one *manufactures* more low zero bits |
| SHR | 3,136 | 960 + 896 + 768 + 512 | shifting right destroys them instead, so it shrinks |
| | **25,726** | | |

Add the column up and it is 25,726 to the digit. **That is the check worth internalising:** a
failure count that factors into a sentence about the design is a hypothesis you can act on; one
that does not is a number you still have to explain. The `SHL`/`SHR` asymmetry alone rules out
every explanation except "something is looking at the bottom of the byte", because nothing else
would care which direction the bits moved.

And `First one: ADD(0x00, 0x10) = 0x10 with N=0 Z=1` hands you a three-line reproducer.

**Why an engineer cares:** you have just localised a bug to one of two wires without opening
the RTL, from a single number and its factorisation. That is what "the count is the diagnosis"
means, and it is the difference between a bug report a designer can act on and a bug report
that says "the ALU is broken".

## Now the part that hurts: a good testbench that cannot see it

This ships complete as
[`labs/common/test_values_only.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_values_only.py).
It is not a strawman. Three tests: `ADD` and `SUB` over twelve operand pairs each — zero, one,
the halves of the byte, the wrap-around; `NAND` over the same twelve, plus twenty shifts; and a
whole sixteen-instruction program checked for both its answer *and* its exact cycle count.

```python
@cocotb.test()
async def v01_arithmetic_over_a_spread_of_operands(dut):
    """ADD and SUB, twelve operand pairs each, every result checked."""
    sp = SimProc(dut)
    await sp.start()

    for a, b in PAIRS:
        await sp.run(set_reg(1, a) + set_reg(2, b) + [ADD(1, 2)])
        assert sp.reg(1) == (a + b) & 0xFF, (
            f"{a} + {b}: r1 is {sp.reg(1)}, expected {(a + b) & 0xFF}.\n"
            f"  {sp.describe()}")
```

**1,889,970 ns** of simulated time — 3.7× the shipped example testbench, twenty-two seconds of
wall clock — and it is more thorough than most first attempts. Point it at the broken core:

```bash
cd labs/common
make check TB=test_values_only BUG=B03
```

**What you should see:**

```
      ok  the golden core                    3 tests, all passed         21.3s
  MISSED  B03_zero_flag_low_nibble           3 tests, all passed         20.1s
------------------------------------------------------------------------
 VERDICT: FAIL — your testbench passes B03_zero_flag_low_nibble too.
   A test that passes on a broken core is not testing that core.
   That bug hides behind: every test that checks results and not flags
```

**`MISSED`.** Not "unlucky". Not "needs more vectors". Structurally incapable: every value this
processor computes is visible in a register or in memory, `N` and `Z` are not, and a test that
only reads registers and memory is testing a strictly smaller machine than the one on the die.
You could run that file for a week.

**The reflex:** *for every instruction that writes a flag, assert the flag. For every
instruction that must not write one, assert it did not move.* Not "check some flags" — a
per-instruction rule, the way you already have a per-instruction rule about the result.

## Four lines that catch it

Here is the whole of the difference, from
[`test_example.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_example.py)'s
fourth test:

```python
    # r1 = 16, and make that the LAST flag-setting result.
    await sp.run(set_reg(1, 16))
    assert sp.reg(1) == 16, f"r1 is {sp.reg(1)}, expected 16"
    n, z = sp.flags()
    assert (n, z) == (0, 0), (
        f"after r1 = 16 the flags are N={n} Z={z}, expected N=0 Z=0.\n"
        f"  16 is 0b00010000: not negative, and not zero. If Z is 1 here, "
        f"something is looking at only part of the byte.")
```

```bash
make check BUG=B03           # TB defaults to test_example
```

```
  caught  B03_zero_flag_low_nibble           6 tests, 2 FAILED            2.7s
        t04_flags_are_state
            AssertionError: after r1 = 16 the flags are N=0 Z=1, expected N=0 Z=0.
```

**16 is the whole trick.** Its low four bits are zero and the byte is not, so it is exactly the
value that separates a full-byte zero-detector from a nibble-wide one. 32, 64, 128 and 240 all
work too. `5` does not, `255` does not, `0` does not. A flag test on values you picked without
thinking about the flag is a flag test that agrees with the bug.

## The half-second that makes it a real bug

Everything so far is a bit in a status register nobody reads. Here is what makes it a chip you
cannot ship. From
[`test_reference.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_reference.py),
the last four lines of `R07`:

```python
    # And the consequence, which is what actually bites: a branch on a bad flag.
    prog = set_reg(1, 16) + [SUB(0, 0), ADD(1, 3), BZ(1), ORI(1), SUB(3, 3)]
    await sp.run(prog)
    assert sp.reg(0) == 1, (
        f"r0 is {sp.reg(0)}, expected 1: the BZ after r1 = 16 was TAKEN, so the "
        f"core thinks 16 is zero.")
```

`r1` holds 16. `ADD r1, r3` adds zero to it, so `r1` is *still* 16 and the flags now describe
16. Then `BZ +1` asks "was that zero?" and skips the next instruction if it was.

On the good core `Z` is 0, the branch is not taken, `ORI 1` runs, `r0` is 1.
On the broken core `Z` is 1, the branch **is** taken, `ORI 1` is skipped, `r0` is 0.

Two instructions later, the machine is executing different code. No register was ever wrong. No
byte of memory was ever wrong. The program went the other way, and from there everything is
wrong, and none of it looks like a flag bug any more.

> This is what "a flag set late, or set wrong, is invisible until something branches on it"
> means in practice. The gap between the defect and the symptom is however many instructions
> you happen to run between the compare and the branch — and on real firmware that can be a
> hundred.

## The other direction: a flag that changes when it should not

The mirror-image bug is `B09_branch_clobbers_flags`, and it is one added line: a branch that
writes the flags with the result of its own PC arithmetic.

Branches on SimProc do **not** set flags, on purpose. The ISA note says so in one sentence:
*"you can compare once and branch on it twice."* That is a real idiom — `BZ here; BNZ there` —
and it is the only stimulus that can see this bug at all, because with one branch per compare
everything works.

```bash
make check TB=test_reference BUG=B09
```

```
  caught  B09_branch_clobbers_flags          11 tests, 2 FAILED              18.1s
        R05_flags_survive_a_branch
            AssertionError: r0 is 8, expected 1.
        R07_zero_and_negative_flags
            AssertionError: after r1 = 128 the N flag is 0; N is bit 7 of the result
```

The program in `R05` is eight lines and it reads like a proof:

```
        SUB   r1, r1        # r1 = 0  ->  Z = 1, N = 0
        BZ    taken         # taken
        ORI   16            # skipped
taken:  BNZ   wrong         # must NOT be taken: Z is still 1
        ORI   1             # r0 = 1, the proof we got here
        JMP   done
wrong:  ORI   8             # r0 = 8 if the flags were clobbered
done:   SUB   r3, r3
```

`r0 == 1` means the flags survived the first branch. `r0 == 8` means they did not. One
register, two possible values, and each one names a different world. **Write your assertions so
that the wrong answer is a sentence, not a number.**

## What to put in your own suite

Four rules, each of which is one line of code per instruction:

1. **After every flag-setting instruction, assert `N` and `Z`.** `sp.flags()` returns the pair.
2. **After every instruction that must leave the flags alone** — `LOAD`, `STORE`, all four
   branches — **assert they did not move.** Read them before, read them after, compare.
3. **Pick values that can tell the two implementations apart.** For `Z`: something non-zero
   whose low nibble is zero (16, 32, 64, 128, 240). For `N`: something ≥ 128, and something
   just below it. `5` proves nothing about either.
4. **Then branch on the flag and check where you landed.** A flag assertion catches the defect;
   a branch catches the *consequence*, and it is the consequence that turns up in silicon.

`set_reg()` clobbers `N` and `Z` — it is built out of `SUB`, `ORI` and `SHIFT`, all of which set
flags. **Set your registers up before the compare, never between the compare and the branch.**
The harness says so in a warning in its own docstring, and it is the single most common way a
flag test ends up testing `set_reg` instead of the design.

Next: [Where bugs hide](guide/where-bugs-hide.md). Or run
[Lab 04](labs/lab-04-your-first-bug-hunt-overview.md), where nobody tells you which of the
thirteen you have been dealt.
