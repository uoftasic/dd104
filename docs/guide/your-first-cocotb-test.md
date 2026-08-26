# Your first cocotb test

**Question this page answers:** *A testbench is a Verilog file, isn't it? Why am I writing
Python?*

You are writing Python because the thing you actually need — "load this program, run it, and
tell me whether register 1 holds 247" — is four lines of Python and about forty lines of
Verilog, and thirty of those forty are bookkeeping you will get subtly wrong.

cocotb does not replace the simulator. Icarus still compiles the SystemVerilog and still runs
it. cocotb attaches to the running simulation through a standard interface the simulator
already exposes (VPI), and hands you the design as a Python object. You drive pins by
assigning to them and read them back by looking.

## The whole thing, running

Everything on this page is in [`labs/cocotb-intro/`](https://github.com/uoftasic/dd104/tree/main/labs/cocotb-intro).

```bash
cd labs/cocotb-intro
make hello
```

## The design

`rtl/counter.sv`, sixteen lines of logic — an 8-bit counter with an enable, a parallel load and
an active-low **synchronous** reset:

```systemverilog
always_ff @(posedge clk) begin
    if (!rst_n)      q <= 8'h00;
    else if (load)   q <= d;
    else if (en)     q <= q + 8'd1;
end

assign tc = en & (q == 8'hFF);
```

(Excerpt. The complete file, with its port list, is
[`labs/cocotb-intro/rtl/counter.sv`](https://github.com/uoftasic/dd104/blob/main/labs/cocotb-intro/rtl/counter.sv).)

## The test

This is the complete contents of
[`labs/cocotb-intro/test_01_hello.py`](https://github.com/uoftasic/dd104/blob/main/labs/cocotb-intro/test_01_hello.py),
with its explanatory header comment and its numbered inline comments removed:

```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def counts_up(dut):
    """Reset the counter, let it count once, and check that it did."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    dut.en.value    = 0
    dut.load.value  = 0
    dut.d.value     = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    assert dut.q.value == 0, f"after reset q is {dut.q.value}, expected 0"

    dut.rst_n.value = 1
    dut.en.value    = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert dut.q.value == 1, f"after one enabled clock q is {dut.q.value}, expected 1"
    dut._log.info(f"q = {int(dut.q.value)} after one enabled clock. That is the whole test.")
```

Five things in that file are worth naming, because every cocotb test you ever write has all
five.

**`@cocotb.test()`** marks a function as a test. cocotb finds them by importing your module and
looking for the decorator. A function without it is not a test — it is just a function, and
cocotb will not run it, will not complain, and will not mention it.

**`async def` and `await`.** Your test is a coroutine. Every `await` is a point where your test
says "wake me when this happens" and the simulator runs until it does. Between `await`s, zero
simulated time passes, no matter how much Python you execute.

**`dut`** is the top-level HDL module, handed to you as an object. `dut.q` is the signal named
`q`. Sub-modules are attributes too: in SimProc you will write
`dut.tt_um_ieeeuoftasic_simproc.U1.CPU1.curr_state`.

**`.value`** on both sides. `dut.rst_n.value = 0` drives a pin; `dut.q.value` reads one. In
cocotb 1.x, leaving the `.value` off a write was the quietest bug in the system — it replaced
the attribute with a plain integer and drove nothing, silently. 2.x catches it:

```
AttributeError: Cannot set attribute 'load' on simulation object counter. Did you forget to add `.value`?
```

That message is a genuine improvement over 1.x and it is worth knowing it exists, because it
means a signal that never changes is *not* explained by a missing `.value`. Look elsewhere.

**The clock is a task you start.** `Clock(dut.clk, 10, unit="ns")` describes a clock; `.start()`
is a coroutine that drives it forever; `cocotb.start_soon(...)` runs that coroutine in the
background. Miss this line and your design simply never moves — every `await RisingEdge(clk)`
waits forever and the test hangs with no message.

## What it prints

```
     0.00ns INFO     cocotb                             Running on Icarus Verilog version 14.0 (devel)
     0.00ns INFO     cocotb                             Seeding Python random module with 1787717251
     0.00ns INFO     cocotb                             Initialized cocotb v2.0.1 from /usr/local/lib/python3.12/dist-packages/cocotb
     0.00ns INFO     cocotb                             Running tests
     0.00ns INFO     cocotb.regression                  running test_01_hello.counts_up (1/1)
                                                            Reset the counter, let it count once, and check that it did.
    21.00ns INFO     cocotb.counter                     q = 1 after one enabled clock. That is the whole test.
    21.00ns INFO     cocotb.regression                  test_01_hello.counts_up passed
    21.00ns INFO     cocotb.regression                  **************************************************************************************
                                                        ** TEST                          STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        **************************************************************************************
                                                        ** test_01_hello.counts_up        PASS          21.00           0.00      21998.10  **
                                                        **************************************************************************************
                                                        ** TESTS=1 PASS=1 FAIL=0 SKIP=0                 21.00           0.00       8584.83  **
                                                        **************************************************************************************
```

Read the left column: that is **simulated** time, in nanoseconds, not wall-clock time. The test
took 21 ns of simulation and rather less than that of your life.

`Seeding Python random module with 1787717251` is cocotb reseeding Python's global `random` on
every run. When a random test fails, that number is how you get the same run back — set
`COCOTB_RANDOM_SEED` to it.

## The line that is not there, and why

Nothing in `test_01_hello.py` says which file to compile or which module is the top. That is in
[`sim.mk`](https://github.com/uoftasic/dd104/blob/main/labs/cocotb-intro/sim.mk). Excerpt —
these are the twelve working lines; the shipped file adds a comment header and the `?=`
defaults for `HERE`, `TB`, `RTL` and `SIM` that the two `$(...)` references below expand to:

```make
TOPLEVEL_LANG       ?= verilog
COCOTB_TOPLEVEL     ?= counter          # the HDL module `dut` attaches to
COCOTB_TEST_MODULES ?= $(TB)            # the PYTHON module holding your tests
VERILOG_SOURCES     ?= $(RTL)

export PYTHONPATH := $(HERE):$(PYTHONPATH)

ifeq ($(SIM),icarus)
  COMPILE_ARGS += -g2012
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
```

Three of those lines are worth remembering because each has a failure mode you will meet:

- **`COCOTB_TEST_MODULES`** is `test_01_hello` — no `.py`, no path. cocotb *imports* it, which
  means it has to be on `PYTHONPATH`; that is what the `export` line is for. Get it wrong and
  you get `ModuleNotFoundError: No module named 'test_01_hello'` wrapped in twenty lines of
  `importlib` traceback.
- **`COMPILE_ARGS += -g2012`.** Icarus defaults to an older Verilog standard, and without this
  flag `logic`, `always_ff` and `always_comb` are all syntax errors — on lines that are
  perfectly good SystemVerilog.
- **`COCOTB_TEST_MODULES` used to be called `MODULE`**, and `COCOTB_TOPLEVEL` used to be
  `TOPLEVEL`. Both old names still work in 2.0.1 and warn. See
  [cocotb 2.x vs every tutorial you will find](guide/cocotb-2x-vs-every-tutorial.md), which is
  the page that will save you the most time in this course.

## Two dead ends that look official

A cocotb test file is a Python file full of `async def`s with a decorator on them. It looks
exactly like something you should be able to run directly, or hand to `pytest`. Both look
official. Neither works, and neither says so.

```bash
python3 test_01_hello.py
```

```
exit=0
```

**Zero bytes of output and a successful exit.** Python imported the module, defined the
function, and stopped — there is no simulator, so there is nothing to run against. Nothing is
wrong and nothing happened.

```bash
python3 -m pytest test_01_hello.py
```

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /work/labs/cocotb-intro
plugins: anyio-4.13.0
collected 0 items

============================ no tests ran in 0.03s =============================
```

Exit 5. `collected 0 items` — pytest is looking for functions named `test_*`, and cocotb tests
are named whatever you called them and marked with `@cocotb.test()`. (cocotb *does* have a
`pytest` integration, via `cocotb_tools.runner`, but it needs a Python file that builds and
launches the simulator. It is not "point pytest at the test file".)

**Reflex check:** a cocotb test only runs when a **simulator** runs it. If you did not see
`Running on Icarus Verilog version 14.0` and a `TESTS=` line, nothing was tested — whatever the
exit code said.

## Try this: break it on purpose

Delete the `Timer` line, so the test reads the counter at the instant of the clock edge:

```python
    await RisingEdge(dut.clk)
    assert dut.q.value == 1, f"after one enabled clock q is {dut.q.value}, expected 1"
```

**What you should see** — measured, not predicted:

```
    20.00ns WARNING  cocotb.Test counts_up.counts_up    after one enabled clock q is 00000000, expected 1
                                                        assert LogicArray('00000000', Range(7, 'downto', 0)) == 1
                                                         +  where LogicArray('00000000', Range(7, 'downto', 0)) = LogicArrayObject(counter.q).value
                                                         +    where LogicArrayObject(counter.q) = HierarchyObject(counter).q
                                                        Traceback (most recent call last):
                                                          File "/work/labs/cocotb-intro/test_norace.py", line 58, in counts_up
                                                            assert dut.q.value == 1, f"after one enabled clock q is {dut.q.value}, expected 1"
                                                        AssertionError: after one enabled clock q is 00000000, expected 1
    20.00ns WARNING  cocotb.regression                  test_norace.counts_up failed
```

Not a hang, not a crash — a wrong value, off by exactly one clock. `await RisingEdge(clk)`
returns *at* the edge, at the same instant the flip-flop is deciding what to become, and under
Icarus you get the old value. The next page measures both numbers side by side and gives you
three ways to stop losing that race.

Two things in that output are worth naming now, because they show up on every failure you will
ever read.

**The `assert ... +  where ...` lines are not part of your message.** They are pytest's
assertion rewriting, which cocotb 2.x enables: it takes your `assert` apart and shows what each
piece evaluated to. `LogicArrayObject(counter.q) = HierarchyObject(counter).q` is it telling you
where the value came from. Useful once you expect it, alarming the first time.

**`q is 00000000`, not `q is 0`.** `dut.q.value` is a `LogicArray`, and printing one gives you
the bit pattern, because a `LogicArray` can hold `X` and `Z` — states that have no integer at
all. `int(dut.q.value)` gives you `0`; on a signal that is partly `X` it raises
`ValueError: Can't convert LogicArray to int: it contains non-0/1 values`. Both behaviours are
correct and you want both.

**Why an engineer cares:** this is not a cocotb quirk, it is the difference between the
*value* on a wire and the value *after* the clock event, and it is the single most common
reason a first testbench reports numbers that are all correct but one cycle late.

Next: [Clocks, resets and triggers](guide/clocks-resets-and-triggers.md).
