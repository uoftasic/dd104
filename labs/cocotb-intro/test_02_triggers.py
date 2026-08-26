"""
DD104 — clocks, resets and triggers.

Six tests, each isolating one thing about how a cocotb test moves through
simulated time.  Every number this file prints was measured on
hpretl/iic-osic-tools:2026.04 (cocotb 2.0.1, Icarus Verilog 14.0); the guide
page "Clocks, resets and triggers" quotes them.

    make triggers
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (RisingEdge, FallingEdge, ClockCycles, Timer,
                             First, with_timeout, SimTimeoutError)
from cocotb.utils import get_sim_time


async def reset(dut, cycles=2):
    """The reset routine every test below starts with.

    Drive every input to a known value, hold rst_n low across `cycles` rising
    edges, then release.  Returning after a Timer rather than an edge means
    the caller starts from a settled design, not from the middle of an edge.
    """
    dut.rst_n.value = 0
    dut.en.value    = 0
    dut.load.value  = 0
    dut.d.value     = 0
    await ClockCycles(dut.clk, cycles)
    dut.rst_n.value = 1
    await Timer(1, unit="ns")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  A clock is a task you start, not a setting you configure
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def a_clock_is_a_background_task(dut):
    """Time does not pass until something drives the clock -- and the first
    edge is free.

    Both halves of that sentence are measured here, and the second half is the
    one that will cost you an hour someday.
    """
    t_before = get_sim_time("ns")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # start_soon() schedules the clock and returns IMMEDIATELY.  No simulated
    # time has passed yet -- the clock will not run until this coroutine
    # awaits something and hands control back to the scheduler.
    assert get_sim_time("ns") == t_before, (
        "start_soon() advanced simulation time; it should not")

    # Clock.start() drives the signal HIGH at t=0 by default (start_high=True).
    # That first 0-to-1 transition is a rising edge, and it costs no time.  So
    # ten edges counted from t=0 span nine periods, not ten.
    await ClockCycles(dut.clk, 10)
    from_time_zero = get_sim_time("ns") - t_before
    dut._log.info(f"10 edges counted from t=0 took {from_time_zero:.0f} ns "
                  f"(nine periods -- the edge at t=0 was free)")
    assert from_time_zero == 90, (
        f"10 edges from t=0 took {from_time_zero} ns, expected 90")

    # From here we are sitting exactly on an edge, and ten more is a clean
    # ten periods.  This is why every test in this lab resets first: after a
    # reset you are at a known phase, and the arithmetic stops surprising you.
    t0 = get_sim_time("ns")
    await ClockCycles(dut.clk, 10)
    from_an_edge = get_sim_time("ns") - t0
    dut._log.info(f"10 more edges, now starting on an edge: {from_an_edge:.0f} ns")
    assert from_an_edge == 100, (
        f"10 edges starting on an edge took {from_an_edge} ns, expected 100")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  The read-after-the-edge race — the one that bites everybody
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def read_after_the_edge(dut):
    """`await RisingEdge(clk)` returns AT the edge, not after it.

    A flip-flop's output changes because of the edge.  cocotb wakes up
    because of the same edge.  Which of the two happens first is not
    something your test gets to decide, and under Icarus the answer is:
    cocotb sees the OLD value.

    This test does not assert that this is correct behaviour.  It measures
    what actually happens and prints both numbers, because a race you have
    watched with your own eyes is one you stop losing.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)
    dut.en.value = 1

    await RisingEdge(dut.clk)
    at_the_edge = str(dut.q.value)
    await Timer(1, unit="ns")
    one_ns_later = str(dut.q.value)

    dut._log.info(f"q read AT the rising edge : {at_the_edge}")
    dut._log.info(f"q read 1 ns after the edge: {one_ns_later}")

    assert at_the_edge != one_ns_later, (
        "the two reads agreed, so this simulator does not have the race this "
        "test is about -- which is worth knowing, but the guide page's "
        "numbers were measured on Icarus 14.0, where they differ")

    # The fix, for the rest of your life: put a small Timer after the edge,
    # or await ReadOnly(), or (best) sample on the opposite edge.
    await FallingEdge(dut.clk)
    dut._log.info(f"q read on the FALLING edge : {str(dut.q.value)} "
                  f"(settled, no Timer needed)")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Timer: absolute time, no clock involved
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def timer_is_absolute_time(dut):
    """Timer waits wall-clock-in-the-simulation, whatever the clock is doing.

    Note there is NO clock started in this test.  Timer does not need one.
    """
    for amount, unit, expect_ns in [(1, "ns", 1.0), (500, "ps", 0.5),
                                    (1, "us", 1000.0)]:
        t0 = get_sim_time("ns")
        await Timer(amount, unit=unit)
        got = get_sim_time("ns") - t0
        dut._log.info(f"Timer({amount}, unit={unit!r}) advanced {got} ns")
        assert got == expect_ns, f"Timer({amount},{unit}) advanced {got} ns, expected {expect_ns}"

    # Two things about Timer that are worth finding out here rather than at
    # 1 a.m.:  Timer(0) is an error, and the unit is spelled "sec", not "s".
    try:
        Timer(0, unit="ns")
        raise AssertionError("Timer(0) was accepted; it should not be")
    except ValueError as e:
        dut._log.info(f"Timer(0, unit='ns') -> ValueError: {e}")

    try:
        Timer(1, unit="s")
        raise AssertionError("unit='s' was accepted; it should not be")
    except ValueError as e:
        dut._log.info(f"Timer(1, unit='s')  -> ValueError: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  ClockCycles counts edges, and it counts them from where you are
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def clockcycles_counts_edges(dut):
    """ClockCycles(clk, n) is n edges, which is n periods only if you are
    already sitting on an edge when you call it."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    # We are 1 ns past an edge here (reset() ends with Timer(1, unit="ns")),
    # so the first of the five edges is only 9 ns away.
    t0 = get_sim_time("ns")
    await ClockCycles(dut.clk, 5)
    from_mid_period = get_sim_time("ns") - t0

    # Now we ARE on an edge, so five more edges is a clean 50 ns.
    t0 = get_sim_time("ns")
    await ClockCycles(dut.clk, 5)
    from_an_edge = get_sim_time("ns") - t0

    dut._log.info(f"ClockCycles(clk, 5) from 1 ns past an edge: {from_mid_period:.0f} ns")
    dut._log.info(f"ClockCycles(clk, 5) starting on an edge   : {from_an_edge:.0f} ns")

    assert from_mid_period == 49, f"expected 49 ns, got {from_mid_period}"
    assert from_an_edge == 50, f"expected 50 ns, got {from_an_edge}"

    # Falling edges instead, for a design you want to sample mid-cycle:
    t0 = get_sim_time("ns")
    await ClockCycles(dut.clk, 3, edge_type=FallingEdge)
    dut._log.info(f"ClockCycles(clk, 3, edge_type=FallingEdge): "
                  f"{get_sim_time('ns') - t0:.0f} ns")


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Reset is a protocol, and this design's is synchronous
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def reset_needs_an_edge(dut):
    """Proving, rather than assuming, that rst_n does nothing without a clock.

    Load the counter with 0x5A, then drive rst_n low and DO NOT clock it.
    The count stays 0x5A.  One edge later it is 0x00.

    This is the single most useful habit in this file: when the datasheet says
    "synchronous reset", write the two-line experiment that shows it, once, and
    then you know instead of assuming.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    dut.load.value = 1
    dut.d.value    = 0x5A
    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")
    dut.load.value = 0
    assert dut.q.value == 0x5A, f"load did not take: q is {dut.q.value}"

    dut.rst_n.value = 0            # asserted, but no edge yet
    await Timer(3, unit="ns")      # a Timer moves time WITHOUT a clock edge
    held = int(dut.q.value)
    dut._log.info(f"rst_n low, no clock edge yet: q = 0x{held:02X}")
    assert held == 0x5A, (
        f"q changed to 0x{held:02X} with rst_n low and no clock edge -- "
        f"that would make this an ASYNCHRONOUS reset, and it is not")

    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")
    dut._log.info(f"one rising edge later     : q = 0x{int(dut.q.value):02X}")
    assert dut.q.value == 0, f"after one clocked reset q is {dut.q.value}, expected 0"

    dut.rst_n.value = 1


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Waiting for something that might never happen
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def a_wait_that_cannot_hang(dut):
    """`await RisingEdge(dut.tc)` on a signal that never rises hangs forever.

    A hung test is the worst failure mode there is: no message, no line
    number, and in CI, a job that burns its whole time budget.  Both fixes
    are one line.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    # en is 0, so tc can never rise. with_timeout turns "hangs forever" into
    # an exception with a name.
    try:
        await with_timeout(RisingEdge(dut.tc), 200, "ns")
        raise AssertionError("tc rose with en low -- it cannot")
    except SimTimeoutError:
        dut._log.info("with_timeout(RisingEdge(dut.tc), 200, 'ns') -> SimTimeoutError, "
                      "as it should: en is low, so tc never rises")

    # First() is the other shape: race the thing you want against a deadline
    # and find out which one arrived.
    deadline = Timer(200, unit="ns")
    winner = await First(RisingEdge(dut.tc), deadline)
    assert winner is deadline, "tc rose with en low -- it cannot"
    dut._log.info("First(RisingEdge(dut.tc), Timer(200, unit='ns')) -> the Timer won")

    # And now make tc actually happen, so the test proves the trigger works
    # and not just that the timeout does.
    dut.load.value = 1
    dut.d.value    = 0xFE
    await ClockCycles(dut.clk, 1)
    dut.load.value = 0
    dut.en.value   = 1
    await with_timeout(RisingEdge(dut.tc), 200, "ns")
    dut._log.info(f"tc went high at t = {get_sim_time('ns'):.0f} ns with q = "
                  f"0x{int(dut.q.value):02X}")
