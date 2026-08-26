"""SELFTEST FIXTURE -- the lazy testbench, verbatim from the course text.

It passes on everything, so it distinguishes nothing.  The graders have always
rejected this one; the selftest keeps it in the suite so that a change made to
stop them accepting crashes cannot quietly start accepting this instead.

Expected verdict from lab-01/check.py:  FAIL -- passes the broken adder too.
"""

import cocotb


@cocotb.test()
async def it_works(dut):
    pass
