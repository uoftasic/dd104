# Clocks, resets and triggers

This page answers: *my test hangs, or reads the wrong value, or finishes instantly. What is
`await` actually waiting for?*

A cocotb test alternates between two states: running Python, and waiting for the simulator.
Simulated time only moves while you are waiting. Every bug on this page comes from being wrong
about which of the two you are doing.

All the output below was measured on `hpretl/iic-osic-tools:2026.08` (cocotb 2.0.1, Icarus
Verilog 14.0) by [`labs/cocotb-intro/test_02_triggers.py`](https://github.com/uoftasic/dd104/blob/main/labs/cocotb-intro/test_02_triggers.py):
six tests, 1832.51 ns of simulation, well under a second of real time. You'll run it in
[cocotb on a counter, Part 2](labs/cocotb-intro-overview.md#part-2-triggers).

## `Clock`, and the edge at t = 0

```python
cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
```

That line does three separate things:

| | |
|---|---|
| `Clock(dut.clk, 10, unit="ns")` | An object that describes a clock. It drives nothing. |
| `.start()` | A coroutine that toggles the signal forever. It still drives nothing, because a coroutine does not run until something runs it. |
| `cocotb.start_soon(...)` | Schedules that coroutine as a background task and returns immediately. |

The test checks that `start_soon` returns immediately:

```python
t_before = get_sim_time("ns")
cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
assert get_sim_time("ns") == t_before
```

> `unit=` matters. The default is `unit="step"`, and one step here is one picosecond. So
> `Clock(dut.clk, 10)` is a 10 picosecond clock. It runs without errors, and every timing number
> in your test is off by a factor of a thousand.

Now count ten clock edges from `t = 0`:

```
    90.00ns INFO  cocotb.counter  10 edges counted from t=0 took 90 ns (nine periods -- the edge at t=0 was free)
   190.00ns INFO  cocotb.counter  10 more edges, now starting on an edge: 100 ns
```

`Clock.start()` drives the signal high at t = 0 (`start_high=True` is the default). That first
`0`→`1` transition is a rising edge and takes no time, so ten edges from `t = 0` span nine
periods. Ten more, starting on an edge, span ten.

You don't need to work around this. Reset first: after a reset you are at a known phase and the
arithmetic stops surprising you.

## Reading at the clock edge

This is the race that costs everyone an hour, measured:

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

The flip-flop changes because of the edge, and your test wakes up because of the same edge. Your
test does not get to decide which happens first, and on Icarus 14.0 you see the old value.

From the outside, this failure does not raise and does not hang. It gives you values that are
all correct and one clock late, which looks exactly like a design that is one clock late, so you
go and read the RTL. That is why it takes an hour.

Three fixes, from crudest to best:

```python
await RisingEdge(dut.clk); await Timer(1, unit="ns")   # crude, obvious, fine
await RisingEdge(dut.clk); await ReadOnly()            # the scheduler's own settled phase
await FallingEdge(dut.clk)                             # sample mid-cycle, like real hardware
```

The third is what real hardware does, launching data on one edge and sampling it far from that
edge, and it needs no extra `await`. The labs use it.

If a testbench ever reports values that are all correct but one cycle out of step, add
`await Timer(1, unit="ns")` after the edge before changing anything else. If the numbers snap
into place, the bug was in the testbench.

## `Timer`: absolute time, no clock needed

```
   226.00ns INFO  cocotb.counter  Timer(1, unit='ns') advanced 1.0 ns
   226.50ns INFO  cocotb.counter  Timer(500, unit='ps') advanced 0.5 ns
  1226.50ns INFO  cocotb.counter  Timer(1, unit='us') advanced 1000.0 ns
```

That test does not start a clock; `Timer` doesn't need one. Use it for settle time, for modelling
a real-world delay, and for the reset experiment below.

Two errors worth meeting here first:

```
  1226.50ns INFO  cocotb.counter  Timer(0, unit='ns') -> ValueError: Timer argument time must be positive
  1226.50ns INFO  cocotb.counter  Timer(1, unit='s')  -> ValueError: Invalid unit (s) provided
```

The legal units are `"step"`, `"fs"`, `"ps"`, `"ns"`, `"us"`, `"ms"` and `"sec"`. Seconds are
spelled `sec`, not `s`.

## `ClockCycles`

```
  1336.50ns INFO  cocotb.counter  ClockCycles(clk, 5) from 1 ns past an edge: 49 ns
  1336.50ns INFO  cocotb.counter  ClockCycles(clk, 5) starting on an edge   : 50 ns
  1361.50ns INFO  cocotb.counter  ClockCycles(clk, 3, edge_type=FallingEdge): 25 ns
```

Five edges are five periods only if you started on an edge. From 1 ns past one, the first of the
five is only 9 ns away, so the total is 49.

`edge_type=FallingEdge` counts falling edges instead. (`ClockCycles(clk, n, rising=False)` also
works; it is the older spelling.)

## Reset

`rst_n` is active low and synchronous: it does nothing until a rising clock edge arrives. SimProc
uses the same convention, and you can test it in four lines instead of taking it on trust:

```python
dut.rst_n.value = 0            # asserted, but no clock edge yet
await Timer(3, unit="ns")      # a Timer moves time WITHOUT a clock edge
```

```
  1385.50ns INFO  cocotb.counter  rst_n low, no clock edge yet: q = 0x5A
  1392.50ns INFO  cocotb.counter  one rising edge later     : q = 0x00
```

`0x5A` survives three nanoseconds of asserted reset and is cleared on the first edge. If the
first line had printed `0x00`, this would be an asynchronous reset, which is a different circuit
with different rules about when reset may be released.

Reset style is hard to change late in a project and does not show up in a block diagram. Two
lines of testbench settle it, once per design.

This is the reset routine the labs use:

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

It drives every input, not just the interesting ones. An input you never drive stays `X`, the `X`
propagates, and you end up debugging a signal that has no value rather than a wrong one.

## Waiting for something that never happens

```python
await RisingEdge(dut.tc)
```

If `tc` never rises, this waits forever. A hung test is the worst failure there is: no message,
no line number, no traceback, and in CI a job that uses up its whole time budget before anyone
learns anything.

Either of these fixes it in one line:

```python
await with_timeout(RisingEdge(dut.tc), 200, "ns")     # raises SimTimeoutError
winner = await First(RisingEdge(dut.tc), Timer(200, unit="ns"))   # tells you which arrived
```

```
  1613.51ns INFO  cocotb.counter  with_timeout(RisingEdge(dut.tc), 200, 'ns') -> SimTimeoutError, as it should: en is low, so tc never rises
  1813.51ns INFO  cocotb.counter  First(RisingEdge(dut.tc), Timer(200, unit='ns')) -> the Timer won
  1832.51ns INFO  cocotb.counter  tc went high at t = 1833 ns with q = 0xFF
```

Use `with_timeout` when the event not arriving is a failure, and `First` when either outcome is
legitimate and you want to branch on it. There is also a whole-test version:

```python
@cocotb.test(timeout_time=50, timeout_unit="us")
async def something_that_might_hang(dut):
    ...
```

Put a timeout on any test that waits on a signal the design generates. In this course that
includes every SimProc test, since they all wait for `done`.

## Triggers

| Trigger | Wakes when |
|---|---|
| `Timer(n, unit=...)` | `n` units of simulated time have passed |
| `RisingEdge(sig)` / `FallingEdge(sig)` | That edge on a 1-bit signal |
| `Edge(sig)` / `ValueChange(sig)` | Any change |
| `ClockCycles(clk, n)` | `n` edges of `clk` |
| `First(a, b, ...)` | The first of several; returns the one that won |
| `Combine(a, b, ...)` | All of them |
| `with_timeout(trig, n, unit)` | `trig`, or `SimTimeoutError` |
| `ReadOnly()` | The settled phase of the current time step: values final, writes forbidden |
| `ReadWrite()` | The phase where writes are allowed |
| `NextTimeStep()` | The next time step, however far away |
| `Event()` | Another coroutine calls `.set()`, for tests that talk to each other |

Import them from `cocotb.triggers`. (`Join`, for waiting on a task you started, moved to
`cocotb.task` in 2.x. Importing it from `cocotb.triggers` still works and warns.)

## Check yourself

1. `Clock(dut.clk, 10)` with no `unit=`. What is the clock period?
2. You start on a rising edge and `await ClockCycles(dut.clk, 3)` with a 10 ns clock. How much
   simulated time passes? What if you started 2 ns after the edge?
3. Your test reads `q` right after `await RisingEdge(dut.clk)` and every value is one count
   behind. Name two ways to fix the testbench.

Next: [cocotb 2.x and older tutorials](guide/cocotb-2x-vs-every-tutorial.md).
