"""DD104 — every entry point in `labs/common`, once, with its answer printed.

    make sim TB=test_api_tour

Nine tests, one per area of the API.  Nothing here is a good test: they assert
almost nothing and they prove almost nothing about the design.  They exist so
that `docs/reference/the-harness-api.md` can show you a worked example of each
call and the exact line it produces, and so that page cannot drift away from
the code — if a signature changes, this file stops running.

Read `test_example.py` for tests worth copying.  Read this one to find out
what you are allowed to ask for.
"""

import cocotb
from cocotb.triggers import RisingEdge

from simproc import SimProc, bit, trace, PARK, FILLER, MEM_DEPTH, CMD_PING
from simproc_asm import (ORI, ADD, SUB, NAND, SHL, SHR, LOAD, STORE,
                         JMP, BZ, BNZ, BPZ, UNIMP,
                         set_reg, assemble, listing, disasm)
from golden import Golden, compare_memory


@cocotb.test()
async def a01_construct_start_and_reset(dut):
    """SimProc(dut) -- start() -- reset()."""
    sp = SimProc(dut, clock_ns=10, uio=8)
    await sp.start()                       # clock, reset, RAM <- 0x0C, UART monitor

    dut._log.info(f"clock period {sp.clock_ns} ns; uio={sp.uio} so "
                  f"clk_per_bit={sp.clk_per_bit}")
    dut._log.info(f"after start(): {sp.describe()}")
    dut._log.info(f"RAM filler is 0x{FILLER:02X}, RAM depth is {MEM_DEPTH}, "
                  f"the parking instruction is 0x{PARK:02X} = {disasm(PARK)}")

    sp.poke(0, 0x5A)
    await sp.reset()                       # clears regs/PC/flags, NOT the RAM
    dut._log.info(f"after reset(): {sp.describe()}, and mem[0] is still "
                  f"0x{sp.peek(0):02X}")
    assert sp.peek(0) == 0x5A


@cocotb.test()
async def a02_the_backdoor(dut):
    """poke() -- peek() -- load() -- memory().

    Note the first two log lines. `poke()` writes a simulator signal, and a
    signal written at time T is not readable until the simulator has stepped.
    Read it back in the same instant and you get the OLD value, with no error
    and no warning. `load()` ends with two clock cycles for exactly this
    reason; a bare `poke()` does not, so put a trigger between a poke and the
    peek that checks it."""
    sp = SimProc(dut)
    await sp.start()

    sp.poke(0x30, 0xA5)
    dut._log.info(f"poke(0x30, 0xA5), peek(0x30) in the same instant -> "
                  f"0x{sp.peek(0x30):02X}   <- the OLD value")
    await RisingEdge(dut.clk)
    dut._log.info(f"one clock later, peek(0x30) -> 0x{sp.peek(0x30):02X}")
    assert sp.peek(0x30) == 0xA5

    park = await sp.load([ORI(5), ADD(1, 0)])
    dut._log.info(f"load() put the program at 0..1 and the parking loop at "
                  f"{park} (0x{sp.peek(park):02X} = {disasm(sp.peek(park))})")

    nonfiller = {a: v for a, v in sp.memory(0, 8).items() if v != FILLER}
    dut._log.info(f"memory(0, 8) minus the filler: "
                  + " ".join(f"{a}:0x{v:02X}" for a, v in nonfiller.items()))

    try:
        sp.poke(64, 0)
    except IndexError as e:
        dut._log.info(f"poke(64, 0) raises: {str(e).splitlines()[0]}")


