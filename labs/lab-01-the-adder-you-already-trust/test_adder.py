"""
DD104 Lab 01 — a testbench for the adder you already trust.

    make sim      run these tests against the good adder   -> they pass
    make check    run them against a broken one            -> they have to FAIL

This file ships working.  `make sim` is green before you touch anything, and
`make check` is not, and closing that gap is the lab.

────────────────────────────────────────────────────────────────────────────
cocotb 2.x, and why the internet will lie to you about it
────────────────────────────────────────────────────────────────────────────
The workbench has cocotb 2.0.1.  Almost every cocotb tutorial you will find is
written for 1.x, and two of the renames bite immediately:

    Timer(1, unit="ns")          2.x.   1.x said units=  (plural)
    COCOTB_TEST_MODULES=...      2.x.   1.x said MODULE=

`units=` still runs in 2.0.1 and prints a DeprecationWarning.  `MODULE=` is
worse: cocotb finds no tests, runs nothing, reports TESTS=0 and exits 0.  A
green run that tested nothing is the exact failure this course is about, and
you can cause it with an environment variable.
"""

import cocotb
from cocotb.triggers import Timer


async def apply(dut, a, b, cin):
    """Drive one input vector, let the combinational logic settle, read it back.

    There is no clock in this design.  `Timer(1, unit="ns")` is the whole of
    the timing model: change the inputs, let simulated time move forward by
    1 ns so the assignments propagate, then sample.  Sampling without that
    Timer reads the value from *before* your assignment.
    """
    dut.a.value = a
    dut.b.value = b
    dut.cin.value = cin
    await Timer(1, unit="ns")
    return int(dut.sum.value), int(dut.cout.value)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  The six cases you would write by hand
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t01_the_obvious_six(dut):
    """Six vectors, picked the way a person picks them.

    Zero, one, a middling pair, a carry between slices, the top of the range,
    and the wrap.  It is a reasonable list.  Note what every entry in it has
    in common — that is the thing worth noticing in this lab, and it is not
    hidden, it is in the third column."""
    cases = [
        # a,  b,  cin
        (0,  0,  0),
        (1,  1,  0),
        (2,  3,  0),
        (7,  8,  0),
        (15, 0,  0),
        (15, 1,  0),
    ]
    for a, b, cin in cases:
        s, c = await apply(dut, a, b, cin)
        got = (c << 4) | s
        want = a + b + cin
        assert got == want, (
            f"{a} + {b} + {cin} gave cout={c} sum={s} (that is {got}), "
            f"expected {want}")

    dut._log.info(f"{len(cases)} hand-picked vectors, all correct")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Exhaustive.  Nearly.
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t02_every_a_and_every_b(dut):
    """Every value of a against every value of b.  256 vectors.

    This is a real improvement on six cases and it is worth running.  It is
    also still not exhaustive, and `make check` will tell you so.

    ── TODO ──────────────────────────────────────────────────────────────────
    The port list is `a`, `b`, `cin` — three inputs, 4 + 4 + 1 = 9 bits, so
    2**9 = 512 possible input vectors.  This loop covers 256 of them.

    Add the third loop.  The shape you want is:

        for cin in range(2):
            for a in range(16):
                for b in range(16):
                    ...

    and count your vectors afterwards, because the count is the result:
    a `checked` of 512 means you have covered the whole input space of this
    design and no bug in it can hide from you.  A `checked` of 256 means half
    the input space has never been driven at all.

    Second change, and it is the one that turns a failing test into a
    diagnosis: do not `assert` on the first bad vector.  Collect the bad ones
    in a list, run all 512, and assert at the end with `len(bad)` in the
    message.  "It is wrong" tells you to start looking.  "256 of 512 are
    wrong" tells you the bug tracks an input that is high exactly half the
    time, and there is only one such input on this module.
    ──────────────────────────────────────────────────────────────────────────
    """
    checked = 0
    for a in range(16):
        for b in range(16):
            cin = 0
            s, c = await apply(dut, a, b, cin)
            got = (c << 4) | s
            want = a + b + cin
            assert got == want, (
                f"{a} + {b} + {cin} gave cout={c} sum={s} (that is {got}), "
                f"expected {want}")
            checked += 1

    # The count is the result.  Print it, look at it, and compare it with 512.
    dut._log.info(f"checked {checked} of the 512 possible input vectors")
