"""
DD104 Lab 05 — a reference solution.

Do not open this before your own `make verdict` is green on both bugs.

    cp solutions/test_lab05.py test_solution.py
    make hunt TB=test_solution
    make verdict TB=test_solution

t01 is unchanged.  t02 has its exact count asserted.  t03 and t04 are new, and
the three of them together check the only three things about this processor
that are not architectural state: the `done` pin, the `halt` pin, and the
clock.
"""

import cocotb

from simproc import SimProc
from simproc_asm import assemble, listing


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
# 1.  The architecture is fine.  Watch.
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t01_every_value_is_correct(dut):
    """Registers and memory, checked after the program runs.

    This test passes on the golden core and on both broken ones. It is here so
    that the first line of your own hunt is a green row you can trust: whatever
    is wrong with the core you were dealt, it is not this."""
    sp = SimProc(dut)
    await sp.start()
    prog = assemble(PROGRAM)

    await sp.run(prog)

    assert sp.reg(1) == 39, f"r1 is {sp.reg(1)}, expected 39"
    assert sp.reg(3) == 0x20, f"r3 is {sp.reg(3)}, expected 0x20"
    assert sp.peek(0x20) == 39, (
        f"mem[0x20] is {sp.peek(0x20)}, expected 39.\n  {sp.describe()}")

    dut._log.info(f"{sp.describe()}")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  A scoreboard triggered on `done`
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t02_the_scoreboard_that_stopped_scoring(dut):
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
async def t03_halt_stays_low_while_running(dut):
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
async def t04_the_program_takes_exactly_37_cycles(dut):
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
