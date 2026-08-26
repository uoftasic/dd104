# Lab 01 — The adder you already trust

Full runnable package: [`labs/lab-01-the-adder-you-already-trust/`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust).

You finished DD102 with a 4-bit ripple-carry adder that simulated correctly. This lab hands
you that adder, a second copy of it with one character changed, and a testbench that cannot
tell them apart.

Fixing the testbench is four lines of work. Working out *which* four lines is the lab.

## Prerequisites

- [IC101](https://uoftasic.com/ic101/) complete — the workbench opens and you can get a shell
- [DD102](https://uoftasic.com/dd102/) complete — you have written a `ripple4.sv`
- DD104 cloned: `mod add dd104` then `mod dd104`
- `cocotb-config --version` says **`2.0.1`**. If it says `1.` anything, you are not in the workbench.
- Read [“It works” is not a result](guide/it-works-is-not-a-result.md) and
  [Your first cocotb test](guide/your-first-cocotb-test.md)

## Objectives

- Write a cocotb testbench for a design you already understand completely
- Watch a reasonable testbench pass on a **broken** adder, and be able to say exactly why
- Count the input space of a design and say what fraction of it your stimulus covered
- Turn a failing test into a *diagnosis*, using the number of failures rather than the fact of them
- Meet the two-sided verdict — pass on the good one, **fail on the bad one** — that every later lab uses

## Theory (short)

**The prior this lab overwrites:** *if I loop over my inputs, I have been thorough.*

A test that passes tells you nothing on its own. This passes:

```python
@cocotb.test()
async def it_works(dut):
    pass
```

It passes on a correct adder, on an adder with its carry-in disconnected, and on an adder made
of a wire. It passes on everything, so it distinguishes nothing, so it is worth nothing.

The useful question is not *did it pass* but *what would it have caught*, and that question has
a mechanical answer: run the same testbench against something you know is wrong, and see. So a
result in this course is always two-sided —

| | must | because |
|---|---|---|
| on the good design | **PASS** | otherwise you are testing the wrong thing |
| on a broken one | **FAIL** | otherwise you are not testing anything |

— and `make check` is what measures both halves.

The design is `ripple4`: two 4-bit inputs, one carry-in, a 4-bit sum and a carry-out. Nine
lines. Its whole input space is $2^{4} \times 2^{4} \times 2^{1} = 512$ vectors, which is
small enough that "test all of them" is a real option rather than a slogan. Take it when it is
available. It very rarely is.

Background: [What a testbench actually is](guide/what-a-testbench-is.md) and
[The lazy testbench](guide/the-lazy-testbench.md).

## Procedure

```bash
mod dd104
cd labs/lab-01-the-adder-you-already-trust
make
```

About **5 seconds**. It ends on `VERDICT: FAIL`, and that is correct.

> **`broken/ripple4.sv` is not hidden, and it says so in its own header.** This lab is not a
> bug hunt — you are allowed to open the file and read the one changed line. The hunt starts in
> [Lab 04](labs/lab-04-your-first-bug-hunt-overview.md). What matters here is the testbench that does or
> does not notice, and reading the RTL first makes that easier to think about, not harder.

### Step 1 — Two green rows that mean nothing

- **Try this:** `make sim`, and read the summary table.
- **What you should see:**

  ```
  ** TEST                                STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
  ********************************************************************************************
  ** test_adder.t01_the_obvious_six       PASS           6.00           0.00       7609.87  **
  ** test_adder.t02_every_a_and_every_b   PASS         256.00           0.01      20845.71  **
  ********************************************************************************************
  ** TESTS=2 PASS=2 FAIL=0 SKIP=0                      262.00           0.01      17915.68  **
  ```

  and, in the log above it:

  ```
  checked 256 of the 512 possible input vectors
  ```

  **`6.00`, `256.00`, `262.00` and `256` are GOLDEN** — simulated time and vector counts do
  not vary, and if yours differ, something has changed and it is worth finding out what. The
  `REAL TIME` and `RATIO` columns are wall clock and will not match anybody else's.

- **Why an engineer cares:** two tests, both green, and one of them is a complete cross product
  of `a` against `b` — 256 vectors, every value of both inputs, which is the shape everybody
  means when they say "I tested it exhaustively". Write down now, before Step 2, whether you
  think this testbench would catch a broken adder.

### Step 2 — The other half of the verdict

- **Try this:** `make check`.
- **What you should see:**

  ```
  ========================================================================
   CHECK   testbench: test_adder      simulator: icarus
  ========================================================================
        ok  src/  the good adder           2 tests, all passed          1.5s
    MISSED  broken/  carry-in dropped      2 tests, all passed          2.1s
  ------------------------------------------------------------------------
   VERDICT: FAIL -- your testbench passes the broken adder too.
     broken/ripple4.sv drops the carry-in on the way into slice 0, so
     every vector with cin = 1 comes out one too small. Every vector
     with cin = 0 is perfectly correct.
     Look at the third column of your stimulus. If cin is 0 in every
     row, this bug is not reachable by anything you drove.
  ========================================================================
  ```

- **Why an engineer cares:** `t02` drives every value of `a` and every value of `b`. It is
  genuinely exhaustive — over two of the three inputs. `cin` is 4 + 4 + 1 = 9 bits' worth of
  input space away from being covered, and $2^{9} = 512$, not 256.

  **"Exhaustive" is a claim about a space you named.** Nothing in a passing run reminds you
  which space you meant.

> **`make: *** [Makefile:49: check] Error 1` is not a broken Makefile.** A failed verdict exits
> non-zero on purpose, so `make` prints an error line underneath it and so that a CI job can
> read the result without grepping for text. The line disappears when the verdict passes. You
> will see it in every lab in this course, and it is always the verdict talking.

### Step 3 — Add the loop, and make the failure a diagnosis

- **Try this:** open `test_adder.py` and do the TODO in `t02`. It is two changes:

  1. Sweep `cin` as well. The shape you want is

     ```python
     for cin in range(2):
         for a in range(16):
             for b in range(16):
                 ...
     ```

  2. Do not `assert` on the first bad vector. Collect the bad ones in a list, run all 512, and
     assert at the end with `len(bad)` in the message.

  The reason for the second change is the whole of Step 4, so do it before you run — and
  `make check` will not give you a PASS without it. Doing only change 1 turns `broken/` red,
  which looks like success and is not: the run stops at the first wrong vector, so the failure
  is an anecdote instead of a count. `check.py` measures how many vectors each run actually
  drove and names whichever half is missing:

  ```
   VERDICT: FAIL -- the second half of the TODO is not done.
     You swept cin: on the good adder you drove all 512 vectors.
     On the broken adder you drove 263 and then stopped, because you are
     still asserting on the first vector that is wrong instead of collecting
     them.
  ```

- **What you should see:** `make sim` now reports `512.00` ns and
  `checked 512 of the 512 possible input vectors`, and `make check` says:

  ```
        ok  src/  the good adder           2 tests, all passed          1.4s
    caught  broken/  carry-in dropped      2 tests, 1 FAILED            1.4s
          t02_exhaustive
              AssertionError: 256 of 512 vectors are wrong. First five: 0+0+1=0 (want 1), 0+1+1
  ------------------------------------------------------------------------
   VERDICT: PASS
  ```

- **Why an engineer cares:** the difference between the two runs is four lines of Python and
  256 vectors of stimulus. Nothing about the design changed, nothing about the assertions
  changed, and the testbench went from worthless to worth committing.

### Step 4 — Read the number, not the failure

- **Try this:** look at the count. **256 of 512.**
- **What you should see:** exactly half.
- **Why an engineer cares:** a failure count that is exactly half the input space means the
  fault tracks a signal that is high in exactly half the vectors. On this module there is
  precisely one such signal, and it is named in the port list. You have just localised a bug
  to a single wire **without opening the RTL**.

  That is not a trick for adders. It is the habit: *the shape of a failure is data.* A count
  that factors cleanly is describing the bug —

  | count | what it says |
  |---|---|
  | exactly half | tracks a signal that is high half the time |
  | 65,024 of 65,536 | 512 survivors, and 512 has a description |
  | 0 values wrong, 25,726 flags wrong | the arithmetic is fine; look at the flag logic |

  The last two are [Lab 03](labs/lab-03-three-blocks-before-the-processor-overview.md), and you will
  derive both by hand.

  This is also why the second TODO change matters. `assert` on the first bad vector stops the
  run at vector 256 and reports one wrong answer. Collecting reports `256 of 512`, and only one
  of those two is a diagnosis.

> **`NameError` is not a caught bug.** There is one more verdict `check.py` can print, and it
> is worth knowing before you meet it:
>
> ```
>   BROKEN  broken/  carry-in dropped      2 tests, 1 BLEW UP           1.3s
>         t02_every_a_and_every_b   <- this test BLEW UP; it checked nothing
>             NameError: name 'summary' is not defined
> ------------------------------------------------------------------------
>  VERDICT: FAIL -- 1 of your tests did not run to the end.
> ```
>
> A misspelled variable in the code that builds your failure message does not show up until
> something is actually wrong — so the test passes the good adder, crashes on the broken one,
> and *looks exactly like a catch*. It is not one: Python stopped before the comparison
> happened, so the run says nothing about either adder. cocotb records both outcomes in
> `results.xml` as `<failure>`, which is precisely why the distinction has to be made
> deliberately. [`labs/common/verdict.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/verdict.py)
> is the one place in DD104 that makes it.

### Step 5 — Ask the same question a different way

- **Try this:**

  ```bash
  cd coverage
  make
  ```

  About **11 seconds**, because it builds the design twice with Verilator — Icarus has no
  coverage instrumentation, so this is the one place in the early course where the strict
  simulator is the only one that can answer.

- **What you should see:** on the six hand-picked cases, `design toggle points : 48`,
  `never toggled : 5`, and the five named:

  ```
      ripple4.sv:3  b[2]:1->0
      ripple4.sv:4  cin:0->1
      ripple4.sv:4  cin:1->0
      ripple4.sv:8  c[0]:0->1
      ripple4.sv:8  c[0]:1->0
  ```

  On all 512: `never toggled : 1`.

- **Why an engineer cares:** the tool has no idea what an adder is, it never looked at whether
  any answer was right, and it named `cin` anyway. Coverage does not ask *is the design
  correct*; it asks *which parts of it did my stimulus never move*, and those are different
  questions with different uses.

  Note also `design line points : 0` in both runs. This design is continuous assignments, and a
  continuous assignment is not a statement that executes, so line coverage has nothing here to
  count. **A report claiming "100 % line coverage" on this adder would be perfectly true and
  completely empty.** The full argument is in
  [Coverage as a question](guide/coverage-is-a-question.md); the add-on has its own
  [`README.md`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust/coverage).

## Expected results

You are done when all of these are true.

| Check | Expected | |
|---|---|---|
| `make check` final line | `VERDICT: PASS` | |
| `make sim` total sim time | `518.00` ns | **GOLDEN** |
| the log line in `t02` | `checked 512 of the 512 possible input vectors` | **GOLDEN** |
| the failure on `broken/` | `256 of 512 vectors are wrong` | **GOLDEN** |
| `make` wall clock | about 5 s | BALLPARK |
| `coverage/`: six cases | 48 toggle points, 5 never toggled, 0 line points | **GOLDEN** |
| `coverage/`: all 512 | 48 toggle points, 1 never toggled, 0 line points | **GOLDEN** |

Wall-clock seconds are the only figures on this page allowed to differ from yours.

> **One survivor is not a bug.** The all-512 run still reports one point that never toggled:
> `a[3]:1->0`. The loops end with `a` at 15, so `a[3]` goes high and the test finishes — there
> is no transition back down because there is nothing after it. That is an artefact of loop
> order, not a gap in stimulus, and knowing the difference is most of what reading a coverage
> report consists of.

## Going further

The reference solution keeps `t01_the_obvious_six` in the file, even though `t02` drives every
vector `t01` drives and 506 more. Deleting it is a perfectly defensible argument. It stays
because a suite is read as often as it is run: six named cases with a comment document what the
module is *for*, and it is the row that goes red first when somebody deletes the module.

Have that argument before you read
[`solutions/README.md`](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust/solutions),
which has one more decision in it worth disagreeing with.

## Links

- [Lab package](https://github.com/uoftasic/dd104/tree/main/labs/lab-01-the-adder-you-already-trust)
- [Coverage as a question, not a metric](guide/coverage-is-a-question.md) — the tool that found `cin` without knowing what an adder is
- [cocotb 2.x vs every tutorial you will find](guide/cocotb-2x-vs-every-tutorial.md) — read before you search for anything
- Next lab: [Lab 02 — The only test this chip has](labs/lab-02-the-only-test-this-chip-has-overview.md), where the same argument is made about a real processor, and thirteen broken ones
