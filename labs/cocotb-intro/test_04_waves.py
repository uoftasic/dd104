"""
DD104 — a run shaped for looking at, not for asserting on.

    make waves

This test asserts almost nothing.  Its job is to produce a waveform with two
clearly-labelled interesting moments in it, so that you have something real to
open in Surfer or GTKWave while you learn where the buttons are:

    * a stretch where the counter is PARKED at 0xFF with en low, and
    * the 0xFF -> 0x00 wrap one clock after en goes high again.

The first of those is the stretch where rtl/counter.sv and
rtl/counter_broken.sv look different -- and, deliberately, nothing this test
logs says so.  Nothing it asserts says so either.  It is visible only as a
picture, which is the entire point of the waveforms page.

Write the logged times down before you open the viewer.  Knowing where to
zoom to is the difference between reading a waveform and scrolling through
one.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
from cocotb.utils import get_sim_time


@cocotb.test()
async def a_wrap_worth_looking_at(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    dut.en.value    = 0
    dut.load.value  = 0
    dut.d.value     = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await Timer(1, unit="ns")
    dut._log.info(f"reset released at t = {get_sim_time('ns'):.0f} ns")

    # Count normally for a while, so there is some ordinary waveform to
    # compare the interesting part against.
    dut.en.value = 1
    await ClockCycles(dut.clk, 10)
    await Timer(1, unit="ns")
    dut._log.info(f"counted to 0x{int(dut.q.value):02X} at t = {get_sim_time('ns'):.0f} ns")

    # Park the counter exactly at 0xFF, with en LOW.
    dut.en.value   = 0
    dut.load.value = 1
    dut.d.value    = 0xFF
    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")
    dut.load.value = 0
    dut._log.info(f"loaded 0xFF at t = {get_sim_time('ns'):.0f} ns  <-- zoom here")

    # Sit still for three clocks.  The count is not moving, so it is not about
    # to wrap, so tc should be 0 for all of it.
    await ClockCycles(dut.clk, 3)
    await Timer(1, unit="ns")
    dut._log.info(f"held 3 clocks with en low, still 0x{int(dut.q.value):02X}, "
                  f"t = {get_sim_time('ns'):.0f} ns")

    # Now enable.  For exactly one clock the counter IS about to wrap.
    dut.en.value = 1
    await Timer(1, unit="ns")
    dut._log.info(f"en high again at t = {get_sim_time('ns'):.0f} ns; the wrap is the next edge")

    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")
    dut._log.info(f"wrapped to 0x{int(dut.q.value):02X} at t = {get_sim_time('ns'):.0f} ns")

    await ClockCycles(dut.clk, 5)
    await Timer(1, unit="ns")
    dut._log.info(f"finished at t = {get_sim_time('ns'):.0f} ns with q = "
                  f"0x{int(dut.q.value):02X}")

    # One assertion, so that this is still a test and not just a recording.
    # Note what it does NOT check: tc.  This test passes on the broken counter.
    assert int(dut.q.value) == 0x05, (
        f"q is 0x{int(dut.q.value):02X}, expected 0x05 "
        f"(0xFF wraps to 0x00, then five more clocks)")
