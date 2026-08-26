"""SELFTEST FIXTURE -- Lab 01 Step 3 with only the FIRST half of the TODO done.

`cin` is swept, so all 512 vectors are driven on the good adder and the broken
adder does go red.  But the assert is still inside the loop, so the run stops
at the first wrong vector and the failure is an anecdote instead of the count
`256 of 512` that Step 4 is entirely about.

This was the second false PASS: the old grader printed
`VERDICT: PASS ... That is a test worth committing`.

Expected verdict from lab-01/check.py:  FAIL -- the second half of the TODO
is not done.
"""

import cocotb
from cocotb.triggers import Timer


async def apply(dut, a, b, cin):
    dut.a.value = a
    dut.b.value = b
    dut.cin.value = cin
    await Timer(1, unit="ns")
    return int(dut.sum.value), int(dut.cout.value)


@cocotb.test()
async def x04_swept_but_stops_at_the_first_bad_vector(dut):
    checked = 0
    for cin in range(2):
        for a in range(16):
            for b in range(16):
                s, c = await apply(dut, a, b, cin)
                got = (c << 4) | s
                want = a + b + cin
                assert got == want, f"{a} + {b} + {cin} gave {got}, expected {want}"
                checked += 1
    dut._log.info(f"checked {checked} of the 512 possible input vectors")
