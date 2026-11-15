"""
DD104 Lab 06 — a reference capstone suite.

Do not open this before your own `make check-all` is 13 of 13.

    cp solutions/test_capstone.py test_solution.py
    make check-all TB=test_solution

Sixteen tests.  Ten of them are Lab 04's suite, three are Lab 05's protocol
checks, and three are new -- one for each bug in this lab's pool.  That
proportion is the honest shape of a capstone: most of the work was already
done, and the last three are the ones that took the longest.

Between them they catch all thirteen bugs in the catalogue.  Read
`../common/test_reference.py` afterwards; it does the same job in eleven tests
and the differences are worth arguing about.
"""

import cocotb

from simproc import SimProc, PARK, trace
from simproc_asm import (ORI, ADD, SUB, NAND, SHL, SHR, LOAD, STORE,
                         JMP, BZ, BNZ, BPZ, assemble, listing, set_reg)
from golden import Golden, compare_memory

SAFE = 0x3F                 # the top address of the 64-byte RAM


# The program every test in this file uses.  Nine instructions, one of them a
# STORE, and a cycle count you can add up by hand:
#
#     SUB 4 + ORI 5 + SHL 4 + SUB 4 + ADD 4 + SUB 4 + ORI 5 + ADD 4 + STORE 3
#   = 37
#
PROGRAM = """
        SUB   r0, r0        # 4    r0 = 0
        ORI   4             # 5    r0 = 4
        SHL   r0, 3         # 4    r0 = 32       -- the address
        SUB   r3, r3        # 4
        ADD   r3, r0        # 4    r3 = 32
        SUB   r1, r1        # 4
        ORI   7             # 5    r0 = 32 | 7 = 39
        ADD   r1, r0        # 4    r1 = 39       -- the data
        STORE r1, r3        # 3    mem[0x20] = 39
"""


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
            sp.poke(a, 0x0C)                  # an unimplemented opcode: 4 cycles,
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

