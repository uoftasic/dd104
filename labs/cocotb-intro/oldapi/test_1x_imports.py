"""
DD104 — 1.x form #4: the imports that no longer resolve.

Two 1.x staples:

    from cocotb.binary import BinaryValue     # the module is gone entirely
    from cocotb.result import TestFailure     # the module survives, empty

They fail differently, and the difference is worth seeing.  `cocotb.binary`
fails with ModuleNotFoundError -- clear.  `cocotb.result` still imports, so
the error is an ImportError about a name, which reads like a typo and is not.

The 2.x replacements: `cocotb.types.LogicArray` for BinaryValue, and a plain
`assert` for TestFailure.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb
from cocotb.triggers import Timer

from cocotb.binary import BinaryValue     # ModuleNotFoundError, at IMPORT time
from cocotb.result import TestFailure     # (never reached)


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def never_runs(dut):
    await Timer(1, unit="ns")
