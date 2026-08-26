"""
DD104 Lab 02 — meeting SimProc, and its test suite.

    make shuttle    the test the chip shipped with, against all fourteen cores
    make sim        this file, against the golden core
    make check      this file, against a broken one

This file ships working: `make sim` is green before you change anything.
`make check` is not, and closing that gap is the lab.

SimProc is a real 8-bit processor.  Four registers, 64 bytes of memory, sixteen
opcodes, a UART for loading programs and poking at memory, and 1,178 lines of
SystemVerilog.  A student team designed it and taped it out.

It shipped with one test.  You are about to read it.
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

    ── TODO ──────────────────────────────────────────────────────────────────
    Run `make check`.  It runs this file against the golden core and then
    against `B01_sub_operands_swapped`, a core whose subtractor computes
    `B - A` instead of `A - B`, and it will tell you that this test passes on
    both.  A test that passes on a processor with a backwards subtractor is not
    testing the subtractor.

    Add a test that catches it.  The trap is worth understanding before you
    write it: `A - B` and `B - A` are the same number whenever `A == B`, and
    also when the difference is exactly 128.  That is 512 of the 65,536
    possible operand pairs.  `SUB rX, rX` — the idiom for 'clear a register',
    which is in nearly every program on this machine — is one of the 512.

    So: subtract two registers holding *different* values, and check the
    result.  `set_reg(1, 200) + set_reg(2, 60) + [SUB(1, 2)]` leaves r1 at
    200 - 60 = 140 on the good core.  Work out what the broken one gives, then
    let `make check` tell you whether you were right.
    ──────────────────────────────────────────────────────────────────────────
    """
    sp = SimProc(dut)
    await sp.start()

    cycles = await sp.run([ORI(5)])          # r0 = r0 | 5, and r0 is 0 after reset

    assert sp.reg(0) == 5, f"r0 is {sp.reg(0)}, expected 5.  {sp.describe()}"
    dut._log.info(f"one ORI, {cycles} clock cycles, r0 = {sp.reg(0)}")