# ─────────────────────────────────────────────────────────────────────────────
# 2.  A scoreboard triggered on `done`
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def p01_done_pulses_once_per_instruction(dut):
    """Count `done` pulses, which is the number of comparisons a done-triggered
    scoreboard would have made.

    A scoreboard is the standard shape for checking a processor: something
    watches for "an instruction finished" and, each time it sees one, compares
    the machine against a model. It is a good design. Almost every professional
    verification environment is built this way.

    Its failure mode is the thing worth learning here. If the pin it triggers
    on stops pulsing, the scoreboard does not report an error -- it has nothing
    to report, because it was never woken up. It goes green. It reports zero
    mismatches, truthfully, having made fewer comparisons than there were
    instructions. **A missing trigger does not fail your test; it silently
    stops your test from testing.**

    ── TODO ──────────────────────────────────────────────────────────────────
    This test currently asserts that at least one instruction retired, which is
    nearly nothing.

    The program above has nine instructions and `sp.run()` reports it takes 37
    clock cycles. `done` should pulse exactly once per retired instruction, so
    there is an exact number this should be, and it is not "more than zero".

    Assert it. Then put the count in the failure message, because "8, expected
    9" and "some pulses are missing" are very different amounts of help -- the
    first one tells you the shortfall is one instruction, and only two
    instructions in that program, SHL and STORE, appear exactly once.
    ──────────────────────────────────────────────────────────────────────────
    """
    sp = SimProc(dut)
    await sp.start()
    prog = assemble(PROGRAM)

    await sp.load(prog)
    cycles = await sp.run()
    dut._log.info(f"the program ran in {cycles} clock cycles")

    # `run()` leaves the PC parked at the end of the program, and `load()` only
    # writes memory -- so without this reset the second run starts inside the
    # parking loop and counts its retires instead of the program's. A reset
    # clears the registers and the PC and leaves the RAM alone, which is
    # exactly what is wanted here.
    await sp.reset()
    pulses = await sp.count_done_pulses(cycles)
    dut._log.info(f"a done-triggered scoreboard would have made {pulses} "
                  f"comparisons for a {len(prog)}-instruction program")

    assert pulses == len(prog), (
        f"`done` pulsed {pulses} times for a {len(prog)}-instruction program.\n"
        f"  One pulse per retired instruction. Every register, flag and byte "
        f"of memory this core produced is correct (t01 passed), so the "
        f"instruction did execute -- it just did not say so.\n"
        f"  The shortfall is {len(prog) - pulses}. Look at the instructions "
        f"that appear exactly {len(prog) - pulses} time(s) in this program: "
        f"one of them retired without pulsing `done`.\n"
        f"  Anything outside this core that waits for `done` -- a debugger, a "
        f"performance counter, a scoreboard in a testbench -- is silently "
        f"skipping that instruction. A scoreboard that misses it does not go "
        f"red. It goes green, having compared one thing fewer than it should.")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  `halt` while RUN is asserted
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def p02_halt_stays_low_while_running(dut):
    """`halt` is high in IDLE. While RUN is asserted it must never be.

    Zero is the only correct answer here, which makes this the cheapest useful
    assertion in the file: one number, one expected value, no arithmetic.

    A core that drops into IDLE for one cycle and immediately restarts itself
    -- because RUN is still asserted -- computes every right answer, in the
    right order, into the right places. Its only symptoms are one wasted cycle
    and a one-cycle blip on a pin. On silicon that is a performance bug and a
    glitch a debugger can see, and nothing that reads registers will ever find
    it."""
    sp = SimProc(dut)
    await sp.start()
    prog = assemble(PROGRAM)

    await sp.load(prog)
    cycles = await sp.run()
    await sp.reset()

    high = await sp.count_halt_cycles(cycles)
    dut._log.info(f"halt was high on {high} of {cycles} running cycles")

    assert high == 0, (
        f"`halt` was high on {high} of the {cycles} cycles the core spent "
        f"running.\n"
        f"  While RUN is asserted the core is not supposed to visit IDLE at "
        f"all. It is visiting it and coming straight back, which is why every "
        f"value this program produces is still correct.\n"
        f"  {high} blip(s) in a program with one STORE in it is a useful "
        f"ratio -- count the instructions of each kind and see which count "
        f"matches.")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  The clock is a result too
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def p03_the_program_takes_exactly_37_cycles(dut):
    """The cycle count of a straight-line program is arithmetic, not measurement.

    ORI 5, ADD/SUB/NAND/SHL/SHR/LOAD 4, STORE and every branch 3:

        SUB 4 + ORI 5 + SHL 4 + SUB 4 + ADD 4 + SUB 4 + ORI 5 + ADD 4 + STORE 3
      = 37

    Write the sum down, assert it, and put the sum in the failure message. Then
    a core that is one cycle slow is a red row with a number attached instead
    of a thing nobody notices, and the size of the difference divided by the
    number of instructions of each kind points straight at the instruction
    responsible.

    This is also the check that would have caught a whole class of bug your
    other tests cannot express: 'the answer is right and it arrived late' is
    not a sentence about registers."""
    sp = SimProc(dut)
    await sp.start()
    prog = assemble(PROGRAM)

    cycles = await sp.run(prog)
    dut._log.info(f"{len(prog)} instructions in {cycles} clock cycles")

    assert cycles == 37, (
        f"the program took {cycles} clock cycles, expected 37.\n"
        f"  4 + 5 + 4 + 4 + 4 + 4 + 5 + 4 + 3 = 37, from the documented "
        f"instruction costs.\n"
        f"  Difference: {cycles - 37}. Divide that by the number of "
        f"instructions of each kind in the program and one of the quotients "
        f"will be a whole number.\n{listing(prog)}")


