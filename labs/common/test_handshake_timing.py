"""DD104 — how long the chip's receiver is busy, measured.

    make sim TB=test_handshake_timing

This file exists because of one sentence in `simproc.py`'s `send_byte`:

    "That trailing idle is not politeness, it is required."

Everything here is a measurement of *why*.  It is the worked example for
`docs/guide/the-handshake-is-the-contract.md`.

Nothing in here needs the processor to execute anything.  The whole subject is
the wire.
"""

# Every test here carries a wall-clock guard. cocotb's timeout_time raises
# SimTimeoutError instead of spinning forever, which matters most in the bug-hunt
# labs: a core with a seeded bug can simply never finish, and a bisecting loop that
# waits for a signal that never arrives will otherwise run until you kill it.
# 5 ms is ~150x the longest legitimate run in this course (33,290 ns).
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.utils import get_sim_time

from simproc import SimProc, CMD_SET_PC, CMD_PING, CMD_RUN
from simproc_asm import ORI


RX_STATES = ["IDLE", "START", "RECEIVE", "DONE"]

# The command t02 sends, as three bytes: SET_PC with an address and an ignored
# data byte.  Change the address here and everything in t02 follows, because
# nothing in t02 is written as a constant -- see the "Try this" in
# docs/guide/the-handshake-is-the-contract.md.
COMMAND = (CMD_SET_PC, 12, 0)


async def watch_rx(sp, cycles):
    """Record (state_name, how_many_clocks) for the receiver, for `cycles`.

    A plain state monitor, and the only thing in this file that is not
    obvious.  It reads UART_RX1.state on every rising edge and collapses runs
    of the same value — so the answer is a list of dwell times, which is the
    shape of the question 'how long is it busy?'."""
    rx = sp.sys.UART1.UART_RX1
    runs = []
    for _ in range(cycles):
        await RisingEdge(sp.dut.clk)
        name = RX_STATES[int(rx.state.value)]
        if runs and runs[-1][0] == name:
            runs[-1][1] += 1
        else:
            runs.append([name, 1])
    return [(n, c) for n, c in runs]


async def watch_bytes_in(sp, cycles):
    """Every byte the chip's receiver actually accepted, in order.

    Not what you sent -- what it heard.  RXdone pulses for one clock when a
    frame has been decoded, and RXout holds the byte."""
    rx = sp.sys.UART1.UART_RX1
    got, prev = [], "0"
    for _ in range(cycles):
        await RisingEdge(sp.dut.clk)
        now = str(rx.RXdone.value)
        if now == "1" and prev != "1":
            got.append(int(rx.RXout.value))
        prev = now
    return got


