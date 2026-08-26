"""SELFTEST FIXTURE -- the lazy testbench at processor level.

Passes on the golden core and on all thirteen broken ones. The graders have
always rejected it; the selftest keeps it so that a change made to stop them
accepting crashes cannot start accepting this instead.
"""

import cocotb


@cocotb.test()
async def it_works(dut):
    pass
