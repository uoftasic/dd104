"""
DD104 — the test SimProc actually shipped with.

This is `test/test.py` from the SimProc repository, unchanged apart from this
docstring and the comments marked DD104.  It is the TinyTapeout project
template, and nobody edited it, which is not unusual and not a scandal — it is
what almost every first tapeout looks like.

Run `make shuttle` to watch it pass on the golden core and on all thirteen
deliberately broken ones.

What it checks, decoded against the pin map in rtl/tt_um_ieeeuoftasic_simproc.sv:

    uo_out == 3   ==   0b00000011
                       bit 0 = uart_tx = 1   a serial line at rest
                       bit 1 = halt    = 1   the core is sitting in IDLE
                       bit 2 = done    = 0   nothing retired

So the assertion is: *the processor is not running.*  It never sends a UART
command, never loads a program, and never executes an instruction.
"""

# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def tt_um_ieeeuoftasic_simproc(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    # Set the input values you want to test
    dut.ui_in.value = 1
    dut.uio_in.value = 0

    # Wait for one clock cycle to see the output values
    await ClockCycles(dut.clk, 100)

    # The following assersion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
    assert dut.uo_out.value == 3

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.