async def send_frame_only(sp, value):
    """One 8N1 frame and NOTHING else — no trailing idle.

    This is `SimProc.send_byte` with its last two lines deleted.  It is what
    almost everybody writes the first time, and it is wrong."""
    frame = [0] + [(value >> i) & 1 for i in range(8)] + [1]
    for b in frame:
        sp.dut.ui_in.value = b
        await ClockCycles(sp.dut.clk, sp.clk_per_bit)


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t01_where_the_receiver_spends_its_time(dut):
    """Send one byte. Measure every state the receiver sits in, in clocks."""
    sp = SimProc(dut)
    await sp.start()
    cpb = sp.clk_per_bit                       # 32 at the default uio = 8

    watcher = cocotb.start_soon(watch_rx(sp, 16 * cpb))
    await sp.send_byte(0x99)
    runs = await watcher

    busy = [(n, c) for n, c in runs if n != "IDLE"]
    dut._log.info(f"clk_per_bit = {cpb}; receiver states: "
                  + "  ".join(f"{n}={c}" for n, c in busy))

    names = [n for n, _ in busy]
    assert names == ["START", "RECEIVE", "DONE"], (
        f"expected the receiver to walk START -> RECEIVE -> DONE exactly once, "
        f"got {names}")

    start_c, recv_c, done_c = (c for _, c in busy)

    assert start_c == ((cpb - 1) >> 1) + 1, (
        f"START lasted {start_c} clocks, expected {((cpb - 1) >> 1) + 1}.\n"
        f"  The RTL leaves START when clkCount == (clk_per_bit-1)>>1 = "
        f"{(cpb - 1) >> 1}, and clkCount starts at 0 -- so it occupies\n"
        f"  {(cpb - 1) >> 1} + 1 clocks. That off-by-one is the difference "
        f"between the page and the code, and the code wins.")

    assert recv_c == 9 * cpb, (
        f"RECEIVE lasted {recv_c} clocks, expected 9 x {cpb} = {9 * cpb} -- "
        f"eight data bits and the parity bit.")

    assert done_c == cpb, (
        f"DONE lasted {done_c} clocks, expected one whole bit period ({cpb}).\n"
        f"  THIS is the one nobody budgets for. The frame is over; the "
        f"receiver is not.")

    total = start_c + recv_c + done_c
    frame = 10 * cpb                            # start + 8 data + stop, as sent
    dut._log.info(
        f"the frame on the wire is {frame} clocks; the receiver is busy for "
        f"{total} -- {total - frame} clocks LONGER, which is "
        f"{(total - frame) / cpb:.2f} of a bit period")
    assert (total, frame) == (336, 320), (
        f"at clk_per_bit=32 this should be 336 busy vs 320 on the wire, "
        f"got {total} vs {frame}")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t02_the_gap_is_not_politeness(dut):
    """The same three bytes, sent back to back with no idle between frames.

    Every byte is correct. Every bit period is correct. The command is
    SET_PC with the address in COMMAND, and the chip sets the PC to something
    else -- specifically, to that address shifted right one bit with the stop
    bit arriving as its new top bit."""
    sp = SimProc(dut)
    await sp.start()

    await sp.uart_cmd(COMMAND[0], addr=COMMAND[1])   # the harness, doing it properly
    good = sp.pc()
    assert good == COMMAND[1], (
        f"the polite version should have set the PC to {COMMAND[1]}; got {good}")

    await sp.reset()
    heard = cocotb.start_soon(watch_bytes_in(sp, 44 * sp.clk_per_bit))
    for b in COMMAND:                           # the same bytes, no gaps
        await send_frame_only(sp, b)
    sp.dut.ui_in.value = 1
    await ClockCycles(sp.dut.clk, 4 * sp.clk_per_bit)
    bad = sp.pc()
    got = await heard

    dut._log.info("sent    : " + " ".join(f"0x{b:02X}" for b in COMMAND))
    dut._log.info("received: " + " ".join(f"0x{b:02X}" for b in got))
    dut._log.info(f"with the inter-frame gap: PC = {good}.  "
                  f"Without it: PC = {bad}.")
    sent = list(COMMAND)
    late = [sent[0]] + [(b >> 1) | 0x80 for b in sent[1:]]
    dut._log.info("if every frame after the first were sampled ONE BIT PERIOD "
                  "LATE, they would arrive as: "
                  + " ".join(f"0x{b:02X}" for b in late))

    # Three things are true for ANY three bytes, and they are the ones worth
    # asserting.  The exact corruption is NOT one of them -- see below.
    assert got[:1] == sent[:1], (
        f"the FIRST frame must arrive intact: the receiver was idle before it. "
        f"Sent 0x{sent[0]:02X}, got {[hex(b) for b in got[:1]]}")
    assert got != sent, (
        f"expected the gapless version to corrupt something. It did not, which "
        f"means the receiver's DONE state has changed and this page needs "
        f"re-measuring.")
    assert bad != good, (
        f"expected the gapless version to land somewhere other than "
        f"{good}; got {bad}")

    # And for the command this file ships with, the corruption is exactly the
    # clean one-bit-period slip, so pin it to the digit.
    if tuple(sent) == (CMD_SET_PC, 12, 0):
        assert got == late and bad == late[1], (
            f"with SET_PC 12 the slip is clean: expected {[hex(b) for b in late]} "
            f"and PC = {late[1]}; got {[hex(b) for b in got]} and PC = {bad}")


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t03_a_ping_still_works_without_the_gap(dut):
    """...and this is why nobody catches it.

    PING ignores its address and data bytes, so the two frames that get
    mangled are the two nobody reads. The reply is 0xAA either way."""
    sp = SimProc(dut)
    await sp.start()
    for b in (CMD_PING, 0, 0):
        await send_frame_only(sp, b)
    sp.dut.ui_in.value = 1
    reply = await sp.recv_byte()
    dut._log.info(f"gapless PING answered 0x{reply:02X} -- a green light on a "
                  f"link that just corrupted two of its three bytes")
    assert reply == 0xAA, f"PING answered 0x{reply:02X}, expected 0xAA"


@cocotb.test(timeout_time=5, timeout_unit="ms")
async def t04_what_a_command_costs_and_the_head_start(dut):
    """Two numbers every SimProc testbench depends on and nobody derives.

    A command is three frames plus the harness's own trailing gap, and the
    chip acts on it BEFORE the last stop bit has finished going out."""
    sp = SimProc(dut)
    await sp.start()
    cpb = sp.clk_per_bit

    t0 = get_sim_time("ns")
    await sp.uart_cmd(CMD_PING)
    cost = round((get_sim_time("ns") - t0) / sp.clock_ns)
    predicted = 3 * (11 * cpb) + (cpb + 16)
    dut._log.info(f"one 3-byte command costs {cost} clock cycles "
                  f"= 3 x 11 x {cpb} (frame + gap) + {cpb} + 16 = {predicted}")
    assert cost == predicted == 1104, (
        f"a command took {cost} clocks; the arithmetic says {predicted} and "
        f"the course quotes 1104")
    await sp.recv_byte()

    # The head start: how far into the RUN command the core begins fetching.
    await sp.load([ORI(1), ORI(2), ORI(4), ORI(8)])
    await sp.set_pc(0)

    marks = {}

    async def watch_first_fetch():
        was = sp.fsm()
        while True:
            await RisingEdge(sp.dut.clk)
            now = sp.fsm()
            if now == "CYCLE_1" and was != "CYCLE_1":
                marks["fetch"] = get_sim_time("ns")
                return
            was = now

    task = cocotb.start_soon(watch_first_fetch())
    t0 = get_sim_time("ns")
    await sp.uart_cmd(CMD_RUN)
    marks["cmd_returned"] = get_sim_time("ns")
    await task
    head = round((marks["cmd_returned"] - marks["fetch"]) / sp.clock_ns)
    dut._log.info(f"the core fetched its first instruction {head} clock cycles "
                  f"BEFORE uart_cmd(RUN) returned")
    assert head == 57, (
        f"the head start is {head} clocks, not the 57 this course quotes. Any "
        f"monitor started after start_running() has already missed that much.")
    await sp.stop_running()