@cocotb.test()
async def a03_reading_the_machine(dut):
    """reg() regs() pc() flags() fsm() halt done snapshot() describe()."""
    sp = SimProc(dut)
    await sp.start()
    await sp.run(set_reg(1, 200))

    dut._log.info(f"reg(1)   -> {sp.reg(1)}")
    dut._log.info(f"regs()   -> {sp.regs()}")
    dut._log.info(f"pc()     -> {sp.pc()}")
    dut._log.info(f"flags()  -> {sp.flags()}     (N, Z)")
    dut._log.info(f"fsm()    -> {sp.fsm()}")
    dut._log.info(f"halt     -> '{sp.halt}'   done -> '{sp.done}'")
    dut._log.info(f"snapshot() -> {sp.snapshot()}")
    dut._log.info(f"describe() -> {sp.describe()}")
    dut._log.info(f"bit(dut.uo_out, 0) -> '{bit(dut.uo_out, 0)}'  "
                  f"(the UART TX pin, idle high)")


@cocotb.test()
async def a04_making_it_go(dut):
    """run() -- step() -- run_cycles() -- set_pc()."""
    sp = SimProc(dut)
    await sp.start()

    cycles = await sp.run([ORI(5), ADD(1, 0)])
    dut._log.info(f"run([ORI(5), ADD(1,0)]) -> {cycles} cycles, r1 = {sp.reg(1)}"
                  f"   (ORI is 5, ADD is 4)")

    await sp.load([ORI(1), ORI(2), ORI(4)])
    await sp.set_pc(0)
    await sp.step(1)
    dut._log.info(f"after step(1):  r0 = {sp.reg(0)}, PC = {sp.pc()}, "
                  f"state {sp.fsm()}")
    await sp.step(2)
    dut._log.info(f"after step(2) more: r0 = {sp.reg(0)}, PC = {sp.pc()}")

    await sp.load([ORI(1), ORI(2), ORI(4), ORI(8)])
    await sp.set_pc(0)
    await sp.run_cycles(10)
    dut._log.info(f"after run_cycles(10): r0 = {sp.reg(0)}, PC = {sp.pc()}")

    # ...and the thing that is NOT obvious about it.  40 unimplemented opcodes,
    # 3 cycles each and no parking loop, so the PC is a clock.
    await sp.load([UNIMP()] * 40, park=False)
    await sp.set_pc(0)
    await sp.run_cycles(10)
    dut._log.info(f"same call on a program that does NOT park: PC = {sp.pc()}. "
                  f"Ten clocks of 3-cycle instructions is PC = 3 -- and it is "
                  f"not 3, because run_cycles COUNTS ten cycles and then asks "
                  f"for a halt, and the halt is a UART command in flight while "
                  f"the core keeps going.")


@cocotb.test()
async def a05_protocol_counters(dut):
    """count_done_pulses() -- count_halt_cycles()."""
    sp = SimProc(dut)
    await sp.start()

    prog = [ORI(1), ADD(1, 0), SUB(2, 2), NAND(3, 3)]
    await sp.load(prog)
    await sp.set_pc(0)
    pulses = await sp.count_done_pulses(17)      # 5 + 4 + 4 + 4
    dut._log.info(f"count_done_pulses(17) over {len(prog)} instructions "
                  f"-> {pulses}")

    await sp.load(prog)
    await sp.set_pc(0)
    high = await sp.count_halt_cycles(17)
    dut._log.info(f"count_halt_cycles(17) -> {high}   "
                  f"(a running core must never be in IDLE)")

    await sp.load([UNIMP(), UNIMP()])
    await sp.set_pc(0)
    pulses = await sp.count_done_pulses(6)
    dut._log.info(f"two unimplemented opcodes, 6 clocks -> {pulses} done "
                  f"pulses: 0x{UNIMP():02X} retires nothing")


@cocotb.test()
async def a06_the_wire(dut):
    """uart_ping() uart_write() uart_read() uart_get_pc() set_baud() send_byte()."""
    sp = SimProc(dut)
    await sp.start()

    dut._log.info(f"uart_ping()      -> 0x{await sp.uart_ping():02X}")
    await sp.uart_write(0x21, 0x3C)
    dut._log.info(f"uart_write(0x21, 0x3C) then uart_read(0x21) -> "
                  f"0x{await sp.uart_read(0x21):02X}")
    await sp.set_pc(9)
    dut._log.info(f"set_pc(9) then uart_get_pc() -> {await sp.uart_get_pc()}")

    await sp.set_baud(16)                    # clk_per_bit = 64
    dut._log.info(f"set_baud(16): clk_per_bit is now {sp.clk_per_bit}; "
                  f"uart_ping() -> 0x{await sp.uart_ping():02X}")
    await sp.set_baud(8)

    await sp.send_byte(CMD_PING)             # the raw bit-banger, one byte
    await sp.send_byte(0)
    await sp.send_byte(0)
    dut._log.info(f"three raw send_byte() calls -> recv_byte() "
                  f"0x{await sp.recv_byte():02X}")


