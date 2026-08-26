"""SELFTEST FIXTURE -- the shape of the bug this course shipped.

Not an example to copy.  This testbench is correct right up until it finds
something wrong, and then the code that builds the failure message raises
NameError.  So it PASSES on the good adder and CRASHES on the broken one,
which the old graders read as `caught` and printed VERDICT: PASS for.

Expected verdict from lab-01/check.py:  FAIL, naming NameError, and saying
that a crash is not a caught bug.
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
async def x02_exhaustive_with_a_broken_failure_path(dut):
    bad = []
    checked = 0
    for cin in range(2):
        for a in range(16):
            for b in range(16):
                s, c = await apply(dut, a, b, cin)
                checked += 1
                if ((c << 4) | s) != a + b + cin:
                    bad.append((a, b, cin))

    dut._log.info(f"checked {checked} of the 512 possible input vectors")

    if bad:
        # `summary` was never assigned. On the good adder this line is never
        # reached; on the broken one it is the only thing that happens.
        raise AssertionError(f"{len(bad)} of {checked} wrong: {summary}")   # noqa: F821
