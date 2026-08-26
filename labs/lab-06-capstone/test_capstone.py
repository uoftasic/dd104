"""
DD104 Lab 06 — the capstone.  Your suite is the deliverable.

    make new         deal one of the three hard bugs
    make hunt        this file against it
    make verdict     the grade for that hunt
    make check-all   this file against all thirteen broken cores

There is no scaffolding in this file beyond what you already know how to
write, and that is deliberate.  Five labs in, you have the harness, the golden
model, a working idea of where bugs hide, and a suite of your own.  What this
lab supplies is framing and a verdict.

────────────────────────────────────────────────────────────────────────────
THE THREE IN THIS LAB'S POOL, DESCRIBED WITHOUT BEING GIVEN AWAY
────────────────────────────────────────────────────────────────────────────
Each one survives a specific, reasonable habit.  None of them is subtle in the
RTL; all three are subtle in the *stimulus*.

  * One is a wrong operator that agrees with the right one on every value you
    would naturally pick.  Two operations that produce the same answer on the
    inputs a sensible person tries are not distinguishable by a sensible
    person's test.  Find the inputs where they disagree, and drive those.

  * One is hidden by reset.  After a reset, several parts of the machine hold
    the same value -- zero -- and while that is true, a result landing in the
    wrong place is indistinguishable from a result landing in the right place.
    Any test whose program is short enough to be readable is a test that runs
    entirely inside that window.

  * One is invisible at the default setting of a parameter, and the link test
    everybody starts with passes over the broken link. `PING -> 0xAA` proves
    two wires are connected. It does not prove they can carry a byte, and the
    reason is a property of the specific bytes 0xF0 and 0xAA.

────────────────────────────────────────────────────────────────────────────
THE COVERAGE LIST
────────────────────────────────────────────────────────────────────────────
Not a checklist to tick. A list of questions to ask about your own suite, and
the answer to each one is a number you can go and measure.

    instructions      Which of the sixteen opcodes has my suite never
                      executed? Including the three unimplemented ones.
    operands          For each instruction, have I run it with rA == rB and
                      with rA != rB?
    fields            Every shift amount (4). Every branch displacement (16).
                      Every 5-bit ORI immediate that overlaps bits already set.
    registers         Has each of the four been a source, a destination, a
                      pointer, and a bystander that must not move?
    flags             Have I asserted N and Z after every flag-setting
                      instruction, and asserted that they do NOT move after
                      the ones that leave them alone?
    memory            Address 0. Address 63. An address above 63.
    protocol          `done` counted. `halt` counted. Cycle counts asserted.
    parameters        clk_per_bit, swept -- not sampled at its default.
    state             Does anything in my suite run for long enough to leave
                      the window where reset has made everything equal?

────────────────────────────────────────────────────────────────────────────
THE HARNESS, IN ONE SCREEN
────────────────────────────────────────────────────────────────────────────
    sp = SimProc(dut); await sp.start()   clock, reset, RAM blanked
    await sp.run(prog) -> cycles          load, run to the parking loop
    await sp.step(n)                      execute exactly n instructions
    await sp.run_cycles(n)                free-run for n cycles of execution
    sp.reg(i)  sp.regs()  sp.pc()  sp.flags()  sp.fsm()
    sp.peek(a)  sp.poke(a, v)             the memory backdoor
    sp.halt  sp.done                      the pins, as '0' / '1' / 'x'
    await sp.count_done_pulses(n)         one pulse per retired instruction
    await sp.count_halt_cycles(n)         zero, while RUN is asserted
    await sp.uart_ping()                  0xAA
    await sp.uart_read(a)  uart_write(a, v)
    await sp.set_baud(uio)                clk_per_bit = uio * 4
    await trace(sp, n, model=g)           compare against golden.py per step

Full reference: ../common/README.md and the docstrings in ../common/simproc.py.

────────────────────────────────────────────────────────────────────────────
Start by bringing your Lab 04 and Lab 05 tests in here -- copy them into this
file, or import them. `make check-all` scores whatever this module contains.
────────────────────────────────────────────────────────────────────────────
"""

import cocotb

from simproc import SimProc, PARK, trace
from simproc_asm import (ORI, ADD, SUB, NAND, SHL, SHR, LOAD, STORE,
                         JMP, BZ, BNZ, BPZ, assemble, listing, set_reg)
from golden import Golden, compare_memory


@cocotb.test()
async def t01_the_chip_answers(dut):
    """A PING, and a warning about what it proves.

    This is the one test this file ships with, and it ships with it so that
    the first row of your capstone run is the sentence this lab most wants you
    to distrust.

    0xF0 goes out, 0xAA comes back, and both of those bytes are unusually
    forgiving. `PING` answering correctly proves that the TX pin, the RX pin,
    the command decoder and the reply path are all connected. It does not
    prove that the link can carry an arbitrary byte at an arbitrary speed, and
    one of the three bugs in this lab's pool lives in precisely that gap."""
    sp = SimProc(dut)
    await sp.start()

    reply = await sp.uart_ping()
    assert reply == 0xAA, f"PING answered 0x{reply:02X}, expected 0xAA"

    dut._log.info(f"PING -> 0x{reply:02X} at the default clk_per_bit = 32. "
                  f"That is one byte, at one speed, in one direction.")


# ─────────────────────────────────────────────────────────────────────────────
# Everything else in this file is yours.
#
# `make check-all` prints, for each of the thirteen bugs, `caught` or `MISSED`
# and -- for the ones you missed -- the one-line description of what that bug
# hides behind. Use that list as your work queue. It is the only place in this
# course where you are handed a hint after failing, and you have earned it by
# then.
# ─────────────────────────────────────────────────────────────────────────────