@cocotb.test()
async def a07_the_assembler(dut):
    """instruction helpers -- set_reg() -- assemble() -- listing() -- disasm()."""
    sp = SimProc(dut)
    await sp.start()

    for word, name in ((ORI(5), "ORI(5)"), (ADD(1, 0), "ADD(1, 0)"),
                       (SUB(2, 3), "SUB(2, 3)"), (NAND(1, 1), "NAND(1, 1)"),
                       (SHL(0, 3), "SHL(0, 3)"), (SHR(0, 1), "SHR(0, 1)"),
                       (LOAD(0, 1), "LOAD(0, 1)"), (STORE(1, 2), "STORE(1, 2)"),
                       (JMP(-1), "JMP(-1)"), (BZ(2), "BZ(2)"),
                       (BNZ(-3), "BNZ(-3)"), (BPZ(1), "BPZ(1)"),
                       (UNIMP(), "UNIMP()")):
        dut._log.info(f"  {name:<12} -> 0x{word:02X}   {disasm(word)}")

    dut._log.info("set_reg(1, 0xB7) is six instructions:\n" +
                  listing(set_reg(1, 0xB7)))

    prog = assemble("""
            SUB   r1, r1
    top:    ORI   1
            BZ    top
            SUB   r3, r3
    """)
    dut._log.info("assemble() resolves the labels:\n" + listing(prog))

    await sp.run(set_reg(1, 0xB7))
    assert sp.reg(1) == 0xB7, f"set_reg built {sp.reg(1)}, expected 183"
    dut._log.info(f"and the hardware agrees: r1 = 0x{sp.reg(1):02X}")


@cocotb.test()
async def a08_the_golden_model(dut):
    """Golden -- step() -- run() -- snapshot() -- compare_memory()."""
    sp = SimProc(dut)
    await sp.start()

    prog = set_reg(1, 20) + set_reg(2, 6) + [SUB(1, 2), STORE(1, 2)]
    g = Golden(prog + [PARK])

    cycles, reason = g.run(len(prog))
    dut._log.info(f"Golden.run({len(prog)}) -> {cycles} cycles, reason={reason}")
    dut._log.info(f"Golden.snapshot() -> {g.snapshot()}")

    await sp.run(prog)
    dut._log.info(f"SimProc.snapshot() -> {sp.snapshot()}")

    diffs = compare_memory(g, sp)
    dut._log.info(f"compare_memory() -> {diffs}   (an empty list is the good "
                  f"answer)")
    assert diffs == [], f"memory disagrees at {diffs}"


@cocotb.test()
async def a09_trace_against_the_model(dut):
    """trace(sp, n, model=g) -- the call that names the first disagreement."""
    sp = SimProc(dut)
    await sp.start()

    prog = set_reg(0, 9) + [ADD(1, 0), SHL(1, 1), NAND(2, 2)]
    g = Golden(prog + [PARK])
    await sp.load(prog)
    await sp.set_pc(0)

    steps, problem = await trace(sp, len(prog), model=g)
    dut._log.info(f"trace() ran {len(steps)} instructions; problem = {problem}")
    for k, addr, word, snap in steps:
        dut._log.info(f"  {k:2d}  @{addr:02d}  0x{word:02X} {disasm(word):<14} "
                      f"regs={snap[0]} PC={snap[1]} N={snap[2]} Z={snap[3]}")
    assert problem is None, problem
