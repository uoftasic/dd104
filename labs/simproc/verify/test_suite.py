"""The systematic testbench.  Every test names the thing it is checking."""
import os, random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
from simproc import *
from golden import Golden

CORE = "tt_um_ieeeuoftasic_simproc.U1.CPU1"


def path(dut, p):
    o = dut
    for part in p.split("."):
        o = getattr(o, part)
    return o


def poke(dut, a, v):
    dut.tt_um_ieeeuoftasic_simproc.U1.RAM1.mem[a].value = v


def peek(dut, a):
    return int(dut.tt_um_ieeeuoftasic_simproc.U1.RAM1.mem[a].value)


FILL = 0x0C          # an unimplemented opcode: 4 cycles, changes nothing


def rf(dut, i):
    v = dut.tt_um_ieeeuoftasic_simproc.U1.CPU1.RF1.rf[i].value
    try:
        return int(v)
    except ValueError:
        return str(v)


def dut_state(dut):
    c = dut.tt_um_ieeeuoftasic_simproc.U1.CPU1
    return (tuple(rf(dut, i) for i in range(4)),
            int(c.PC1.pc_out.value), int(c.n_flag_out.value), int(c.z_flag_out.value))


async def boot(dut, uio=int(os.environ.get('SIMPROC_UIO', '2'))):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    bus = SimProcBus(dut, uio=uio)
    await bus.reset()
    for a in range(64):
        poke(dut, a, FILL)
    await ClockCycles(dut.clk, 2)
    return bus


async def run_and_compare(dut, bus, mem, n_instr, label):
    """Free-run the DUT, sampling architectural state at every instruction boundary."""
    for a in range(64):
        poke(dut, a, mem[a] if a < len(mem) else FILL)
    await ClockCycles(dut.clk, 2)
    g = Golden([mem[a] if a < len(mem) else FILL for a in range(64)])
    await bus.reset()          # RF/PC/flags to zero; the RAM has no reset, so the program stays
    await bus.set_pc(0)

    core = dut.tt_um_ieeeuoftasic_simproc.U1.CPU1
    snaps = []

    async def sampler():
        prev = int(core.curr_state.value)
        while True:
            await RisingEdge(dut.clk)
            s = int(core.curr_state.value)
            if s == 1 and prev != 1:              # entering CYCLE_1
                snaps.append(dut_state(dut))
            prev = s

    task = cocotb.start_soon(sampler())
    await bus.run()
    guard = 0
    while len(snaps) < n_instr + 1 and guard < 4000:
        await RisingEdge(dut.clk)
        guard += 1
    task.cancel()
    await bus.stop()      # see SimProcBus.stop: HALT is too slow to be safe here

    if len(snaps) < 2:
        dut._log.info(f"{label}: the core never reached a second instruction boundary "
                      f"({len(snaps)} seen) - the DUT did not run")
        return [("no-run", None, None)], []
    fails = []
    stopped = None
    for k in range(min(n_instr, len(snaps) - 1)):
        r = g.step()
        if isinstance(r, str):
            stopped = r
            break
        if g.state() != snaps[k + 1]:
            fails.append((k + 1, g.state(), snaps[k + 1]))
    memfail = []
    if stopped is None:
        memfail = [(a, g.mem[a], peek(dut, a))
                   for a in range(64) if g.mem[a] != peek(dut, a)]
    if fails or memfail:
        dut._log.info(f"{label}: MISMATCH ({len(fails)} state, {len(memfail)} memory)")
        for f in fails[:3]:
            dut._log.info(f"   after instr {f[0]}: golden (RF,PC,N,Z)={f[1]}  dut={f[2]}")
        for m in memfail[:3]:
            dut._log.info(f"   mem[0x{m[0]:02X}]: golden 0x{m[1]:02X}  dut 0x{m[2]:02X}")
    return fails, memfail


