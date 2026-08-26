"""
DD104 — your first cocotb test.

One test against rtl/counter.sv.  Run it:

    make hello

Everything here is cocotb 2.0.1 syntax.  If a tutorial you found says `units=`
or `cocotb.fork`, it was written for cocotb 1.x.  Some of it still runs here
(with a warning), some of it does not run at all — `make oldapi` shows you
exactly which, and the guide page "cocotb 2.x vs every tutorial you will find"
explains why.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def counts_up(dut):
    """Reset the counter, let it count once, and check that it did."""

    # 1. A clock.  Clock(...) describes one; .start() is a coroutine that
    #    drives it forever; start_soon() runs that coroutine in the
    #    background.  Without this line nothing in the design ever moves.
    #
    #    `unit="ns"` is not optional decoration.  The default is
    #    unit="step" — Clock(dut.clk, 10) is a 10-simulator-step clock,
    #    which here is 10 picoseconds, not 10 nanoseconds.
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # 2. Reset.  rst_n is ACTIVE LOW and SYNCHRONOUS: driving it low does
    #    nothing at all until a rising clock edge arrives.
    dut.rst_n.value = 0
    dut.en.value    = 0
    dut.load.value  = 0
    dut.d.value     = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    assert dut.q.value == 0, f"after reset q is {dut.q.value}, expected 0"

    # 3. Release reset and enable counting.
    dut.rst_n.value = 1
    dut.en.value    = 1

    # 4. One clock edge, then a pause before reading.
    #
    #    The pause is the part everyone leaves out.  `await RisingEdge(clk)`
    #    returns AT the edge, at the same instant the flip-flop inside the
    #    counter is deciding what to become — so `dut.q.value` here is still
    #    the OLD value.  Measured, in this exact design: reading straight
    #    after the edge gives 00000000; reading 1 ns later gives 00000001.
    #    test_02_triggers.py prints both, side by side.
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert dut.q.value == 1, f"after one enabled clock q is {dut.q.value}, expected 1"

    dut._log.info(f"q = {int(dut.q.value)} after one enabled clock. That is the whole test.")
