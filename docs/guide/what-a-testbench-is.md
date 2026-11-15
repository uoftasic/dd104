# What a testbench is

This page answers: *what am I writing when I write a testbench? It isn't the design, and it
isn't quite a program either.*

A **testbench** is a second circuit whose job is doubt. Take that literally. The design under
test, the **DUT**, has inputs and outputs, and something has to sit on the other end of those
wires: something that drives the inputs, watches the outputs, and has an opinion about what it
sees. That something is a circuit too. You just never manufacture it.

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

Every testbench does three jobs: drive, observe and decide. A testbench that misses a bug has
failed at one of them, so it helps to keep them separate:

| Job | The question | How it fails |
|---|---|---|
| Drive | Did I put the design in the situation where the bug lives? | The bug is never provoked |
| Observe | Am I looking at the signal that would show it? | The bug happens off-screen |
| Decide | Do I have a right answer to compare against? | The bug happens in full view and nothing objects |

The shipped SimProc test from [the previous page](../guide/it-works-is-not-a-result.md) fails at
drive. It never puts the processor in a situation where any of the thirteen bugs can show up,
so observe and decide have nothing to work with.

## Tests that can fail

Here is the shortest possible testbench:

```python
@cocotb.test()
async def it_works(dut):
    pass
```

It passes on the golden core, on the core whose `SUB` is backwards, on the core that writes
every result into the wrong register, and on the core that never signals that an instruction
finished. Since it passes on everything, it tells them apart from nothing.

Every testbench sits somewhere between that and a complete proof, and the only way to find out
where yours sits is to make it fail on purpose. Until you have seen a test go red, treat it as a
guess about your own code.

That is why the DD104 verdict has two sides:

| | Must be | Because otherwise |
|---|---|---|
| On the golden core | PASS | You are testing the wrong thing, or your expectations are wrong |
| On a known-broken core | FAIL | You are not testing anything |

Neither half means anything alone. `make check` measures both, and it will not give you a
passing verdict until you have both.

## Four ways to catch one bug

Here is `make check` running the shipped example testbench, `labs/common/test_example.py`,
against the core whose `SUB` computes `B - A`. You'll run it yourself in
[Lab 02, Part 3](../labs/lab-02-the-only-test-this-chip-has-overview.md#part-3-the-example-testbench).

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
   Your testbench passes the good core, and on B01_sub_operands_swapped a check FIRED:
       t03_arithmetic_on_different_values: AssertionError: r1 is 199, expected 247.
       t04_flags_are_state: AssertionError: after r1 = 255 the flags are N=0 Z=0, expected N=1 Z=0
...
```

Four tests caught the same one-line bug in four different ways, and each is a different kind of
observation:

| Test | What it noticed | Which job |
|---|---|---|
| `t03` | A register holds `199` where `247` was expected | Decide: a value against a known answer |
| `t04` | The flags say `N=0 Z=0` after an operation that should set `N` | Observe: architectural state that is not a register |
| `t05` | The program never reached the address it parks at | Drive: the machine took a path that does not end |
| `t06` | Instruction 19 disagreed with a reference model | Decide: an independent implementation |

`t05` is worth a second look. Nothing in it inspected a wrong value. It ran a loop controlled by
a subtraction, the subtraction went the wrong way, and the loop never ended. The symptom was a
timeout, not a mismatch. A timeout is a perfectly good bug report as long as your testbench has
a deadline. A testbench with no timeout hangs forever and tells you nothing.

## Reading a failure message

You will spend most of this course looking at red text, so it pays to read it well.

```
AssertionError: r1 is 199, expected 247.
```

This is a good failure message. It has what happened (`199`), what should have happened
(`247`), and where to look (`r1`). The same bug with a worse testbench gives you this:

```
AssertionError
```

Same bug, same instant, no information. The difference is entirely in how the assertion was
written:

```python
assert sp.reg(1) == 247, f"r1 is {sp.reg(1)}, expected 247."
```

Give every assertion you write in this course a message that names both numbers. In six weeks,
whether past-you bothered is what decides whether a failure costs you an hour of confusion.

The wrong number is a clue in its own right. `t03` runs three instructions on `r1 = 200` and
`r2 = 60`:

| Step | On the golden core | On `B01`, where SUB is backwards |
|---|---|---|
| `ADD r1, r2` | `200 + 60 = 260`, wraps to 4 | Same: 4 |
| `SUB r1, r2` | `4 - 60 = -56`, wraps to 200 | `60 - 4` = 56 |
| `NAND r1, r2` | `~(200 & 60) = ~8` = 247 | `~(56 & 60) = ~56` = 199 |

The number you are shown, `199`, is two instructions downstream of the bug. Walk it backwards
and the middle row gives it away: `200 + 56 = 256`. The two results are exact negations of each
other, which is what swapping the operands of a subtraction does and nothing else does. Reading
a wrong number this way is a skill you can practise on every failure you cause.

## The second circuit in cocotb

In classic Verilog the testbench is Verilog too: a module with no ports that instantiates the
DUT and wiggles its inputs. It really is a second circuit in the same language.

cocotb moves the testbench into Python. Your Python does not run inside the simulation; it runs
beside it, and the two take turns. `await Timer(1, unit="ns")` does not sleep. It hands control
back to the simulator, asks it to advance one nanosecond of simulated time, and asks to be woken
when it gets there.

That is why the numbers in a cocotb result line are not wall-clock seconds:

```
** test_six_cases.six_cases       PASS           6.00           0.00       6151.51  **
                                                 └─ sim time (ns)  └─ real (s)  └─ ns/s
```

That is six nanoseconds of simulated time, one per case, in almost no real time. Simulated time
is deterministic, so you can reason about it: when a DD104 page quotes an exact number of
nanoseconds, yours will match to the digit. Seconds will not.

A cocotb test also needs a simulator underneath it. `python3` and `pytest` on a test file both
run nothing and report success; [Your first cocotb test](../guide/your-first-cocotb-test.md#two-commands-that-run-nothing)
shows what they print.

## The shortest complete DD104 test

This is a complete file. It comes from the harness's six worked tests in
[`labs/common/test_example.py`](https://github.com/uoftasic/dd104/blob/main/labs/common/test_example.py),
and copying that file is how you are meant to start every SimProc lab.

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

Drive (`sp.run`), observe (`sp.reg` and the returned cycle count), decide (two assertions, each
with a message). The count is nine because `ORI` takes five cycles and `ADD` takes four.
Checking the cycle count is an observation most people skip, and it matters: two of the thirteen
bugs leave every register, flag and byte of memory correct and disturb only timing and handshake
pins. A testbench that only compares values cannot see them.

The full harness reference is [The SimProc harness](../reference/the-harness-api.md).

## Check yourself

1. Before trusting a green test, what should you do to it?
2. A test reports `r1 is 199, expected 247` on a core you suspect has a swapped `SUB`. Using the
   table above, which instruction's result would you check first, and what sum would confirm the
   swap?

Next: [Your first cocotb test](../guide/your-first-cocotb-test.md).