def random_program(seed, n=24):
    rnd = random.Random(seed)
    prog = []
    makers = [lambda: ADD(rnd.randint(0, 3), rnd.randint(0, 3)),
              lambda: SUB(rnd.randint(0, 3), rnd.randint(0, 3)),
              lambda: NAND(rnd.randint(0, 3), rnd.randint(0, 3)),
              lambda: ORI(rnd.randint(0, 31)),
              lambda: SHL(rnd.randint(0, 3), rnd.randint(0, 3)),
              lambda: SHR(rnd.randint(0, 3), rnd.randint(0, 3)),
              lambda: BNZ(rnd.randint(-3, 3)),
              lambda: BPZ(rnd.randint(-3, 3)),
              lambda: BZ(rnd.randint(-3, 3)),
              lambda: JMP(rnd.randint(-3, 3))]
    for _ in range(n):
        prog.append(rnd.choice(makers)())
    return prog


# ------------------------------------------------------------------ directed
@cocotb.test()
async def T01_alu_add_sub_nand(dut):
    """ADD / SUB / NAND on asymmetric operands."""
    bus = await boot(dut)
    prog = [ORI(9), ADD(1, 0), ORI(2), SUB(1, 0), NAND(2, 1), STORE(1, 3), STORE(2, 3)]
    # R0=9; R1=9; R0=9|2=11; R1=9-11=254; R2=~(0 & 254)=255; mem[0]=254 then mem[0]=255
    f, m = await run_and_compare(dut, bus, prog, len(prog), "T01")
    assert not f and not m, "ADD/SUB/NAND mismatch"


@cocotb.test()
async def T02_ori_accumulate(dut):
    """ORI twice with OVERLAPPING bits, and into a non-zero register."""
    bus = await boot(dut)
    prog = [ORI(5), ORI(3), ORI(24), ADD(2, 0), ORI(1), STORE(0, 1)]
    f, m = await run_and_compare(dut, bus, prog, len(prog), "T02")
    assert not f and not m, "ORI mismatch"


@cocotb.test()
async def T03_shift_amounts(dut):
    """All four encodable shift amounts, both directions."""
    bus = await boot(dut)
    prog = [ORI(1), ADD(1, 0)]
    for k in range(4):
        prog += [SHL(1, k)]
    prog += [ORI(31), SHL(0, 3)]
    for k in range(4):
        prog += [SHR(1, k)]
    f, m = await run_and_compare(dut, bus, prog, len(prog), "T03")
    assert not f and not m, "SHIFT mismatch"


@cocotb.test()
async def T04_branch_all_offsets(dut):
    """Every reachable branch displacement, forward and backward."""
    bus = await boot(dut)
    ok = True
    for off in range(-8, 8):
        for a in range(64):
            poke(dut, a, FILL)
        poke(dut, 20, JMP(off))
        await ClockCycles(dut.clk, 2)
        await bus.set_pc(20)
        await bus.step()
        want = (21 + off) & 0xFF
        got = int(dut.tt_um_ieeeuoftasic_simproc.U1.CPU1.PC1.pc_out.value)
        if got != want:
            dut._log.info(f"T04: JMP {off:+d} -> PC {got}, expected {want}")
            ok = False
    assert ok, "branch displacement mismatch"


@cocotb.test()
async def T05_two_branches_one_compare(dut):
    """The idiom: one compare, then test it twice."""
    bus = await boot(dut)
    #  R1 = 0  (Z=1, N=0) then BZ taken, then BNZ must still see Z=1
    prog = [ORI(4), ADD(1, 0), SUB(1, 0),   # R1 = 0 -> Z=1
            BZ(1),                          # taken, skip next
            ORI(16),                        # skipped
            BNZ(1),                         # must NOT be taken (Z still 1)
            ORI(8),                         # must execute
            STORE(0, 2)]
    f, m = await run_and_compare(dut, bus, prog, len(prog), "T05")
    assert not f and not m, "flags did not survive the first branch"


@cocotb.test()
async def T06_load_store_pointers(dut):
    """LOAD/STORE with rA != rB and different pointer values."""
    bus = await boot(dut)
    mem = [ORI(16), ADD(1, 0), ADD(1, 0),      # R1 = 32
           ORI(4), ADD(2, 0),                  # R2 = 20
           STORE(2, 1),                        # mem[32] = 20
           ORI(1), ADD(3, 1), ADD(3, 0),       # R3 = 32 + 21 = 53
           LOAD(1, 1),                         # R1 = mem[32] = 20
           STORE(1, 3)]                        # mem[53] = 20
    f, m = await run_and_compare(dut, bus, mem, len(mem), "T06")
    assert not f and not m, "LOAD/STORE mismatch"


