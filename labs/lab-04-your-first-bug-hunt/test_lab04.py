"""
DD104 Lab 04 — your first bug hunt.

    make new        deal a mystery core
    make hunt       this file against it
    make verdict    the grade

This file ships with four tests that all pass on the golden core, and they are
a deliberately *ordinary* starting suite — the tests a competent person writes
in twenty minutes without thinking very hard about hiding places.  Somewhere
between one and three of the bugs in this lab's pool walk straight past them.

Your job is not to admire them.  It is to find what they do not drive.

────────────────────────────────────────────────────────────────────────────
THE THREE QUESTIONS THAT FIND BUGS IN THIS LAB
────────────────────────────────────────────────────────────────────────────
1.  Which fields of the instruction word does my stimulus never vary?
    SHIFT has a two-bit amount field. Every branch has a four-bit
    displacement. If a test only ever shifts by 1, two of the four amounts
    have never been driven.

2.  Where do two of my operands happen to be the same register?
    `ADD r1, r1` cannot tell a write-back to rA from a write-back to rB.
    `LOAD r1, r1` cannot tell a pointer read from a destination read. Both are
    idioms, both are things you write without noticing, and both make a whole
    class of bug invisible.

3.  What state do I read after the program finishes, and what do I never read?
    Four registers, 64 bytes of memory, two flags, a PC, a `done` pulse and a
    `halt` pin. A test that checks one register is blind to seven other kinds
    of thing being wrong.

────────────────────────────────────────────────────────────────────────────
THE HARNESS, IN ONE SCREEN
────────────────────────────────────────────────────────────────────────────
    sp = SimProc(dut); await sp.start()   clock, reset, RAM blanked
    await sp.run(prog) -> cycles          load, run to the parking loop
    await sp.step(n)                      execute exactly n instructions
    sp.reg(i)  sp.regs()  sp.pc()  sp.flags()  sp.fsm()
    sp.peek(a)  sp.poke(a, v)             the memory backdoor
    sp.halt  sp.done                      the pins, as '0' / '1' / 'x'
    sp.describe()                         one line of everything, for messages
    await trace(sp, n, model=g)           step and compare against golden.py

Full reference: ../common/README.md and the docstrings in ../common/simproc.py.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb

from simproc import SimProc, PARK, trace
from simproc_asm import (ORI, ADD, SUB, NAND, SHL, SHR, LOAD, STORE,
                         JMP, BZ, BNZ, BPZ, assemble, listing, set_reg)
from golden import Golden, compare_memory


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Arithmetic
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t01_arithmetic(dut):
    """ADD, SUB and NAND on operands that are not equal to each other.

    Lab 03 finished the ALU exhaustively, so this is not really an ALU test any
    more — it is a test that the right two registers reach the ALU and the
    answer gets back to the right one."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run(set_reg(1, 200) + set_reg(2, 60) +
                 [ADD(1, 2), SUB(1, 2), NAND(1, 2)])

    assert sp.reg(1) == 247, (
        f"r1 is {sp.reg(1)}, expected 247.\n"
        f"  200 + 60 = 260, wraps to 4;  4 - 60 = -56, wraps to 200;\n"
        f"  ~(200 & 60) = ~8 = 247.\n  {sp.describe()}")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Shifts
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t02_shifts(dut):
    """Shift left and shift right.

    Read this one against question 1 above before you go looking anywhere
    else."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run(set_reg(1, 0x0C) + [SHL(1, 1)])
    assert sp.reg(1) == 0x18, f"0x0C << 1 gave 0x{sp.reg(1):02X}, expected 0x18"

    await sp.run(set_reg(1, 0x0C) + [SHR(1, 1)])
    assert sp.reg(1) == 0x06, f"0x0C >> 1 gave 0x{sp.reg(1):02X}, expected 0x06"


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Memory
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t03_load_and_store(dut):
    """Put a byte in memory, read it back through a pointer.

    Read this one against question 2."""
    sp = SimProc(dut)
    await sp.start()
    sp.poke(0x30, 0x5A)

    await sp.run(set_reg(1, 0x30) + [LOAD(1, 1)])
    assert sp.reg(1) == 0x5A, (
        f"LOAD r1, r1 from address 0x30 gave 0x{sp.reg(1):02X}, expected 0x5A.\n"
        f"  {sp.describe()}")

    await sp.run(set_reg(1, 0x99) + set_reg(2, 0x31) + [STORE(1, 2)])
    assert sp.peek(0x31) == 0x99, (
        f"STORE r1, r2 put 0x{sp.peek(0x31):02X} at 0x31, expected 0x99")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  A loop
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t04_a_loop(dut):
    """Sum 1..5 and store the answer, with an exact cycle count.

    The value check tests the arithmetic. The cycle count tests that every
    instruction takes the number of cycles the datasheet claims — and a wrong
    cycle count divided by the number of loop iterations is a very short list
    of suspects."""
    sp = SimProc(dut)
    await sp.start()

    prog = assemble("""
            SUB   r0, r0
            ORI   1
            SUB   r2, r2
            ADD   r2, r0        # r2 = 1
            SUB   r0, r0
            ORI   5             # r0 = 5, the counter
            SUB   r1, r1        # r1 = 0, the total
    loop:   ADD   r1, r0
            SUB   r0, r2
            BNZ   loop
            SUB   r0, r0
            ORI   4
            SHL   r0, 3         # r0 = 32
            SUB   r3, r3
            ADD   r3, r0
            STORE r1, r3        # mem[0x20] = total
    """)
    cycles = await sp.run(prog)

    assert sp.peek(0x20) == 15, (
        f"mem[0x20] is {sp.peek(0x20)}, expected 15 (1+2+3+4+5).\n"
        f"  {sp.describe()}\n{listing(prog)}")
    assert cycles == 109, (
        f"the program took {cycles} clock cycles, expected 109.\n"
        f"  setup 30 + loop (4+4+3) x 5 + finish 24 = 109.\n"
        f"  The arithmetic is right, so this is a timing difference.")


# ─────────────────────────────────────────────────────────────────────────────
# TODO — the tests you write
# ─────────────────────────────────────────────────────────────────────────────
#
# Nothing below this line exists yet. Add tests until `make verdict` gives you
# three green rows. Some shapes that are worth having in any suite for this
# machine, in the order they tend to pay off:
#
#   * A shift by every amount the field can hold, in both directions.
#     `SHL(1, k)` for k in 0..3 and the same for `SHR`. Eight assertions, and
#     they cover a field that t02 samples at exactly one value.
#
#   * Every operation with rA and rB as DIFFERENT registers, and the register
#     that should not have changed checked as well as the one that should.
#     `sp.regs()` returns all four at once, which makes this one line.
#
#   * LOAD with the pointer in one register and the destination in another,
#     and the pointer checked afterwards to prove it was not overwritten.
#
#   * Every branch displacement the four-bit field can hold, -8 through +7.
#     `sp.set_pc(a)` and `sp.step()` let you check the PC after exactly one
#     branch, which is the cleanest possible statement of "did it land where
#     the ISA says". Forward is the half you will write first.
#
#   * One compare followed by TWO branches. `BZ x; BNZ y` off a single
#     comparison is an idiom you write on day one, and it is the only shape
#     that notices if a branch quietly rewrites the flags on its way past.
#
#   * `await trace(sp, n, model=Golden(prog + [PARK]))` — step a program and
#     compare every register, the PC and both flags against golden.py after
#     every instruction. This is the highest-leverage test you can write and
#     it takes four lines. Its honest limitation: the model knows nothing
#     about `done` or `halt`, so a core that computes everything correctly and
#     gets its handshake wrong sails straight through. That is Lab 05.
#
# `../common/test_reference.py` is a suite that catches all thirteen bugs.
# Read it AFTER `make verdict` is green, not before — it is a much better
# read once you have your own suite to compare it against.
