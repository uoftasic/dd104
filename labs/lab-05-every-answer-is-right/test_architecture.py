"""
DD104 Lab 05 — an architecturally complete testbench, here to prove a negative.

    make blind

Ten tests.  Between them they check all four registers, the PC, both flags and
every byte of memory, after every instruction of a mixed program; every shift
amount in both directions; every branch displacement from -8 to +7; a compare
followed by two branches; LOAD and STORE through pointers held in a different
register from the data.  It is the suite Lab 04 grows into, and it catches
every bug in Labs 03 and 04.

It is also completely blind to both bugs in Lab 05, and `make blind` runs it
against them so you can watch that happen before you start.

There is nothing wrong with this file.  It is not lazy and it is not
incomplete.  It reads architectural state -- registers, memory, flags, the PC
-- and that is the whole category of thing it can see. `done`, `halt` and the
clock count are not architectural state, and no amount of more-of-the-same
reaches them.
"""

import cocotb

from simproc import SimProc, PARK, trace
from simproc_asm import (ORI, ADD, SUB, NAND, SHL, SHR, LOAD, STORE,
                         JMP, BZ, BNZ, BPZ, assemble, listing, set_reg)
from golden import Golden, compare_memory


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Arithmetic
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
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

@cocotb.test()
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

@cocotb.test()
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

@cocotb.test()
async def t04_a_loop(dut):
    """Sum 1..5 and store the answer, with an exact cycle count.

    Lab 04's version of this test also asserted an exact cycle count. This one
    does not, deliberately: a cycle count is a timing property, not an
    architectural one, and this file exists to show you exactly how far you can
    get while looking only at architectural state. Putting the cycle assertion
    back is one of the things Lab 05 asks you to do."""
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
    dut._log.info(f"the program took {cycles} clock cycles -- unchecked, on purpose")


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Sweep the field, do not sample it
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t05_every_shift_amount(dut):
    """All four shift amounts, both directions.

    The amount field is `instr[4:3]`, two bits, so 0, 1, 2 and 3 are all legal
    and all reachable. t02 drives one of them. Shifting by 1 is what everybody
    writes, which makes it the worst possible single sample: a decoder that
    drops the top bit of this field is exactly right at 0 and 1 and wrong at
    2 and 3.

    Eight assertions to cover a field completely. There is no cleverness here
    at all and that is the point -- most missing coverage is missing because
    nobody wrote the loop, not because the loop was hard."""
    sp = SimProc(dut)
    await sp.start()

    for k in range(4):
        await sp.run(set_reg(1, 0x0C) + [SHL(1, k)])
        want = (0x0C << k) & 0xFF
        assert sp.reg(1) == want, (
            f"0x0C << {k} gave 0x{sp.reg(1):02X}, expected 0x{want:02X}.\n"
            f"  If shifts by 0 and 1 are right and 2 and 3 are not, the shift "
            f"amount is losing a bit between the instruction word and the ALU.")

    for k in range(4):
        await sp.run(set_reg(1, 0xC0) + [SHR(1, k)])
        want = 0xC0 >> k
        assert sp.reg(1) == want, (
            f"0xC0 >> {k} gave 0x{sp.reg(1):02X}, expected 0x{want:02X}")

    dut._log.info("all four shift amounts, both directions")


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Distinct operands, and the register that should not have moved
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t06_the_result_lands_in_rA_and_only_rA(dut):
    """`ADD rA, rB` writes rA. Check rB as well -- especially rB.

    The instruction word is `AA BB oooo`. rA is bits 7:6 and rB is bits 5:4,
    they are two bits apart, and a write-back that reads the wrong one of them
    is a single-character edit. It is also completely invisible to any test
    where rA and rB are the same register, which is most of them, because
    `ADD r1, r1` and `SUB r0, r0` are how you double and how you clear.

    So: four distinct values in four registers, one operation, and all four
    registers checked afterwards. `sp.regs()` gives you all four at once."""
    sp = SimProc(dut)
    await sp.start()

    # r0 goes LAST. `set_reg` builds every constant in r0 and then copies it,
    # because ORI is the only way to get a literal into this machine and ORI
    # only ever writes r0. So `set_reg(0, x) + set_reg(1, y)` sets r0 and then
    # immediately destroys it. Set r0 last, or watch a correct core fail your
    # test -- which is exactly what the first draft of this file did.
    setup = (set_reg(1, 0x20) + set_reg(2, 0x03) + set_reg(3, 0x5C) +
             set_reg(0, 0x10))

    await sp.run(setup + [ADD(1, 2)])
    got = sp.regs()          # a tuple of four ints, not a list
    assert got == (0x10, 0x23, 0x03, 0x5C), (
        f"after ADD r1, r2 the registers are {[hex(v) for v in got]}, "
        f"expected r1 = 0x23 and everything else unchanged.\n"
        f"  r1 should be 0x20 + 0x03 = 0x23 and r2 should not have moved.\n"
        f"  If r2 holds 0x23 and r1 still holds 0x20, the write-back is using "
        f"the rB field of the instruction instead of the rA field.")

    await sp.run(setup + [SUB(3, 2)])
    got = sp.regs()
    assert got == (0x10, 0x20, 0x03, 0x59), (
        f"after SUB r3, r2 the registers are {[hex(v) for v in got]}, "
        f"expected r3 = 0x5C - 0x03 = 0x59 and nothing else moved")

    await sp.run(setup + [NAND(0, 3)])
    got = sp.regs()
    assert got == (0xEF, 0x20, 0x03, 0x5C), (
        f"after NAND r0, r3 the registers are {[hex(v) for v in got]}, "
        f"expected r0 = ~(0x10 & 0x5C) = 0xEF and nothing else moved")

    dut._log.info("three operations, four registers checked after each")