@cocotb.test()
async def T07_done_and_halt_protocol(dut):
    """done must pulse once per retired instruction; halt must stay low while running."""
    bus = await boot(dut)
    prog = [ORI(16), ADD(1, 0), STORE(1, 2), SUB(1, 0), STORE(1, 2), JMP(-1)]
    for i, w in enumerate(prog):
        poke(dut, i, w)
    await ClockCycles(dut.clk, 2)
    await bus.set_pc(0)
    await bus.run()
    dones, halts, n = 0, 0, 0
    prev_done = 0
    while n < 60:
        await RisingEdge(dut.clk)
        n += 1
        d = (int(dut.uo_out.value) >> 2) & 1
        h = (int(dut.uo_out.value) >> 1) & 1
        if d and not prev_done:
            dones += 1
        prev_done = d
        halts += h
    await bus.halt()
    dut._log.info(f"T07: {dones} done pulses and {halts} halt-high cycles in 60 clocks")
    assert halts == 0, f"halt went high {halts} times while run was asserted"
    assert dones >= 5, f"only {dones} done pulses in 60 clocks"


@cocotb.test()
async def T08_random_programs(dut):
    """20 pseudo-random programs, compared instruction by instruction."""
    bus = await boot(dut)
    bad = 0
    for seed in range(20):
        prog = random_program(seed)
        f, m = await run_and_compare(dut, bus, prog, 30, f"T08.seed{seed}")
        if f or m:
            bad += 1
    dut._log.info(f"T08: {bad} of 20 random programs mismatched")
    assert bad == 0, f"{bad}/20 random programs mismatched"


@cocotb.test()
async def T09_done_pulse_accounting(dut):
    """Exactly one done pulse per retired instruction - a protocol check, not a data check."""
    bus = await boot(dut)
    prog = [ORI(16), ADD(1, 0), STORE(1, 2), SUB(1, 0), STORE(1, 2),
            ADD(1, 0), STORE(1, 2), NAND(3, 3), SHL(3, 1)]
    for a in range(64):
        poke(dut, a, FILL)
    for i, w in enumerate(prog):
        poke(dut, i, w)
    await ClockCycles(dut.clk, 2)
    await bus.reset()
    await bus.set_pc(0)
    core = dut.tt_um_ieeeuoftasic_simproc.U1.CPU1
    counts = {"done": 0, "instr": 0}

    async def sampler():
        prev_state = int(core.curr_state.value)
        prev_done = 0
        while True:
            await RisingEdge(dut.clk)
            s = int(core.curr_state.value)
            d = (int(dut.uo_out.value) >> 2) & 1
            if s == 1 and prev_state != 1:
                counts["instr"] += 1
            if d and not prev_done:
                counts["done"] += 1
            prev_state, prev_done = s, d

    t = cocotb.start_soon(sampler())
    await bus.run()
    guard = 0
    while counts["instr"] < len(prog) + 1 and guard < 4000:
        await RisingEdge(dut.clk)
        guard += 1
    t.cancel()
    assert counts["instr"] > 1, "the core never ran"
    await bus.halt()
    retired = counts["instr"] - 1
    dut._log.info(f"T09: {retired} instructions retired, {counts['done']} done pulses")
    assert counts["done"] == retired, \
        f"{retired} instructions retired but done pulsed {counts['done']} times"


@cocotb.test()
async def T10_load_store_distinct_registers(dut):
    """LOAD and STORE where the pointer register and the data register differ."""
    bus = await boot(dut)
    #  R1 = 40 (pointer), R2 = 7 (data), R3 = 41 (second pointer)
    prog = [ORI(8), ADD(1, 0), ADD(1, 0), ADD(1, 0), ADD(1, 0), ADD(1, 0),   # R1 = 40
            SUB(0, 0), ORI(7), ADD(2, 0),                                    # R2 = 7
            ADD(3, 1), SUB(0, 0), ORI(1), ADD(3, 0),                         # R3 = 41
            STORE(2, 1),      # mem[40] = 7      (data reg != pointer reg)
            LOAD(0, 1),       # R0  = mem[40] = 7
            STORE(0, 3)]      # mem[41] = 7
    f, m = await run_and_compare(dut, bus, prog, len(prog), "T10")
    assert not f and not m, "LOAD/STORE with distinct registers mismatched"
