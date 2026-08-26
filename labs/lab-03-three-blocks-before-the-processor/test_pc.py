"""
DD104 Lab 03 — the program counter.  Fifteen lines of RTL, verified completely.

    make pc

    module program_counter (
        input  logic            clk,
        input  logic            rst,
        input  logic    [7:0]   pc_in,
        input  logic            pc_wr,
        output logic    [7:0]   pc_out
    );
        always_ff @ (posedge clk) begin
            if (rst)         pc_out <= 8'b0;
            else if (pc_wr)  pc_out <= pc_in;
        end
    endmodule

That is the entire module.  It is an 8-bit register with a synchronous reset
and a load enable, and there are exactly four things it can be asked to do:
reset, load, hold, and reset-while-loading.  This file tests all four, and when
it passes there is no behaviour left in `program_counter` that is untested.

You will almost never be able to say that sentence about a design.  Say it
here, out loud, because it is the thing that makes unit testing worth the
trouble: a small block can be *finished*.  A 1,178-line processor cannot.

This file ships complete.  Read it, run it, and use it as the model for the
register-file tests you write in `test_rf.py`.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def setup(dut):
    """Start a 10 ns clock and put the PC in a known state.

    Everything here drives on the falling edge and samples after the rising
    edge.  That is not decoration — it is the single most common source of
    'my testbench is wrong' in a synchronous design.  Drive on one edge, sample
    on the other, and a race between your stimulus and the DUT's clock cannot
    happen."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.pc_wr.value = 0
    dut.pc_in.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


async def cycle(dut, rst, pc_wr, pc_in):
    """One clock cycle with these inputs.  Returns pc_out after the edge."""
    dut.rst.value = rst
    dut.pc_wr.value = pc_wr
    dut.pc_in.value = pc_in
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    return int(dut.pc_out.value)


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t01_reset_makes_it_zero(dut):
    """rst = 1 for one edge puts the counter at 0, from anywhere."""
    await setup(dut)
    await cycle(dut, rst=0, pc_wr=1, pc_in=0xA5)
    assert int(dut.pc_out.value) == 0xA5

    pc = await cycle(dut, rst=1, pc_wr=0, pc_in=0)
    assert pc == 0, f"after reset pc_out is 0x{pc:02X}, expected 0x00"


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t02_load_when_pc_wr(dut):
    """pc_wr = 1 loads pc_in on the next rising edge.  All 256 values."""
    await setup(dut)
    for v in range(256):
        pc = await cycle(dut, rst=0, pc_wr=1, pc_in=v)
        assert pc == v, f"loaded 0x{v:02X}, read back 0x{pc:02X}"
    dut._log.info("all 256 values load correctly")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t03_hold_when_not_pc_wr(dut):
    """pc_wr = 0 holds, no matter what is on pc_in.

    This is the test people skip, and it is the one that catches an enable
    wired to a constant.  A PC that loads correctly and never holds passes
    t02 perfectly."""
    await setup(dut)
    await cycle(dut, rst=0, pc_wr=1, pc_in=0x42)

    for junk in (0x00, 0xFF, 0x42, 0x13):
        pc = await cycle(dut, rst=0, pc_wr=0, pc_in=junk)
        assert pc == 0x42, (
            f"with pc_wr = 0 and pc_in = 0x{junk:02X}, pc_out moved to "
            f"0x{pc:02X}. It should still be 0x42.")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t04_reset_beats_load(dut):
    """rst and pc_wr both high: reset wins.

    Read the RTL and this is obvious — `if (rst)` comes first.  Test it
    anyway.  Priority between two control inputs is a decision somebody made,
    it is invisible from the port list, and the next person to touch this file
    can reverse it by swapping two branches."""
    await setup(dut)
    pc = await cycle(dut, rst=1, pc_wr=1, pc_in=0xFF)
    assert pc == 0, (
        f"with rst = 1 and pc_wr = 1 the counter went to 0x{pc:02X}. "
        f"Reset is supposed to win.")
