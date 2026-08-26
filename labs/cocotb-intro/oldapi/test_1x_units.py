"""
DD104 — 1.x form #1: `units=`.  THE DANGEROUS ONE.

Every cocotb tutorial written before 2025 spells the time-unit argument
`units=`.  Here is the thing nobody tells you:

    IT STILL WORKS.

cocotb 2.0.1 accepts `units=`, does the right thing, and prints a
DeprecationWarning that scrolls past in a wall of INFO lines.  This test
PASSES.  Run it and read the warnings -- they are the whole point.

    make oldapi
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def the_old_spelling_still_runs(dut):
    # 1.x spelling. Works, warns.
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await Timer(20, units="ns")

    # 1.x value accessors. All three work, all three warn.
    dut.rst_n.value = 1
    dut.en.value    = 0
    dut.load.value  = 1
    dut.d.value     = 0x2A
    await Timer(20, units="ns")
    dut.load.value  = 0
    await Timer(1, units="ns")

    v = dut.q.value
    dut._log.info(f"v.integer = {v.integer}")   # deprecated -> use int(v) or v.to_unsigned()
    dut._log.info(f"v.binstr  = {v.binstr}")    # deprecated -> use str(v)

    assert v.integer == 0x2A
