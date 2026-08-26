# Writing the bug report

**Question this page answers:** *I found it. What do I actually hand to the designer?*

A reproducer. Not a description, not a patch, not a paragraph in a chat window.

Here is the sentence the whole capstone is built on, and it is the one that surprises people:

> **The test is the deliverable, not the fix.**

That is not modesty about your debugging. It is an observation about which of the two artifacts
survives. A patch is something one person did once, in one file, on one afternoon. A test that
fails on the broken design and passes on the fixed one is what stops the bug coming back —
next year, in a rewrite, done by somebody who has never heard of you. One of those two things
is still doing work in 2031.

DD104 mechanises exactly that. `make verdict` has three rows, and the middle row is the
deliverable:

```
      ok  1. the golden core          must PASS      3 tests, all passed        4.2s
  caught  2. the core you were dealt  must FAIL      3 tests, 1 FAILED          3.4s
        t01_sub_with_two_distinct_operands
            AssertionError: SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = 156.
    FAIL  3. core/ as it stands now   must PASS      3 tests, 1 FAILED          3.4s
```

Row 2 is rebuilt **fresh from the bug catalogue every time**, never read from `core/`. So when
you apply the fix, row 3 goes green and **row 2 does not change**:

```
      ok  1. the golden core          must PASS      3 tests, all passed        4.2s
  caught  2. the core you were dealt  must FAIL      3 tests, 1 FAILED          3.4s
      ok  3. core/ as it stands now   must PASS      3 tests, all passed        3.5s
------------------------------------------------------------------------
 VERDICT: PASS
   Row 2 is the part worth keeping. Commit that test.
```

You cannot get a green row 2 by editing the file the test runs against. That is the mechanism
that makes "the test is the deliverable" a fact about the grader rather than an opinion on a
slide.

## The five parts, and why they are in that order

