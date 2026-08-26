"""
DD104 — what did the random generator actually cover?

`test_reference.R10` runs eight random programs and compares the result
against `golden.py`.  It is a real test and it finds real things.  This
script measures what it *never* produces, which is the more useful half.

    make gap                    the eight seeds R10 uses, then 1,000 more

No simulator is involved.  It runs the same generator R10 uses — imported
from `test_reference.py`, so there is one copy of it and not two — through
`golden.py`, and counts how many instructions land in each of nine windows.

A **window** is an input condition some bug in the catalogue needs before it
can be seen at all.  `SUB rX, rY` with `rX != rY` is the window for a swapped
subtract: outside it, a backwards SUB gives the right answer.  Bug catalogue
entry, window, and the test that was written on purpose to enter it:

    B01  a SUB whose operands are different AND not 128 apart      R01
    B02  a NAND with two different operands                        R01
    B06  a shift by 2 or 3                                         R03
    B05  a branch with a negative displacement                     R04
    B09  two branches off one comparison                           R05
    B07  a LOAD or STORE at all                                    R06
    B03  a flag-setting result that is non-zero, low nibble zero   R07
    B10  an ORI whose immediate sets a bit r0 already had          R02
    B11  a second ORI, after r0 is no longer zero                  R02

Read the output as two separate findings.  Some windows this generator
enters constantly.  Some it enters rarely.  And some it can never enter,
because the generator does not emit those instructions — no amount of extra
seeds will change a structural zero, and that is the whole argument for
directed tests.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simproc_asm import JMP
from golden import Golden

PARK = JMP(-1)

WINDOWS = [
    ("B01  SUB, operands differ by neither 0 nor 128", "sub_asym"),
    ("B02  NAND with two different operands", "nand_asym"),
    ("B06  shift by 2 or 3", "shift_big"),
    ("B05  branch with a negative displacement", "branch_back"),
    ("B09  two branches off one comparison", "two_branch"),
    ("B07  any LOAD or STORE", "mem_op"),
    ("B03  non-zero result whose low nibble is zero", "z_window"),
    ("B10  ORI that sets a bit r0 already had", "ori_overlap"),
    ("B11  ORI executed while r0 is non-zero", "ori_second"),
]

FLAG_SETTING = (0b0100, 0b0110, 0b1000)      # ADD, SUB, NAND
BRANCHES = (0b0001, 0b0101, 0b1001, 0b1010)  # JMP, BPZ, BNZ, BZ


def scan(prog, limit=200):
    """Run one program through the model and count window entries."""
    hits = {key: 0 for _, key in WINDOWS}
    g = Golden(list(prog) + [PARK])
    end = len(prog)
    prev_was_branch = False
    for _ in range(limit):
        if g.pc >= end:                 # reached the parking JMP
            break
        instr = g.mem[g.pc]
        op4, op3 = instr & 0xF, instr & 0x7
        rA, rB = (instr >> 6) & 3, (instr >> 4) & 3
        a, b = g.regs[rA], g.regs[rB]
        r0_before = g.regs[0]

        if op3 == 0b011:
            if (instr >> 3) & 3 in (2, 3):
                hits["shift_big"] += 1
        elif op3 == 0b111:
            imm = (instr >> 3) & 0x1F
            if r0_before & imm:
                hits["ori_overlap"] += 1
            if r0_before:
                hits["ori_second"] += 1
        elif op4 == 0b0110 and ((a - b) & 0xFF) != ((b - a) & 0xFF):
            hits["sub_asym"] += 1
        elif op4 == 0b1000 and a != b:
            hits["nand_asym"] += 1
        elif op4 in (0b0000, 0b0010):
            hits["mem_op"] += 1

        if op4 in BRANCHES:
            disp = (instr >> 4) & 0xF
            if disp >= 8:
                hits["branch_back"] += 1
            if prev_was_branch:
                hits["two_branch"] += 1

        result = g.step()
        if isinstance(result, str):
            break

        # The Z window is a property of the RESULT, so it is read after the step.
        if op3 == 0b011 or op3 == 0b111 or op4 in FLAG_SETTING:
            dest = 0 if op3 == 0b111 else rA
            v = g.regs[dest]
            if v != 0 and (v & 0xF) == 0:
                hits["z_window"] += 1

        prev_was_branch = op4 in BRANCHES
    return hits


def sweep(seeds, generator):
    total = {key: 0 for _, key in WINDOWS}
    programs = {key: 0 for _, key in WINDOWS}
    instructions = 0
    for seed in seeds:
        prog = generator(seed)
        instructions += len(prog)
        hits = scan(prog)
        for key, n in hits.items():
            total[key] += n
            programs[key] += 1 if n else 0
    return total, programs, instructions


def report(title, seeds, generator):
    total, programs, instructions = sweep(seeds, generator)
    n = len(seeds)
    print(f"\n{title}")
    print("-" * 72)
    print(f"{'window':<52}{'entered':>9}{'programs':>11}")
    for label, key in WINDOWS:
        mark = "  " if total[key] else " *"
        print(f"{mark}{label:<50}{total[key]:>9}{programs[key]:>7} of {n}")
    print("-" * 72)
    cold = [label for label, key in WINDOWS if not total[key]]
    print(f"{n} programs, {instructions} instructions written, "
          f"{len(cold)} of {len(WINDOWS)} windows never entered")
    return cold


if __name__ == "__main__":
    from test_reference import random_program

    print("=" * 72)
    print(" GAP   what the random generator covers, and what it cannot")
    print("=" * 72)

    report("the eight seeds R10 actually runs", range(8), random_program)
    cold = report("one thousand seeds", range(1000), random_program)

    print("\nA window still cold after a thousand programs is not bad luck.")
    print("Read `random_program` in test_reference.py and you will find the")
    print("reason written in its docstring: it emits no LOAD and no STORE, and")
    print("no backward branches, because a random address is usually outside")
    print("the 64-byte RAM and a random loop is an infinite loop.")
    print("\nThose exclusions are correct. They are also the exact shape of")
    print("what you must write by hand:")
    for label in cold:
        print(f"    {label}")
    print("\nAnd one more, which no count on this page can show you: R10")
    print("compares REGISTERS only. Every flag window it enters is invisible")
    print("to it anyway. Coverage of the stimulus and coverage of the check")
    print("are two different questions, and you have to ask both.")