# ─────────────────────────────────────────────────────────────────────────────
# c01  ORI, with a bit that is already set
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def c01_ori_over_bits_already_set(dut):
    """Three ORIs, chosen so the immediates overlap.

    ORI is the only way to get a constant into this machine, and the natural
    way to use it is the way `set_reg` does: clear the register, then OR in
    disjoint groups of bits, shifting between them. Disjoint is the operative
    word. When two operands share no set bits, `a | b` and `a + b` are the
    same number -- so every constant you would naturally build is built
    correctly by a machine whose ORI adds.

    And the first ORI after a reset is `0 | imm`, which is `0 + imm`, so even
    an overlapping immediate is right the first time.

    You have to OR a bit into a register that already has it. 5 | 3 = 7;
    5 + 3 = 8. Then 7 | 24 = 31; 8 + 24 = 32. One is a bit pattern and the
    other is a sum, and after two instructions they are one apart."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run([ORI(5), ORI(3), ORI(24)])

    assert sp.reg(0) == 31, (
        f"r0 is {sp.reg(0)}, expected 31.\n"
        f"  5 | 3 = 7, then 7 | 24 = 31.\n"
        f"  32 means the immediates were ADDED: 5 + 3 = 8, 8 + 24 = 32. OR and "
        f"ADD agree on every pair of operands that share no set bits, which is "
        f"every constant anybody builds on purpose.\n"
        f"  {sp.describe()}")


# ─────────────────────────────────────────────────────────────────────────────
# c02  which register ORI writes, once reset is no longer hiding it
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def c02_ori_writes_r0_and_only_r0(dut):
    """ORI's destination, checked outside the window where reset hides it.

    ORI has no register field. All five spare bits of the instruction are the
    immediate, so r0 is the only register it can possibly write, and every
    other register must be untouched by it.

    The reason this needs saying is that after a reset all four registers hold
    zero, and while that is true, `r0 = 0 | imm` and `r1 = 0 | imm` put the
    same value in the machine. A short readable test program runs entirely
    inside that window. The value is right and only its register is wrong, so
    a test that looks for the value rather than at r0 sees nothing amiss until
    the second ORI -- by which time you have stopped looking.

    So: make r0 non-zero first, and check all four registers, not just the one
    you expected to change."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run([ORI(5), SHL(0, 3), ORI(3)])

    assert sp.reg(0) == 43, (
        f"r0 is {sp.reg(0)}, expected 43.\n"
        f"  ORI 5 -> 5; SHL 3 -> 40; ORI 3 -> 40 | 3 = 43.\n"
        f"  {sp.describe()}")
    assert sp.regs()[1:] == (0, 0, 0), (
        f"ORI moved a register other than r0: {sp.regs()}.\n"
        f"  ORI has no register field, so r0 is the only destination it can "
        f"have. If the value you were expecting in r0 turned up in r1 instead, "
        f"note that the FIRST ORI of this program computed the right value: "
        f"both registers were zero when it ran.")


# ─────────────────────────────────────────────────────────────────────────────
# c03  the UART, swept rather than sampled
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def c03_baud_sweep(dut):
    """Five bit periods, and a real byte at each one.

    `clk_per_bit` is `uio_in x 4`. Every lab in this course runs at the default
    `uio_in = 8`, so `clk_per_bit = 32` -- one point of a range that silicon
    will be used across. A parametric design tested at one parameter value has
    been tested once.

    Two things are checked at each speed, and the second one is the point.
    PING alone is not a link test: 0xF0 already has its top bit set and the
    reply 0xAA is a fixed pattern, so a receiver whose bit period is one clock
    too long still gets both of them exactly right while mangling every byte
    that carries data. A link test that passes over a broken link is worse than
    no link test, because you believe it.

    A receiver that is slightly slow walks further off centre with every bit of
    a frame, so it fails at SHORT bit periods first and is invisible at long
    ones. Which speeds work is therefore the diagnosis, not just the result --
    read the list in the failure message before you go anywhere near the
    RTL."""
    sp = SimProc(dut)
    await sp.start()

    failures = []
    for uio in (4, 8, 16, 32, 64):
        await sp.set_baud(uio)
        try:
            reply = await sp.uart_ping()
        except Exception as e:                                  # noqa: BLE001
            failures.append((uio, sp.clk_per_bit, f"PING raised {type(e).__name__}"))
            continue
        if reply != 0xAA:
            failures.append((uio, sp.clk_per_bit, f"PING answered 0x{reply:02X}"))
            continue
        try:
            await sp.uart_write(SAFE, 0x5A)
            got = await sp.uart_read(SAFE)
        except Exception as e:                                  # noqa: BLE001
            failures.append((uio, sp.clk_per_bit,
                             f"PING was fine, then WRITE/READ raised "
                             f"{type(e).__name__}"))
            continue
        if got != 0x5A:
            failures.append((uio, sp.clk_per_bit,
                             f"PING was fine, then wrote 0x5A and read back "
                             f"0x{got:02X}"))
        else:
            dut._log.info(f"uio_in={uio:3d}  clk_per_bit={sp.clk_per_bit:4d}  "
                          f"PING 0xAA and 0x5A round-tripped")

    assert not failures, (
        "the UART did not work at every speed it is specified for:\n" +
        "\n".join(f"    uio_in={u:3d}  clk_per_bit={c:4d}   {why}"
                  for u, c, why in failures) +
        "\n  Note WHICH speeds are fine, and note that PING kept working at "
        "speeds\n  where a data byte did not. Both facts are the diagnosis.")