[`BUG-REPORT-template.md`](https://github.com/uoftasic/dd104/blob/main/labs/lab-06-capstone/BUG-REPORT-template.md)
ships in the capstone package. There is a complete worked example beside it —
[`BUG-REPORT-EXAMPLE.md`](https://github.com/uoftasic/dd104/blob/main/labs/lab-06-capstone/BUG-REPORT-EXAMPLE.md),
filled in for `B01_sub_operands_swapped`, which is deliberately **not** one of the capstone's
three. Read the shape; then write yours.

The order is not arbitrary. It is the order in which the reader needs each part.

### 1. The smallest program that reproduces it

**Minimise. Cut instructions until it stops failing, then put the last one back.**

A ten-line repro and a three-line repro are the same bug and very different amounts of somebody
else's day. Every instruction you leave in is one the reader has to rule out.

The worked example is three instructions of setup and one `SUB`, and it ships complete as
[`labs/common/test_b01_repro.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_b01_repro.py):

```python
    sp = SimProc(dut)
    await sp.start()

    await sp.run(set_reg(1, 200) + set_reg(2, 100) + [SUB(1, 2)])
    got = sp.reg(1)
```

No loop, no branch, no memory, no model, no UART traffic beyond what the harness needs to start
the core. And it comes with the command that runs it:

```bash
cd labs/common
make check TB=test_b01_repro BUG=B01
```

**A repro that is not runnable is a description.** Give the file, give the command, and make
sure both work from a clean clone — the person reading your report does not have your shell
history.

### 2. Expected versus actual, as numbers, with the arithmetic shown

Not "r1 is wrong". Three things: the number you expected, the number you got, **and the sum that
produces the expected one**. The third is what turns a complaint into a claim somebody can
check.

Write it into the assertion, not into the report — then it appears at 2 a.m. on somebody else's
machine without anyone re-deriving it:

```python
    assert got == 100, (
        f"SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = {got}.\n"
        f"  expected  200 - 100 = 100\n"
        f"  got       {got}\n"
        f"  note      (100 - 200) mod 256 = {(100 - 200) & 0xFF}, which is what a "
        f"core computing rB - rA would give\n"
        f"  {sp.describe()}")
```

`make verdict VERBOSE=1` prints the whole thing:

```
 SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = 156.
     expected  200 - 100 = 100
     got       156
     note      (100 - 200) mod 256 = 156, which is what a core computing rB - rA would give
     PC=13  r0=100 r1=156 r2=100 r3=  0  N=1 Z=0  IDLE
 assert 156 == 100
```

Read that and you know which line of RTL to open. You did not re-run anything, add a print, or
open a waveform. **That is the standard**, and the last line — `sp.describe()` — is one call.

### 3. The shape

**How many things are wrong, out of how many — and what that count implies before anybody opens
the RTL.**

A count is a diagnosis when it *factors*. Drive the ALU exhaustively, 393,216 vectors, about
nineteen seconds:

```
ALU ADD  value_mismatch=     0 flag_mismatch=     0
ALU SUB  value_mismatch= 65024 flag_mismatch= 65024
ALU OR   value_mismatch=     0 flag_mismatch=     0
ALU NAND value_mismatch=     0 flag_mismatch=     0
ALU SHL  value_mismatch=     0 flag_mismatch=     0
ALU SHR  value_mismatch=     0 flag_mismatch=     0
```

65,024 of 65,536 `SUB` pairs wrong, everything else perfect. **Now account for the 512
survivors**, because that is where the diagnosis lives: `A - B == B - A (mod 256)` exactly when
`2(A - B) == 0 (mod 256)`, which is when `A - B` is `0` or `128`. That is 256 pairs with
`A == B`, plus 256 with `|A - B| == 128`, and `65,536 − 512 = 65,024` to the digit.

Nothing except "the operands are the wrong way round" produces exactly 512 survivors. You have
localised the bug from a single number.

Three shapes worth recognising:

| the count says | it means |
|---|---|
| `0` value mismatches, `25,726` flag mismatches | the arithmetic is fine; look at the flag logic |
| exactly half | the fault tracks a signal that is high half the time |
| a count that factors into a sentence | you have a hypothesis; go and confirm it |
| a count that does not factor | you have a number, and still owe an explanation |

And the free finding in that table above: `65024` appears in **both** columns. `N` and `Z` are
computed from `ALUout`, so they are wrong exactly when it is. The flag logic is not implicated,
and you did not have to test it separately to know that.

### 4. Where it is *not*

This is the part everybody skips and it is the part that makes the report credible. It is also
what localises the fix.

- Which instructions are unaffected? *(`ADD`, `OR`, `NAND`, `SHL`, `SHR`: zero of 65,536 each.)*
- Which registers, addresses, flags?
- Does it survive a reset? *(This one is combinational, so a reset is irrelevant — and saying so
  rules out an entire class of explanation.)*
- Does it depend on the operands being different? *(Yes — and `SUB rX, rX` is the idiom for
  "clear a register", which is why the bug survives almost every program in this course.)*
- Which of your other tests pass on this core, and what does that rule out?

The worked example ships two tests that **pass** on the broken core, on purpose:
`t02_the_idiom_that_hides_it` and `t03_the_512_survivors`. A report that only contains red is a
report that has not been checked.

> This is where a habit from software testing betrays you. There, a passing test in a bug report
> is noise. Here it is evidence: each one is a region of the design the reader can stop
> suspecting, and narrowing the search is most of what debugging is.

### 5. The reflex the suite gained

One line. The rule a person can carry to the next design, and the test that enforces it here, by
name.

> Reflex: *never test a binary operation with `op(x, x)`. Aliased operands make a swapped,
> mirrored or wrong-source implementation indistinguishable from a correct one — and the aliases
> you write by habit (`SUB rX, rX` for clear, `NAND rX, rX` for not, `LOAD rX, rX` for a pointer
> dereference in place) are exactly the ones you will never suspect.*
>
> Enforced by: `t01_sub_with_two_distinct_operands` in `labs/common/test_b01_repro.py`, which
> fails on this core and passes on the golden one.

**Demonstration plus a one-line rule is a reflex. Demonstration alone is an anecdote.** The
sentence has to be short enough to still be in someone's head six months later, and it has to
name a test, or nothing enforces it.

## Four ways a bug report fails

**"It doesn't work."** No numbers, so nobody can tell whether they have fixed it.

**A patch with no test.** The fastest way to have the same bug twice. If you also fixed it,
good — put the diff at the bottom, under the reproducer.

**A repro that only runs on your machine.** A file path that is not in the repo, a testbench
that imports something you wrote at 1 a.m., a `make` invocation with four variables set.
Everything in your report must run from a clean clone with the command you printed.

**A red test with no green one.** `make verdict`'s first row exists for this. A test that fails
on the broken core and *also* fails on the golden one has not found your bug; it has found your
testbench. Row 1 must be `ok` before row 2 means anything.

## Try this

Write the smallest one you can, end to end, on a bug you have already seen.

```bash
cd labs/lab-04-your-first-bug-hunt
make new BUGPICK=B01        # deal a core you already know the answer to
make verdict TB=test_b01_repro
```

**What you should see:** rows 1 and 2 green-ish, row 3 `FAIL` — the test exists, the design is
still broken. Now fix it. Line 811 of `core/simproc_system.sv`:

```systemverilog
            SUB:        ALUout = B - A;     ->     SUB:        ALUout = A - B;
```

```bash
make verdict TB=test_b01_repro
```

**What you should see:** `VERDICT: PASS`, and **row 2 unchanged**. That is the whole idea in one
diff.

Then do it again with a bug nobody has told you the answer to — `make new` with no `BUGPICK` —
and write the report from
[`BUG-REPORT-template.md`](https://github.com/uoftasic/dd104/blob/main/labs/lab-06-capstone/BUG-REPORT-template.md).
The capstone's definition of done is `13 of 13 caught` **and** a `BUG-REPORT.md` with all five
parts in it. The five parts take about twenty minutes once the test exists, and the test is the
part you already did.

Next: [Lab 06 — the capstone](labs/lab-06-capstone-overview.md).
