"""SELFTEST FIXTURE -- the crash-instead-of-catch shape, on the handshake.

Not an example to copy.  Lab 05's pool (`B08`, `B13`) changes no register, no
flag and no byte of memory, so a fixture that compares architectural state
cannot reach it at all -- that is the entire point of that lab.  This one
counts `done` pulses, which does reach it, and then raises NameError while
building the failure message.

So it passes the golden core and crashes on the dealt one.

Expected verdict from lab-05/hunt.py and lab-06/hunt.py:  FAIL, row 2 marked
BROKEN, naming NameError.
"""

import cocotb

from golden import Golden
from simproc import SimProc
from simproc_asm import ORI, ADD, SUB, NAND, SHL, STORE, set_reg

SAFE = 0x30


@cocotb.test()
async def x01_done_pulses_with_a_broken_failure_path(dut):
    sp = SimProc(dut)
    await sp.start()

    prog = (set_reg(2, SAFE) +
            [ORI(1), ADD(1, 0), STORE(1, 2), SUB(1, 0), STORE(1, 2),
             NAND(1, 1), SHL(1, 1), ADD(1, 2), STORE(1, 2)])
    cycles, reason = Golden(prog).run(len(prog))
    assert reason is None, reason

    await sp.load(prog)
    await sp.set_pc(0)
    pulses = await sp.count_done_pulses(cycles)

    if pulses != len(prog):
        # `missing` was never assigned. On the golden core this line is never
        # reached; on a core that drops a `done` pulse it is all that happens.
        raise AssertionError(
            f"`done` pulsed {pulses} times for {len(prog)} instructions: "
            f"{missing}")                                        # noqa: F821
