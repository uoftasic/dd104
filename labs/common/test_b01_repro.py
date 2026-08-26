"""DD104 — a minimal reproducer, as a bug report should ship one.

    make sim   TB=test_b01_repro              # 3 tests, all pass on the good core
    make check TB=test_b01_repro BUG=B01      # ... and t01 FAILS on the broken one

This is the test half of the worked report in
`docs/guide/writing-the-bug-report.md`.  It is deliberately small: three tests,
one program each, no loops, no model, nothing that needs explaining.

`B01_sub_operands_swapped` is not one of the capstone's three, so nothing here
gives that lab away.  It is here because it is the clearest example in the
catalogue of a report whose *numbers* do the arguing.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb

from simproc import SimProc
from simproc_asm import SUB, set_reg


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t01_sub_with_two_distinct_operands(dut):
    """THE REPRODUCER.  Three instructions' worth of setup and one SUB.

    200 - 100 = 100.  A core that computes B - A gets 100 - 200 = -100, which
    in eight bits is 156.  Both numbers are in the failure message, and so is
    the sum, because `r1 is 156` on its own makes the reader do the algebra."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run(set_reg(1, 200) + set_reg(2, 100) + [SUB(1, 2)])
    got = sp.reg(1)

    assert got == 100, (
        f"SUB r1, r2 with r1 = 200 and r2 = 100 left r1 = {got}.\n"
        f"  expected  200 - 100 = 100\n"
        f"  got       {got}\n"
        f"  note      (100 - 200) mod 256 = {(100 - 200) & 0xFF}, which is what a "
        f"core computing rB - rA would give\n"
        f"  {sp.describe()}")

    dut._log.info(f"200 - 100 = {got}")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t02_the_idiom_that_hides_it(dut):
    """`SUB rX, rX` is how you write 'clear a register' on this machine.

    It is in every program in this course, including the setup lines of t01.
    A - A and A - A are the same subtraction whichever way round you do it, so
    the bug is invisible to it. This test PASSES on the broken core, and it is
    in the file on purpose: a report that shows what still works is a report a
    designer can act on."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run(set_reg(1, 200) + [SUB(1, 1)])
    assert sp.reg(1) == 0, f"SUB r1, r1 left r1 = {sp.reg(1)}, expected 0"

    dut._log.info("SUB r1, r1 clears r1 on a core with the operands swapped, "
                  "exactly as it does on a good one")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t03_the_512_survivors(dut):
    """The other operand pairs that agree, and why there are exactly 512.

    A - B == B - A (mod 256) iff 2(A - B) == 0 (mod 256) iff A - B is 0 or 128.
    That is 256 pairs with A == B and 256 with |A - B| == 128:  512 of 65,536.
    So an exhaustive SUB sweep must report 65,024 wrong -- and if it reports
    some other number, this is a different bug from the one in the report."""
    sp = SimProc(dut)
    await sp.start()

    for a, b in ((7, 7), (0, 128), (128, 0), (200, 72), (72, 200)):
        await sp.run(set_reg(1, a) + set_reg(2, b) + [SUB(1, 2)])
        assert sp.reg(1) == (a - b) & 0xFF, (
            f"{a} - {b}: r1 is {sp.reg(1)}, expected {(a - b) & 0xFF}. "
            f"This pair is supposed to agree on BOTH cores.")

    survivors = sum(1 for a in range(256) for b in range(256)
                    if (a - b) % 256 in (0, 128))
    dut._log.info(f"5 survivor pairs checked in hardware; by construction there "
                  f"are {survivors} of 65,536, leaving {65536 - survivors} wrong")
    assert survivors == 512