# ─────────────────────────────────────────────────────────────────────────────
# 7.  A pointer that is not also the destination
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t07_load_through_a_separate_pointer(dut):
    """`LOAD rA, rB` reads mem[rB] into rA, with rA and rB different.

    t03 uses `LOAD r1, r1` -- load through a pointer into itself. It is a real
    idiom, it is what you write when you are walking a list and do not need the
    address afterwards, and it is *correct on a core that reads the address out
    of rA instead of rB*, because on that instruction the two registers are the
    same register.

    This is the trap that is worth remembering from Lab 04, because it is not
    about being careless. `LOAD r1, r1` is a perfectly good instruction to
    test. It is just not sufficient, and nothing about looking at it says so.

    Three distinct things here: the destination, the pointer, and the value.
    And the pointer is checked afterwards, because a LOAD is not allowed to
    eat its own address."""
    sp = SimProc(dut)
    await sp.start()
    sp.poke(0x2A, 0x77)
    sp.poke(0x2B, 0xEE)

    await sp.run(set_reg(2, 0x2A) + [LOAD(1, 2)])
    assert sp.reg(1) == 0x77, (
        f"LOAD r1, r2 with r2 = 0x2A gave r1 = 0x{sp.reg(1):02X}, expected 0x77.\n"
        f"  {sp.describe()}\n"
        f"  If r1 came back holding mem[whatever r1 was], the address is being "
        f"taken from the rA field instead of the rB field -- which is invisible "
        f"to any test that writes LOAD rX, rX.")
    assert sp.reg(2) == 0x2A, (
        f"r2 was the pointer and is now 0x{sp.reg(2):02X}; it should still be 0x2A")

    # And a STORE whose data and address are in different registers, for the
    # same reason.
    await sp.run(set_reg(1, 0x5C) + set_reg(3, 0x2B) + [STORE(1, 3)])
    assert sp.peek(0x2B) == 0x5C, (
        f"STORE r1, r3 put 0x{sp.peek(0x2B):02X} at 0x2B, expected 0x5C")
    assert sp.peek(0x2A) == 0x77, "the STORE also changed mem[0x2A]"

    dut._log.info("LOAD and STORE with the pointer in a different register")


