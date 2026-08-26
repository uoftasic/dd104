"""
DD104 — a worked testbench.

Six tests, each one a shape you will reuse.  Run it:

    make sim          # against the good core:  6 tests, 6 pass
    make check        # against a broken core:  it has to FAIL there too

Copy this file, rename it, and change it.  That is the intended workflow —
`make sim TB=test_mine` runs whatever module you name.

The comments here explain *why each test is shaped the way it is*, because the
shape is the lesson.  A test that checks `2 + 2 == 4` is not wrong, it is just
not load-bearing: it passes on almost every broken processor too.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb

from simproc import SimProc, PARK, trace
from simproc_asm import (ORI, ADD, SUB, NAND, SHL, SHR, LOAD, STORE,
                         BZ, BPZ, assemble, listing, set_reg)
from golden import Golden, compare_memory


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Is it alive?
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t01_the_chip_answers(dut):
    """PING should come back 0xAA.

    Start every session with this.  When a test fails, the first question is
    'is the chip broken or is my harness broken?', and a PING answers it in
    two lines.

    Be careful what you conclude from a PING that works, though.  0xF0 already
    has its top bit set and the reply 0xAA is a fixed pattern, so a UART whose
    bit period is slightly wrong still gets both of them right.  A working PING
    proves the wires are connected.  It does not prove the link works."""
    sp = SimProc(dut)
    await sp.start()

    reply = await sp.uart_ping()
    assert reply == 0xAA, f"PING answered 0x{reply:02X}, expected 0xAA"

    assert sp.halt == "1", (
        f"after reset the core should be in IDLE with halt high, "
        f"but halt is '{sp.halt}' and the state is {sp.fsm()}")

    dut._log.info(f"PING -> 0x{reply:02X}, and the core is {sp.fsm()}")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  One instruction, one step, one register
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t02_one_instruction(dut):
    """The smallest useful test: load one instruction, step once, look."""
    sp = SimProc(dut)
    await sp.start()
    await sp.load([ORI(5)])              # r0 = r0 | 5, and r0 is 0 after reset

    dut._log.info(f"before: {sp.describe()}")
    await sp.step()                      # STEP = exactly one instruction
    dut._log.info(f"after:  {sp.describe()}")

    assert sp.reg(0) == 5, f"r0 is {sp.reg(0)}, expected 5"
    assert sp.pc() == 1, f"PC is {sp.pc()}, expected 1"
    assert sp.flags() == (0, 0), f"flags are {sp.flags()}, expected N=0 Z=0"


# ─────────────────────────────────────────────────────────────────────────────
# 3.  The test that would catch a swapped subtract
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t03_arithmetic_on_different_values(dut):
    """ADD, SUB and NAND — on operands that are NOT equal to each other.

    This is the shape, and it is the whole point of the test.

    The natural way to write a SUB test is `SUB r1, r1` and check you got
    zero, because 'clear a register' is the idiom you use constantly.  But
    A - B and B - A give the same answer whenever A == B — so that test passes
    on a core whose subtractor has its operands backwards.  Out of all 65,536
    (A,B) pairs, exactly 512 survive a swap.  Pick your operands from the other
    65,024 on purpose.

    Same trap in NAND: `NAND rX, rX` is how you write NOT in a machine that has
    no NOT instruction, so it is the most common NAND anyone writes — and it
    is exactly the case where NAND and NOR agree."""
    sp = SimProc(dut)
    await sp.start()

    prog = (set_reg(1, 200) +           # r1 = 200
            set_reg(2, 60) +            # r2 = 60
            [ADD(1, 2),                 # r1 = 200 + 60 = 260 -> 4 (it wraps!)
             SUB(1, 2),                 # r1 = 4 - 60 = -56 -> 200
             NAND(1, 2)])               # r1 = ~(200 & 60) = ~8 = 247
    await sp.run(prog)

    r1 = sp.reg(1)
    assert r1 == 247, (
        f"r1 is {r1}, expected 247.\n"
        f"  200 + 60 = 260, which does not fit in 8 bits, so it wraps to 4.\n"
        f"  4 - 60 = -56, which wraps to 200.\n"
        f"  ~(200 & 60) = ~8 = 247.\n"
        f"  {sp.describe()}")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Flags are results too
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t04_flags_are_state(dut):
    """N and Z, checked on values chosen to make a lazy Z-detector wrong.

    A processor's flags are architectural state — they are as much a result as
    the byte in the register, and every branch you will ever write depends on
    them.  A test that only ever checks register values cannot see a flag bug
    at all.  Not 'is unlikely to': cannot.

    16 is the interesting value here.  Its low four bits are zero and the byte
    is not, so a zero-detector that only looks at the bottom nibble says
    'Z = 1' — and a value-only test never notices."""
    sp = SimProc(dut)
    await sp.start()

    # r1 = 16, and make that the LAST flag-setting result.
    await sp.run(set_reg(1, 16))
    assert sp.reg(1) == 16, f"r1 is {sp.reg(1)}, expected 16"
    n, z = sp.flags()
    assert (n, z) == (0, 0), (
        f"after r1 = 16 the flags are N={n} Z={z}, expected N=0 Z=0.\n"
        f"  16 is 0b00010000: not negative, and not zero. If Z is 1 here, "
        f"something is looking at only part of the byte.")

    # And a genuinely zero result, to prove Z can be 1 at all — otherwise a
    # core with Z permanently stuck at 0 would sail through the check above.
    await sp.run([SUB(1, 1)])
    n, z = sp.flags()
    assert (n, z) == (0, 1), f"after r1 = 0 the flags are N={n} Z={z}, expected N=0 Z=1"

    # A negative result: 0 - 1 = 255, whose top bit is set.
    await sp.run(set_reg(1, 0) + set_reg(2, 1) + [SUB(1, 2)])
    n, z = sp.flags()
    assert (n, z) == (1, 0), f"after r1 = 255 the flags are N={n} Z={z}, expected N=1 Z=0"


# ─────────────────────────────────────────────────────────────────────────────
# 5.  A loop, and a cycle count you can predict
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t05_a_loop_and_its_cycle_count(dut):
    """Sum 1..5, store the answer, and check how long it took.

    The value check (`mem[0x20] == 15`) tests the arithmetic.  The cycle check
    tests something else entirely: that every instruction takes the number of
    cycles the datasheet claims.  ORI is 5 cycles, ADD/SUB/NAND/SHIFT/LOAD are
    4, STORE and every branch are 3.  Add them up:

        setup    4+5+4+4+4+5+4                = 30
        loop     (ADD 4 + SUB 4 + BNZ 3) x 5  = 55
        finish   4+5+4+4+4+3                  = 24
                                                ---
                                                109

    If the total comes out at 114, something takes an extra cycle five times —
    which is once per loop iteration, and that narrows the search enormously.
    A test that only checks the answer would have said nothing."""
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
    dut._log.info("the program under test:\n" + listing(prog))

    cycles = await sp.run(prog)

    answer = sp.peek(0x20)
    assert answer == 15, (
        f"mem[0x20] is {answer}, expected 15 (1+2+3+4+5).\n  {sp.describe()}")
    assert cycles == 109, (
        f"the program took {cycles} clock cycles, expected 109.\n"
        f"  The arithmetic is right, so this is a timing difference: some "
        f"instruction is not taking the number of cycles it should.")

    dut._log.info(f"1+2+3+4+5 = {answer} in {cycles} clock cycles")


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Against the model, instruction by instruction
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t06_against_the_golden_model(dut):
    """Step a program and compare EVERY register, the PC and both flags after
    EVERY instruction against golden.py.

    This is the highest-leverage test in the file, because it checks things you
    did not think to check.  The directed tests above look at one register at a
    time; this one notices if instruction 4 quietly wrote the right value into
    the wrong register.

    It is also the test with the most honest limitation in the file.  The model
    has no idea `done` or `halt` exist, so a core that computes every answer
    correctly and gets its handshake wrong sails straight through.  That is not
    a flaw in this test — it is the reason a test suite needs more than one
    kind of test in it."""
    sp = SimProc(dut)
    await sp.start()

    prog = (set_reg(1, 0xC3) + set_reg(2, 0x1D) + set_reg(3, 0x30) +
            [ADD(1, 2),        # 195 + 29 = 224
             SUB(1, 2),        # 224 - 29 = 195
             NAND(1, 2),       # ~(195 & 29) = ~1 = 254
             SHL(1, 2),        # 254 << 2 = 248 (the top two bits fall off)
             SHR(1, 3),        # 248 >> 3 = 31
             STORE(1, 3),      # mem[0x30] = 31
             BZ(2),            # NOT taken: the last flag-setting result was 31
             ORI(9),           # r0 = 48 | 9 = 57
             LOAD(0, 3),       # r0 = mem[0x30] = 31   (LOAD does not set flags)
             BPZ(1),           # taken: N is still 0, from the SHR six back
             ADD(2, 2),        # skipped
             SUB(3, 1)])       # 48 - 31 = 17
    await sp.load(prog)                   # load() also writes the parking loop
    model = Golden(prog + [PARK])         # so the model gets it too

    # 30 instructions in memory; 29 execute, because BPZ skips one.
    steps, problem = await trace(sp, 29, model=model)
    assert problem is None, f"{problem}\n\nthe program:\n{listing(prog)}"

    mismatches = compare_memory(model, sp)
    assert not mismatches, (
        "memory disagrees with the model at: " +
        ", ".join(f"0x{a:02X} (model {m}, chip {d})" for a, m, d in mismatches))

    dut._log.info(f"{len(steps)} instructions, every register / PC / flag / byte "
                  f"of memory agreed with golden.py")
