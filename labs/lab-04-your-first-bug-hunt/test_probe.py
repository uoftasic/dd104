"""
DD104 Lab 04 — scratch space for probe programs.

    make probe TB=test_probe

That is the whole point of this file.  `make hunt` and `make verdict` capture
the simulator's output and print a summary of it, so that the verdict stays a
readable table -- which is right for the loop and useless for the one job you
are about to do, which is running a four-instruction program and READING WHAT
CAME OUT.  `make probe` runs exactly the same simulation and swallows nothing:
every print(), every dut._log line, live, in order, plus the underlying
`make -f sim.mk` command in case you want to run it by hand.

`make probe` on its own probes test_lab04.py.  Point it here instead and
test_lab04.py stays a suite instead of filling up with scaffolding you will
delete.  Nothing in this file is ever graded -- `make verdict` only ever runs
TB=test_lab04.

Delete these, write your own, leave them failing, leave them half-written.
It is scratch paper.

────────────────────────────────────────────────────────────────────────────
WHAT YOU CAN READ, AND HOW TO PRINT IT
────────────────────────────────────────────────────────────────────────────
    sp.reg(i)       one register, as an int
    sp.regs()       all four at once, as a tuple -- the highest-value probe
    sp.pc()         the program counter
    sp.flags()      (Z, N)
    sp.peek(a)      one byte of memory, no simulation time spent
    sp.memory()     a dict of the non-filler bytes
    sp.fsm()        the state machine's current state, by name
    sp.halt         sp.done          the pins, as '0' / '1' / 'x'
    sp.describe()   one line of all of it -- the fastest thing to print

An assertion message is a probe too, and a better one: it only prints when
something is wrong.  `assert x == y, f"...{sp.describe()}"` is usually the
right end state for anything you work out in here.
"""

import cocotb

from simproc import SimProc
from simproc_asm import ADD, SHL, LOAD, listing, set_reg


@cocotb.test()
async def p01_what_do_the_registers_do(dut):
    """Question 4 — which register ends up wrong?

    Three one-instruction programs, each printing all four registers. Run
    `make probe TB=test_probe` and read the three lines against each other.
    """
    sp = SimProc(dut)
    await sp.start()

    prog = set_reg(1, 200) + set_reg(2, 60) + [ADD(1, 2)]
    await sp.run(prog)
    print(f"  ADD  r1, r2   ->  regs = {sp.regs()}   (want r1 = 4)")

    await sp.run(set_reg(1, 0x0C) + [SHL(1, 2)])
    print(f"  SHL  r1, 2    ->  regs = {sp.regs()}   (want r1 = 0x30)")

    sp.poke(0x2A, 0x77)
    await sp.run(set_reg(2, 0x2A) + [LOAD(1, 2)])
    print(f"  LOAD r1, r2   ->  regs = {sp.regs()}   (want r1 = 0x77, r2 = 0x2A)")

    # dut._log goes through cocotb's logger, so it is timestamped and it says
    # which test it came from. For anything you might want to find again in a
    # long log, prefer it to print().
    dut._log.info("everything, in one line: %s", sp.describe())

    # And when a program surprises you, print the program. Note how long it
    # is: set_reg() is a MACRO -- it expands to however many instructions this
    # machine needs to get a constant into a register, and "instruction 3" in
    # a trace means the third of THESE, not the third one you wrote.
    print(listing(prog))


@cocotb.test()
async def p02_step_one_instruction_at_a_time(dut):
    """The other shape of probe: stop after every instruction.

    `sp.step(1)` executes exactly one, so you can watch the machine change
    instead of being handed the state forty instructions later.
    """
    sp = SimProc(dut)
    await sp.start()

    prog = set_reg(1, 0x0C) + [SHL(1, 1), SHL(1, 1), ADD(1, 1)]
    await sp.load(prog)
    for n in range(len(prog)):
        await sp.step(1)
        print(f"  after instruction {n}:  pc={sp.pc():2d}  regs={sp.regs()}  "
              f"flags={sp.flags()}")
