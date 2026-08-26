"""
DD104 — 1.x form #2: `cocotb.fork`.  This one is simply gone.

1.x tutorials start a clock like this:

    cocotb.fork(Clock(dut.clk, 10, units="ns").start())

In 2.x the function does not exist.  The replacement is `cocotb.start_soon`,
which takes the same argument and returns the same kind of Task.

Run this and read the traceback -- the error names the missing attribute, so
it is one of the easier 1.x failures to recognise.
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
async def fork_is_gone(dut):
    cocotb.fork(Clock(dut.clk, 10, unit="ns").start())   # AttributeError
    await Timer(10, unit="ns")
