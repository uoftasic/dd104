"""
DD104 Lab 01 — a reference solution.

Do not open this before you have your own `make check` verdict.  It is four
lines different from the file you were given and the four lines are not the
interesting part; what they buy you is.

    cp solutions/test_adder.py test_solution.py
    make check TB=test_solution
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
async def t01_the_obvious_six(dut):
    """Kept, unchanged, on purpose.

    It is a weak test and it stays in the file.  It runs in 6 ns, it is the
    first thing that goes red when the module is truly broken, and reading six
    named cases is how a reviewer works out what the module is supposed to do.
    A fast weak test and a slow strong test are not competing."""
    cases = [(0, 0, 0), (1, 1, 0), (2, 3, 0), (7, 8, 0), (15, 0, 0), (15, 1, 0)]
    for a, b, cin in cases:
        s, c = await apply(dut, a, b, cin)
        got = (c << 4) | s
        want = a + b + cin
        assert got == want, (
            f"{a} + {b} + {cin} gave cout={c} sum={s} (that is {got}), "
            f"expected {want}")
    dut._log.info(f"{len(cases)} hand-picked vectors, all correct")


@cocotb.test()
async def t02_exhaustive(dut):
    """All 512 input vectors, and a failure message that is a diagnosis.

    Two changes from the shipped version:

    1.  `cin` is swept.  4 + 4 + 1 = 9 bits of input, 2**9 = 512 vectors, and
        this design is small enough that you can simply try all of them.  Most
        designs are not — an 8-bit ALU with a 3-bit opcode is 2**19 = 524,288
        and still fine, an 8-bit multiplier pair is 65,536 and fine, a 32-bit
        adder is 2**65 and never happening.  When exhaustive fits, take it.

    2.  Failures are collected instead of raised.  The first bad vector tells
        you there is a bug; all 256 of them tell you which one.  Exactly half
        of the input space failing means the failure tracks a signal that is
        high in exactly half the vectors, and `cin` is the only such signal on
        this module.  That sentence is written before ever opening the RTL."""
    bad = []
    checked = 0
    for cin in range(2):
        for a in range(16):
            for b in range(16):
                s, c = await apply(dut, a, b, cin)
                got = (c << 4) | s
                want = a + b + cin
                checked += 1
                if got != want:
                    bad.append((a, b, cin, got, want))

    dut._log.info(f"checked {checked} of the 512 possible input vectors, "
                  f"{len(bad)} wrong")

    if bad:
        first = ", ".join(f"{a}+{b}+{c}={g} (want {w})" for a, b, c, g, w in bad[:5])
        raise AssertionError(
            f"{len(bad)} of {checked} vectors are wrong. First five: {first}.\n"
            f"  {len(bad)}/{checked} is exactly half the input space, so the "
            f"failure tracks an input that is high in half the vectors.\n"
            f"  Every wrong vector above has cin=1 and every one is short by "
            f"exactly 1: the carry-in is not reaching the adder.")
