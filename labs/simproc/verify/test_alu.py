"""All 6 ALU ops x 256 x 256 = 393,216 vectors against a spec model.

No processor, no UART, no program.  Drive A, B and ALUop; read ALUout, N, Z.
This is the whole of Lab 1's argument: three of the shipped bugs live entirely
inside this module, and a unit test finds them in about twenty seconds without
knowing that a processor exists.

The spec model is the ALU as specified, not as implemented -- 8-bit wrap, and a
shift amount taken from B[1:0], because that is all the SHIFT instruction can
encode.
"""
import cocotb
from cocotb.triggers import Timer

ADD, SUB, OR, NAND, SHL, SHR = range(6)
NAMES = ["ADD", "SUB", "OR", "NAND", "SHL", "SHR"]


def spec(op, a, b):
    if op == ADD:
        r = (a + b) & 0xFF
    elif op == SUB:
        r = (a - b) & 0xFF
    elif op == OR:
        r = (a | b) & 0xFF
    elif op == NAND:
        r = (~(a & b)) & 0xFF
    elif op == SHL:
        r = (a << (b & 3)) & 0xFF
    else:
        r = (a >> (b & 3)) & 0xFF
    return r, (r >> 7) & 1, int(r == 0)


@cocotb.test()
async def exhaustive(dut):
    total = 0
    bad_value = [0] * 6
    bad_flag = [0] * 6
    for op in range(6):
        for a in range(256):
            for b in range(256):
                dut.ALUop.value = op
                dut.A.value = a
                dut.B.value = b
                await Timer(1, unit="ns")
                total += 1
                want = spec(op, a, b)
                got = (int(dut.ALUout.value), int(dut.N.value), int(dut.Z.value))
                if got[0] != want[0]:
                    bad_value[op] += 1
                if got[1:] != want[1:]:
                    bad_flag[op] += 1
    dut._log.info(f"ALU vectors={total}")
    for op in range(6):
        dut._log.info(f"ALU {NAMES[op]:4s} value_mismatch={bad_value[op]:6d} "
                      f"flag_mismatch={bad_flag[op]:6d}")
    assert not any(bad_value) and not any(bad_flag), (
        "ALU disagrees with the spec on "
        f"{sum(bad_value)} values and {sum(bad_flag)} flag pairs")
