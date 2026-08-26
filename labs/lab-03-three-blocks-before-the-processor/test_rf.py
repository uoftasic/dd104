"""
DD104 Lab 03 — the register file.  Thirty lines of RTL, and the block you are
going to write the tests for.

    make rf

    module register_file (
        input  logic       clk, rst, RFWrite,
        input  logic [1:0] regA, regB, regW,
        input  logic [7:0] dataW,
        output logic [7:0] dataA, dataB
    );
        logic [7:0] rf[0:3];
        always_ff @ (posedge clk) begin
            if (rst)          rf[0] <= 0; rf[1] <= 0; rf[2] <= 0; rf[3] <= 0;
            else if (RFWrite) rf[regW] <= dataW;
        end
        always_comb begin
            dataA = rf[regA];
            dataB = rf[regB];
        end
    endmodule

(The reset branch really is four separate assignments in the source; it is
shown squashed here to fit.)

Four 8-bit registers.  Two combinational read ports, one synchronous write
port.  There is one architectural fact in this module that is worth knowing
before you write a single line of SimProc assembly, and t03 is where you
find it.

This file ships with t01 and t02 written and t03, t04 and t05 as TODOs.
`make rf` is green now and will stay green; `make rf` with three more tests
in it means something.
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
    """10 ns clock, one cycle of reset, everything idle."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.RFWrite.value = 0
    dut.regA.value = 0
    dut.regB.value = 0
    dut.regW.value = 0
    dut.dataW.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.rst.value = 0
    await Timer(1, unit="ns")


async def write(dut, reg, value):
    """One synchronous write.  Returns after the edge that performed it."""
    dut.RFWrite.value = 1
    dut.regW.value = reg
    dut.dataW.value = value
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.RFWrite.value = 0


async def read(dut, a, b):
    """Both read ports at once.  These are combinational — no edge involved."""
    dut.regA.value = a
    dut.regB.value = b
    await Timer(1, unit="ns")
    return int(dut.dataA.value), int(dut.dataB.value)


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t01_reset_clears_all_four(dut):
    """After reset every register reads 0 on both ports."""
    await setup(dut)
    for i in range(4):
        a, b = await read(dut, i, i)
        assert (a, b) == (0, 0), f"after reset r{i} reads dataA={a} dataB={b}"
    dut._log.info("all four registers are 0 after reset")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t02_write_then_read_back(dut):
    """Write a distinct value into each register and read all four back.

    The values are distinct on purpose.  Write 0x11 into every register and a
    register file that ignores `regW` and writes all four at once passes
    perfectly."""
    await setup(dut)
    values = [0x11, 0x22, 0x44, 0x88]
    for i, v in enumerate(values):
        await write(dut, i, v)

    for i, v in enumerate(values):
        a, _ = await read(dut, i, 0)
        assert a == v, f"r{i} reads 0x{a:02X}, expected 0x{v:02X}"
    dut._log.info(f"wrote {[hex(v) for v in values]}, read all four back")


# ─────────────────────────────────────────────────────────────────────────────
# TODO — three more tests.  Each one is five to ten lines.
# ─────────────────────────────────────────────────────────────────────────────

# t03_r0_is_not_special
#
#     Most small processors hardwire register 0 to the constant zero: writes to
#     it are discarded, reads always return 0.  RISC-V does. MIPS does.  It is
#     common enough that you should assume it until you have checked.
#
#     Check it.  Write 0xFF into r0 and read it back.  Then write into r0 a
#     second time with a different value and read it again — one write landing
#     is not proof, because a file that latches the first write and then sticks
#     would also pass.
#
#     Whatever you find, this test is the record of it.  What you find changes
#     how you read every ORI instruction in this course, so find it now rather
#     than at 1 a.m. in Lab 05.


# t04_a_write_disturbs_nothing_else
#
#     Fill all four registers with distinct values, write to r2, and check that
#     r0, r1 and r3 are untouched.  A decoder with an off-by-one, an index
#     wired to the wrong field, a write enable that is really a broadcast — all
#     three pass t02 and fail this.
#
#     The shape: snapshot all four, do one write, snapshot again, compare the
#     three that should not have moved.


# t05_no_write_without_RFWrite
#
#     Put a value on `dataW` and a register number on `regW` with RFWrite = 0,
#     clock it, and check nothing changed.  This is the same test as
#     `t03_hold_when_not_pc_wr` in test_pc.py and it catches the same class of
#     mistake: an enable that is not actually enabling anything.
#
#     Run it for several cycles, not one.  "It did not write on the first edge"
#     and "it does not write" are different claims.
