"""
DD104 Lab 02 — a reference solution.

Do not open this before your own `make check` says PASS.  The added test is
eight lines and the eight lines are not the point; the choice of operands is.

    cp solutions/test_lab02.py test_solution.py
    make check TB=test_solution

t01 and t02 are unchanged from the file you were given.  t03 has lost its TODO
block.  t04 is new, and it is the only test in the file that would notice if
the subtractor were wired backwards.
"""

import cocotb
from cocotb.triggers import ClockCycles

from simproc import SimProc
from simproc_asm import ORI, SUB, set_reg


# ─────────────────────────────────────────────────────────────────────────────
# 1.  The shipped test, reproduced here so you can read it in context
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t01_the_test_this_chip_shipped_with(dut):
    """`test/test.py` from the SimProc repository, in three lines.

    The real file is `../common/test_shuttle.py` and it is the TinyTapeout
    template with the module name changed.  What it does:

        dut.ui_in.value  = 1
        dut.uio_in.value = 0
        await ClockCycles(dut.clk, 100)
        assert dut.uo_out.value == 3

    Decode the 3 against the pin map in `../common/rtl/README.md`:

        uo_out[0] = uart_tx      1   the serial line, idle high
        uo_out[1] = halt         1   the core is sitting in IDLE
        uo_out[2] = done         0   no instruction retired this cycle
        uo_out[7:3]              0

    3 = 0b00000011.  This test asserts that the processor **is not running.**

    It sends no command.  It loads no program.  It executes no instruction.  It
    never sets `run`.  And it is the only test this chip has ever had."""
    sp = SimProc(dut)
    await sp.start()

    dut.ui_in.value = 1
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 100)

    assert int(dut.uo_out.value) == 3, f"uo_out is {int(dut.uo_out.value)}, expected 3"
    dut._log.info(f"uo_out = {int(dut.uo_out.value)}, and the core is {sp.fsm()}")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  The same three pins, read as three pins
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t02_what_that_number_meant(dut):
    """Same instant, same chip, the assertion written so a person can read it.

    This is not a better test.  It is exactly as strong as t01 — it passes on
    every broken core in the catalogue too.  It is a better *sentence*: when it
    fails, the message names the pin instead of handing you an integer to
    decode at 2 a.m.

    'Assert on the decoded meaning, not on the bus value' is a habit worth
    forming early, and it costs nothing."""
    sp = SimProc(dut)
    await sp.start()
    await ClockCycles(dut.clk, 100)

    assert sp.halt == "1", f"halt is '{sp.halt}' — the core should be in IDLE after reset"
    assert sp.done == "0", f"done is '{sp.done}' — nothing should be retiring"
    assert sp.fsm() == "IDLE", f"the FSM is in {sp.fsm()}, expected IDLE"

    dut._log.info(f"halt={sp.halt} done={sp.done} state={sp.fsm()} — "
                  f"this is a processor doing nothing, and t01 asserted exactly that")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Make it do something
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t03_one_instruction_that_actually_runs(dut):
    """Load a program, run it, and check a register.

    `sp.run(prog)` loads the program through the memory backdoor, starts the
    core, waits for the program to park itself, and returns an exact clock
    count.  `sp.reg(0)` reads r0 out of the register file.

    Three lines, and already infinitely stronger than the shipped test, because
    at least one instruction executed.

    t04 below is the test that makes this file worth running.
    """
    sp = SimProc(dut)
    await sp.start()

    cycles = await sp.run([ORI(5)])          # r0 = r0 | 5, and r0 is 0 after reset

    assert sp.reg(0) == 5, f"r0 is {sp.reg(0)}, expected 5.  {sp.describe()}"
    dut._log.info(f"one ORI, {cycles} clock cycles, r0 = {sp.reg(0)}")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  A subtraction that a swapped subtractor cannot survive
# ─────────────────────────────────────────────────────────────────────────────

@cocotb.test()
async def t04_subtract_two_different_numbers(dut):
    """200 - 60, on a machine where 512 of 65,536 operand pairs would lie.

    `A - B == B - A` exactly when `A == B`, and also when the difference is
    128 (because 128 is its own negation in eight bits).  That is 256 + 256 =
    512 pairs out of 65,536, and one of them — `SUB rX, rX` — is the idiom
    everybody reaches for to zero a register.  Write the natural test and you
    land in the 0.78 % of the input space where the bug is invisible.

    So the operands here are chosen to be outside it: 200 and 60.  On a correct
    core r1 ends at 140.  On a core with the operands swapped it is 60 - 200 =
    -140, which in eight bits is 116.  The two answers are 24 apart and neither
    is a special value, which is exactly what you want from a test vector."""
    sp = SimProc(dut)
    await sp.start()

    await sp.run(set_reg(1, 200) + set_reg(2, 60) + [SUB(1, 2)])

    assert sp.reg(1) == 140, (
        f"r1 is {sp.reg(1)}, expected 140 (200 - 60).\n"
        f"  If it is 116, the subtractor computed 60 - 200 = -140, which wraps "
        f"to 116: the operands are the right way round in your program and the "
        f"wrong way round in the hardware.\n"
        f"  {sp.describe()}")

    # N is 1 here, and if you predicted 0 you have just met the machine's
    # only opinion about signedness.  140 is 0b10001100; N is defined as
    # `ALUout[7]`, the top bit, with no notion of what the byte means.  Read
    # as unsigned, 200 - 60 = 140 is positive.  Read as signed, the same eight
    # bits are -116.  The ALU does not choose between those readings; N just
    # reports the bit, and `BPZ` will not branch here.
    n, z = sp.flags()
    assert (n, z) == (1, 0), (
        f"after 200 - 60 = 140 the flags are N={n} Z={z}, expected N=1 Z=0.\n"
        f"  140 = 0b10001100, and N is literally bit 7 of the result.")

    dut._log.info(f"200 - 60 = {sp.reg(1)}, flags N={n} Z={z}")
