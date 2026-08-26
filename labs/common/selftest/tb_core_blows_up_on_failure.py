"""SELFTEST FIXTURE -- the same shape, at processor level.

Not an example to copy.  Drives a short program, compares the registers, and
builds its failure message out of `diagnosis`, which was never assigned. So it
passes the golden core and raises NameError on every broken one.

Expected verdict from common/check.py and from every hunt.py:  FAIL, with the
row marked BROKEN and the exception named.
"""

import cocotb

from simproc import SimProc
from simproc_asm import ADD, SUB, NAND, set_reg


@cocotb.test()
async def x01_alu_values_with_a_broken_failure_path(dut):
    sp = SimProc(dut)
    await sp.start()

    prog = set_reg(1, 200) + set_reg(2, 60) + [ADD(1, 2), SUB(1, 2), NAND(1, 2)]
    await sp.run(prog)

    got = sp.regs()
    want = (60, 247, 60, 0)
    if got != want:
        raise AssertionError(f"registers are {got}, expected {want}: "
                             f"{diagnosis}")                        # noqa: F821
