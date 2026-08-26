"""DD104 — one test, two simulators, two different answers.

    make sim TB=test_two_simulators SIM=icarus
    make sim TB=test_two_simulators SIM=verilator

Both runs simulate exactly 60,520.00 ns.  Both pass.  They disagree about what
the chip put on its TX pin, and neither of them is wrong.

This is the worked example for `docs/guide/two-simulators-two-jobs.md`.

The design under test has a real defect: `dp_ram` is 64 bytes deep and the
address bus is 8 bits wide, so addresses 64..255 are off the end of the array.
Verilator says so statically, before running anything:

    verilator --lint-only --timescale 1ns/1ps --top-module tb \\
        rtl/tt_um_ieeeuoftasic_simproc.sv rtl/simproc_system.sv rtl/tb.v

    %Warning-WIDTHTRUNC: rtl/simproc_system.sv:848:16: Bit extraction of
                         array[63:0] requires 6 bit index, not 8 bits.

Icarus never mentions it, and shows it to you at run time as an X on a pin --
if your test happens to read one of those addresses.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb
from cocotb.triggers import RisingEdge

from simproc import SimProc, CMD_READ
from simproc_asm import ORI, ADD


async def read_raw(sp, addr, timeout_cycles=20000):
    """READ over the wire, returning the eight characters the TX pin produced.

    `SimProc.recv_byte` refuses a frame containing an X, which is the right
    behaviour for a test -- but here the X *is* the subject, so we take the
    bit string instead of an int."""
    await sp.uart_cmd(CMD_READ, addr, 0)
    for _ in range(timeout_cycles):
        if sp._rx:
            return sp._rx.pop(0)
        await RisingEdge(sp.dut.clk)
    raise TimeoutError(f"no reply to READ {addr} in {timeout_cycles} clocks")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def s01_the_same_read_off_the_end_of_the_ram(dut):
    """Read address 100. The RAM has 64 entries. Ask each simulator what happens."""
    sp = SimProc(dut)
    await sp.start()

    sim = cocotb.SIM_NAME.lower()
    sp.poke(36, 0x5A)                       # 100 - 64 == 36; mark it
    await RisingEdge(dut.clk)

    in_range = await read_raw(sp, 36)
    off_end = await read_raw(sp, 100)

    dut._log.info(f"simulator: {cocotb.SIM_NAME}")
    dut._log.info(f"READ  36  (in range)      -> {in_range}")
    dut._log.info(f"READ 100  (off the end)   -> {off_end}")

    assert in_range == "01011010", (
        f"address 36 holds 0x5A, so this must read back 01011010; got {in_range}")

    if "icarus" in sim:
        assert off_end == "XXXXXXXX", (
            f"Icarus is 4-state: mem[100] on a 64-entry array is X, and the X "
            f"propagates all the way out of the chip. Got {off_end}.")
        dut._log.info(
            "Icarus is 4-STATE. The read is out of bounds, the array yields X, "
            "and eight X bits leave the chip on a pin. That is a loud, "
            "correct answer -- and you only get it if your stimulus happens "
            "to read address 100.")
    else:
        assert off_end == "01011010", (
            f"Verilator is 2-state: it truncated 100 to 6 bits (100 & 63 = 36) "
            f"and handed back the byte at address 36. Got {off_end}.")
        dut._log.info(
            "Verilator is 2-STATE. There is no X to propagate, so 100 was "
            "truncated to 6 bits -- 100 & 63 = 36 -- and you got the byte from "
            "address 36. A plausible wrong answer, silently. Verilator told "
            "you about this line at LINT time instead; Icarus never does.")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def s02_simulated_time_is_identical(dut):
    """The thing the two simulators never disagree about.

    Wall clock differs by 2-3x in both directions depending on the run. The
    simulated time does not move: the design is the same state machine either
    way, and a cycle count you measure under one is valid under the other."""
    sp = SimProc(dut)
    await sp.start()
    cycles = await sp.run([ORI(5), ADD(1, 0)])      # 5 cycles + 4 cycles
    assert (sp.reg(1), cycles) == (5, 9), (
        f"r1={sp.reg(1)} after {cycles} cycles, expected 5 after 9")
    dut._log.info(f"{cocotb.SIM_NAME}: r1 = {sp.reg(1)} in {cycles} clock "
                  f"cycles -- ORI is 5 and ADD is 4, on both simulators")
