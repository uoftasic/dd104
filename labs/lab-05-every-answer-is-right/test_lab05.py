"""
DD104 Lab 05 — every answer is right and it is still broken.

    make blind      an architecturally complete testbench, blind to both bugs
    make new        deal a mystery core
    make hunt       this file against it
    make verdict    the grade

Run `make blind` first, before you read any further.

Both cores in this lab's pool produce correct values in every register, correct
flags, a correct PC and correct memory, for every program you can write.  The
golden model agrees with them completely.  Your Lab 04 suite passes on them.

They are still broken, and on real silicon both of them would be found by a
customer rather than by you.

────────────────────────────────────────────────────────────────────────────
WHAT IS LEFT WHEN THE VALUES ARE ALL RIGHT
────────────────────────────────────────────────────────────────────────────
Three things, and this lab is about all three:

  `done`   pulses high for one cycle as each instruction retires. Anything
           outside the core that wants to know "has an instruction finished"
           watches this pin -- a debugger, a performance counter, a
           scoreboard in a testbench.

  `halt`   is high while the core is sitting in IDLE. While RUN is asserted
           it should stay low, continuously, with no gaps.

  cycles   `sp.run()` returns an exact clock count. Every instruction on this
           machine has a documented cost: ORI 5, ADD/SUB/NAND/SHL/SHR/LOAD 4,
           STORE and every branch 3. A program's cycle count is therefore
           predictable to the digit, and a design that produces every right
           answer one cycle late is a design that missed its timing budget.

None of the three is architectural state. None of them appears in `golden.py`.
That is not an oversight in the model -- a model of the instruction set has
nothing to say about a handshake -- it is the reason a suite needs more than
one kind of test in it.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
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

@cocotb.test(timeout_time=5, timeout_unit="ms")
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

@cocotb.test(timeout_time=5, timeout_unit="ms")
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
    first one tells you the shortfall is one instruction, and there is only one
    instruction in that program that appears exactly once.
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

    assert pulses > 0, (
        f"the core never pulsed `done` at all in {cycles} cycles -- nothing "
        f"retired.\n  {sp.describe()}")


# ─────────────────────────────────────────────────────────────────────────────
# TODO — the tests you write
# ─────────────────────────────────────────────────────────────────────────────
#
# Two more shapes, and between them they cover this lab's whole pool.
#
#   * `halt` must stay low for the entire time RUN is asserted.
#     `await sp.count_halt_cycles(n)` runs the loaded program for n cycles of
#     execution and returns how many of them had `halt` high. While the core is
#     running that number has exactly one correct value.
#
#     A core that drops into IDLE for a single cycle and then restarts itself
#     computes every right answer, in the right order, into the right places.
#     It just does it more slowly, and anything watching `halt` to decide
#     whether the processor is running sees it stop and start.
#
#   * The cycle count itself. `sp.run()` returns it. The instruction costs are
#     in the docstring at the top of this file and in ../common/README.md, so
#     the expected total for any straight-line program is arithmetic, not
#     measurement. Assert it, and put the arithmetic in the message.
#
#     This is the check that turns "it is one cycle slow" from a thing nobody
#     notices into a red row with a number attached.
#
# `make hunt` runs this file against the core you were dealt. `make verdict`
# grades it. Row 2 -- your testbench FAILING on the dealt core -- is the
# deliverable.
