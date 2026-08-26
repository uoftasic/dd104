"""SELFTEST FIXTURE -- a testbench that blows up on every core it is given.

Not an example to copy.  This file exists so that `make selftest` can prove
the graders refuse it.  `total` is never defined, so every test raises
NameError on its first vector, on the good adder and on the broken one alike.

Expected verdict from lab-01/check.py:  FAIL, naming NameError.
"""

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def x01_crashes_on_the_first_vector(dut):
    dut.a.value = 3
    dut.b.value = 4
    dut.cin.value = 0
    await Timer(1, unit="ns")
    assert int(dut.sum.value) == total          # noqa: F821  -- deliberate
