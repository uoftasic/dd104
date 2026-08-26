"""One tiny program per variant, run on whatever core is in ../src.

The point is the numbers in the variant READMEs.  A student-facing bug report
that says "you will see the wrong answer" teaches nothing; one that says "you
will see 249 where 7 belongs" is a lead.  So every number quoted to a student
comes from this file, run on the clean core and on the buggy one, and the two
outputs are diffed.

Each demo prints one line:

    SYMPTOM <id>  R=[r0,r1,r2,r3]  mem{...}   -- <what the program computes>
"""
import cocotb
from cocotb.triggers import ClockCycles, RisingEdge
from simproc import *
from test_suite import boot, poke, peek, rf, FILL

RUN_CLOCKS = 300          # every demo below finishes in well under this


def setr0(v):
    """R0 <- v, for v <= 31."""
    return [SUB(0, 0), ORI(v)]


def copy0(k):
    """Rk <- R0."""
    return [SUB(k, k), ADD(k, 0)]


DEMOS = [
    ("bug-01", "R1 = 9, R0 = 2, then R1 = R1 - R0",
     setr0(9) + copy0(1) + setr0(2) + [SUB(1, 0)], {}, []),

    ("bug-02", "R1 = 0x33, R0 = 0x0F, then R1 = NAND(R1, R0)",
     setr0(3) + [SHL(0, 2), SHL(0, 2), ORI(3)] + copy0(1) + setr0(15) + [NAND(1, 0)], {}, []),

    ("bug-03", "R0 = 16 (not zero), then BZ over an ORI 1 that must run",
     setr0(16) + [BZ(1), ORI(1)], {}, []),

    ("bug-04", "R0 = 5, R1 = R1 + R0, R0 = 2, R1 = R1 + R0",
     setr0(5) + [SUB(1, 1), ADD(1, 0)] + setr0(2) + [ADD(1, 0)], {}, []),

    ("bug-05", "count R0 down from 3 with a backward BNZ",
     setr0(1) + copy0(1) + setr0(3) + [SUB(0, 1), BNZ(-2)], {}, []),

    ("bug-06", "R1 = 1 << 2, then R0 = 1 << 3",
     setr0(1) + [SHL(0, 2)] + copy0(1) + setr0(1) + [SHL(0, 3)], {}, []),

    ("bug-07", "R1 = 40 is the pointer, R0 = 0, then R0 = mem[R1]",
     setr0(8) + [SHL(0, 2), ORI(8)] + copy0(1) + [SUB(0, 0), LOAD(0, 1)],
     {40: 0x5A}, [40]),

    ("bug-09", "R0 = 0 sets Z, then BZ and BNZ both read that one compare",
     setr0(4) + [SUB(0, 0), BZ(1), ORI(16), BNZ(1), ORI(8)], {}, []),

    ("bug-10", "R0 = 0, ORI 5, ORI 3 -- the immediates share a bit",
     [SUB(0, 0), ORI(5), ORI(3)], {}, []),

    ("bug-11", "same two ORIs, watching both R0 and R1",
     [SUB(0, 0), SUB(1, 1), ORI(5), ORI(3)], {}, []),

    ("bug-11b", "one ORI only -- the first one after a reset",
     [SUB(0, 0), SUB(1, 1), ORI(5)], {}, []),

    ("bug-06b", "R1 = 64 built by adding, then R1 >> 3",
     setr0(16) + copy0(1) + [ADD(1, 0), ADD(1, 0), ADD(1, 0), SHR(1, 3)], {}, []),

    ("bug-10b", "R0 = 0, ORI 8, ORI 3 -- the immediates share no bits",
     [SUB(0, 0), ORI(8), ORI(3)], {}, []),

    ("bug-13", "three STOREs into mem[32..34]",
     setr0(16) + copy0(2) + [ADD(2, 0)] + setr0(7) + copy0(1)
     + [STORE(1, 2), ADD(1, 0), STORE(1, 2), ADD(1, 0), STORE(1, 2)],
     {}, [32]),
]


async def run_program(dut, bus, prog, preload):
    for a in range(64):
        poke(dut, a, FILL)
    for a, v in preload.items():
        poke(dut, a, v)
    for i, w in enumerate(prog):
        poke(dut, i, w)
    await ClockCycles(dut.clk, 2)
    await bus.reset()
    await bus.set_pc(0)
    await bus.run()
    await ClockCycles(dut.clk, RUN_CLOCKS)
    # Read the state BEFORE stopping: stop() pulses rst_n, which clears the
    # register file.  Only the RAM survives a reset.


@cocotb.test()
async def symptoms(dut):
    bus = await boot(dut, uio=8)
    for name, what, prog, preload, watch in DEMOS:
        await run_program(dut, bus, prog, preload)
        regs = [rf(dut, i) for i in range(4)]
        mem = " ".join(f"mem[{a}]={peek(dut, a)}" for a in watch)
        dut._log.info(f"SYMPTOM {name:8s} R={regs}  {mem}   -- {what}")
        await bus.stop()


@cocotb.test()
async def protocol_counters(dut):
    """done pulses per retired instruction, and halt while run is asserted."""
    bus = await boot(dut, uio=8)
    prog = (setr0(16) + copy0(2) + [ADD(2, 0)] + setr0(7) + copy0(1)
            + [STORE(1, 2), ADD(1, 0), STORE(1, 2), ADD(1, 0), STORE(1, 2)])
    for a in range(64):
        poke(dut, a, FILL)
    for i, w in enumerate(prog):
        poke(dut, i, w)
    await ClockCycles(dut.clk, 2)
    await bus.reset()
    await bus.set_pc(0)

    core = dut.tt_um_ieeeuoftasic_simproc.U1.CPU1
    c = {"instr": 0, "done": 0, "halt": 0}

    async def sampler():
        # Nothing counts until the core actually leaves IDLE.  The RUN command
        # takes ~1,050 clocks to shift in at clk_per_bit = 32, and the core is
        # halted for all of them -- counting those would drown the signal.
        prev_s, prev_d, started = 0, 0, False
        while True:
            await RisingEdge(dut.clk)
            s = int(core.curr_state.value)
            d = (int(dut.uo_out.value) >> 2) & 1
            h = (int(dut.uo_out.value) >> 1) & 1
            if not started:
                if s == 0:
                    continue
                started = True
            if s == 1 and prev_s != 1:
                c["instr"] += 1
            if d and not prev_d:
                c["done"] += 1
            c["halt"] += h
            prev_s, prev_d = s, d

    t = cocotb.start_soon(sampler())
    await bus.run()
    while c["instr"] < len(prog) + 1:
        await RisingEdge(dut.clk)
    t.cancel()
    await bus.stop()
    dut._log.info(f"SYMPTOM protocol  {len(prog)} instructions in the program, "
                  f"{c['instr'] - 1} retired, {c['done']} done pulses, "
                  f"{c['halt']} clocks with halt high while run was asserted")