# ─────────────────────────────────────────────────────────────────────────────
# 8.  Against the model, after every instruction
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t08_against_the_golden_model(dut):
    """Step a mixed program and compare everything, every instruction.

    This is the highest-leverage test in the file: four lines of setup, and it
    checks four registers, the PC and both flags after every single
    instruction, including the ones you did not think to check. When it fails
    it names the instruction number, the address, the disassembled instruction
    and the field that disagreed.

    Its limitation is worth writing down next to it rather than discovering:
    `golden.py` models architectural state and nothing else. It has no idea
    `done` or `halt` exist. A core that computes every answer correctly and
    gets its handshake wrong passes this test perfectly. That is Lab 05."""
    sp = SimProc(dut)
    await sp.start()
    sp.poke(0x30, 0x1F)

    prog = (set_reg(1, 0xC3) + set_reg(2, 0x1D) + set_reg(3, 0x30) +
            [ADD(1, 2),        # 195 + 29 = 224
             SUB(1, 2),        # 224 - 29 = 195
             NAND(1, 2),       # ~(195 & 29) = ~1 = 254
             SHL(1, 2),        # 254 << 2 = 248
             SHR(1, 3),        # 248 >> 3 = 31
             STORE(1, 3),      # mem[0x30] = 31
             LOAD(0, 3),       # r0 = mem[0x30] = 31
             ORI(9),           # r0 = 31 | 9 = 31
             SUB(3, 1)])       # 48 - 31 = 17

    await sp.load(prog)
    model = Golden(prog + [PARK])

    steps, problem = await trace(sp, len(prog), model=model)
    assert problem is None, f"{problem}\n\nthe program:\n{listing(prog)}"

    mismatches = compare_memory(model, sp)
    assert not mismatches, (
        "memory disagrees with the model at: " +
        ", ".join(f"0x{a:02X} (model {m}, chip {d})" for a, m, d in mismatches))

    dut._log.info(f"{len(steps)} instructions, every register / PC / flag / byte "
                  f"of memory agreed with golden.py")


# ─────────────────────────────────────────────────────────────────────────────
# 9.  Both halves of the number line
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t09_branches_go_backwards_too(dut):
    """Every displacement the field can hold: -8 through +7.

    The displacement is `instr[7:4]`, four bits, signed, and the target is
    `PC_of_the_branch + 1 + displacement`. That is sixteen values and half of
    them are negative -- and the negative half is the half a loop needs, so a
    suite full of "skip the next instruction" covers forward branches
    perfectly and never terminates a loop.

    Sign extension is a silent half of the number line. It is also the half
    you test second, if at all, because forward is what you write first.

    The check here is the PC after a single unconditional JMP, which is the
    cleanest possible statement of "did the target land where the ISA says".
    `sp.set_pc()` puts the PC somewhere with room on both sides."""
    sp = SimProc(dut)
    await sp.start()

    base = 20
    for disp in range(-8, 8):
        await sp.reset()
        for a in range(64):
            sp.poke(a, 0x0C)                  # an unimplemented opcode: 3 cycles,
        sp.poke(base, JMP(disp))              # PC+1, no state change
        await sp.set_pc(base)
        await sp.step()
        want = base + 1 + disp
        assert sp.pc() == want, (
            f"JMP {disp:+d} from address {base} landed at {sp.pc()}, "
            f"expected {want}.\n"
            f"  target = PC_of_the_branch + 1 + displacement.\n"
            f"  If every forward branch is right and the backward ones land 16 "
            f"too far along, the displacement is being zero-extended instead of "
            f"sign-extended.")

    dut._log.info("all 16 displacements, -8 through +7")


# ─────────────────────────────────────────────────────────────────────────────
# 10.  One compare, two branches
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t10_a_compare_survives_the_first_branch(dut):
    """Set the flags once, then branch on them twice.

    `BZ over_a; BNZ over_b` is an idiom you write on day one: one comparison,
    two different things to do about it. It only works if a branch leaves the
    flags alone -- and on this machine branches compute their own target
    through the ALU, which means the hardware has an adder producing flags
    during every single branch and a `flag_wr` line one character away from
    being asserted.

    A suite that uses each compare exactly once cannot see that. This one uses
    it twice on purpose."""
    sp = SimProc(dut)
    await sp.start()

    # r1 = 0 sets Z. Then BZ (taken) and BNZ (not taken) off the SAME compare.
    prog = assemble("""
            SUB   r1, r1        # r1 = 0  ->  Z = 1, N = 0
            BZ    two           # taken:   Z is set
    two:    BNZ   three         # NOT taken: Z is still set
            ORI   1             # this must execute
    three:  ORI   2
    """)
    await sp.run(prog)

    assert sp.reg(0) == 3, (
        f"r0 is {sp.reg(0)}, expected 3.\n"
        f"  SUB r1, r1 sets Z. BZ is taken. BNZ must NOT be taken, because the "
        f"BZ is not allowed to have changed the flags -- so both ORIs run and "
        f"r0 ends at 1 | 2 = 3.\n"
        f"  r0 = 2 means the BNZ was taken, which means the flags moved between "
        f"the compare and the second branch.\n"
        f"  {sp.describe()}")

    dut._log.info(f"one compare, two branches, r0 = {sp.reg(0)}")
