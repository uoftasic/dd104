# What a testbench actually is

**Question this page answers:** *What am I writing when I write a testbench? It isn't the
design, and it isn't quite a program either.*

A testbench is **a second circuit whose job is doubt.**

That is not a metaphor about attitude. It is a structural description, and taking it
literally is the fastest way to get good at this. Your design under test — the **DUT** — has
inputs and outputs. Something has to be on the other end of those wires: something that
drives the inputs, watches the outputs, and holds an opinion about what it sees. That
something is a circuit too. It is just a circuit you never manufacture.

```
        ┌──────────────────────────┐
        │        TESTBENCH         │
        │                          │
        │   drive ──────────┐      │
        │                   ▼      │
        │            ┌────────────┐│
        │            │    DUT     ││
        │            └────────────┘│
        │                   │      │
        │   observe ◄───────┘      │
        │      │                   │
        │      ▼                   │
        │   decide  ── PASS / FAIL │
        └──────────────────────────┘
```

**Drive, observe, decide.** Every testbench ever written is those three jobs, and every
testbench that fails to catch a bug failed at exactly one of them. Keeping them separate in
your head is most of the skill:

| job | the question | how it fails |
|---|---|---|
| **drive** | did I put the design in the situation where the bug lives? | the bug is never provoked |
| **observe** | am I looking at the signal that would show it? | the bug happens off-screen |
| **decide** | do I have a right answer to compare against? | the bug happens in full view and nothing objects |

The shipped SimProc test from [the previous page](guide/it-works-is-not-a-result.md) fails at
**drive**, comprehensively. It never puts the processor in a situation where any of the
thirteen bugs can express itself, so the other two jobs have nothing to work with.

## Doubt is the job

Here is the shortest possible testbench:

```python
@cocotb.test()
async def it_works(dut):
    pass
```

It passes. It passes on the golden core, on the core whose `SUB` is backwards, on the core
that writes every result into the wrong register, and on the core that never signals that an
instruction finished. It passes on everything, so it distinguishes nothing, so it is worth
nothing.

Every testbench sits somewhere on the line between that and a complete proof, and **the only
way to find out where yours sits is to make it fail on purpose.** A test you have never seen
go red is not yet a test; it is a hypothesis about your own code.

That is why the DD104 verdict is two-sided:

| | must be | because otherwise |
|---|---|---|
| on the golden core | **PASS** | you are testing the wrong thing, or your expectations are wrong |
| on a known-broken core | **FAIL** | you are not testing anything |

Neither half alone means anything. `make check` is the target that measures both, and it will
not hand you a passing verdict until you have both.

## Watching it happen

```bash
cd labs/common
make check
```

```
========================================================================
 CHECK   testbench: test_example      simulator: icarus
========================================================================
      ok  the golden core                    6 tests, all passed          7.8s
  caught  B01_sub_operands_swapped           6 tests, 4 FAILED            8.8s
        t03_arithmetic_on_different_values
            AssertionError: r1 is 199, expected 247.
        t04_flags_are_state
            AssertionError: after r1 = 255 the flags are N=0 Z=0, expected N=1 Z=0
        t05_a_loop_and_its_cycle_count
            TimeoutError: the program did not reach its parking loop at address 16 within 20000 clock
        t06_against_the_golden_model
            AssertionError: instruction 19, at address 19 (0x66 = SUB   r1, r2), left the machine in a
------------------------------------------------------------------------
 VERDICT: PASS
   Your testbench passes the good core and catches B01_sub_operands_swapped.
   That bug teaches: the number is the diagnostic: 65,024 of 65,536 vectors wrong has a shape
========================================================================
```

Seventeen seconds, two runs, one verdict. Read the middle of that block carefully, because
**four different tests caught the same one-line bug in four different ways**, and each way is
a different kind of observation:

| test | what it noticed | which of the three jobs |
|---|---|---|
| `t03` | a register holds `199` where `247` was expected | **decide** — a value against a known answer |
| `t04` | the flags say `N=0 Z=0` after an operation that should set `N` | **observe** — architectural state that is not a register |
| `t05` | the program never reached the address it parks at | **drive** — the machine took a path that does not terminate |
| `t06` | instruction 19 disagreed with a reference model | **decide** — an independent implementation |

`t05` is worth a second look. Nothing in it inspected a wrong value. It ran a loop, the loop
was controlled by a subtraction, the subtraction went the wrong way, and the loop never
ended. **The symptom was a timeout, not a mismatch** — and a timeout is a perfectly good bug
report as long as your testbench has a deadline. A testbench with no timeout hangs forever and
tells you nothing.

## Reading a FAIL you caused on purpose

Get comfortable now, because you will spend most of this course looking at red text.

```
AssertionError: r1 is 199, expected 247.
```

This is a **good** failure message and it is worth taking apart, because writing messages
like it is a real part of the job. It contains the thing that happened (`199`), the thing that
should have happened (`247`), and the name of where to look (`r1`). Compare with the failure
you get from the same bug and a worse testbench:

```
AssertionError
```

Same bug. Same instant. Zero information. The difference is entirely in how the assertion was
written:

```python
assert sp.reg(1) == 247, f"r1 is {sp.reg(1)}, expected 247."
```

**Every assertion you write in this course gets a message, and the message names both
numbers.** In six weeks the only thing standing between you and an hour of confusion will be
whether past-you bothered.

And the wrong number itself is a clue, which is a habit worth starting now. `t03` runs three
instructions on `r1 = 200` and `r2 = 60`:

| step | on the golden core | on `B01`, where SUB is backwards |
|---|---|---|
| `ADD r1, r2` | `200 + 60 = 260`, wraps to **4** | same — **4** |
| `SUB r1, r2` | `4 - 60 = -56`, wraps to **200** | `60 - 4` = **56** |
| `NAND r1, r2` | `~(200 & 60) = ~8` = **247** | `~(56 & 60) = ~56` = **199** |

The number you are shown is `199`, and it is **two instructions downstream of the bug**. Walk
it backwards and the signature appears at the middle row: `200 + 56 = 256`. The two results
are exact negations of each other, which is what swapping the operands of a subtraction does
and nothing else does. **The wrong number is not noise. It is a fingerprint** — and reading
it is a skill you can practise on every failure you cause.

## What "a second circuit" means in cocotb

In classic Verilog you write the testbench in Verilog too — a module with no ports that
instantiates the DUT and wiggles it. It really is a second circuit in the same language.

cocotb moves the testbench into Python, and the boundary shifts but does not disappear. Your
Python does not run *inside* the simulation; it runs **beside** it, and the two take turns.
When you write `await Timer(1, unit="ns")`, you are not sleeping. You are handing control back
to the simulator, telling it to advance one nanosecond of simulated time, and asking to be
woken when it gets there.

That is why the numbers in a cocotb result line are not wall-clock seconds:

```
** test_six_cases.six_cases       PASS           6.00           0.00       6151.51  **
                                                 └─ sim time (ns)  └─ real (s)  └─ ns/s
```

Six nanoseconds of simulated time — one per case — in effectively no real time at all.
**Simulated time is deterministic and yours to reason about; wall-clock time is not.** When a
DD104 page quotes an exact number of nanoseconds, that number will match yours to the digit.
When it quotes seconds, it will not.

## The three ways to run a cocotb test that do not run a cocotb test

A cocotb test is **not** a Python program and **not** a pytest test. It needs a simulator
underneath it, and in this course the only thing that starts one is `make`. All three of
these look right and are green:

```bash
python3 -m pytest test_example.py
```

```
collected 0 items

============================ no tests ran in 0.06s =============================
```

Exit **5**. No error, no traceback, nothing ran.

```bash
python3 test_example.py
```

**Zero bytes of output, exit 0.** The module imported, the decorated function was defined,
and Python reached the end of the file with nothing to do.

And the third: any **cocotb 1.x** tutorial. Most of it warns and keeps going —
`Timer(1, units="ns")` and `MODULE=` in a Makefile both still run on 2.0.1 and print a
deprecation line. What actually stops you is `cocotb.fork`, which dies with `AttributeError:
module 'cocotb' has no attribute 'fork'` and never mentions that the problem is a version.
See [cocotb 2.x vs every tutorial you will find](guide/cocotb-2x-vs-every-tutorial.md) for
the measured split between the two.

## The shortest complete DD104 test

This is a complete file. It ships as part of the harness — the six worked tests it comes from
are [`labs/common/test_example.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_example.py),
and copying that file is the intended way to start every lab in this course.

```python
import cocotb
from simproc import SimProc
from simproc_asm import ORI, ADD

@cocotb.test()
async def r1_gets_five(dut):
    sp = SimProc(dut)
    await sp.start()                              # clock, reset, blank memory
    cycles = await sp.run([ORI(5), ADD(1, 0)])    # r0 = 5 ; r1 = r1 + r0
    assert sp.reg(1) == 5, f"r1 is {sp.reg(1)}, expected 5"
    assert cycles == 9, f"took {cycles} cycles, expected 5 + 4"
```

Drive (`sp.run`), observe (`sp.reg`, and the returned cycle count), decide (two assertions,
each with a message). Nine cycles because `ORI` takes five and `ADD` takes four — and
**checking the cycle count is an observation most people skip.** That matters more than it
sounds: two of the thirteen bugs in this course leave every register, every flag and every
byte of memory correct, and the only thing they disturb is timing and handshake pins. A
testbench that only ever compares values cannot see them at all.

Run it:

```bash
cd labs/common
cp test_example.py test_mine.py     # then edit
make sim   TB=test_mine
make check TB=test_mine BUG=B01
```

Full harness reference: [The SimProc harness](reference/the-harness-api.md) and
[`labs/common/README.md`](https://github.com/uoftasic/dd104/blob/main/labs/common/README.md).

## The reflex

> **Break it on purpose before you trust the green.** Change one character in the design —
> or point `make check` at a core someone already broke — and watch your test go red. A test
> you have never seen fail has told you nothing.

Next: [The lazy testbench](guide/the-lazy-testbench.md), where a perfectly reasonable six-case
testbench passes on a broken adder, and the exhaustive sweep does not just say *no* — it says
*how*.
