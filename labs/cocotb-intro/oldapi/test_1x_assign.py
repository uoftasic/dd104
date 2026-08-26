"""
DD104 — 1.x form #3: the `<=` assignment operator.

1.x let you write a signal the way Verilog does:

    dut.d <= 0x2A

2.x removed it.  Signals are written with `.value`:

    dut.d.value = 0x2A

The failure is a plain Python TypeError about `<=`, which is a confusing thing
to read if you did not know `<=` had ever been an assignment.  Read it once
here and you will recognise it forever.
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
async def le_is_not_assignment_any_more(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n <= 1          # TypeError
    await Timer(10, unit="ns")
