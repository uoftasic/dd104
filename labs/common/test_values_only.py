"""DD104 — a thorough testbench that never reads a flag.

    make sim   TB=test_values_only              # 3 tests, all pass
    make check TB=test_values_only BUG=B03      # ... and so does the broken core

This file is not a bad testbench.  It checks arithmetic on many operand pairs
instead of one, it checks a whole program's answer AND its cycle count, and it
checks memory.  It is more thorough than most first attempts.

It is also structurally incapable of finding `B03_zero_flag_low_nibble`, and no
amount of adding more of the same kind of test would change that.  It is the
worked example for `docs/guide/flags-are-state.md`.

The rule it exists to demonstrate:

    Every value this processor computes is visible in a register or in memory.
    N and Z are not.  A test that only reads registers and memory is testing a
    strictly smaller machine than the one on the die.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb

from simproc import SimProc
from simproc_asm import ADD, SUB, NAND, SHL, SHR, STORE, assemble, set_reg


# Operand pairs chosen the way anyone sensible would choose them: zero, one,
# small, large, the wrap-around, the halves of the byte.
PAIRS = [(0, 0), (0, 1), (1, 1), (5, 3), (16, 0), (15, 1),
         (127, 1), (128, 128), (200, 100), (255, 1), (170, 85), (240, 15)]


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def v01_arithmetic_over_a_spread_of_operands(dut):
    """ADD and SUB, twelve operand pairs each, every result checked."""
    sp = SimProc(dut)
    await sp.start()

    for a, b in PAIRS:
        await sp.run(set_reg(1, a) + set_reg(2, b) + [ADD(1, 2)])
        assert sp.reg(1) == (a + b) & 0xFF, (
            f"{a} + {b}: r1 is {sp.reg(1)}, expected {(a + b) & 0xFF}.\n"
            f"  {sp.describe()}")

        await sp.run(set_reg(1, a) + set_reg(2, b) + [SUB(1, 2)])
        assert sp.reg(1) == (a - b) & 0xFF, (
            f"{a} - {b}: r1 is {sp.reg(1)}, expected {(a - b) & 0xFF}.\n"
            f"  {sp.describe()}")

    dut._log.info(f"{2 * len(PAIRS)} runs through ADD and SUB, every result "
                  f"correct")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def v02_logic_and_shifts(dut):
    """NAND, SHL and SHR — the rest of the ALU, still values only."""
    sp = SimProc(dut)
    await sp.start()

    for a, b in PAIRS:
        await sp.run(set_reg(1, a) + set_reg(2, b) + [NAND(1, 2)])
        assert sp.reg(1) == (~(a & b)) & 0xFF, (
            f"NAND({a}, {b}): r1 is {sp.reg(1)}, "
            f"expected {(~(a & b)) & 0xFF}.\n  {sp.describe()}")

    for v in (0, 1, 16, 129, 255):
        for amt in (1, 3):
            await sp.run(set_reg(1, v) + [SHL(1, amt)])
            assert sp.reg(1) == (v << amt) & 0xFF, (
                f"{v} << {amt}: r1 is {sp.reg(1)}, expected {(v << amt) & 0xFF}")
            await sp.run(set_reg(1, v) + [SHR(1, amt)])
            assert sp.reg(1) == v >> amt, (
                f"{v} >> {amt}: r1 is {sp.reg(1)}, expected {v >> amt}")

    dut._log.info(f"NAND on {len(PAIRS)} pairs, and 20 shifts, every "
                  f"result correct")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def v03_a_whole_program_and_its_cycle_count(dut):
    """Sum 1..5 and store it — the answer, the memory, and the timing."""
    sp = SimProc(dut)
    await sp.start()

    prog = assemble("""
            SUB   r0, r0
            ORI   1
            SUB   r2, r2
            ADD   r2, r0
            SUB   r0, r0
            ORI   5
            SUB   r1, r1
    loop:   ADD   r1, r0
            SUB   r0, r2
            BNZ   loop
            SUB   r0, r0
            ORI   4
            SHL   r0, 3
            SUB   r3, r3
            ADD   r3, r0
            STORE r1, r3
    """)
    cycles = await sp.run(prog)

    assert sp.peek(0x20) == 15, (
        f"mem[0x20] is {sp.peek(0x20)}, expected 15.\n  {sp.describe()}")
    assert cycles == 109, (
        f"the program took {cycles} clock cycles, expected 109")

    dut._log.info(f"1+2+3+4+5 = {sp.peek(0x20)} in {cycles} clock cycles")
