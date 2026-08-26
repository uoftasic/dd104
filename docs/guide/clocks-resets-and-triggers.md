# Clocks, resets and triggers

**Question this page answers:** *My test hangs / reads the wrong value / finishes instantly.
What is `await` actually waiting for?*

A cocotb test is a coroutine that alternates between two states: **running Python** and
**waiting for the simulator**. Simulated time only moves while you are waiting. Every bug on
this page is a version of one mistake — being wrong about which of those two things you are
doing.

Everything here is measured on `hpretl/iic-osic-tools:2026.04` (cocotb 2.0.1, Icarus Verilog
14.0) by [`labs/cocotb-intro/test_02_triggers.py`](https://github.com/uoftasic/dd104/blob/main/labs/cocotb-intro/test_02_triggers.py):

```bash
cd labs/cocotb-intro
make triggers
```

Six tests, six PASS, 1832.51 ns of simulation, well under a second of your time.

## `Clock` — and the edge that is free

```python
cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
```

Three separate things, and it is worth being able to name them:

| | |
|---|---|
| `Clock(dut.clk, 10, unit="ns")` | an object that *describes* a clock. Drives nothing. |
| `.start()` | a coroutine that toggles the signal forever. Still drives nothing — coroutines do not run until something runs them. |
| `cocotb.start_soon(...)` | schedules that coroutine as a background task and returns **immediately** |

`start_soon` returning immediately is checkable, and the test checks it:

```python
t_before = get_sim_time("ns")
cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
assert get_sim_time("ns") == t_before
```

> **`unit=` is not optional decoration.** The default is `unit="step"`, and one step here is
> one picosecond. `Clock(dut.clk, 10)` is a 10 **picosecond** clock — it runs, nothing errors,
> and every timing number in your test is off by a factor of a thousand.

Now the part that surprises people. Ten clock edges, counted from `t = 0`:

```
    90.00ns INFO  cocotb.counter  10 edges counted from t=0 took 90 ns (nine periods -- the edge at t=0 was free)
   190.00ns INFO  cocotb.counter  10 more edges, now starting on an edge: 100 ns
```

`Clock.start()` drives the signal **high at t = 0** (`start_high=True` is the default). That
first `0`→`1` transition is a rising edge and it costs no time, so ten edges from `t = 0` span
**nine** periods. Ten more, now that you are sitting on an edge, span a clean ten.

This is not a bug to work around — it is a reason to **reset first**. After a reset you are at a
known phase, and the arithmetic stops surprising you.

## The read-after-the-edge race

This is the one that costs everybody an hour, so here it is measured rather than described:

```python
await RisingEdge(dut.clk)
at_the_edge = str(dut.q.value)
await Timer(1, unit="ns")
one_ns_later = str(dut.q.value)
```

```
   221.00ns INFO  cocotb.counter  q read AT the rising edge : 00000000
   221.00ns INFO  cocotb.counter  q read 1 ns after the edge: 00000001
   225.00ns INFO  cocotb.counter  q read on the FALLING edge : 00000001 (settled, no Timer needed)
```

The flip-flop changes **because of** the edge. Your test wakes up **because of** the same edge.
Which happens first is not something your test gets to decide, and on Icarus 14.0 the answer is:
you see the old value.

Notice what this failure mode looks like from the outside. It does not raise. It does not hang.
It gives you *consistently correct values, one clock late* — which reads exactly like a design
that is one clock late, so you go and look at the RTL. That is why it costs an hour.

Three fixes, in increasing order of how much you should like them:

```python
await RisingEdge(dut.clk); await Timer(1, unit="ns")   # crude, obvious, fine
await RisingEdge(dut.clk); await ReadOnly()            # the scheduler's own settled phase
await FallingEdge(dut.clk)                             # sample mid-cycle, like real hardware
```

The third is what a real chip does — data is launched on one edge and sampled far from it — and
it needs no extra `await` at all. It is also what the labs use.

**Reflex check:** any time a testbench reports values that are all correct but one cycle out of
step, delete nothing and add `await Timer(1, unit="ns")` after the edge. If the numbers snap
into place, the bug was in the testbench.

## `Timer` — absolute time, no clock required

```
   226.00ns INFO  cocotb.counter  Timer(1, unit='ns') advanced 1.0 ns
   226.50ns INFO  cocotb.counter  Timer(500, unit='ps') advanced 0.5 ns
  1226.50ns INFO  cocotb.counter  Timer(1, unit='us') advanced 1000.0 ns
```

`Timer` needs no clock. That test does not start one. Use it for settle time, for modelling a
real-world delay, and for the experiment further down that proves a reset is synchronous.

Two things it is better to find out here than at 1 a.m.:

```
  1226.50ns INFO  cocotb.counter  Timer(0, unit='ns') -> ValueError: Timer argument time must be positive
  1226.50ns INFO  cocotb.counter  Timer(1, unit='s')  -> ValueError: Invalid unit (s) provided
```

The legal units are `"step"`, `"fs"`, `"ps"`, `"ns"`, `"us"`, `"ms"`, `"sec"`. **Seconds are
spelled `sec`, not `s`.**

## `ClockCycles` — it counts edges, from wherever you are

```
  1336.50ns INFO  cocotb.counter  ClockCycles(clk, 5) from 1 ns past an edge: 49 ns
  1336.50ns INFO  cocotb.counter  ClockCycles(clk, 5) starting on an edge   : 50 ns
  1361.50ns INFO  cocotb.counter  ClockCycles(clk, 3, edge_type=FallingEdge): 25 ns
```

Five edges is five *periods* only if you were on an edge when you asked. One nanosecond past
one, the first of the five is only 9 ns away, and the total is 49.

`edge_type=FallingEdge` counts the other kind. (`ClockCycles(clk, n, rising=False)` also works
and is the older spelling.)

## Reset is a protocol, and this one is synchronous

`rst_n` is **active low** and **synchronous** — it does nothing at all until a rising clock edge
arrives. That is SimProc's convention too, and it is a claim you can test in four lines instead
of believing:

```python
dut.rst_n.value = 0            # asserted, but no clock edge yet
await Timer(3, unit="ns")      # a Timer moves time WITHOUT a clock edge
```

```
  1385.50ns INFO  cocotb.counter  rst_n low, no clock edge yet: q = 0x5A
  1392.50ns INFO  cocotb.counter  one rising edge later     : q = 0x00
```

`0x5A` survives three nanoseconds of asserted reset, and dies on the first edge. If the first
line had printed `0x00`, this would be an **asynchronous** reset — a different circuit, with
different rules about when it may be released.

**Why an engineer cares:** reset style is one of the few things that is genuinely hard to change
late, and it is invisible in a block diagram. Two lines of testbench settle it, and you only
have to do it once per design.

The reset routine the labs use, in full:

```python
async def reset(dut, cycles=2):
    dut.rst_n.value = 0
    dut.en.value    = 0
    dut.load.value  = 0
    dut.d.value     = 0
    await ClockCycles(dut.clk, cycles)
    dut.rst_n.value = 1
    await Timer(1, unit="ns")
```

Driving **every** input, not just the interesting ones, is the point. An input you never drive
stays `X`, `X` propagates, and you end up debugging a signal that has no value rather than the
wrong one.

## The wait that hangs forever

```python
await RisingEdge(dut.tc)
```

If `tc` never rises, this waits for the heat death of the universe. A hung test is the worst
failure there is: no message, no line number, no traceback, and in CI a job that burns its
entire time budget before anyone learns anything.

Both fixes are one line:

```python
await with_timeout(RisingEdge(dut.tc), 200, "ns")     # raises SimTimeoutError
winner = await First(RisingEdge(dut.tc), Timer(200, unit="ns"))   # tells you which arrived
```

```
  1613.51ns INFO  cocotb.counter  with_timeout(RisingEdge(dut.tc), 200, 'ns') -> SimTimeoutError, as it should: en is low, so tc never rises
  1813.51ns INFO  cocotb.counter  First(RisingEdge(dut.tc), Timer(200, unit='ns')) -> the Timer won
  1832.51ns INFO  cocotb.counter  tc went high at t = 1833 ns with q = 0xFF
```

`with_timeout` when *not arriving* is a failure. `First` when either outcome is legitimate and
you want to branch on it. There is also a whole-test version:

```python
@cocotb.test(timeout_time=50, timeout_unit="us")
async def something_that_might_hang(dut):
    ...
```

**Put a timeout on any test that waits on a design-generated signal.** In this course that means
every SimProc test that waits for `done` — which is every SimProc test.

## The trigger list, complete enough

| trigger | wakes when |
|---|---|
| `Timer(n, unit=...)` | `n` units of simulated time have passed |
| `RisingEdge(sig)` / `FallingEdge(sig)` | that edge on a 1-bit signal |
| `Edge(sig)` / `ValueChange(sig)` | any change |
| `ClockCycles(clk, n)` | `n` edges of `clk` |
| `First(a, b, ...)` | the first of several; returns the one that won |
| `Combine(a, b, ...)` | all of them |
| `with_timeout(trig, n, unit)` | `trig`, or `SimTimeoutError` |
| `ReadOnly()` | the settled phase of the current time step — values final, writes forbidden |
| `ReadWrite()` | the phase where writes are allowed |
| `NextTimeStep()` | the next time step, however far away |
| `Event()` | another coroutine calls `.set()` — for tests that talk to each other |

Import them from `cocotb.triggers`. (`Join`, for waiting on a task you started, moved to
`cocotb.task` in 2.x — importing it from `cocotb.triggers` still works and warns.)

Next: [cocotb 2.x vs every tutorial you will find](guide/cocotb-2x-vs-every-tutorial.md) — read
this one before you search the web for anything, not after.
