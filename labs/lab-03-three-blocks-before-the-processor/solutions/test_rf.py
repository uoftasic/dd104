"""
DD104 Lab 03 — a reference solution for test_rf.py.

Do not open this before your own three tests run.

    cp solutions/test_rf.py test_rf_solution.py
    make rf TB_RF=test_rf_solution

Five tests, and after them there is no behaviour left in `register_file` that
is untested: reset, write, read, isolation, and the write enable.  That is the
whole module.
"""

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


@cocotb.test()
async def t01_reset_clears_all_four(dut):
    """After reset every register reads 0 on both ports."""
    await setup(dut)
    for i in range(4):
        a, b = await read(dut, i, i)
        assert (a, b) == (0, 0), f"after reset r{i} reads dataA={a} dataB={b}"
    dut._log.info("all four registers are 0 after reset")


@cocotb.test()
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


@cocotb.test()
async def t03_r0_is_not_special(dut):
    """r0 is an ordinary register.  It is not hardwired to zero.

    This is the architectural fact worth carrying out of Lab 03, and it is
    worth carrying because most of the small processors you will meet do the
    opposite.  RISC-V's `x0` reads as zero and discards writes; MIPS's `$zero`
    does the same.  Assuming SimProc works that way is a completely reasonable
    assumption and it is wrong.

    Two writes, not one.  A file that latched the first write and then stuck
    would pass a single-write version of this test."""
    await setup(dut)

    await write(dut, 0, 0xFF)
    a, _ = await read(dut, 0, 0)
    assert a == 0xFF, (
        f"wrote 0xFF into r0 and read back 0x{a:02X}. If this is 0x00, r0 is "
        f"hardwired to zero and every ORI in this course means something "
        f"different from what the writeups say.")

    await write(dut, 0, 0x5A)
    a, _ = await read(dut, 0, 0)
    assert a == 0x5A, f"second write to r0 read back 0x{a:02X}, expected 0x5A"

    dut._log.info("r0 holds what you put in it -- it is a normal register")


@cocotb.test()
async def t04_a_write_disturbs_nothing_else(dut):
    """One write moves one register.  Snapshot, write, snapshot, compare."""
    await setup(dut)
    values = [0x11, 0x22, 0x44, 0x88]
    for i, v in enumerate(values):
        await write(dut, i, v)

    before = [(await read(dut, i, 0))[0] for i in range(4)]
    await write(dut, 2, 0xEE)
    after = [(await read(dut, i, 0))[0] for i in range(4)]

    assert after[2] == 0xEE, f"r2 is 0x{after[2]:02X}, expected the 0xEE we wrote"
    for i in (0, 1, 3):
        assert after[i] == before[i], (
            f"writing to r2 also changed r{i}: 0x{before[i]:02X} -> "
            f"0x{after[i]:02X}. One write is supposed to move one register.")

    dut._log.info(f"before {[hex(v) for v in before]} -> after {[hex(v) for v in after]}")


@cocotb.test()
async def t05_no_write_without_RFWrite(dut):
    """RFWrite = 0 holds, for several cycles, with live data on the bus.

    Several cycles, because 'it did not write on the first edge' and 'it does
    not write' are different claims and only the second one is the
    requirement."""
    await setup(dut)
    await write(dut, 1, 0x3C)

    dut.RFWrite.value = 0
    dut.regW.value = 1
    for junk in (0x00, 0xFF, 0xA5, 0x3C):
        dut.dataW.value = junk
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        a, _ = await read(dut, 1, 0)
        assert a == 0x3C, (
            f"with RFWrite = 0 and dataW = 0x{junk:02X}, r1 moved to "
            f"0x{a:02X}. It should still be 0x3C.")

    dut._log.info("four cycles with RFWrite low and live data on dataW: nothing moved")
