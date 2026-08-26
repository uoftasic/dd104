"""The baud sweep: does the link work at every clk_per_bit the wrapper can build?

Two checks per setting, and the second one is the point:

  1. PING must answer 0xAA.
  2. A byte must survive a WRITE / READ round trip.

A link can pass (1) and fail (2).  0xF0 already has bit 7 set, so a receiver
that samples the last data bit one bit-time late reads the stop bit -- also 1 --
and PING comes back perfect over a link that cannot carry data.
"""
import cocotb
from cocotb.clock import Clock
from simproc import SimProcBus

# uio_in -> clk_per_bit is x4 in the wrapper: 1->4, 2->8, 4->16, 8->32 ...
SWEEP = (1, 2, 4, 8, 16, 32, 64)
PATTERN = (0x5A, 0xC3, 0x80, 0x01, 0xFF, 0x00)


@cocotb.test()
async def baud_sweep(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    rows, bad = [], []
    for uio in SWEEP:
        bus = SimProcBus(dut, uio=uio)
        await bus.reset()
        ping, rt = "----", "----"
        try:
            v = await bus.ping()
            ping = f"0x{v:02X}" if v == 0xAA else f"0x{v:02X} WRONG"
            if v != 0xAA:
                bad.append((uio, bus.cpb, "PING"))
        except Exception as e:
            ping = type(e).__name__
            bad.append((uio, bus.cpb, "PING"))
        try:
            wrong = 0
            for val in PATTERN:
                await bus.write(0x10, val)
                if await bus.read(0x10) != val:
                    wrong += 1
            rt = f"{len(PATTERN) - wrong}/{len(PATTERN)}"
            if wrong:
                bad.append((uio, bus.cpb, "round-trip"))
        except Exception as e:
            rt = type(e).__name__
            bad.append((uio, bus.cpb, "round-trip"))
        rows.append((uio, bus.cpb, ping, rt))

    dut._log.info("  uio_in  clk_per_bit   PING    bytes back")
    for uio, cpb, ping, rt in rows:
        dut._log.info(f"  {uio:6d}  {cpb:11d}   {ping:9s} {rt}")
    assert not bad, ("the link fails at " +
                     ", ".join(f"clk_per_bit={c} ({w})" for _, c, w in bad))
