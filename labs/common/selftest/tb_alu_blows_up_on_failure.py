"""SELFTEST FIXTURE -- the exact testbench that produced `3 of 3 ALU bugs
caught` from a grader that could not tell a crash from a catch.

Not an example to copy.  Values and flags are compared correctly; the code
that builds the failure message refers to `value_per_op`, which was never
assigned.  So it passes the golden ALU (nothing mismatches, the message is
never built) and raises NameError on B01, B02 and B03 alike.

Expected verdict from lab-03/check.py:  FAIL / NO COUNT, naming NameError.
"""

import cocotb
from cocotb.triggers import Timer

ADD, SUB, OR, NAND, SHL, SHR = 0, 1, 2, 3, 4, 5
OPS = {ADD: "ADD", SUB: "SUB", OR: "OR", NAND: "NAND", SHL: "SHL", SHR: "SHR"}


def spec(op, a, b):
    if op == ADD:
        out = (a + b) & 0xFF
    elif op == SUB:
        out = (a - b) & 0xFF
    elif op == OR:
        out = a | b
    elif op == NAND:
        out = (~(a & b)) & 0xFF
    elif op == SHL:
        out = (a << (b & 3)) & 0xFF
    elif op == SHR:
        out = a >> (b & 3)
    else:
        out = 0
    return out, (out >> 7) & 1, int(out == 0)


async def alu(dut, op, a, b):
    dut.ALUop.value = op
    dut.A.value = a
    dut.B.value = b
    await Timer(1, unit="ns")
    return int(dut.ALUout.value), int(dut.N.value), int(dut.Z.value)


@cocotb.test()
async def x01_every_vector_with_a_broken_failure_path(dut):
    bad_values, bad_flags, checked = [], [], 0
    for op in OPS:
        for a in range(256):
            for b in range(256):
                got = await alu(dut, op, a, b)
                want = spec(op, a, b)
                checked += 1
                if got[0] != want[0]:
                    bad_values.append((op, a, b))
                if got[1:] != want[1:]:
                    bad_flags.append((op, a, b))

    dut._log.info(f"{checked} vectors checked, {len(bad_values)} value "
                  f"mismatches, {len(bad_flags)} flag mismatches")

    if bad_values or bad_flags:
        raise AssertionError(
            f"{len(bad_values)} value mismatches {value_per_op}, "        # noqa: F821
            f"{len(bad_flags)} flag mismatches.")
